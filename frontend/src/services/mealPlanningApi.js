// src/services/mealPlanningApi.js
import axios from 'axios';
import AuthService from './auth.service';
import store from '../store';

// Derive the Meal-Planning base-URL dynamically so that it works in
// both local development and when the app is deployed (e.g. Render).
//
// 1. We start with VUE_APP_API_URL if it exists – this is the same env
//    var used by http.service.js and normally points to
//    "https://your-backend.onrender.com/api" in prod *or*
//    "http://localhost:8000/api" in dev.
// 2. We strip the trailing "/api" segment (because the meal-planning
//    endpoints live at "/meal-planning/api/…" instead of the generic
//    "/api/…" prefix).
// 3. Finally we append "/meal-planning/api".
//
// If the env var isn’t provided we fall back to localhost so that the
// developer experience stays unchanged.

const DEFAULT_API_ROOT = 'http://localhost:8000/api';
const API_ROOT = (process.env.VUE_APP_API_URL || DEFAULT_API_ROOT).replace(/\/api\/?$/, '');
const API_BASE_URL = `${API_ROOT}/meal-planning/api`;

// Create axios instance with base configuration - MATCHING your http.service.js pattern
// Increase timeout to 30 seconds (Render can take ~20-30 s to wake a sleeping service)
// and enable credentials in case cookies are needed.
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// ---------------------------------------------------------------------------
// Render hibernation helper (mirrors logic from http.service.js)
// ---------------------------------------------------------------------------

/**
 * On Render the backend may spin down after a period of inactivity and respond
 * with HTTP 503 for the first request.  This helper shows a user-friendly
 * loading message, repeatedly pings the root URL to wake the service, then
 * retries the original API request once the service is responsive.
 *
 * @param {import('axios').AxiosRequestConfig} originalRequest – The request
 *        config that triggered the 503 so we can replay it once the service
 *        is awake.
 * @returns {Promise<import('axios').AxiosResponse>}
 */
async function handleServiceHibernation(originalRequest) {
  console.log('[MealPlanningApi] Service appears to be hibernating. Attempting to wake up…');

  // Inform the UI (optional – only if the store/ui module exists)
  if (store?.commit) {
    store.commit('ui/setLoading', {
      isLoading: true,
      message: 'Starting meal-planning service… this can take up to 60 s.'
    });
  }

  // Attempt to wake the service with exponential back-off
  const maxAttempts = 4;
  const delays = [5000, 10000, 15000, 20000]; // 5 s, 10 s, 15 s, 20 s

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      console.log(`[MealPlanningApi] Wake-up attempt ${attempt + 1}/${maxAttempts}`);

      if (store?.commit) {
        store.commit('ui/setLoading', {
          isLoading: true,
          message: `Waking meal-planning service… attempt ${attempt + 1}/${maxAttempts}`,
        });
      }

      // Wait for the back-off delay
      await new Promise(resolve => setTimeout(resolve, delays[attempt]));

      // Ping the root of the backend (without /api) – that is enough to wake it
      await axios.get(API_ROOT + '/', {
        timeout: 30000,
        headers: {
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
      });

      // Give the application a couple of seconds to fully boot
      await new Promise(resolve => setTimeout(resolve, 3000));

      console.log('[MealPlanningApi] Service wake-up successful – retrying original request…');
      return api(originalRequest);
    } catch (wakeErr) {
      console.warn(`[MealPlanningApi] Wake-up attempt ${attempt + 1} failed:`, wakeErr?.message || wakeErr);

      // After last failed attempt, fall through to retry the request anyway
      if (attempt === maxAttempts - 1) {
        console.warn('[MealPlanningApi] All wake-up attempts exhausted – proceeding to final retry.');
      }
    }
  }

  // Final attempt with original request – if this still fails we propagate
  try {
    return await api(originalRequest);
  } finally {
    if (store?.commit) {
      store.commit('ui/setLoading', { isLoading: false });
    }
  }
}

