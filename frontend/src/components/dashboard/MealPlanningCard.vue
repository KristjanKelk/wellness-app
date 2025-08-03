<!-- src/components/dashboard/MealPlanningCard.vue -->
<template>
  <div class="meal-planning-card dashboard-card">
    <div class="card__header">
      <h3 class="card__title">
        <i class="fas fa-utensils card__icon"></i>
        Meal Planning
      </h3>
      <p class="card__subtitle">AI-powered nutrition planning</p>
    </div>

    <div class="card__content">
      <div class="features-grid">
        <div class="feature">
          <i class="fas fa-search"></i>
          <span>Browse {{ recipeCount }} Recipes</span>
        </div>
        <div class="feature">
          <i class="fas fa-user-cog"></i>
          <span>Set Nutrition Goals</span>
        </div>
        <div class="feature">
          <i class="fas fa-calendar-alt"></i>
          <span>Generate Meal Plans</span>
        </div>
        <div class="feature">
          <i class="fas fa-chart-line"></i>
          <span>Track Progress</span>
        </div>
      </div>

      <div class="quick-stats" v-if="hasNutritionProfile">
        <div class="stat">
          <span class="stat-label">Daily Calories</span>
          <span class="stat-value">{{ nutritionProfile?.calorie_target || 2000 }}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Protein Goal</span>
          <span class="stat-value">{{ Math.round(nutritionProfile?.protein_target || 0) }}g</span>
        </div>
      </div>

      <div class="setup-prompt" v-else>
        <i class="fas fa-arrow-right"></i>
        <span>Complete your nutrition profile to get started</span>
      </div>
    </div>

    <div class="card__actions">
      <button
        @click="$emit('navigate-to-meal-planning')"
        class="btn btn-primary"
      >
        <i class="fas fa-utensils"></i>
        Open Meal Planning
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MealPlanningCard',
  props: {
    nutritionProfile: {
      type: Object,
      default: null
    }
  },
  emits: ['navigate-to-meal-planning'],
  data() {
    return {
      recipeCount: 5000 // Updated with a more realistic number
    }
  },
  computed: {
    hasNutritionProfile() {
      return this.nutritionProfile && this.nutritionProfile.calorie_target;
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.meal-planning-card {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  overflow: hidden;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }
}

.card__header {
  padding: $spacing-4 $spacing-4 $spacing-2;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: $white;
  text-align: center;

  .card__title {
    margin: 0 0 $spacing-1 0;
    font-size: 1.3rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-2;
  }

  .card__icon {
    font-size: 1.2rem;
  }

  .card__subtitle {
    margin: 0;
    opacity: 0.9;
    font-size: 0.9rem;
  }
}

.card__content {
  padding: $spacing-4;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-3;
  margin-bottom: $spacing-4;
}

.feature {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  font-size: 0.9rem;
  color: $primary-dark;

  i {
    color: #667eea;
    font-size: 1rem;
    width: 16px;
  }
}

.quick-stats {
  display: flex;
  justify-content: space-between;
  padding: $spacing-3;
  background: rgba(#667eea, 0.05);
  border-radius: $border-radius;
  border-left: 4px solid #667eea;
}

.stat {
  text-align: center;

  .stat-label {
    display: block;
    font-size: 0.75rem;
    color: $gray;
    margin-bottom: 2px;
  }

  .stat-value {
    display: block;
    font-size: 1.1rem;
    font-weight: 600;
    color: $primary-dark;
  }
}

.setup-prompt {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  padding: $spacing-3;
  background: rgba($warning, 0.1);
  border-radius: $border-radius;
  color: darken($warning, 20%);
  font-size: 0.9rem;
  border-left: 4px solid $warning;

  i {
    font-size: 0.8rem;
  }
}

.card__actions {
  padding: 0 $spacing-4 $spacing-4;

  .btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-2;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    color: $white;
    padding: $spacing-3;
    border-radius: $border-radius;
    font-weight: 500;
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: $shadow;
    }

    i {
      font-size: 0.9rem;
    }
  }
}
</style>