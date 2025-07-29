// src/services/mealPlanningApi.js
import axios from 'axios';
import AuthService from './auth.service';
import store from '../store';

const API_BASE_URL = (process.env.VUE_APP_API_URL || 'https://wellness-app-tx2c.onrender.com/api').replace(/\/+$/, '').replace('/api', '') + '/meal-planning/api';

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
  // Expose the api instance for advanced usage
  api,

  // Recipe endpoints
  getRecipes(params = {}) {
    // Clean up parameters and add debugging
    const cleanParams = {}
    
    // Basic pagination
    if (params.page) cleanParams.page = params.page
    if (params.page_size) cleanParams.page_size = params.page_size
    
    // Search parameters
    if (params.search && params.search.trim()) {
      cleanParams.search = params.search.trim()
    }
    
    // Filter parameters
    if (params.cuisine && params.cuisine.trim()) {
      cleanParams.cuisine = params.cuisine.trim()
    }
    
    if (params.meal_type && params.meal_type.trim()) {
      cleanParams.meal_type = params.meal_type.trim()
    }
    
    if (params.dietary_preferences && params.dietary_preferences.trim()) {
      cleanParams.dietary_preferences = params.dietary_preferences.trim()
    }
    
    if (params.max_calories && params.max_calories.trim()) {
      cleanParams.max_calories = parseInt(params.max_calories.trim())
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🔗 API request: /recipes/', cleanParams)
    }
    return api.get('/recipes/', { params: cleanParams })
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

  saveRecipeToMyCollection(recipeId) {
    return api.post(`/recipes/${recipeId}/save_to_my_recipes/`)
  },

  saveRecipeFromMealPlan(recipeData) {
    return api.post(`/recipes/save_from_meal_plan/`, recipeData)
  },

  removeRecipeFromMyCollection(recipeId) {
    return api.delete(`/recipes/${recipeId}/`)
  },

  getMyRecipes(params = {}) {
    // Get only user's saved recipes
    const cleanParams = { ...params, my_recipes: 'true' }
    
    // Basic pagination
    if (!cleanParams.page) cleanParams.page = 1
    if (!cleanParams.page_size) cleanParams.page_size = 100
    
    // Search parameters
    if (cleanParams.search && cleanParams.search.trim()) {
      cleanParams.search = cleanParams.search.trim()
    }
    
    // Filter parameters
    if (cleanParams.cuisine && cleanParams.cuisine.trim()) {
      cleanParams.cuisine = cleanParams.cuisine.trim()
    }
    
    if (cleanParams.meal_type && cleanParams.meal_type.trim()) {
      cleanParams.meal_type = cleanParams.meal_type.trim()
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log('🔗 API request: /recipes/ (my recipes only)', cleanParams)
    }
    return api.get('/recipes/', { params: cleanParams })
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

  // AI-powered nutrition profile generation
  async generateNutritionProfile(profileData) {
    try {
      return await api.post('/nutrition-profile/ai_generate/', profileData)
    } catch (error) {
      console.error('Error generating AI nutrition profile:', error)
      throw error
    }
  },

  // Enhanced Meal Plan endpoints with AI features and improved pagination handling
  getMealPlans(params = {}) {
    const cleanParams = {
      page: params.page || 1,
      page_size: params.page_size || 20,
      ordering: params.ordering || '-created_at'
    }
    
    // Add any filtering parameters
    if (params.plan_type) cleanParams.plan_type = params.plan_type
    if (params.is_active !== undefined) cleanParams.is_active = params.is_active
    if (params.start_date) cleanParams.start_date = params.start_date
    if (params.end_date) cleanParams.end_date = params.end_date

    if (process.env.NODE_ENV === 'development') {
      console.log('🔗 API request: /meal-plans/', cleanParams)
    }
    return api.get('/meal-plans/', { params: cleanParams })
  },

  getMealPlan(id) {
    return api.get(`/meal-plans/${id}/`)
  },

  generateMealPlan(planData) {
    if (process.env.NODE_ENV === 'development') {
      console.log('🎯 Generating meal plan with data:', planData)
    }
    // Enhanced meal plan generation with AI features
    return api.post('/meal-plans/generate/', planData)
  },

  deleteMealPlan(planId) {
    if (process.env.NODE_ENV === 'development') {
      console.log('🗑️ Deleting meal plan:', planId)
    }
    return api.delete(`/meal-plans/${planId}/`)
  },

  async regenerateMeal(planId, day, mealType) {
    try {
      console.log('Regenerating meal:', { planId, day, mealType })
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
      console.log('Getting meal alternatives:', { planId, day, mealType, count })
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
      console.log('Analyzing meal plan:', planId)
      return await api.get(`/meal-plans/${planId}/analyze/`)
    } catch (error) {
      if (error.response?.status === 404) {
        console.warn('Meal plan analysis endpoint not implemented yet')
        // Return mock analysis data for development
        return {
          data: {
            overall_score: 85,
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
              'Excellent meal plan with well-balanced nutrition',
              'Great variety of cuisines and cooking methods',
              'Protein distribution is optimal throughout the day'
            ],
            health_highlights: [
              'Well-balanced macronutrients',
              'Good variety of nutrient-dense foods',
              'Appropriate calorie distribution across meals'
            ],
            areas_for_improvement: [
              'Consider adding more omega-3 rich foods',
              'Could include more antioxidant-rich vegetables'
            ]
          }
        }
      }
      throw error
    }
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

  getDashboardData(params = {}) {
    const cleanParams = {
      days: params.days || 7,
      ...params
    }
    return api.get('/nutrition-logs/dashboard_data/', { params: cleanParams })
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
        // Return default dietary preferences matching your backend model
        return {
          data: [
            'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo',
            'mediterranean', 'dash', 'low_carb', 'low_fat', 'high_protein',
            'intermittent_fasting', 'whole30', 'raw_food', 'gluten_free',
            'dairy_free', 'flexitarian'
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
        // Return default allergens list matching your backend model
        return {
          data: [
            'nuts', 'peanuts', 'dairy', 'gluten', 'eggs', 'fish',
            'shellfish', 'soy', 'sesame', 'sulfites', 'nightshades',
            'histamine'
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
        // Return default cuisines list matching your backend model
        return {
          data: [
            'italian', 'mexican', 'asian', 'indian', 'mediterranean',
            'american', 'french', 'thai', 'japanese', 'chinese',
            'greek', 'middle_eastern'
          ]
        }
      }
      throw error
    }
  },

  // Spoonacular integration endpoints
  async connectSpoonacular() {
    try {
      return await api.post('/nutrition-profile/connect_spoonacular/')
    } catch (error) {
      console.error('Failed to connect to Spoonacular:', error)
      throw error
    }
  },

  async getSpoonacularStatus() {
    try {
      return await api.get('/nutrition-profile/spoonacular_status/')
    } catch (error) {
      console.error('Failed to get Spoonacular status:', error)
      throw error
    }
  },

  async getSpoonacularMealPlan(startDate = null) {
    try {
      const params = startDate ? { start_date: startDate } : {}
      return await api.get('/nutrition-profile/spoonacular_meal_plan/', { params })
    } catch (error) {
      console.error('Failed to get Spoonacular meal plan:', error)
      throw error
    }
  },

  async addToSpoonacularMealPlan(mealData) {
    try {
      return await api.post('/nutrition-profile/add_to_spoonacular_meal_plan/', mealData)
    } catch (error) {
      console.error('Failed to add to Spoonacular meal plan:', error)
      throw error
    }
  },

  async getSpoonacularShoppingList() {
    try {
      return await api.get('/nutrition-profile/spoonacular_shopping_list/')
    } catch (error) {
      console.error('Failed to get Spoonacular shopping list:', error)
      throw error
    }
  },

  async generateSpoonacularShoppingList(startDate, endDate) {
    try {
      return await api.post('/nutrition-profile/generate_spoonacular_shopping_list/', {
        start_date: startDate,
        end_date: endDate
      })
    } catch (error) {
      console.error('Failed to generate Spoonacular shopping list:', error)
      throw error
    }
  }
}

// Enhanced helper functions with support for the new meal plan structure
export const mealPlanningHelpers = {
  /**
   * Format dietary preference for display
   */
  formatDietaryPreference(preference) {
    if (!preference) return ''
    return preference
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  },

  /**
   * Format cuisine name for display
   */
  formatCuisine(cuisine) {
    if (!cuisine) return ''
    return cuisine.charAt(0).toUpperCase() + cuisine.slice(1)
  },

  /**
   * Calculate macro percentages from nutrition data
   */
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

  /**
   * Format duration in minutes to a readable format
   */
  formatDuration(minutes) {
    if (!minutes || minutes < 0) return '0min'
    if (minutes < 60) {
      return `${minutes}min`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}min` : `${hours}h`
  },

  /**
   * Calculate nutrition score based on actual vs target values
   */
  calculateNutritionScore(actual, target, tolerance = 0.1) {
    if (!target || target <= 0) return 100

    const difference = Math.abs(actual - target)
    const allowedDifference = target * tolerance

    if (difference <= allowedDifference) {
      return 100
    }

    const score = Math.max(0, 100 - (difference / target) * 100)
    return Math.round(score)
  },

  /**
   * Get color for macronutrient visualization
   */
  getMacroColor(macro) {
    const colors = {
      protein: '#ff6b6b',
      carbs: '#4ecdc4',
      carbohydrates: '#4ecdc4',
      fat: '#45b7d1',
      fats: '#45b7d1'
    }
    return colors[macro?.toLowerCase()] || '#95a5a6'
  },

  /**
   * Format calories for display
   */
  formatCalories(calories) {
    if (!calories || calories < 0) return '0'
    if (calories >= 1000) {
      return `${(calories / 1000).toFixed(1)}k`
    }
    return Math.round(calories).toString()
  },

  /**
   * Get color for difficulty level
   */
  getDifficultyColor(difficulty) {
    const colors = {
      easy: '#27ae60',
      medium: '#f39c12',
      hard: '#e74c3c'
    }
    return colors[difficulty?.toLowerCase()] || '#95a5a6'
  },

  /**
   * Validate nutrition profile data
   */
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

  /**
   * Create meal plan request object with defaults
   */
  createMealPlanRequest(options = {}) {
    const defaults = {
      plan_type: 'daily',
      start_date: new Date().toISOString().split('T')[0],
      use_preferences: true,
      regenerate_existing: false
    }

    return { ...defaults, ...options }
  },

  /**
   * Extract total meal count from meal plan data
   */
  getMealCount(mealPlan) {
    if (!mealPlan?.meal_plan_data?.meals) return 0

    let totalMeals = 0
    Object.values(mealPlan.meal_plan_data.meals).forEach(dayMeals => {
      if (Array.isArray(dayMeals)) {
        totalMeals += dayMeals.length
      }
    })
    return totalMeals
  },

  /**
   * Extract nutrition value from recipe with fallback handling
   */
  getNutritionValue(recipe, nutrient) {
    if (!recipe) return 0
    
    // Try estimated_nutrition first (from your API response)
    if (recipe.estimated_nutrition && recipe.estimated_nutrition[nutrient] !== undefined) {
      return Math.round(recipe.estimated_nutrition[nutrient])
    }
    
    // Fallback to nutrition object
    if (recipe.nutrition && recipe.nutrition[nutrient] !== undefined) {
      return Math.round(recipe.nutrition[nutrient])
    }

    // Try other common naming patterns
    const nutrientMappings = {
      'calories': ['calories_per_serving', 'kcal'],
      'protein': ['protein_per_serving'],
      'carbs': ['carbs_per_serving', 'carbohydrates'],
      'fat': ['fat_per_serving', 'fats']
    }

    if (nutrientMappings[nutrient]) {
      for (const mapping of nutrientMappings[nutrient]) {
        if (recipe[mapping] !== undefined) {
          return Math.round(recipe[mapping])
        }
      }
    }
    
    return 0
  },

  /**
   * Format meal plan date range for display
   */
  formatDateRange(startDate, endDate) {
    if (!startDate || !endDate) return 'Date unknown'
    
    const start = new Date(startDate).toLocaleDateString()
    const end = new Date(endDate).toLocaleDateString()

    if (startDate === endDate) {
      return start
    }
    return `${start} - ${end}`
  },

  /**
   * Handle API errors with user-friendly messages
   */
  handleApiError(error, fallbackMessage = 'An error occurred') {
    console.error('API Error:', error)

    if (error.response?.data?.detail) {
      return error.response.data.detail
    }
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    if (error.response?.data?.error) {
      return error.response.data.error
    }
    if (error.message) {
      return error.message
    }
    return fallbackMessage
  },

  /**
   * Check if a meal plan is from the new API structure
   */
  isNewMealPlanStructure(mealPlan) {
    return !!(mealPlan?.meal_plan_data?.meals && 
              mealPlan?.daily_averages && 
              mealPlan?.generation_version)
  },

  /**
   * Get all dates from a meal plan
   */
  getMealPlanDates(mealPlan) {
    if (!mealPlan?.meal_plan_data?.meals) return []
    return Object.keys(mealPlan.meal_plan_data.meals).sort()
  },

  /**
   * Get meals for a specific date
   */
  getMealsForDate(mealPlan, date) {
    if (!mealPlan?.meal_plan_data?.meals?.[date]) return []
    return mealPlan.meal_plan_data.meals[date]
  }
}

export default mealPlanningApi