// Add request interceptor for authentication - SAME as your http.service.js
api.interceptors.request.use(
  config => {
    const token = getAccessToken();
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token;
    }
    return config;
  },
  error => {
    console.error('Meal Planning API request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling - SAME as your http.service.js
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    // -------------------------------------------------------------
    // Gracefully handle Render hibernation (HTTP 503) and bad gateway (502)
    // -------------------------------------------------------------
    if (error.response?.status === 503 && !originalRequest._hibernation_retry) {
      originalRequest._hibernation_retry = true;
      return handleServiceHibernation(originalRequest);
    }

    if (error.response?.status === 502 && !originalRequest._gateway_retry) {
      originalRequest._gateway_retry = true;
      console.log('[MealPlanningApi] Gateway error – retrying in 5 s…');
      await new Promise(resolve => setTimeout(resolve, 5000));
      return api(originalRequest);
    }

    // -------------------------------------------------------------
    // Authentication – refresh the JWT on 401, same as before
    // -------------------------------------------------------------
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const response = await AuthService.refreshToken();
        if (response?.access) {
          originalRequest.headers['Authorization'] = 'Bearer ' + response.access;

          if (store?.state?.auth?.status?.loggedIn) {
            await store.dispatch('auth/refreshToken', response.access);
          }
          return axios(originalRequest);
        }
      } catch (refreshError) {
        AuthService.logout();

        if (store?.state?.auth?.status?.loggedIn) {
          store.commit('auth/logout');
        }
        setTimeout(() => {
          window.location.href = '/login';
        }, 100);
        return Promise.reject(refreshError);
      }
    }
    // Enhanced diagnostic output (align with http.service.js)
    if (error.response) {
      const errorInfo = {
        status: error.response.status,
        statusText: error.response.statusText,
        url: error.config?.url,
        method: error.config?.method,
        data: error.response.data,
        headers: error.response.headers,
      };

      if (error.response.status === 503) {
        console.error('[MealPlanningApi] Service hibernation detected:', errorInfo);
      } else if (error.response.status === 502) {
        console.error('[MealPlanningApi] Gateway error:', errorInfo);
      } else {
        console.error('[MealPlanningApi] API error:', errorInfo);
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('[MealPlanningApi] Request timeout:', error.message);
    } else {
      console.error('[MealPlanningApi] Network error:', error.message);
    }

    return Promise.reject(error);
  }
);

/**
 * Get the current access token from store or storage - SAME as your http.service.js
 * @returns {string|null} Access token or null
 */
function getAccessToken() {
  // Try to get token from store
  if (store?.state?.auth?.user?.access) {
    return store.state.auth.user.access;
  }
  const user = AuthService.getCurrentUser();
  return user?.access || null;
}

