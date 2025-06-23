<!-- src/components/meal-planning/MealPlanDetailModal.vue -->
<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ formatPlanType(mealPlan.plan_type) }} Meal Plan</h2>
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
              <span class="stat-label">Average Daily Calories:</span>
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
          </div>
        </div>

        <div class="meals-section" v-if="mealPlan.meal_plan_data && mealPlan.meal_plan_data.meals">
          <h3>Meal Details</h3>
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
                    <h5 class="meal-title">
                      {{ meal.recipe?.title || `${formatMealType(meal.meal_type)}` }}
                    </h5>
                    <span class="meal-time">{{ meal.time || '12:00' }}</span>
                  </div>

                  <div class="meal-nutrition" v-if="meal.recipe?.nutrition || meal.recipe?.estimated_nutrition">
                    <div class="nutrition-item">
                      <span>Calories: {{ (meal.recipe.nutrition?.calories || meal.recipe.estimated_nutrition?.calories || 0) }}</span>
                    </div>
                    <div class="nutrition-item">
                      <span>Protein: {{ (meal.recipe.nutrition?.protein || meal.recipe.estimated_nutrition?.protein || 0) }}g</span>
                    </div>
                    <div class="nutrition-item">
                      <span>Carbs: {{ (meal.recipe.nutrition?.carbs || meal.recipe.estimated_nutrition?.carbs || 0) }}g</span>
                    </div>
                    <div class="nutrition-item">
                      <span>Fat: {{ (meal.recipe.nutrition?.fat || meal.recipe.estimated_nutrition?.fat || 0) }}g</span>
                    </div>
                  </div>

                  <div class="meal-actions">
                    <button
                      @click="regenerateMeal(date, meal.meal_type)"
                      class="btn btn-sm btn-outline"
                    >
                      <i class="fas fa-redo"></i>
                      Regenerate
                    </button>
                    <button
                      @click="getAlternatives(date, meal.meal_type)"
                      class="btn btn-sm btn-secondary"
                    >
                      <i class="fas fa-exchange-alt"></i>
                      Alternatives
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
        <button @click="generateShoppingList" class="btn btn-primary">
          <i class="fas fa-shopping-cart"></i>
          Generate Shopping List
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
  emits: ['close', 'regenerate-meal', 'get-alternatives'],
  methods: {
    formatPlanType(type) {
      return type.charAt(0).toUpperCase() + type.slice(1)
    },

    formatDateRange(startDate, endDate) {
      const start = new Date(startDate).toLocaleDateString()
      const end = new Date(endDate).toLocaleDateString()

      if (startDate === endDate) {
        return start
      }
      return `${start} - ${end}`
    },

    formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric'
      })
    },

    formatMealType(type) {
      return type.charAt(0).toUpperCase() + type.slice(1)
    },

    getTotalMeals() {
      if (!this.mealPlan.meal_plan_data?.meals) return 0

      let total = 0
      Object.values(this.mealPlan.meal_plan_data.meals).forEach(dayMeals => {
        total += dayMeals.length
      })
      return total
    },

    regenerateMeal(date, mealType) {
      this.$emit('regenerate-meal', {
        day: date,
        mealType: mealType
      })
    },

    getAlternatives(date, mealType) {
      this.$emit('get-alternatives', {
        day: date,
        mealType: mealType
      })
    },

    generateShoppingList() {
      // TODO: Implement shopping list generation
      alert('Shopping list generation coming soon!')
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
  max-width: 900px;
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

  h2 {
    margin: 0;
    font-size: 1.6rem;
    color: #333;
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
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
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
  gap: 16px;
}

.meal-card {
  background: $white;
  border: 1px solid $gray-lighter;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
  }
}

.meal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .meal-title {
    margin: 0;
    font-size: 1.1rem;
    color: $dark;
    font-weight: 600;
  }

  .meal-time {
    background: $light;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 0.85rem;
    color: $gray;
    font-weight: 500;
  }
}

.meal-nutrition {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: rgba($primary, 0.05);
  border-radius: 6px;

  .nutrition-item {
    font-size: 0.85rem;
    color: $gray;

    span {
      font-weight: 500;
    }
  }
}

.meal-actions {
  display: flex;
  gap: 8px;
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

    h2 {
      font-size: 1.4rem;
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
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .meal-nutrition {
    grid-template-columns: 1fr 1fr;
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