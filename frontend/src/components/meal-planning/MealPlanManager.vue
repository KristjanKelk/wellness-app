<!-- src/components/meal-planning/MealPlanManager.vue -->
<template>
  <div class="meal-plan-manager">
    <!-- AI Generation Status -->
    <div v-if="generationStatus" class="generation-status" :class="generationStatus.type">
      <div class="status-content">
        <i :class="generationStatus.icon"></i>
        <div class="status-text">
          <h4>{{ generationStatus.title }}</h4>
          <p>{{ generationStatus.message }}</p>
          <div v-if="generationStatus.steps" class="generation-steps">
            <div
              v-for="(step, index) in generationStatus.steps"
              :key="index"
              class="step"
              :class="{ 'completed': step.completed, 'active': step.active }"
            >
              <i :class="step.completed ? 'fas fa-check' : step.active ? 'fas fa-spinner fa-spin' : 'fas fa-clock'"></i>
              <span>{{ step.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate New Meal Plan Section -->
    <div class="generate-section">
      <div class="section-header">
        <h2>AI-Powered Meal Planning</h2>
        <p>Let our advanced AI create a personalized meal plan based on your health profile, dietary preferences, and nutrition goals</p>
      </div>

      <form @submit.prevent="generateMealPlan" class="generate-form">
        <div class="form-row">
          <div class="form-group">
            <label for="plan_type">Plan Type</label>
            <select
              id="plan_type"
              v-model="generateForm.plan_type"
              class="form-select"
            >
              <option value="daily">Daily Plan (1 day)</option>
              <option value="weekly">Weekly Plan (7 days)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="start_date">Start Date</label>
            <input
              id="start_date"
              v-model="generateForm.start_date"
              type="date"
              class="form-input"
              :min="today"
            />
          </div>

          <div class="form-group">
            <label for="target_calories">Target Calories (optional)</label>
            <input
              id="target_calories"
              v-model.number="generateForm.target_calories"
              type="number"
              min="1000"
              max="5000"
              placeholder="Uses your health profile default"
              class="form-input"
            />
            <small class="form-hint">Leave empty to use your calculated target from health profile</small>
          </div>
        </div>

        <div class="advanced-options" v-if="showAdvancedOptions">
          <h4>Advanced Options</h4>
          <div class="form-row">
            <div class="form-group">
              <label>Preferred Cuisines (override profile)</label>
              <div class="checkbox-group">
                <label v-for="cuisine in availableCuisines" :key="cuisine" class="checkbox-label">
                  <input
                    type="checkbox"
                    :value="cuisine"
                    v-model="generateForm.cuisine_preferences"
                  />
                  <span>{{ cuisine }}</span>
                </label>
              </div>
            </div>

            <div class="form-group">
              <label for="max_cook_time">Max Cooking Time (minutes)</label>
              <input
                id="max_cook_time"
                v-model.number="generateForm.max_cook_time"
                type="number"
                min="10"
                max="120"
                placeholder="No limit"
                class="form-input"
              />
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button
            type="button"
            @click="showAdvancedOptions = !showAdvancedOptions"
            class="btn btn-outline"
          >
            <i :class="showAdvancedOptions ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
            {{ showAdvancedOptions ? 'Hide' : 'Show' }} Advanced Options
          </button>

          <button
            type="submit"
            class="btn btn-primary generate-btn"
            :disabled="generating"
          >
            <i class="fas fa-brain" v-if="!generating"></i>
            <i class="fas fa-spinner fa-spin" v-else></i>
            {{ generating ? 'AI is Creating Your Plan...' : 'Generate AI Meal Plan' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Existing Meal Plans Section -->
    <div class="existing-plans-section">
      <div class="section-header">
        <h2>Your AI-Generated Meal Plans</h2>
        <p>Previously generated personalized meal plans</p>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading your meal plans...</p>
      </div>

      <div v-else-if="mealPlans.length === 0" class="empty-state">
        <i class="fas fa-brain"></i>
        <h3>No AI meal plans yet</h3>
        <p>Generate your first AI-powered, personalized meal plan above!</p>
      </div>

      <div v-else class="meal-plans-grid">
        <div
          v-for="plan in mealPlans"
          :key="plan.id"
          class="meal-plan-card"
          @click="viewMealPlan(plan)"
        >

          <div class="plan-header">
            <h3>{{ plan ? formatPlanType(plan.plan_type) : 'Loading...' }} Plan</h3>
            <span class="plan-date">{{ plan ? formatDateRange(plan.start_date, plan.end_date) : 'Date unknown' }}</span>
            <div class="ai-badge">
              <i class="fas fa-brain"></i>
              <span>AI v{{ plan.generation_version || '1.0' }}</span>
            </div>
          </div>

          <div class="plan-stats">
            <div class="stat">
              <span class="stat-value">{{ plan?.avg_daily_calories ? Math.round(plan.avg_daily_calories) : 'N/A' }}</span>
              <span class="stat-label">Avg Calories</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ getMealCount(plan) }}</span>
              <span class="stat-label">Meals</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ plan.nutritional_balance_score?.toFixed(1) || 'N/A' }}</span>
              <span class="stat-label">Balance Score</span>
            </div>
          </div>

          <div class="plan-nutrition" v-if="plan.daily_averages">
            <h4>Daily Nutrition Averages</h4>
            <div class="nutrition-grid">
              <div class="nutrition-item">
                <span class="nutrition-label">Protein:</span>
                <span class="nutrition-value">{{ Math.round(plan.daily_averages.protein || 0) }}g</span>
              </div>
              <div class="nutrition-item">
                <span class="nutrition-label">Carbs:</span>
                <span class="nutrition-value">{{ Math.round(plan.daily_averages.carbs || 0) }}g</span>
              </div>
              <div class="nutrition-item">
                <span class="nutrition-label">Fat:</span>
                <span class="nutrition-value">{{ Math.round(plan.daily_averages.fat || 0) }}g</span>
              </div>
            </div>
          </div>

          <div class="quality-scores" v-if="plan.variety_score || plan.preference_match_score">
            <div class="score-item">
              <span class="score-label">Variety:</span>
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (plan.variety_score * 10) + '%' }"></div>
              </div>
              <span class="score-value">{{ plan.variety_score?.toFixed(1) || 'N/A' }}</span>
            </div>
            <div class="score-item">
              <span class="score-label">Preference:</span>
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (plan.preference_match_score * 10) + '%' }"></div>
              </div>
              <span class="score-value">{{ plan.preference_match_score?.toFixed(1) || 'N/A' }}</span>
            </div>
          </div>

          <div class="plan-actions">
            <button @click.stop="viewMealPlan(plan)" class="btn btn-outline">
              <i class="fas fa-eye"></i>
              View Details
            </button>
            <button @click.stop="analyzeMealPlan(plan)" class="btn btn-info">
              <i class="fas fa-chart-line"></i>
              AI Analysis
            </button>
            <button @click.stop="regeneratePlan(plan)" class="btn btn-secondary">
              <i class="fas fa-redo"></i>
              Regenerate
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Meal Plan Detail Modal -->
    <meal-plan-detail-modal
      v-if="selectedPlan"
      :meal-plan="selectedPlan"
      @close="selectedPlan = null"
      @regenerate-meal="(mealData) => regenerateMeal(selectedPlan.id, mealData)"
      @get-alternatives="(mealData) => getMealAlternatives(selectedPlan.id, mealData)"
      @analyze-plan="analyzeMealPlanFromModal"
    />

    <!-- Nutritional Analysis Modal -->
    <nutritional-analysis-modal
      v-if="showAnalysisModal && currentAnalysis"
      :analysis="currentAnalysis"
      :meal-plan="selectedPlanForAnalysis"
      @close="closeAnalysisModal"
    />
  </div>