export const mealPlanningApi = {
  // Expose the api instance for advanced usage
  api,

  // Recipe endpoints
  getRecipes(params = {}) {
    return api.get('/recipes/', { params })
  },

  getRecipe(id) {
    return api.get(`/recipes/${id}/`)
  },

  searchRecipes(searchData) {
    return api.post('/recipes/search/', searchData)
  },

  rateRecipe(recipeId, rating, review = '') {
    return api.post(`/recipes/${recipeId}/rate/`, { rating, review })
  },

  // Enhanced recipe methods for AI features (with fallbacks)
  async generateRecipe(recipeParams) {
    try {
      return await api.post('/recipes/generate/', recipeParams)
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Recipe generation endpoint not implemented yet')
        return Promise.reject(new Error('Recipe generation feature coming soon'))
      }
      throw error
    }
  },

  async getIngredientSubstitutions(recipeId, ingredientName, options = {}) {
    try {
      return await api.post(`/recipes/${recipeId}/substitute-ingredient/`, {
        ingredient_name: ingredientName,
        ...options
      })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Ingredient substitution endpoint not implemented yet')
        return Promise.reject(new Error('Ingredient substitution feature coming soon'))
      }
      throw error
    }
  },

  async scaleRecipe(recipeId, newServings) {
    try {
      return await api.post(`/recipes/${recipeId}/scale/`, { servings: newServings })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Recipe scaling endpoint not implemented yet')
        return Promise.reject(new Error('Recipe scaling feature coming soon'))
      }
      throw error
    }
  },

  // Ingredient endpoints
  getIngredients(params = {}) {
    return api.get('/ingredients/', { params })
  },

  getIngredient(id) {
    return api.get(`/ingredients/${id}/`)
  },

  // Nutrition Profile endpoints with improved error handling
  async getNutritionProfile() {
    try {
      return await api.get('/nutrition-profile/current/')
    } catch (error) {
      if (error.response?.status === 404) {
        // Return a default profile structure if none exists
        return {
          data: {
            calorie_target: 2000,
            protein_target: 100,
            carb_target: 250,
            fat_target: 67,
            dietary_preferences: [],
            allergies_intolerances: [],
            cuisine_preferences: []
          }
        }
      }
      throw error
    }
  },

  async updateNutritionProfile(profileData) {
    try {
      // Try PATCH first (most RESTful)
      return await api.patch('/nutrition-profile/current/', profileData)
    } catch (error) {
      if (error.response?.status === 405) {
        // If PATCH not allowed, try PUT
        try {
          return await api.put('/nutrition-profile/current/', profileData)
        } catch (putError) {
          if (putError.response?.status === 405) {
            // If PUT also not allowed, try POST
            return await api.post('/nutrition-profile/update_profile/', profileData)
          }
          throw putError
        }
      }
      throw error
    }
  },

  calculateNutritionTargets() {
    return api.post('/nutrition-profile/calculate_targets/')
  },

  // Enhanced Meal Plan endpoints with AI features and fallbacks
  getMealPlans(params = {}) {
    return api.get('/meal-plans/', { params })
  },

  getMealPlan(id) {
    return api.get(`/meal-plans/${id}/`)
  },

  generateMealPlan(planData) {
    // Enhanced meal plan generation with AI features
    return api.post('/meal-plans/generate/', planData)
  },

  async regenerateMeal(planId, day, mealType) {
    try {
      // Updated regenerate meal endpoint
      return await api.post(`/meal-plans/${planId}/regenerate_meal/`, {
        day: day,
        meal_type: mealType
      })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Meal regeneration endpoint not implemented yet')
        return Promise.reject(new Error('Meal regeneration feature coming soon'))
      }
      throw error
    }
  },

  // New AI-powered methods with fallbacks
  async getMealAlternatives(planId, day, mealType, count = 3) {
    try {
      return await api.post(`/meal-plans/${planId}/get_alternatives/`, {
        day: day,
        meal_type: mealType,
        count: count
      })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Meal alternatives endpoint not implemented yet')
        return { data: [] }
      }
      throw error
    }
  },

  async swapMeal(planId, day, mealType, newRecipe) {
    try {
      return await api.post(`/meal-plans/${planId}/swap_meal/`, {
        day: day,
        meal_type: mealType,
        new_recipe: newRecipe
      })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Meal swap endpoint not implemented yet')
        return Promise.reject(new Error('Meal swap feature coming soon'))
      }
      throw error
    }
  },

  async analyzeMealPlan(planId) {
    try {
      return await api.get(`/meal-plans/${planId}/analyze/`)
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Meal plan analysis endpoint not implemented yet')
        // Return mock analysis data for development
        return {
          data: {
            overall_score: 75,
            nutritional_adequacy: {
              calories: { status: 'adequate', percentage_of_target: 98 },
              protein: { status: 'adequate', percentage_of_target: 105 },
              carbs: { status: 'adequate', percentage_of_target: 92 },
              fat: { status: 'adequate', percentage_of_target: 103 }
            },
            meal_distribution: {
              breakfast_percentage: 25,
              lunch_percentage: 35,
              dinner_percentage: 40,
              balance_rating: 'excellent'
            },
            variety_analysis: {
              cuisine_diversity: 'good',
              ingredient_variety: 'excellent',
              cooking_method_diversity: 'good'
            },
            recommendations: [
              'Consider adding more fiber-rich vegetables',
              'Excellent protein distribution throughout the day'
            ],
            health_highlights: [
              'Well-balanced macronutrients',
              'Good variety of nutrient-dense foods'
            ],
            areas_for_improvement: [
              'Could increase omega-3 fatty acids'
            ]
          }
        }
      }
      throw error
    }
  },

  deleteMealPlan(planId) {
    return api.delete(`/meal-plans/${planId}/`)
  },

  generateShoppingList(planId, options = {}) {
    return api.post(`/meal-plans/${planId}/generate_shopping_list/`, {
      exclude_items: options.exclude_ingredients || [],
      group_by_category: options.group_by_category !== false,
      ...options
    })
  },

  // Nutrition Log endpoints
  getNutritionLogs(params = {}) {
    return api.get('/nutrition-logs/', { params })
  },

  getNutritionLog(id) {
    return api.get(`/nutrition-logs/${id}/`)
  },

  logNutrition(nutritionData) {
    return api.post('/nutrition-logs/', nutritionData)
  },

  analyzeNutrition(analysisData) {
    return api.post('/nutrition-logs/analyze/', analysisData)
  },

  getNutritionAnalytics(params = {}) {
    return api.get('/nutrition-logs/analytics/', { params })
  },

  getDashboardData() {
    return api.get('/nutrition-logs/dashboard_data/')
  },

  // New AI insights and recommendations with fallbacks
  async getNutritionInsights(params = {}) {
    try {
      return await api.get('/ai-insights/', { params })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('AI insights endpoint not implemented yet')
        return { data: [] }
      }
      throw error
    }
  },

  async getMealRecommendations(params = {}) {
    try {
      return await api.get('/recommendations/', { params })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Meal recommendations endpoint not implemented yet')
        return { data: [] }
      }
      throw error
    }
  },

  // Utility endpoints with fallbacks
  async calculateNutrition(ingredients, servings) {
    try {
      return await api.post('/calculate-nutrition/', {
        ingredients: ingredients,
        servings: servings
      })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Nutrition calculation endpoint not implemented yet')
        // Return mock calculation for development
        return {
          data: {
            calories: 400,
            protein: 25,
            carbs: 45,
            fat: 15
          }
        }
      }
      throw error
    }
  },

  async validateDietaryRestrictions(ingredients, dietaryPreferences, allergies) {
    try {
      return await api.post('/validate-dietary/', {
        ingredients: ingredients,
        dietary_preferences: dietaryPreferences,
        allergies: allergies
      })
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Dietary validation endpoint not implemented yet')
        return {
          data: {
            is_compliant: true,
            violations: [],
            warnings: []
          }
        }
      }
      throw error
    }
  },

  async getDietaryPreferences() {
    try {
      return await api.get('/dietary-preferences/')
    } catch (error) {
      if (error.response?.status === 404) {
        // Return default dietary preferences
        return {
          data: [
            'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo',
            'mediterranean', 'low_carb', 'low_fat', 'high_protein',
            'gluten_free', 'dairy_free', 'low_sodium', 'diabetic',
            'heart_healthy', 'whole30'
          ]
        }
      }
      throw error
    }
  },

  async getAllergens() {
    try {
      return await api.get('/allergens/')
    } catch (error) {
      if (error.response?.status === 404) {
        // Return default allergens list
        return {
          data: [
            'milk', 'eggs', 'fish', 'shellfish', 'tree_nuts',
            'peanuts', 'wheat', 'soybeans', 'sesame', 'sulfites'
          ]
        }
      }
      throw error
    }
  },

  async getCuisines() {
    try {
      return await api.get('/cuisines/')
    } catch (error) {
      if (error.response?.status === 404) {
        // Return default cuisines list
        return {
          data: [
            'american', 'italian', 'mexican', 'chinese', 'japanese',
            'indian', 'thai', 'mediterranean', 'french', 'greek',
            'middle_eastern', 'korean', 'vietnamese', 'spanish'
          ]
        }
      }
      throw error
    }
  }
}

