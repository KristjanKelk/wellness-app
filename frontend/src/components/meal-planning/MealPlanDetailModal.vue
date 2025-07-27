<!-- src/components/meal-planning/MealPlanDetailModal.vue -->
<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ formatPlanType(mealPlan.plan_type) }} Meal Plan</h2>
        <div class="ai-generation-info">
          <span class="ai-badge">
            <i class="fas fa-brain"></i>
            AI v{{ mealPlan.generation_version || '1.0' }}
          </span>
          <span class="model-badge">{{ mealPlan.ai_model_used || 'AI Model' }}</span>
        </div>
        <button @click="$emit('close')" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <div class="plan-overview">
          <div class="overview-stats">
            <div class="stat-item">
              <span class="stat-label">Date Range:</span>
              <span class="stat-value">{{ formatDateRange(mealPlan.start_date, mealPlan.end_date) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Total Calories:</span>
              <span class="stat-value">{{ Math.round(mealPlan.total_calories || 0) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Avg Daily Calories:</span>
              <span class="stat-value">{{ Math.round(mealPlan.avg_daily_calories || 0) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Total Meals:</span>
              <span class="stat-value">{{ getTotalMeals() }}</span>
            </div>
            <div class="stat-item" v-if="mealPlan.nutritional_balance_score">
              <span class="stat-label">Balance Score:</span>
              <span class="stat-value">{{ mealPlan.nutritional_balance_score.toFixed(1) }}/10</span>
            </div>
            <div class="stat-item" v-if="mealPlan.days_count">
              <span class="stat-label">Days:</span>
              <span class="stat-value">{{ mealPlan.days_count }}</span>
            </div>
          </div>

          <!-- Daily Nutritional Averages -->
          <div class="nutrition-overview" v-if="mealPlan.daily_averages">
            <h4>Daily Nutritional Averages</h4>
            <div class="nutrition-grid">
              <div class="nutrition-item">
                <span class="nutrition-label">Protein:</span>
                <span class="nutrition-value">{{ Math.round(mealPlan.daily_averages.protein || 0) }}g</span>
              </div>
              <div class="nutrition-item">
                <span class="nutrition-label">Carbohydrates:</span>
                <span class="nutrition-value">{{ Math.round(mealPlan.daily_averages.carbs || 0) }}g</span>
              </div>
              <div class="nutrition-item">
                <span class="nutrition-label">Fat:</span>
                <span class="nutrition-value">{{ Math.round(mealPlan.daily_averages.fat || 0) }}g</span>
              </div>
              <div class="nutrition-item">
                <span class="nutrition-label">Calories:</span>
                <span class="nutrition-value">{{ Math.round(mealPlan.daily_averages.calories || 0) }}</span>
              </div>
            </div>
          </div>

          <!-- Quality Scores -->
          <div class="quality-scores" v-if="mealPlan.variety_score || mealPlan.preference_match_score">
            <h4>Plan Quality Metrics</h4>
            <div class="scores-grid">
              <div class="score-item" v-if="mealPlan.nutritional_balance_score">
                <span class="score-label">Nutritional Balance:</span>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: (mealPlan.nutritional_balance_score * 10) + '%' }"></div>
                </div>
                <span class="score-value">{{ mealPlan.nutritional_balance_score.toFixed(1) }}/10</span>
              </div>
              <div class="score-item" v-if="mealPlan.variety_score">
                <span class="score-label">Variety Score:</span>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: (mealPlan.variety_score * 10) + '%' }"></div>
                </div>
                <span class="score-value">{{ mealPlan.variety_score.toFixed(1) }}/10</span>
              </div>
              <div class="score-item" v-if="mealPlan.preference_match_score">
                <span class="score-label">Preference Match:</span>
                <div class="score-bar">
                  <div class="score-fill" :style="{ width: (mealPlan.preference_match_score * 10) + '%' }"></div>
                </div>
                <span class="score-value">{{ mealPlan.preference_match_score.toFixed(1) }}/10</span>
              </div>
            </div>
          </div>
        </div>

        <div class="meals-section" v-if="mealPlan.meal_plan_data && mealPlan.meal_plan_data.meals">
          <h3>Detailed Meal Plan</h3>
          <div class="meals-grid">
            <div
              v-for="(dayMeals, date) in mealPlan.meal_plan_data.meals"
              :key="date"
              class="day-meals"
            >
              <h4 class="day-header">{{ formatDate(date) }}</h4>
              <div class="meals-list">
                <div
                  v-for="(meal, index) in dayMeals"
                  :key="index"
                  class="meal-card"
                >
                  <div class="meal-header">
                    <div class="meal-title-section">
                      <h5 class="meal-title">
                        {{ getMealTitle(meal) }}
                      </h5>
                      <span class="meal-type-badge" :class="getMealTypeClass(meal.meal_type || 'meal')">
                        {{ formatMealType(meal.meal_type || 'Meal') }}
                      </span>
                    </div>
                    <div class="meal-meta">
                      <span class="meal-time">
                        <i class="fas fa-clock"></i>
                        {{ getMealTime(meal) }}
                      </span>
                      <span class="meal-cuisine" v-if="meal.recipe?.cuisine">
                        <i class="fas fa-globe"></i>
                        {{ meal.recipe.cuisine }}
                      </span>
                    </div>
                  </div>

                  <!-- Recipe Details -->
                  <div class="recipe-details" v-if="meal.recipe">
                    <!-- Cooking Information -->
                    <div class="cooking-info" v-if="meal.recipe.prep_time || meal.recipe.cook_time || meal.recipe.total_time">
                      <div class="time-info">
                        <span v-if="meal.recipe.prep_time" class="time-item">
                          <i class="fas fa-cut"></i>
                          Prep: {{ meal.recipe.prep_time }}min
                        </span>
                        <span v-if="meal.recipe.cook_time" class="time-item">
                          <i class="fas fa-fire"></i>
                          Cook: {{ meal.recipe.cook_time }}min
                        </span>
                        <span v-if="meal.recipe.total_time" class="time-item">
                          <i class="fas fa-hourglass-half"></i>
                          Total: {{ meal.recipe.total_time }}min
                        </span>
                        <span v-if="meal.recipe.servings" class="time-item">
                          <i class="fas fa-users"></i>
                          Serves: {{ meal.recipe.servings }}
                        </span>
                      </div>
                    </div>

                    <!-- Nutritional Information -->
                    <div class="meal-nutrition">
                      <h6>Nutritional Information</h6>
                      <div class="nutrition-details">
                        <div class="nutrition-item">
                          <span class="nutrition-label">Calories:</span>
                          <span class="nutrition-value">{{ getNutritionValue(meal.recipe, 'calories') }}</span>
                        </div>
                        <div class="nutrition-item">
                          <span class="nutrition-label">Protein:</span>
                          <span class="nutrition-value">{{ getNutritionValue(meal.recipe, 'protein') }}g</span>
                        </div>
                        <div class="nutrition-item">
                          <span class="nutrition-label">Carbs:</span>
                          <span class="nutrition-value">{{ getNutritionValue(meal.recipe, 'carbs') }}g</span>
                        </div>
                        <div class="nutrition-item">
                          <span class="nutrition-label">Fat:</span>
                          <span class="nutrition-value">{{ getNutritionValue(meal.recipe, 'fat') }}g</span>
                        </div>
                      </div>
                    </div>

                    <!-- Ingredients -->
                    <div class="ingredients-section" v-if="meal.recipe.ingredients && meal.recipe.ingredients.length">
                      <h6>Ingredients</h6>
                      <div class="ingredients-list">
                        <div 
                          v-for="(ingredient, idx) in meal.recipe.ingredients" 
                          :key="idx"
                          class="ingredient-item"
                        >
                          <span class="ingredient-quantity">{{ ingredient.quantity }}</span>
                          <span class="ingredient-unit">{{ ingredient.unit }}</span>
                          <span class="ingredient-name">{{ ingredient.name }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Instructions -->
                    <div class="instructions-section" v-if="meal.recipe.instructions && meal.recipe.instructions.length">
                      <h6>Instructions</h6>
                      <div class="instructions-list">
                        <div 
                          v-for="(instruction, idx) in meal.recipe.instructions" 
                          :key="idx"
                          class="instruction-item"
                        >
                          <span class="instruction-number">{{ idx + 1 }}</span>
                          <span class="instruction-text">{{ instruction }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Target Information -->
                    <div class="target-info" v-if="meal.target_calories || meal.target_protein || meal.target_carbs || meal.target_fat">
                      <h6>Meal Targets</h6>
                      <div class="targets-grid">
                        <div class="target-item" v-if="meal.target_calories">
                          <span class="target-label">Target Calories:</span>
                          <span class="target-value">{{ Math.round(meal.target_calories) }}</span>
                        </div>
                        <div class="target-item" v-if="meal.target_protein">
                          <span class="target-label">Target Protein:</span>
                          <span class="target-value">{{ Math.round(meal.target_protein) }}g</span>
                        </div>
                        <div class="target-item" v-if="meal.target_carbs">
                          <span class="target-label">Target Carbs:</span>
                          <span class="target-value">{{ Math.round(meal.target_carbs) }}g</span>
                        </div>
                        <div class="target-item" v-if="meal.target_fat">
                          <span class="target-label">Target Fat:</span>
                          <span class="target-value">{{ Math.round(meal.target_fat) }}g</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="meal-actions">
                    <button
                      @click="debugAndRegenerateMeal(date, meal, index)"
                      class="btn btn-sm btn-outline"
                      :title="`Regenerate ${meal.meal_type || 'meal'} for ${formatDate(date)}`"
                    >
                      <i class="fas fa-redo"></i>
                      Regenerate
                    </button>
                    <button
                      @click="getAlternatives(date, meal.meal_type || inferMealTypeFromTime(new Date()))"
                      class="btn btn-sm btn-secondary"
                    >
                      <i class="fas fa-exchange-alt"></i>
                      Alternatives
                    </button>
                    <button
                      @click="viewRecipeDetails(meal.recipe)"
                      class="btn btn-sm btn-info"
                    >
                      <i class="fas fa-info-circle"></i>
                      Recipe Details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="no-meals">
          <i class="fas fa-utensils"></i>
          <p>No meal details available</p>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="$emit('close')" class="btn btn-secondary">Close</button>
        <button @click="generateShoppingList" class="btn btn-success">
          <i class="fas fa-shopping-cart"></i>
          Generate Shopping List
        </button>
        <button @click="analyzePlan" class="btn btn-info">
          <i class="fas fa-chart-line"></i>
          AI Analysis
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MealPlanDetailModal',
  props: {
    mealPlan: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'regenerate-meal', 'get-alternatives', 'analyze-plan'],
  mounted() {
    console.log('=== MealPlanDetailModal Mounted ===')
    console.log('Meal Plan ID:', this.mealPlan?.id)
    console.log('Plan Type:', this.mealPlan?.plan_type)
    console.log('Has meal_plan_data:', !!this.mealPlan?.meal_plan_data)
    console.log('Has meals:', !!this.mealPlan?.meal_plan_data?.meals)
    
    if (this.mealPlan?.meal_plan_data?.meals) {
      const mealDates = Object.keys(this.mealPlan.meal_plan_data.meals)
      console.log('Available meal dates:', mealDates)
      console.log('Total meal days:', mealDates.length)
      
      // Log first day's meals as sample
      if (mealDates.length > 0) {
        const firstDate = mealDates[0]
        const firstDayMeals = this.mealPlan.meal_plan_data.meals[firstDate]
        console.log(`Sample meals for ${firstDate}:`, firstDayMeals)
      }
    } else {
      console.log('No meal data available - checking structure:')
      console.log('mealPlan keys:', Object.keys(this.mealPlan || {}))
      if (this.mealPlan?.meal_plan_data) {
        console.log('meal_plan_data keys:', Object.keys(this.mealPlan.meal_plan_data))
      }
    }
    console.log('=====================================')
  },
  methods: {
    formatPlanType(type) {
      if (!type) return 'Unknown'
      return type.charAt(0).toUpperCase() + type.slice(1)
    },

    formatDateRange(startDate, endDate) {
      if (!startDate || !endDate) {
        console.log('formatDateRange: Missing dates - start:', startDate, 'end:', endDate)
        return 'Date unknown'
      }
      
      try {
        const startDateObj = new Date(startDate)
        const endDateObj = new Date(endDate)
        
        if (isNaN(startDateObj.getTime()) || isNaN(endDateObj.getTime())) {
          console.log('formatDateRange: Invalid dates - start:', startDate, 'end:', endDate)
          return 'Invalid date range'
        }
        
        const start = startDateObj.toLocaleDateString()
        const end = endDateObj.toLocaleDateString()

        if (startDate === endDate) {
          return start
        }
        return `${start} - ${end}`
      } catch (error) {
        console.error('formatDateRange error:', error, 'for dates:', startDate, endDate)
        return 'Date error'
      }
    },

    formatDate(dateStr) {
      try {
        if (!dateStr) {
          console.log('formatDate: dateStr is null/undefined')
          return 'Unknown Date'
        }
        
        const date = new Date(dateStr)
        if (isNaN(date.getTime())) {
          console.log('formatDate: Invalid date for input:', dateStr)
          return dateStr // Return original string if can't parse
        }
        
        return date.toLocaleDateString('en-US', {
          weekday: 'long',
          month: 'short',
          day: 'numeric'
        })
      } catch (error) {
        console.error('formatDate error:', error, 'for input:', dateStr)
        return dateStr || 'Unknown Date'
      }
    },

    formatMealType(type) {
      if (!type) return 'Meal'
      // Handle different possible meal type formats
      const cleanType = String(type).toLowerCase().trim()
      const typeMap = {
        'breakfast': 'Breakfast',
        'lunch': 'Lunch', 
        'dinner': 'Dinner',
        'snack': 'Snack',
        'dessert': 'Dessert'
      }
      return typeMap[cleanType] || type.charAt(0).toUpperCase() + type.slice(1)
    },

    getMealTitle(meal) {
      console.log('getMealTitle called for meal:', meal)
      
      // If we have a recipe with a title, use that
      if (meal?.recipe?.title) {
        return meal.recipe.title
      }
      
      // If we have a recipe with a name, use that
      if (meal?.recipe?.name) {
        return meal.recipe.name
      }
      
      // Fallback to meal type
      const mealType = this.formatMealType(meal?.meal_type)
      console.log('getMealTitle fallback to meal type:', mealType)
      return mealType
    },

    inferMealTypeFromTime(date) {
      const hour = date.getHours()
      if (hour >= 5 && hour < 11) return 'breakfast'
      if (hour >= 11 && hour < 16) return 'lunch'
      if (hour >= 16 && hour < 22) return 'dinner'
      return 'snack'
    },

    getMealTime(meal) {
      console.log('getMealTime called for meal:', meal)
      
      // Check various possible time fields
      if (meal?.time) {
        return meal.time
      }
      if (meal?.scheduled_time) {
        return meal.scheduled_time
      }
      
      // Default times based on meal type
      const mealType = meal?.meal_type?.toLowerCase()
      const defaultTimes = {
        'breakfast': '08:00',
        'lunch': '12:00',
        'dinner': '18:00',
        'snack': '15:00'
      }
      
      const defaultTime = defaultTimes[mealType] || '12:00'
      console.log('getMealTime using default time:', defaultTime, 'for meal type:', mealType)
      return defaultTime
    },

    getMealTypeClass(type) {
      if (!type) return 'meal'
      return String(type).toLowerCase()
    },

    getTotalMeals() {
      if (!this.mealPlan.meal_plan_data?.meals) return 0

      let total = 0
      Object.values(this.mealPlan.meal_plan_data.meals).forEach(dayMeals => {
        if (Array.isArray(dayMeals)) {
          total += dayMeals.length
        }
      })
      return total
    },

    // Helper method to get nutrition values from different possible structures
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

    debugAndRegenerateMeal(date, meal, index) {
      console.log('=== debugAndRegenerateMeal called ===')
      console.log('Date from template:', date)
      console.log('Date type:', typeof date)
      console.log('Meal object:', meal)
      console.log('Meal index:', index)
      console.log('Meal.meal_type:', meal?.meal_type)
      console.log('Meal.meal_type type:', typeof meal?.meal_type)
      
      const mealType = meal.meal_type || this.inferMealTypeFromTime(new Date())
      console.log('Computed mealType:', mealType)
      console.log('About to call regenerateMeal with:', { date, mealType })
      console.log('==========================================')
      
      this.regenerateMeal(date, mealType)
    },

    regenerateMeal(date, mealType) {
      console.log('=== regenerateMeal called ===')
      console.log('Date:', date)
      console.log('Date type:', typeof date)
      console.log('MealType (raw):', mealType)
      console.log('MealType type:', typeof mealType)
      
      // Debug: Check if date is unexpectedly a meal type
      const possibleMealTypes = ['breakfast', 'lunch', 'dinner', 'snack']
      if (possibleMealTypes.includes(String(date).toLowerCase())) {
        console.error('🚨 BUG DETECTED: Date parameter contains meal type instead of date!', {
          dateParam: date,
          mealTypeParam: mealType,
          stackTrace: new Error().stack
        })
        // This helps identify where the wrong call is coming from
      }
      
      // Validate date parameter
      if (!date || typeof date !== 'string') {
        console.error('Invalid date provided:', date, 'type:', typeof date)
        return
      }
      
      // Ensure mealType is properly defined
      if (!mealType || mealType === 'undefined' || mealType === 'null') {
        console.error('Invalid mealType provided:', mealType)
        // Try to infer from time or provide a fallback
        const inferredMealType = this.inferMealTypeFromTime(new Date())
        console.log('Using inferred meal type:', inferredMealType)
        mealType = inferredMealType
      }
      
      // Clean up the mealType string
      const cleanMealType = String(mealType).toLowerCase().trim()
      
      // Additional validation to ensure we have valid values
      let finalMealType = cleanMealType
      if (!finalMealType || finalMealType === 'undefined' || finalMealType === 'null') {
        console.error('Failed to determine valid mealType, using breakfast as fallback')
        finalMealType = 'breakfast'
      }
      
      console.log('Final date:', date)
      console.log('Final cleaned mealType:', finalMealType)
      console.log('=============================')
      
      this.$emit('regenerate-meal', {
        day: date,
        mealType: finalMealType
      })
    },

    getAlternatives(date, mealType) {
      console.log('=== getAlternatives called ===')
      console.log('Date:', date)
      console.log('MealType (raw):', mealType)
      
      // Ensure mealType is properly defined
      if (!mealType || mealType === 'undefined' || mealType === 'null') {
        console.error('Invalid mealType provided for alternatives:', mealType)
        const inferredMealType = this.inferMealTypeFromTime(new Date())
        console.log('Using inferred meal type for alternatives:', inferredMealType)
        mealType = inferredMealType
      }
      
      // Clean up the mealType string
      const cleanMealType = String(mealType).toLowerCase().trim()
      
      console.log('Final cleaned mealType for alternatives:', cleanMealType)
      console.log('==================================')
      
      this.$emit('get-alternatives', {
        day: date,
        mealType: cleanMealType
      })
    },

    viewRecipeDetails(recipe) {
      // For now, just show an alert. In a full implementation, 
      // this could open another modal or navigate to a recipe detail page
      if (recipe) {
        alert(`Recipe: ${recipe.title}\n\nThis feature will show full recipe details in a future update.`)
      }
    },

    generateShoppingList() {
      // TODO: Implement shopping list generation
      alert('Shopping list generation coming soon!')
    },

    analyzePlan() {
      this.$emit('analyze-plan', this.mealPlan)
    }
  }
}
</script>

<style lang="scss" scoped>
$primary: #007bff;
$secondary: #6c757d;
$success: #28a745;
$danger: #dc3545;
$warning: #ffc107;
$info: #17a2b8;
$light: #f8f9fa;
$dark: #343a40;
$white: #ffffff;
$gray: #6c757d;
$gray-light: #adb5bd;
$gray-lighter: #e9ecef;

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: $white;
  border-radius: 16px;
  max-width: 1000px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid $gray-lighter;
  background: linear-gradient(135deg, rgba($primary, 0.05), rgba($primary, 0.02));
  position: relative;

  h2 {
    margin: 0;
    font-size: 1.6rem;
    color: #333;
  }

  .ai-generation-info {
    display: flex;
    gap: 8px;
    align-items: center;

    .ai-badge {
      background: linear-gradient(135deg, #6f42c1, #8b5cf6);
      color: white;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      display: flex;
      align-items: center;
      gap: 4px;
      font-weight: 500;

      i {
        font-size: 0.7rem;
      }
    }

    .model-badge {
      background: linear-gradient(135deg, #17a2b8, #20c997);
      color: white;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 500;
    }
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    color: $gray;
    transition: all 0.2s ease;

    &:hover {
      background: rgba($gray, 0.1);
      color: #333;
    }
  }
}

.modal-body {
  padding: 32px;
}

.plan-overview {
  margin-bottom: 32px;
  padding: 24px;
  background: $light;
  border-radius: 12px;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: $white;
  border-radius: 8px;
  border: 1px solid $gray-lighter;

  .stat-label {
    font-weight: 500;
    color: $gray;
    font-size: 0.9rem;
  }

  .stat-value {
    font-weight: 600;
    color: $dark;
    font-size: 1rem;
  }
}

.nutrition-overview {
  margin-bottom: 24px;

  h4 {
    margin: 0 0 16px 0;
    font-size: 1.1rem;
    color: $dark;
    font-weight: 600;
  }

  .nutrition-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
  }

  .nutrition-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: rgba($success, 0.1);
    border-radius: 6px;
    font-size: 0.9rem;

    .nutrition-label {
      color: $gray;
      font-weight: 500;
    }

    .nutrition-value {
      color: $dark;
      font-weight: 600;
    }
  }
}

.quality-scores {
  h4 {
    margin: 0 0 16px 0;
    font-size: 1.1rem;
    color: $dark;
    font-weight: 600;
  }

  .scores-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .score-item {
    display: flex;
    align-items: center;
    gap: 12px;

    .score-label {
      font-size: 0.9rem;
      color: $gray;
      min-width: 140px;
      font-weight: 500;
    }

    .score-bar {
      flex: 1;
      height: 8px;
      background: $gray-lighter;
      border-radius: 4px;
      overflow: hidden;

      .score-fill {
        height: 100%;
        background: linear-gradient(90deg, #28a745, #20c997);
        transition: width 0.3s ease;
      }
    }

    .score-value {
      font-size: 0.9rem;
      font-weight: 600;
      color: $dark;
      min-width: 40px;
      text-align: right;
    }
  }
}

.meals-section {
  h3 {
    margin: 0 0 24px 0;
    font-size: 1.3rem;
    color: $dark;
    display: flex;
    align-items: center;
    gap: 12px;

    &::before {
      content: '';
      width: 4px;
      height: 24px;
      background: $primary;
      border-radius: 2px;
    }
  }
}

.meals-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.day-meals {
  border: 1px solid $gray-lighter;
  border-radius: 12px;
  overflow: hidden;
}

.day-header {
  margin: 0;
  padding: 16px 20px;
  background: $primary;
  color: $white;
  font-size: 1.1rem;
  font-weight: 600;
}

.meals-list {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.meal-card {
  background: $white;
  border: 1px solid $gray-lighter;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
  }
}

.meal-header {
  margin-bottom: 16px;

  .meal-title-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .meal-title {
      margin: 0;
      font-size: 1.2rem;
      color: $dark;
      font-weight: 600;
    }

    .meal-type-badge {
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 500;
      text-transform: uppercase;
      
      &.breakfast {
        background: rgba(#ffc107, 0.2);
        color: #d39e00;
      }
      
      &.lunch {
        background: rgba(#28a745, 0.2);
        color: #1e7e34;
      }
      
      &.dinner {
        background: rgba(#dc3545, 0.2);
        color: #bd2130;
      }
      
      &.snack {
        background: rgba(#6f42c1, 0.2);
        color: #59359a;
      }
    }
  }

  .meal-meta {
    display: flex;
    gap: 16px;
    align-items: center;

    .meal-time, .meal-cuisine {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.85rem;
      color: $gray;

      i {
        font-size: 0.8rem;
      }
    }
  }
}

.recipe-details {
  .cooking-info {
    margin-bottom: 16px;
    padding: 12px;
    background: rgba($info, 0.05);
    border-radius: 8px;

    .time-info {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;

      .time-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 0.85rem;
        color: $gray;

        i {
          font-size: 0.8rem;
          color: $info;
        }
      }
    }
  }

  h6 {
    margin: 0 0 8px 0;
    font-size: 1rem;
    color: $dark;
    font-weight: 600;
  }
}

.meal-nutrition {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba($success, 0.05);
  border-radius: 8px;

  .nutrition-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;

    .nutrition-item {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;

      .nutrition-label {
        color: $gray;
        font-weight: 500;
      }

      .nutrition-value {
        color: $dark;
        font-weight: 600;
      }
    }
  }
}

.ingredients-section, .instructions-section {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba($warning, 0.05);
  border-radius: 8px;

  .ingredients-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 8px;

    .ingredient-item {
      display: flex;
      gap: 4px;
      font-size: 0.85rem;
      color: $dark;

      .ingredient-quantity {
        font-weight: 600;
        color: $primary;
      }

      .ingredient-unit {
        color: $gray;
      }

      .ingredient-name {
        flex: 1;
      }
    }
  }

  .instructions-list {
    .instruction-item {
      display: flex;
      gap: 12px;
      margin-bottom: 8px;
      font-size: 0.9rem;
      color: $dark;

      .instruction-number {
        background: $primary;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.8rem;
        flex-shrink: 0;
      }

      .instruction-text {
        line-height: 1.5;
      }
    }
  }
}

.target-info {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba($secondary, 0.05);
  border-radius: 8px;

  .targets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 8px;

    .target-item {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;

      .target-label {
        color: $gray;
        font-weight: 500;
      }

      .target-value {
        color: $dark;
        font-weight: 600;
      }
    }
  }
}

.meal-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;

  i {
    font-size: 0.8rem;
  }

  &.btn-sm {
    padding: 6px 12px;
    font-size: 0.8rem;
  }

  &.btn-outline {
    background: transparent;
    border: 1px solid $gray-lighter;
    color: $gray;

    &:hover {
      background: $light;
      color: $dark;
    }
  }

  &.btn-secondary {
    background: $secondary;
    color: $white;

    &:hover {
      background: darken($secondary, 10%);
    }
  }

  &.btn-primary {
    background: $primary;
    color: $white;

    &:hover {
      background: darken($primary, 10%);
    }
  }

  &.btn-info {
    background: $info;
    color: $white;

    &:hover {
      background: darken($info, 10%);
    }
  }

  &.btn-success {
    background: $success;
    color: $white;

    &:hover {
      background: darken($success, 10%);
    }
  }
}

.no-meals {
  text-align: center;
  padding: 60px 20px;
  color: $gray;

  i {
    font-size: 3rem;
    margin-bottom: 16px;
    display: block;
    color: $gray-light;
  }

  p {
    margin: 0;
    font-size: 1.1rem;
  }
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 32px;
  border-top: 1px solid $gray-lighter;
  background: rgba($gray, 0.02);
}

// Responsive design
@media (max-width: 768px) {
  .modal-overlay {
    padding: 10px;
  }

  .modal-content {
    max-height: 95vh;
  }

  .modal-header {
    padding: 20px 24px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    h2 {
      font-size: 1.4rem;
    }

    .ai-generation-info {
      order: -1;
    }

    .close-btn {
      position: absolute;
      top: 16px;
      right: 16px;
    }
  }

  .modal-body {
    padding: 24px 20px;
  }

  .overview-stats {
    grid-template-columns: 1fr;
  }

  .stat-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .meal-header {
    .meal-title-section {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .meal-meta {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
  }

  .nutrition-details {
    grid-template-columns: 1fr 1fr;
  }

  .ingredients-list {
    grid-template-columns: 1fr;
  }

  .meal-actions {
    flex-direction: column;
  }

  .modal-footer {
    padding: 20px 24px;
    flex-direction: column;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>