</template>

<script>
import { mealPlanningApi } from '@/services/mealPlanningApi'
import MealPlanDetailModal from './MealPlanDetailModal.vue'
import NutritionalAnalysisModal from './NutritionalAnalysisModal.vue'

export default {
  name: 'MealPlanManager',
  components: {
    MealPlanDetailModal,
    NutritionalAnalysisModal
  },
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['meal-plan-generated'],
  data() {
    return {
      mealPlans: [],
      selectedPlan: null,
      selectedPlanForAnalysis: null,
      currentAnalysis: null,
      showAnalysisModal: false,
      generating: false,
      showAdvancedOptions: false,
      generationStatus: null,
      generateForm: {
        plan_type: 'daily',
        start_date: '',
        target_calories: null,
        cuisine_preferences: [],
        max_cook_time: null
      },
      availableCuisines: [
        'Mediterranean', 'Asian', 'Italian', 'Mexican', 'American',
        'Indian', 'Middle Eastern', 'French', 'Japanese', 'Thai'
      ]
    }
  },
  computed: {
    today() {
      return new Date().toISOString().split('T')[0]
    }
  },
  async mounted() {
    // Set default start date to today
    this.generateForm.start_date = this.today
    await this.loadMealPlans()
  },
  methods: {
    async loadMealPlans() {
      try {
        console.log('=== Loading Meal Plans ===')
        const response = await mealPlanningApi.getMealPlans()
        console.log('API response status:', response?.status)
        console.log('API response data type:', typeof response?.data)
        
        // Handle different response structures safely
        const mealPlansData = response?.data?.results || response?.data || []
        console.log('Found', mealPlansData.length, 'meal plans')
        
        // Log each plan briefly
        mealPlansData.forEach((plan, index) => {
          console.log(`Plan ${index + 1}:`, {
            id: plan.id,
            type: plan.plan_type,
            hasMealData: !!plan.meal_plan_data,
            hasMeals: !!plan.meal_plan_data?.meals,
            dateRange: `${plan.start_date} to ${plan.end_date}`
          })
        })
        
        this.mealPlans = mealPlansData
        console.log('Meal plans loaded successfully')
        console.log('==========================')
      } catch (error) {
        console.error('=== Failed to load meal plans ===')
        console.error('Error:', error.message)
        console.error('Response:', error.response?.data)
        console.error('================================')
        this.mealPlans = [] // Set empty array to prevent null errors
        this.showError('Failed to load meal plans')
      }
    },

    // Helper method to count meals in a plan based on the new structure
    getMealCount(plan) {
      if (!plan?.meal_plan_data?.meals) {
        console.log('getMealCount: No meal_plan_data.meals found for plan', plan?.id)
        return 'N/A'
      }
      
      let totalMeals = 0
      Object.values(plan.meal_plan_data.meals).forEach(dayMeals => {
        if (Array.isArray(dayMeals)) {
          totalMeals += dayMeals.length
        }
      })
      
      console.log(`getMealCount: Plan ${plan.id} has ${totalMeals} total meals`)
      return totalMeals || 'N/A'
    },

    async generateMealPlan() {
      this.generating = true
      this.showGenerationStatus()

      try {
        const planData = { ...this.generateForm }

        // Clean up form data
        if (!planData.target_calories) {
          delete planData.target_calories
        }
        if (!planData.max_cook_time) {
          delete planData.max_cook_time
        }
        if (planData.cuisine_preferences.length === 0) {
          delete planData.cuisine_preferences
        }

        // Update generation status
        this.updateGenerationStep('strategy', true)

        const response = await mealPlanningApi.generateMealPlan(planData)
        
        // Update status to show recipe saving
        this.updateGenerationStep('recipes', true)

        // Mark all steps as completed
        this.generationStatus.steps.forEach(step => {
          step.completed = true
          step.active = false
        })

        // Show success status
        this.generationStatus = {
          type: 'success',
          icon: 'fas fa-check-circle',
          title: 'Meal Plan Generated Successfully!',
          message: 'Your personalized AI meal plan is ready to view. All recipes have been saved to your recipe library.'
        }

        // Add to meal plans list
        this.mealPlans.unshift(response.data)

        this.showSuccess('AI meal plan generated successfully!')
        this.$emit('meal-plan-generated', response.data)

        // Clear the status after a delay
        setTimeout(() => {
          this.generationStatus = null
          this.viewMealPlan(response.data)
        }, 2000)

      } catch (error) {
        console.error('Failed to generate meal plan:', error)
        this.generationStatus = {
          type: 'error',
          icon: 'fas fa-exclamation-circle',
          title: 'Generation Failed',
          message: 'Failed to generate meal plan. Please try again.'
        }
        this.showError('Failed to generate meal plan. Please try again.')

        setTimeout(() => {
          this.generationStatus = null
        }, 3000)
      } finally {
        this.generating = false
      }
    },

    showGenerationStatus() {
      this.generationStatus = {
        type: 'generating',
        icon: 'fas fa-brain',
        title: 'AI is Creating Your Meal Plan',
        message: 'Our AI is analyzing your profile and generating personalized meals...',
        steps: [
          { name: 'Analyzing your health profile', completed: false, active: true },
          { name: 'Creating meal strategy', completed: false, active: false },
          { name: 'Generating meal structure', completed: false, active: false },
          { name: 'Creating detailed recipes', completed: false, active: false },
          { name: 'Optimizing nutrition balance', completed: false, active: false }
        ]
      }

      // Simulate step progression
      setTimeout(() => this.updateGenerationStep('strategy'), 1000)
      setTimeout(() => this.updateGenerationStep('structure'), 3000)
      setTimeout(() => this.updateGenerationStep('recipes'), 5000)
      setTimeout(() => this.updateGenerationStep('optimization'), 7000)
    },

    updateGenerationStep(stepType, forceComplete = false) {
      if (!this.generationStatus || !this.generationStatus.steps) return

      const stepIndex = {
        'profile': 0,
        'strategy': 1,
        'structure': 2,
        'recipes': 3,
        'optimization': 4
      }[stepType]

      if (stepIndex !== undefined) {
        // Complete previous steps
        for (let i = 0; i < stepIndex; i++) {
          this.generationStatus.steps[i].completed = true
          this.generationStatus.steps[i].active = false
        }

        // Update current step
        if (forceComplete) {
          this.generationStatus.steps[stepIndex].completed = true
          this.generationStatus.steps[stepIndex].active = false
        } else {
          this.generationStatus.steps[stepIndex].active = true
        }
      }
    },

    async regeneratePlan(plan) {
      try {
        const confirmed = confirm('Generate a new AI meal plan with the same settings? This will create a completely new plan.')
        if (!confirmed) return

        this.generating = true
        this.showGenerationStatus()

        const planData = {
          plan_type: plan.plan_type,
          start_date: plan.start_date
        }

        const response = await mealPlanningApi.generateMealPlan(planData)

        // Add new plan to the beginning of the list
        this.mealPlans.unshift(response.data)

        this.generationStatus = {
          type: 'success',
          icon: 'fas fa-check-circle',
          title: 'New Meal Plan Generated!',
          message: 'Your fresh AI meal plan is ready. New recipes have been added to your library.'
        }

        this.showSuccess('New AI meal plan generated!')
        this.$emit('meal-plan-generated', response.data)

        setTimeout(() => {
          this.generationStatus = null
        }, 2000)

      } catch (error) {
        console.error('Failed to regenerate meal plan:', error)
        this.generationStatus = {
          type: 'error',
          icon: 'fas fa-exclamation-circle',
          title: 'Regeneration Failed',
          message: 'Failed to regenerate meal plan.'
        }
        this.showError('Failed to regenerate meal plan')

        setTimeout(() => {
          this.generationStatus = null
        }, 3000)
      } finally {
        this.generating = false
      }
    },

    viewMealPlan(plan) {
      console.log('=== Meal Plan Details ===')
      console.log('Plan ID:', plan?.id)
      console.log('Plan Type:', plan?.plan_type)
      console.log('Has meal_plan_data:', !!plan?.meal_plan_data)
      console.log('Has meals:', !!plan?.meal_plan_data?.meals)
      console.log('Meals structure:', plan?.meal_plan_data?.meals)
      if (plan?.meal_plan_data?.meals) {
        console.log('Available meal dates:', Object.keys(plan.meal_plan_data.meals))
        console.log('Sample meal data for first date:', Object.values(plan.meal_plan_data.meals)[0])
      }
      console.log('=========================')
      this.selectedPlan = plan
    },

    async regenerateMeal(planId, mealData) {
      try {
        console.log('=== Regenerating Meal ===')
        console.log('Plan ID:', planId)
        console.log('Meal Data:', mealData)
        
        if (!mealData) {
          console.error('regenerateMeal: mealData is null/undefined')
          throw new Error('Meal data is required')
        }
        
        const { day, mealType } = mealData
        console.log('Day:', day)
        console.log('Meal Type:', mealType)
        
        if (!day || !mealType) {
          console.error('regenerateMeal: day or mealType missing', { day, mealType })
          throw new Error('Day and meal type are required')
        }
        
        console.log('Making API call to regenerate meal...')
        const response = await mealPlanningApi.regenerateMeal(planId, day, mealType)
        console.log('Regeneration successful, updating UI...')

        // Update the meal plan in our list
        const planIndex = this.mealPlans.findIndex(p => p.id === planId)
        if (planIndex !== -1) {
          this.mealPlans[planIndex] = response.data
          this.selectedPlan = response.data
          console.log('Meal plan updated in list')
        }

        this.showSuccess(`${mealType} meal regenerated successfully!`)
        console.log('========================')
      } catch (error) {
        console.error('=== Failed to regenerate meal ===')
        console.error('Error message:', error.message)
        console.error('Error response:', error.response?.data)
        console.error('Full error:', error)
        console.error('================================')
        this.showError(`Failed to regenerate meal: ${error.message}`)
      }
    },

    async getMealAlternatives(planId, mealData) {
      try {
        console.log('=== Getting Meal Alternatives ===')
        console.log('Plan ID:', planId)
        console.log('Meal Data:', mealData)
        
        if (!mealData) {
          console.error('getMealAlternatives: mealData is null/undefined')
          throw new Error('Meal data is required')
        }
        
        const { day, mealType } = mealData
        console.log('Day:', day)
        console.log('Meal Type:', mealType)
        
        if (!day || !mealType) {
          console.error('getMealAlternatives: day or mealType missing', { day, mealType })
          throw new Error('Day and meal type are required')
        }
        
        console.log('Making API call to get alternatives...')
        const response = await mealPlanningApi.getMealAlternatives(planId, day, mealType)
        console.log('Alternatives retrieved:', response.data?.length || 0, 'options')
        console.log('===============================')
        return response.data || []
      } catch (error) {
        console.error('=== Failed to get meal alternatives ===')
        console.error('Error message:', error.message)
        console.error('Error response:', error.response?.data)
        console.error('Full error:', error)
        console.error('=====================================')
        this.showError(`Failed to get meal alternatives: ${error.message}`)
        return []
      }
    },

    async analyzeMealPlan(plan) {
      try {
        this.selectedPlanForAnalysis = plan

        // Show loading state
        this.currentAnalysis = {
          loading: true,
          message: 'AI is analyzing your meal plan nutrition...'
        }
        this.showAnalysisModal = true

        const response = await mealPlanningApi.analyzeMealPlan(plan.id)
        this.currentAnalysis = response.data

      } catch (error) {
        console.error('Failed to analyze meal plan:', error)
        this.currentAnalysis = {
          error: true,
          message: 'Failed to analyze meal plan. Please try again.'
        }
        this.showError('Failed to analyze meal plan')
      }
    },

    async analyzeMealPlanFromModal(plan) {
      // Close the detail modal first
      this.selectedPlan = null
      // Then trigger the analysis
      await this.analyzeMealPlan(plan)
    },

    closeAnalysisModal() {
      this.showAnalysisModal = false
      this.currentAnalysis = null
      this.selectedPlanForAnalysis = null
    },

    formatPlanType(planType) {
      if (!planType || typeof planType !== 'string') {
        return 'Unknown'
      }
      return planType.charAt(0).toUpperCase() + planType.slice(1)
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

    showSuccess(message) {
      this.$toast?.success?.(message) || alert(message)
    },

    showError(message) {
      this.$toast?.error?.(message) || alert(message)
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.meal-plan-manager {
  max-width: 1200px;
  margin: 0 auto;
}

// Generation Status Styles
.generation-status {
  margin-bottom: $spacing-6;
  padding: $spacing-5;
  border-radius: $border-radius-lg;
  border-left: 4px solid;

  &.generating {
    background: linear-gradient(135deg, rgba(#007bff, 0.1), rgba(#007bff, 0.05));
    border-left-color: #007bff;
  }

  &.success {
    background: linear-gradient(135deg, rgba(#28a745, 0.1), rgba(#28a745, 0.05));
    border-left-color: #28a745;
  }

  &.error {
    background: linear-gradient(135deg, rgba(#dc3545, 0.1), rgba(#dc3545, 0.05));
    border-left-color: #dc3545;
  }
}

.status-content {
  display: flex;
  align-items: flex-start;
  gap: $spacing-4;

  i {
    font-size: 1.5rem;
    margin-top: 2px;

    .generating & { color: #007bff; }
    .success & { color: #28a745; }
    .error & { color: #dc3545; }
  }
}

.status-text {
  flex: 1;

  h4 {
    margin: 0 0 $spacing-2 0;
    font-size: 1.2rem;
    font-weight: 600;
  }

  p {
    margin: 0;
    color: $gray;
  }
}

.generation-steps {
  margin-top: $spacing-4;
  display: flex;
  flex-direction: column;
  gap: $spacing-2;
}

.step {
  display: flex;
  align-items: center;
  gap: $spacing-3;
  padding: $spacing-2;
  border-radius: $border-radius;
  transition: all 0.3s ease;

  &.completed {
    background: rgba(#28a745, 0.1);

    i { color: #28a745; }
    span { color: #28a745; font-weight: 500; }
  }

  &.active {
    background: rgba(#007bff, 0.1);

    i { color: #007bff; }
    span { color: #007bff; font-weight: 500; }
  }

  i {
    font-size: 0.9rem;
    width: 16px;
    color: $gray-light;
  }

  span {
    font-size: 0.9rem;
    color: $gray;
  }
}

// Enhanced form styles
.generate-section, .existing-plans-section {
  margin-bottom: $spacing-8;
}

.section-header {
  text-align: center;
  margin-bottom: $spacing-6;

  h2 {
    margin: 0 0 $spacing-2 0;
    color: $primary-dark;
    font-size: 1.8rem;
    font-weight: 600;
  }

  p {
    margin: 0;
    color: $gray;
    font-size: 1.1rem;
    max-width: 600px;
    margin: 0 auto;
  }
}

.generate-form {
  background: $white;
  padding: $spacing-6;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  border: 1px solid $gray-lighter;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: $spacing-4;
  margin-bottom: $spacing-5;
}

.form-group {
  label {
    display: block;
    margin-bottom: $spacing-2;
    font-weight: 500;
    color: $primary-dark;
  }
}

.form-hint {
  display: block;
  margin-top: $spacing-1;
  font-size: 0.85rem;
  color: $gray;
}

.form-input, .form-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid $gray-lighter;
  border-radius: $border-radius;
  font-size: 1rem;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: $primary;
    box-shadow: 0 0 0 3px rgba($primary, 0.1);
  }
}

.advanced-options {
  margin-top: $spacing-5;
  padding-top: $spacing-5;
  border-top: 1px solid $gray-lighter;

  h4 {
    margin: 0 0 $spacing-4 0;
    color: $primary-dark;
    font-size: 1.1rem;
  }
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: $spacing-2;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  padding: $spacing-2;
  border-radius: $border-radius;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background: rgba($primary, 0.05);
  }

  input[type="checkbox"] {
    margin: 0;
  }
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: $spacing-4;
  margin-top: $spacing-6;
}

.generate-btn {
  flex: 1;
  max-width: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-2;
  padding: $spacing-4;
  font-size: 1.1rem;
  font-weight: 600;
  background: linear-gradient(135deg, $primary, lighten($primary, 10%));
  border: none;
  color: $white;
  border-radius: $border-radius;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  &:disabled {
    opacity: 0.8;
    cursor: not-allowed;
  }

  i {
    font-size: 1rem;
  }
}

// Enhanced meal plan cards
.meal-plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: $spacing-6;
}

.meal-plan-card {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  padding: $spacing-5;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid $gray-lighter;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
  }

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(135deg, $primary, lighten($primary, 20%));
  }
}

.plan-header {
  margin-bottom: $spacing-4;
  position: relative;

  h3 {
    margin: 0 0 $spacing-1 0;
    color: $primary-dark;
    font-size: 1.3rem;
    font-weight: 600;
  }

  .plan-date {
    color: $gray;
    font-size: 0.9rem;
  }

  .ai-badge {
    position: absolute;
    top: 0;
    right: 0;
    background: linear-gradient(135deg, #6f42c1, #8b5cf6);
    color: white;
    padding: 4px 8px;
    border-radius: $border-radius;
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    gap: 4px;

    i {
      font-size: 0.7rem;
    }
  }
}

.plan-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: $spacing-4;
  padding: $spacing-3;
  background: rgba($primary, 0.05);
  border-radius: $border-radius;
}

.stat {
  text-align: center;

  .stat-value {
    display: block;
    font-size: 1.3rem;
    font-weight: 600;
    color: $primary-dark;
    margin-bottom: 2px;
  }

  .stat-label {
    display: block;
    font-size: 0.75rem;
    color: $gray;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

// New nutrition display section
.plan-nutrition {
  margin-bottom: $spacing-4;
  padding: $spacing-3;
  background: rgba(#28a745, 0.05);
  border-radius: $border-radius;

  h4 {
    margin: 0 0 $spacing-2 0;
    font-size: 0.9rem;
    color: $primary-dark;
    font-weight: 600;
  }

  .nutrition-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: $spacing-2;
  }

  .nutrition-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;

    .nutrition-label {
      color: $gray;
      font-weight: 500;
    }

    .nutrition-value {
      color: $primary-dark;
      font-weight: 600;
    }
  }
}

.quality-scores {
  margin-bottom: $spacing-4;
}

.score-item {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  margin-bottom: $spacing-2;

  .score-label {
    font-size: 0.85rem;
    color: $gray;
    min-width: 80px;
  }

  .score-bar {
    flex: 1;
    height: 6px;
    background: $gray-lighter;
    border-radius: 3px;
    overflow: hidden;

    .score-fill {
      height: 100%;
      background: linear-gradient(90deg, #28a745, #20c997);
      transition: width 0.3s ease;
    }
  }

  .score-value {
    font-size: 0.85rem;
    font-weight: 500;
    color: $primary-dark;
    min-width: 30px;
    text-align: right;
  }
}

.plan-actions {
  display: flex;
  gap: $spacing-2;

  .btn {
    flex: 1;
    padding: $spacing-2;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;

    i {
      font-size: 0.8rem;
    }

    &.btn-info {
      background: #17a2b8;
      color: white;
      border: none;

      &:hover {
        background: #138496;
      }
    }
  }
}

// Loading and empty states
.loading-state, .empty-state {
  text-align: center;
  padding: $spacing-8;
  color: $gray;
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid $gray-lighter;
  border-left: 4px solid $primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto $spacing-4;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: $spacing-4;
  display: block;
  color: $gray-light;
}

// Responsive design
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .generate-btn {
    max-width: none;
  }

  .meal-plans-grid {
    grid-template-columns: 1fr;
  }

  .plan-actions {
    flex-direction: column;
  }

  .nutrition-grid {
    grid-template-columns: 1fr;
  }
}
</style>