// Enhanced helper functions remain the same as before
export const mealPlanningHelpers = {
  // All your existing helper functions...
  formatDietaryPreference(preference) {
    return preference
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  },

  formatCuisine(cuisine) {
    return cuisine.charAt(0).toUpperCase() + cuisine.slice(1)
  },

  calculateMacroPercentages(calories, protein, carbs, fat) {
    const totalCalories = calories || (protein * 4 + carbs * 4 + fat * 9)

    if (totalCalories === 0) {
      return { protein: 0, carbs: 0, fat: 0 }
    }

    return {
      protein: Math.round((protein * 4 / totalCalories) * 100),
      carbs: Math.round((carbs * 4 / totalCalories) * 100),
      fat: Math.round((fat * 9 / totalCalories) * 100)
    }
  },

  formatDuration(minutes) {
    if (minutes < 60) {
      return `${minutes}min`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}min` : `${hours}h`
  },

  calculateNutritionScore(actual, target, tolerance = 0.1) {
    if (!target) return 100

    const difference = Math.abs(actual - target)
    const allowedDifference = target * tolerance

    if (difference <= allowedDifference) {
      return 100
    }

    const score = Math.max(0, 100 - (difference / target) * 100)
    return Math.round(score)
  },

  getMacroColor(macro) {
    const colors = {
      protein: '#ff6b6b',
      carbs: '#4ecdc4',
      fat: '#45b7d1'
    }
    return colors[macro] || '#95a5a6'
  },

  formatCalories(calories) {
    if (calories >= 1000) {
      return `${(calories / 1000).toFixed(1)}k`
    }
    return Math.round(calories).toString()
  },

  getDifficultyColor(difficulty) {
    const colors = {
      easy: '#27ae60',
      medium: '#f39c12',
      hard: '#e74c3c'
    }
    return colors[difficulty] || '#95a5a6'
  },

  validateNutritionProfile(profile) {
    const errors = []

    if (!profile.calorie_target || profile.calorie_target < 1000 || profile.calorie_target > 5000) {
      errors.push('Calorie target must be between 1000 and 5000')
    }

    if (!profile.protein_target || profile.protein_target < 0 || profile.protein_target > 500) {
      errors.push('Protein target must be between 0 and 500g')
    }

    if (!profile.carb_target || profile.carb_target < 0 || profile.carb_target > 1000) {
      errors.push('Carbohydrate target must be between 0 and 1000g')
    }

    if (!profile.fat_target || profile.fat_target < 0 || profile.fat_target > 300) {
      errors.push('Fat target must be between 0 and 300g')
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  },

  createMealPlanRequest(options = {}) {
    const defaults = {
      plan_type: 'daily',
      start_date: new Date().toISOString().split('T')[0],
      use_preferences: true,
      regenerate_existing: false
    }

    return { ...defaults, ...options }
  },

  handleApiError(error, fallbackMessage = 'An error occurred') {
    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.message) {
      return error.message
    }
    return fallbackMessage
  }
}

export default mealPlanningApi