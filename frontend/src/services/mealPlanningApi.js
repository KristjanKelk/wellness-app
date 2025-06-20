// src/services/mealPlanningApi.js
import axios from 'axios';
import AuthService from './auth.service';
import store from '../store';

const API_BASE_URL = 'http://localhost:8000/meal-planning/api';

// Create axios instance with base configuration - MATCHING your http.service.js pattern
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

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
    if (error.response) {
      console.error(
        `Meal Planning API Error: ${error.response.status} ${error.response.statusText}`,
        error.response.data
      );
    } else {
      console.error('Meal Planning API Error:', error.message);
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

  // Ingredient endpoints
  getIngredients(params = {}) {
    return api.get('/ingredients/', { params })
  },

  getIngredient(id) {
    return api.get(`/ingredients/${id}/`)
  },

  // Nutrition Profile endpoints
  getNutritionProfile() {
    return api.get('/nutrition-profile/')
  },

  updateNutritionProfile(profileData) {
    return api.put('/nutrition-profile/', profileData)
  },

  calculateNutritionTargets() {
    return api.post('/nutrition-profile/calculate_targets/')
  },

  // Meal Plan endpoints
  getMealPlans(params = {}) {
    return api.get('/meal-plans/', { params })
  },

  getMealPlan(id) {
    return api.get(`/meal-plans/${id}/`)
  },

  generateMealPlan(planData) {
    return api.post('/meal-plans/generate/', planData)
  },

  regenerateMeal(planId, mealData) {
    return api.post(`/meal-plans/${planId}/regenerate_meal/`, mealData)
  },

  generateShoppingList(planId, excludeItems = []) {
    return api.post(`/meal-plans/${planId}/generate_shopping_list/`, {
      exclude_items: excludeItems,
      group_by_category: true
    })
  },

  // Nutrition Log endpoints
  getNutritionLogs(params = {}) {
    return api.get('/nutrition-logs/', { params })
  },

  getNutritionLog(id) {
    return api.get(`/nutrition-logs/${id}/`)
  },

  analyzeNutrition(analysisData) {
    return api.post('/nutrition-logs/analyze/', analysisData)
  },

  getDashboardData() {
    return api.get('/nutrition-logs/dashboard_data/')
  }
}

// Helper functions for common operations
export const mealPlanningHelpers = {
  // Format dietary preferences for display
  formatDietaryPreference(preference) {
    return preference
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  },

  // Format cuisine names
  formatCuisine(cuisine) {
    return cuisine.charAt(0).toUpperCase() + cuisine.slice(1)
  },

  // Calculate macro percentages
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

  // Format time duration
  formatDuration(minutes) {
    if (minutes < 60) {
      return `${minutes}min`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}min` : `${hours}h`
  },

  // Calculate nutrition score
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

  // Get macro color for charts
  getMacroColor(macro) {
    const colors = {
      protein: '#ff6b6b',
      carbs: '#4ecdc4',
      fat: '#45b7d1'
    }
    return colors[macro] || '#95a5a6'
  },

  // Format calories for display
  formatCalories(calories) {
    if (calories >= 1000) {
      return `${(calories / 1000).toFixed(1)}k`
    }
    return Math.round(calories).toString()
  },

  // Get difficulty color
  getDifficultyColor(difficulty) {
    const colors = {
      easy: '#27ae60',
      medium: '#f39c12',
      hard: '#e74c3c'
    }
    return colors[difficulty] || '#95a5a6'
  },

  // Validate nutrition profile data
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

  // Generate meal plan request data
  createMealPlanRequest(options = {}) {
    const defaults = {
      plan_type: 'daily',
      start_date: new Date().toISOString().split('T')[0],
      use_preferences: true,
      regenerate_existing: false
    }

    return { ...defaults, ...options }
  }
}

export default mealPlanningApi