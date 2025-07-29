<!-- src/components/meal-planning/NutritionProfileSetup.vue -->
<template>
  <div class="nutrition-profile-setup">
    <div class="profile-card">
      <div class="card-header">
        <h2>🎯 Your Personalized Nutrition Profile</h2>
        <p>Let AI help you create the perfect nutrition plan tailored to your goals</p>
        
        <!-- AI Quick Setup Button -->
        <button 
          v-if="!hasExistingProfile" 
          @click="showAIWizard = true"
          class="ai-wizard-btn"
          type="button"
        >
          <i class="fas fa-magic"></i>
          Generate with AI
        </button>
      </div>

      <!-- AI Wizard Modal -->
      <div v-if="showAIWizard" class="ai-wizard-overlay" @click="showAIWizard = false">
        <div class="ai-wizard-modal" @click.stop>
          <div class="ai-wizard-header">
            <h3>🤖 AI Nutrition Profile Generator</h3>
            <button @click="showAIWizard = false" class="close-btn">&times;</button>
          </div>
          
          <div class="ai-wizard-content">
            <div class="ai-step" v-if="aiStep === 1">
              <h4>Tell me about yourself</h4>
              <div class="form-grid">
                <div class="form-group">
                  <label>Age</label>
                  <input v-model.number="aiProfile.age" type="number" min="13" max="100" class="form-input" />
                </div>
                <div class="form-group">
                  <label>Gender</label>
                  <select v-model="aiProfile.gender" class="form-select">
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Height (cm)</label>
                  <input v-model.number="aiProfile.height" type="number" min="100" max="250" class="form-input" />
                </div>
                <div class="form-group">
                  <label>Weight (kg)</label>
                  <input v-model.number="aiProfile.weight" type="number" min="30" max="300" class="form-input" />
                </div>
              </div>
            </div>

            <div class="ai-step" v-if="aiStep === 2">
              <h4>What's your primary goal?</h4>
              <div class="goal-options">
                <button 
                  v-for="goal in goalOptions" 
                  :key="goal.value"
                  @click="aiProfile.goal = goal.value"
                  :class="['goal-option', { active: aiProfile.goal === goal.value }]"
                >
                  <div class="goal-icon">{{ goal.icon }}</div>
                  <div class="goal-text">
                    <h5>{{ goal.label }}</h5>
                    <p>{{ goal.description }}</p>
                  </div>
                </button>
              </div>
            </div>

            <div class="ai-step" v-if="aiStep === 3">
              <h4>Activity Level</h4>
              <div class="activity-options">
                <button 
                  v-for="activity in activityOptions" 
                  :key="activity.value"
                  @click="aiProfile.activity = activity.value"
                  :class="['activity-option', { active: aiProfile.activity === activity.value }]"
                >
                  <div class="activity-icon">{{ activity.icon }}</div>
                  <div class="activity-text">
                    <h5>{{ activity.label }}</h5>
                    <p>{{ activity.description }}</p>
                  </div>
                </button>
              </div>
            </div>

            <div class="ai-step" v-if="aiStep === 4">
              <h4>Dietary Preferences</h4>
              <div class="dietary-preferences">
                <button 
                  v-for="diet in popularDiets" 
                  :key="diet.value"
                  @click="toggleDiet(diet.value)"
                  :class="['diet-option', { active: aiProfile.diets.includes(diet.value) }]"
                >
                  <span class="diet-emoji">{{ diet.emoji }}</span>
                  <span>{{ diet.label }}</span>
                </button>
              </div>
            </div>

            <div class="ai-step" v-if="aiStep === 5">
              <div class="generating-profile" v-if="generatingProfile">
                <div class="spinner"></div>
                <h4>🧠 AI is analyzing your preferences...</h4>
                <p>Creating your personalized nutrition profile</p>
              </div>
              
              <div v-else class="profile-preview">
                <h4>✨ Your AI-Generated Profile</h4>
                <div class="profile-summary">
                  <div class="macro-preview">
                    <div class="macro-item">
                      <span class="macro-label">Daily Calories</span>
                      <span class="macro-value">{{ aiGeneratedProfile.calorie_target }}</span>
                    </div>
                    <div class="macro-item">
                      <span class="macro-label">Protein</span>
                      <span class="macro-value">{{ aiGeneratedProfile.protein_target }}g</span>
                    </div>
                    <div class="macro-item">
                      <span class="macro-label">Carbs</span>
                      <span class="macro-value">{{ aiGeneratedProfile.carb_target }}g</span>
                    </div>
                    <div class="macro-item">
                      <span class="macro-label">Fat</span>
                      <span class="macro-value">{{ aiGeneratedProfile.fat_target }}g</span>
                    </div>
                  </div>
                  
                  <div class="meal-plan-preview">
                    <h5>Recommended Meal Structure</h5>
                    <p>{{ aiGeneratedProfile.meals_per_day }} meals per day</p>
                    <p>{{ aiGeneratedProfile.snacks_per_day || 0 }} snacks per day</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="ai-wizard-footer">
            <button 
              v-if="aiStep > 1" 
              @click="aiStep--" 
              class="btn-secondary"
            >
              Back
            </button>
            
            <button 
              v-if="aiStep < 5" 
              @click="nextAIStep" 
              class="btn-primary"
              :disabled="!canProceedToNextStep"
            >
              Next
            </button>
            
            <button 
              v-if="aiStep === 5 && !generatingProfile" 
              @click="applyAIProfile" 
              class="btn-success"
            >
              Apply This Profile
            </button>
          </div>
        </div>
      </div>

      <!-- Validation Errors -->
      <div v-if="validationErrors.length > 0" class="error-messages">
        <div class="error-card">
          <h4>Please fix the following issues:</h4>
          <ul>
            <li v-for="error in validationErrors" :key="error">{{ error }}</li>
          </ul>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading your profile...</p>
      </div>

      <form v-else @submit.prevent="saveProfile" class="profile-form">
        <!-- Enhanced Nutrition Targets with Visual Indicators -->
        <div class="form-section">
          <h3>🎯 Daily Nutrition Targets</h3>
          <div class="targets-grid">
            <div class="form-group enhanced-input">
              <label for="calorie_target">Daily Calories</label>
              <div class="input-wrapper">
                <input
                  id="calorie_target"
                  v-model.number="formData.calorie_target"
                  type="number"
                  min="1000"
                  max="5000"
                  class="form-input"
                  required
                />
                <div class="input-hint">
                  <i class="fas fa-fire"></i>
                  <span>{{ getCalorieRecommendation() }}</span>
                </div>
              </div>
            </div>

            <div class="form-group enhanced-input">
              <label for="protein_target">Protein (g)</label>
              <div class="input-wrapper">
                <input
                  id="protein_target"
                  v-model.number="formData.protein_target"
                  type="number"
                  min="0"
                  max="500"
                  class="form-input"
                  required
                />
                <div class="input-hint">
                  <i class="fas fa-dumbbell"></i>
                  <span>{{ (formData.protein_target / formData.calorie_target * 100 * 4).toFixed(0) }}% of calories</span>
                </div>
              </div>
            </div>

            <div class="form-group enhanced-input">
              <label for="carb_target">Carbs (g)</label>
              <div class="input-wrapper">
                <input
                  id="carb_target"
                  v-model.number="formData.carb_target"
                  type="number"
                  min="0"
                  max="1000"
                  class="form-input"
                  required
                />
                <div class="input-hint">
                  <i class="fas fa-bread-slice"></i>
                  <span>{{ (formData.carb_target / formData.calorie_target * 100 * 4).toFixed(0) }}% of calories</span>
                </div>
              </div>
            </div>

            <div class="form-group enhanced-input">
              <label for="fat_target">Fat (g)</label>
              <div class="input-wrapper">
                <input
                  id="fat_target"
                  v-model.number="formData.fat_target"
                  type="number"
                  min="0"
                  max="300"
                  class="form-input"
                  required
                />
                <div class="input-hint">
                  <i class="fas fa-oil-can"></i>
                  <span>{{ (formData.fat_target / formData.calorie_target * 100 * 9).toFixed(0) }}% of calories</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Macro Distribution Visualization -->
          <div class="macro-distribution">
            <h4>Macronutrient Distribution</h4>
            <div class="macro-chart">
              <div class="macro-bar">
                <div 
                  class="macro-segment protein" 
                  :style="{ width: proteinPercentage + '%' }"
                ></div>
                <div 
                  class="macro-segment carbs" 
                  :style="{ width: carbPercentage + '%' }"
                ></div>
                <div 
                  class="macro-segment fat" 
                  :style="{ width: fatPercentage + '%' }"
                ></div>
              </div>
              <div class="macro-legend">
                <div class="legend-item">
                  <span class="legend-color protein"></span>
                  <span>Protein {{ proteinPercentage }}%</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color carbs"></span>
                  <span>Carbs {{ carbPercentage }}%</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color fat"></span>
                  <span>Fat {{ fatPercentage }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Dietary Preferences with Conflict Detection -->
        <div class="form-section">
          <h3>Dietary Preferences</h3>
          <div v-if="dietaryConflicts.length > 0" class="conflict-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <span>Warning: Some selected preferences may conflict with each other</span>
            <ul>
              <li v-for="conflict in dietaryConflicts" :key="conflict">{{ conflict }}</li>
            </ul>
          </div>
          <div class="preferences-grid">
            <label
              v-for="preference in availableDietaryPreferences"
              :key="preference.value"
              class="checkbox-label"
              :class="{ 'disabled': isPreferenceDisabled(preference.value) }"
            >
              <input
                v-model="formData.dietary_preferences"
                type="checkbox"
                :value="preference.value"
                :disabled="isPreferenceDisabled(preference.value)"
                class="checkbox-input"
                @change="checkDietaryConflicts"
              />
              <span class="checkbox-custom"></span>
              {{ preference.label }}
              <span v-if="isPreferenceDisabled(preference.value)" class="disabled-reason">
                (Conflicts with current selection)
              </span>
            </label>
          </div>
        </div>

        <!-- Allergies & Intolerances -->
        <div class="form-section">
          <h3>Allergies & Intolerances</h3>
          <div class="preferences-grid">
            <label
              v-for="allergy in availableAllergies"
              :key="allergy.value"
              class="checkbox-label"
            >
              <input
                v-model="formData.allergies_intolerances"
                type="checkbox"
                :value="allergy.value"
                class="checkbox-input"
              />
              <span class="checkbox-custom"></span>
              {{ allergy.label }}
            </label>
          </div>
        </div>

        <!-- Cuisine Preferences -->
        <div class="form-section">
          <h3>Favorite Cuisines</h3>
          <div class="preferences-grid">
            <label
              v-for="cuisine in availableCuisines"
              :key="cuisine.value"
              class="checkbox-label"
            >
              <input
                v-model="formData.cuisine_preferences"
                type="checkbox"
                :value="cuisine.value"
                class="checkbox-input"
              />
              <span class="checkbox-custom"></span>
              {{ cuisine.label }}
            </label>
          </div>
        </div>

        <!-- Disliked Ingredients -->
        <div class="form-section">
          <h3>Disliked Ingredients</h3>
          <div class="form-group">
            <label for="disliked_ingredients">Ingredients you want to avoid</label>
            <input
              id="disliked_ingredients"
              v-model="dislikedIngredientsInput"
              type="text"
              class="form-input"
              placeholder="Enter ingredients separated by commas (e.g., mushrooms, tofu, cilantro)"
              @blur="updateDislikedIngredients"
            />
            <span class="form-help">Separate multiple ingredients with commas</span>
            <div v-if="formData.disliked_ingredients.length > 0" class="ingredient-tags">
              <span
                v-for="ingredient in formData.disliked_ingredients"
                :key="ingredient"
                class="ingredient-tag"
              >
                {{ ingredient }}
                <button type="button" @click="removeDislikedIngredient(ingredient)" class="remove-tag">×</button>
              </span>
            </div>
          </div>
        </div>

        <!-- Meal Preferences -->
        <div class="form-section">
          <h3>Meal Preferences</h3>
          <div class="meal-prefs-grid">
            <div class="form-group">
              <label for="meals_per_day">Meals per Day</label>
              <select
                id="meals_per_day"
                v-model.number="formData.meals_per_day"
                class="form-select"
              >
                <option value="2">2 meals</option>
                <option value="3">3 meals</option>
                <option value="4">4 meals</option>
                <option value="5">5 meals</option>
                <option value="6">6 meals</option>
              </select>
            </div>

            <div class="form-group">
              <label for="timezone">Timezone</label>
              <select
                id="timezone"
                v-model="formData.timezone"
                class="form-select"
              >
                <option value="UTC">UTC</option>
                <option value="Europe/London">London</option>
                <option value="Europe/Berlin">Berlin</option>
                <option value="Europe/Tallinn">Tallinn (Estonia)</option>
                <option value="America/New_York">New York</option>
                <option value="America/Los_Angeles">Los Angeles</option>
                <option value="Asia/Tokyo">Tokyo</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Save Button -->
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="saving || hasValidationErrors">
            <span v-if="saving">
              <i class="fas fa-spinner fa-spin"></i>
              Saving...
            </span>
            <span v-else>
              <i class="fas fa-save"></i>
              Save Profile
            </span>
          </button>

          <button type="button" @click="calculateTargets" class="btn btn-secondary">
            <i class="fas fa-calculator"></i>
            Auto-Calculate Targets
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { mealPlanningApi } from '@/services/mealPlanningApi'

export default {
  name: 'NutritionProfileSetup',
  props: {
    profile: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['profile-updated'],
  data() {
    return {
      saving: false,
      validationErrors: [],
      dietaryConflicts: [],
      dislikedIngredientsInput: '',
      formData: {
        calorie_target: 2000,
        protein_target: 100,
        carb_target: 250,
        fat_target: 67,
        dietary_preferences: [],
        allergies_intolerances: [],
        cuisine_preferences: [],
        disliked_ingredients: [],
        meals_per_day: 3,
        timezone: 'Europe/Tallinn'
      },
      availableDietaryPreferences: [
        { value: 'vegetarian', label: 'Vegetarian', conflicts: ['paleo'] },
        { value: 'vegan', label: 'Vegan', conflicts: ['paleo', 'pescatarian', 'keto'] },
        { value: 'pescatarian', label: 'Pescatarian', conflicts: ['vegan', 'vegetarian', 'paleo'] },
        { value: 'keto', label: 'Ketogenic', conflicts: ['vegan', 'high_carb', 'mediterranean'] },
        { value: 'paleo', label: 'Paleo', conflicts: ['vegetarian', 'vegan', 'pescatarian', 'mediterranean'] },
        { value: 'mediterranean', label: 'Mediterranean', conflicts: ['keto', 'paleo', 'low_carb'] },
        { value: 'low_carb', label: 'Low Carb', conflicts: ['mediterranean', 'high_carb'] },
        { value: 'high_carb', label: 'High Carb', conflicts: ['keto', 'low_carb'] },
        { value: 'high_protein', label: 'High Protein', conflicts: [] },
        { value: 'gluten_free', label: 'Gluten Free', conflicts: [] },
        { value: 'dairy_free', label: 'Dairy Free', conflicts: [] },
        { value: 'low_sodium', label: 'Low Sodium', conflicts: [] },
        { value: 'diabetic', label: 'Diabetic Friendly', conflicts: ['high_carb'] },
        { value: 'heart_healthy', label: 'Heart Healthy', conflicts: [] },
        { value: 'whole30', label: 'Whole30', conflicts: ['vegetarian', 'vegan'] }
      ],
      availableAllergies: [
        { value: 'nuts', label: 'Tree Nuts' },
        { value: 'peanuts', label: 'Peanuts' },
        { value: 'dairy', label: 'Dairy/Lactose' },
        { value: 'gluten', label: 'Gluten' },
        { value: 'eggs', label: 'Eggs' },
        { value: 'fish', label: 'Fish' },
        { value: 'shellfish', label: 'Shellfish' },
        { value: 'soy', label: 'Soy' },
        { value: 'sesame', label: 'Sesame' },
        { value: 'sulfites', label: 'Sulfites' }
      ],
      availableCuisines: [
        { value: 'italian', label: 'Italian' },
        { value: 'mexican', label: 'Mexican' },
        { value: 'asian', label: 'Asian' },
        { value: 'indian', label: 'Indian' },
        { value: 'mediterranean', label: 'Mediterranean' },
        { value: 'american', label: 'American' },
        { value: 'french', label: 'French' },
        { value: 'thai', label: 'Thai' },
        { value: 'japanese', label: 'Japanese' },
        { value: 'chinese', label: 'Chinese' },
        { value: 'middle_eastern', label: 'Middle Eastern' },
        { value: 'korean', label: 'Korean' },
        { value: 'greek', label: 'Greek' },
        { value: 'spanish', label: 'Spanish' }
      ],
      aiStep: 1,
      showAIWizard: false,
      aiProfile: {
        age: null,
        gender: '',
        height: null,
        weight: null,
        goal: '',
        activity: '',
        diets: []
      },
      goalOptions: [
        { value: 'weight_loss', label: 'Weight Loss', icon: '🔥', description: 'Lose weight by burning more calories than you consume' },
        { value: 'muscle_gain', label: 'Muscle Gain', icon: '💪', description: 'Gain muscle mass while maintaining a healthy weight' },
        { value: 'maintenance', label: 'Maintenance', icon: '⚖️', description: 'Maintain your current weight and body composition' },
        { value: 'performance', label: 'Performance', icon: '⚽️', description: 'Optimize for athletic performance' }
      ],
      activityOptions: [
        { value: 'sedentary', label: 'Sedentary (little or no exercise)', icon: '💺' },
        { value: 'light', label: 'Lightly Active (exercise 1-3 days/week)', icon: '🏃' },
        { value: 'moderate', label: 'Moderately Active (exercise 3-5 days/week)', icon: '🏃‍♂️' },
        { value: 'very_active', label: 'Very Active (exercise 6-7 days/week)', icon: '🏃‍♂️' },
        { value: 'extra_active', label: 'Extra Active (very intense exercise, physical job, or 2x training)', icon: '💪' }
      ],
      popularDiets: [
        { value: 'keto', label: 'Ketogenic', emoji: '🧘‍♂️' },
        { value: 'paleo', label: 'Paleo', emoji: '🥑' },
        { value: 'mediterranean', label: 'Mediterranean', emoji: '🌊' },
        { value: 'low_carb', label: 'Low Carb', emoji: '🍎' },
        { value: 'high_protein', label: 'High Protein', emoji: '💪' },
        { value: 'vegan', label: 'Vegan', emoji: '🌱' },
        { value: 'vegetarian', label: 'Vegetarian', emoji: '🥦' },
        { value: 'gluten_free', label: 'Gluten Free', emoji: '🌾' },
        { value: 'dairy_free', label: 'Dairy Free', emoji: '🥛' },
        { value: 'low_sodium', label: 'Low Sodium', emoji: '🧂' }
      ],
      aiGeneratedProfile: null,
      generatingProfile: false,
      hasExistingProfile: false
    }
  },
  computed: {
    hasValidationErrors() {
      return this.validationErrors.length > 0 || this.dietaryConflicts.length > 0
    },
    proteinPercentage() {
      if (this.formData.calorie_target === 0) return 0;
      return Math.round((this.formData.protein_target * 4 / this.formData.calorie_target) * 100);
    },
    carbPercentage() {
      if (this.formData.calorie_target === 0) return 0;
      return Math.round((this.formData.carb_target * 4 / this.formData.calorie_target) * 100);
    },
    fatPercentage() {
      if (this.formData.calorie_target === 0) return 0;
      return Math.round((this.formData.fat_target * 9 / this.formData.calorie_target) * 100);
    },
    canProceedToNextStep() {
      switch (this.aiStep) {
        case 1:
          return this.aiProfile.age && this.aiProfile.gender && this.aiProfile.height && this.aiProfile.weight;
        case 2:
          return this.aiProfile.goal;
        case 3:
          return this.aiProfile.activity;
        case 4:
          return true; // Optional step
        default:
          return true;
      }
    }
  },
  watch: {
    profile: {
      immediate: true,
      handler(newProfile) {
        if (newProfile) {
          this.formData = { ...this.formData, ...newProfile }
          // Update disliked ingredients input
          if (newProfile.disliked_ingredients) {
            this.dislikedIngredientsInput = newProfile.disliked_ingredients.join(', ')
          }
          this.checkDietaryConflicts()
          this.hasExistingProfile = true;
        } else {
          this.hasExistingProfile = false;
        }
      }
    }
  },
  methods: {
    async saveProfile() {
      // Validate form first
      this.validateForm()
      if (this.hasValidationErrors) {
        return
      }

      this.saving = true
      try {
        // Call the API directly instead of just emitting
        const response = await mealPlanningApi.updateNutritionProfile(this.formData)

        // Emit the updated profile to parent component
        this.$emit('profile-updated', response.data)

        // Show success message
        this.$toast?.success?.('Nutrition profile saved successfully!') ||
        alert('Nutrition profile saved successfully!')

      } catch (error) {
        console.error('Error saving profile:', error)
        const errorMessage = error.response?.data?.detail ||
                            error.response?.data?.message ||
                            error.message ||
                            'Failed to save nutrition profile'

        this.$toast?.error?.(errorMessage) ||
        alert(errorMessage)
      } finally {
        this.saving = false
      }
    },

    validateForm() {
      this.validationErrors = []

      // Validate calorie target
      if (!this.formData.calorie_target || this.formData.calorie_target < 1000 || this.formData.calorie_target > 5000) {
        this.validationErrors.push('Daily calories must be between 1000 and 5000')
      }

      // Validate protein target
      if (!this.formData.protein_target || this.formData.protein_target < 0 || this.formData.protein_target > 500) {
        this.validationErrors.push('Protein target must be between 0 and 500g')
      }

      // Validate carb target
      if (!this.formData.carb_target || this.formData.carb_target < 0 || this.formData.carb_target > 1000) {
        this.validationErrors.push('Carbohydrate target must be between 0 and 1000g')
      }

      // Validate fat target
      if (!this.formData.fat_target || this.formData.fat_target < 0 || this.formData.fat_target > 300) {
        this.validationErrors.push('Fat target must be between 0 and 300g')
      }

      // Check if total macros match calories approximately
      const totalCaloriesFromMacros = (this.formData.protein_target * 4) +
                                     (this.formData.carb_target * 4) +
                                     (this.formData.fat_target * 9)

      const calorieDifference = Math.abs(totalCaloriesFromMacros - this.formData.calorie_target)
      if (calorieDifference > 100) {
        this.validationErrors.push(`Macro calories (${Math.round(totalCaloriesFromMacros)}) don't match calorie target (${this.formData.calorie_target}). Difference: ${Math.round(calorieDifference)} calories`)
      }
    },

    checkDietaryConflicts() {
      this.dietaryConflicts = []
      const selected = this.formData.dietary_preferences

      // Check for conflicts between selected preferences
      for (let i = 0; i < selected.length; i++) {
        for (let j = i + 1; j < selected.length; j++) {
          const pref1 = this.availableDietaryPreferences.find(p => p.value === selected[i])
          const pref2 = this.availableDietaryPreferences.find(p => p.value === selected[j])

          if (pref1?.conflicts?.includes(selected[j])) {
            this.dietaryConflicts.push(`${pref1.label} conflicts with ${pref2.label}`)
          }
        }
      }
    },

    isPreferenceDisabled(preferenceValue) {
      const selected = this.formData.dietary_preferences
      if (selected.includes(preferenceValue)) return false

      const preference = this.availableDietaryPreferences.find(p => p.value === preferenceValue)
      if (!preference?.conflicts) return false

      // Check if any selected preference conflicts with this one
      return selected.some(selectedPref => preference.conflicts.includes(selectedPref))
    },

    updateDislikedIngredients() {
      if (this.dislikedIngredientsInput.trim()) {
        this.formData.disliked_ingredients = this.dislikedIngredientsInput
          .split(',')
          .map(ingredient => ingredient.trim())
          .filter(ingredient => ingredient.length > 0)
      } else {
        this.formData.disliked_ingredients = []
      }
    },

    removeDislikedIngredient(ingredient) {
      this.formData.disliked_ingredients = this.formData.disliked_ingredients.filter(
        item => item !== ingredient
      )
      this.dislikedIngredientsInput = this.formData.disliked_ingredients.join(', ')
    },

    calculateTargets() {
      // Get user's health profile for better calculation
      const baseCalories = 2000 // This should ideally come from health profile

      // Check selected dietary preferences for macro distribution
      const isKeto = this.formData.dietary_preferences.includes('keto')
      const isLowCarb = this.formData.dietary_preferences.includes('low_carb')
      const isHighProtein = this.formData.dietary_preferences.includes('high_protein')

      let proteinRatio, carbRatio, fatRatio

      if (isKeto) {
        proteinRatio = 0.25
        carbRatio = 0.05
        fatRatio = 0.70
      } else if (isLowCarb) {
        proteinRatio = 0.30
        carbRatio = 0.20
        fatRatio = 0.50
      } else if (isHighProtein) {
        proteinRatio = 0.35
        carbRatio = 0.35
        fatRatio = 0.30
      } else {
        // Standard balanced diet
        proteinRatio = 0.25
        carbRatio = 0.45
        fatRatio = 0.30
      }

      this.formData.calorie_target = baseCalories
      this.formData.protein_target = Math.round((baseCalories * proteinRatio) / 4)
      this.formData.carb_target = Math.round((baseCalories * carbRatio) / 4)
      this.formData.fat_target = Math.round((baseCalories * fatRatio) / 9)

      // Validate after auto-calculation
      this.validateForm()
    },

    async applyAIProfile() {
      try {
        // Apply the AI-generated profile to the form
        this.formData = { ...this.formData, ...this.aiGeneratedProfile }
        this.hasExistingProfile = true
        this.showAIWizard = false
        
        // Save the profile automatically
        await this.saveProfile()
        
        this.$toast?.success?.('🎉 AI-generated nutrition profile applied successfully!')
      } catch (error) {
        console.error('Error applying AI profile:', error)
        this.$toast?.error?.('Failed to apply AI profile. Please try manually adjusting your settings.')
      }
    },

    async nextAIStep() {
      if (this.aiStep === 4) {
        // Generate AI profile when moving from step 4 to 5
        this.generatingProfile = true
        this.aiStep++
        
        try {
          // Call AI service to generate nutrition profile
          const response = await mealPlanningApi.generateNutritionProfile({
            user_data: {
              age: this.aiProfile.age,
              gender: this.aiProfile.gender,
              height: this.aiProfile.height,
              weight: this.aiProfile.weight
            },
            goals: {
              primary_goal: this.aiProfile.goal,
              activity_level: this.aiProfile.activity
            },
            preferences: {
              dietary_preferences: this.aiProfile.diets
            }
          })
          
          this.aiGeneratedProfile = response.data
          
          // Auto-apply after 2 seconds for better UX
          setTimeout(() => {
            this.generatingProfile = false
          }, 2000)
          
        } catch (error) {
          console.error('Error generating AI profile:', error)
          // Fallback to manual calculation
          this.aiGeneratedProfile = this.calculateAIProfile()
          this.generatingProfile = false
        }
      } else if (this.aiStep < 5) {
        this.aiStep++
      }
    },

    calculateAIProfile() {
      // Fallback calculation if AI service fails
      const { age, gender, height, weight, goal, activity } = this.aiProfile
      
      // Calculate BMR using Mifflin-St Jeor Equation
      let bmr
      if (gender === 'male') {
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
      } else {
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
      }
      
      // Activity multipliers
      const activityMultipliers = {
        sedentary: 1.2,
        light: 1.375,
        moderate: 1.55,
        very_active: 1.725,
        extra_active: 1.9
      }
      
      let tdee = bmr * (activityMultipliers[activity] || 1.2)
      
      // Adjust for goals
      if (goal === 'weight_loss') {
        tdee -= 500 // 1 lb per week
      } else if (goal === 'muscle_gain') {
        tdee += 300 // Moderate surplus
      }
      
      // Calculate macros based on diet preferences
      let proteinRatio = 0.25
      let carbRatio = 0.45
      let fatRatio = 0.30
      
      if (this.aiProfile.diets.includes('keto')) {
        proteinRatio = 0.25
        carbRatio = 0.05
        fatRatio = 0.70
      } else if (this.aiProfile.diets.includes('high_protein')) {
        proteinRatio = 0.35
        carbRatio = 0.40
        fatRatio = 0.25
      } else if (this.aiProfile.diets.includes('low_carb')) {
        proteinRatio = 0.30
        carbRatio = 0.20
        fatRatio = 0.50
      }
      
      return {
        calorie_target: Math.round(tdee),
        protein_target: Math.round(tdee * proteinRatio / 4),
        carb_target: Math.round(tdee * carbRatio / 4),
        fat_target: Math.round(tdee * fatRatio / 9),
        meals_per_day: goal === 'muscle_gain' ? 4 : 3,
        snacks_per_day: goal === 'muscle_gain' ? 2 : 1,
        dietary_preferences: this.aiProfile.diets
      }
    },

    getCalorieRecommendation() {
      const calories = this.formData.calorie_target
      if (calories < 1200) return 'Very Low (may be too restrictive)'
      if (calories < 1800) return 'Low (weight loss focused)'
      if (calories < 2500) return 'Moderate (maintenance/slow change)'
      if (calories < 3000) return 'High (muscle gain/active lifestyle)'
      return 'Very High (intensive training)'
    },

    toggleDiet(diet) {
      const index = this.aiProfile.diets.indexOf(diet);
      if (index > -1) {
        this.aiProfile.diets.splice(index, 1);
      } else {
        this.aiProfile.diets.push(diet);
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.nutrition-profile-setup {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  overflow: hidden;
}

.card-header {
  padding: $spacing-6;
  background: linear-gradient(135deg, $primary, lighten($primary, 10%));
  color: $white;
  text-align: center;

  h2 {
    margin: 0 0 $spacing-2 0;
    font-size: 1.8rem;
    font-weight: 600;
  }

  p {
    margin: 0;
    opacity: 0.9;
  }
}

.error-messages {
  padding: $spacing-4 $spacing-6;
  background: #fee;
  border-bottom: 1px solid $gray-lighter;
}

.error-card {
  color: #c53030;

  h4 {
    margin: 0 0 $spacing-2 0;
    font-size: 1rem;
  }

  ul {
    margin: 0;
    padding-left: $spacing-4;
  }
}

.conflict-warning {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: $border-radius;
  padding: $spacing-3;
  margin-bottom: $spacing-4;
  color: #856404;

  i {
    margin-right: $spacing-2;
  }

  ul {
    margin: $spacing-2 0 0 0;
    padding-left: $spacing-4;
  }
}

.loading-state {
  padding: $spacing-8;
  text-align: center;
  color: $gray;
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

.profile-form {
  padding: $spacing-6;
}

.form-section {
  margin-bottom: $spacing-8;

  h3 {
    margin: 0 0 $spacing-4 0;
    color: $primary-dark;
    font-size: 1.2rem;
    font-weight: 600;
    padding-bottom: $spacing-2;
    border-bottom: 2px solid $gray-lighter;
  }
}

.targets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: $spacing-4;
}

.meal-prefs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: $spacing-4;
}

.preferences-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: $spacing-3;
}

.form-group {
  label {
    display: block;
    margin-bottom: $spacing-2;
    font-weight: 500;
    color: $primary-dark;
  }
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

.form-help {
  display: block;
  margin-top: $spacing-1;
  font-size: 0.85rem;
  color: $gray;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  cursor: pointer;
  padding: $spacing-2;
  border-radius: $border-radius;
  transition: background-color 0.2s ease;

  &:hover:not(.disabled) {
    background-color: rgba($primary, 0.05);
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;

    .disabled-reason {
      font-size: 0.8rem;
      color: $gray;
      font-style: italic;
    }
  }
}

.checkbox-input {
  display: none;

  &:checked + .checkbox-custom {
    background-color: $primary;
    border-color: $primary;

    &::after {
      opacity: 1;
    }
  }

  &:disabled + .checkbox-custom {
    background-color: $gray-lighter;
    border-color: $gray-lighter;
  }
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid $gray-lighter;
  border-radius: 4px;
  position: relative;
  transition: all 0.2s ease;

  &::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: $white;
    font-size: 12px;
    font-weight: bold;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
}

.ingredient-tags {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-2;
  margin-top: $spacing-2;
}

.ingredient-tag {
  background: $primary;
  color: $white;
  padding: $spacing-1 $spacing-2;
  border-radius: $border-radius;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: $spacing-1;

  .remove-tag {
    background: none;
    border: none;
    color: $white;
    cursor: pointer;
    font-weight: bold;
    padding: 0;
    margin-left: $spacing-1;

    &:hover {
      color: rgba($white, 0.7);
    }
  }
}

.form-actions {
  display: flex;
  gap: $spacing-4;
  justify-content: center;
  padding-top: $spacing-4;
  border-top: 1px solid $gray-lighter;

  @include responsive('sm') {
    flex-direction: column;
  }
}

.btn {
  padding: 12px 24px;
  border-radius: $border-radius;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  display: flex;
  align-items: center;
  gap: $spacing-2;

  &.btn-primary {
    background: $primary;
    color: $white;

    &:hover:not(:disabled) {
      background: darken($primary, 10%);
    }

    &:disabled {
      background: $gray-lighter;
      cursor: not-allowed;
    }
  }

  &.btn-secondary {
    background: $gray-light;
    color: $primary-dark;

    &:hover {
      background: darken($gray-light, 5%);
    }
  }
}

.ai-wizard-btn {
  background: $secondary;
  color: $white;
  padding: $spacing-2 $spacing-4;
  border-radius: $border-radius;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: $spacing-2;
  margin-top: $spacing-4;
  box-shadow: $shadow-sm;

  &:hover {
    background: darken($secondary, 10%);
  }

  i {
    font-size: 1rem;
  }
}

.ai-wizard-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba($black, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.ai-wizard-modal {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-lg;
  width: 90%;
  max-width: 600px;
  max-height: 90%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-wizard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-4;
  background: $primary;
  color: $white;
  border-bottom: 1px solid darken($primary, 10%);

  h3 {
    margin: 0;
    font-size: 1.5rem;
  }

  .close-btn {
    background: none;
    border: none;
    color: $white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: $spacing-1;
    line-height: 1;
  }
}

.ai-wizard-content {
  flex-grow: 1;
  padding: $spacing-4;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.ai-step {
  display: none;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;

  &.active {
    display: block;
    opacity: 1;
    transform: translateY(0);
  }

  h4 {
    margin-bottom: $spacing-3;
    color: $primary-dark;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: $spacing-4;
}

.goal-options, .activity-options, .dietary-preferences {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: $spacing-3;
}

.goal-option, .activity-option, .diet-option {
  background: $gray-lightest;
  border: 1px solid $gray-lighter;
  border-radius: $border-radius;
  padding: $spacing-3;
  display: flex;
  align-items: center;
  gap: $spacing-2;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: $gray-lighter;
    border-color: $primary;
  }

  &.active {
    background: $primary;
    color: $white;
    border-color: $primary;
  }
}

.goal-icon, .activity-icon {
  font-size: 1.5rem;
}

.goal-text, .activity-text {
  h5 {
    margin: 0 0 $spacing-1 0;
    font-size: 1rem;
  }

  p {
    margin: 0;
    font-size: 0.8rem;
    color: $gray;
  }
}

.diet-emoji {
  font-size: 1.5rem;
}

.generating-profile {
  text-align: center;
  padding: $spacing-6;
  color: $gray;

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid $gray-lighter;
    border-left: 4px solid $primary;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto $spacing-3;
  }

  h4 {
    margin: 0 0 $spacing-2 0;
    font-size: 1.2rem;
  }

  p {
    font-size: 0.9rem;
  }
}

.profile-preview {
  padding: $spacing-4;
  background: $gray-lightest;
  border-radius: $border-radius;
  margin-top: $spacing-4;

  h4 {
    margin-bottom: $spacing-3;
    color: $primary-dark;
  }

  .profile-summary {
    display: flex;
    flex-direction: column;
    gap: $spacing-3;
  }

  .macro-preview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: $spacing-2;
    text-align: center;

    .macro-item {
      .macro-label {
        display: block;
        font-size: 0.8rem;
        color: $gray;
        margin-bottom: $spacing-1;
      }
      .macro-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: $primary;
      }
    }
  }

  .meal-plan-preview {
    margin-top: $spacing-3;
    padding-top: $spacing-3;
    border-top: 1px dashed $gray-lighter;

    h5 {
      margin-bottom: $spacing-2;
      color: $primary-dark;
    }

    p {
      margin: 0;
      font-size: 0.9rem;
      color: $gray;
    }
  }
}

 .enhanced-input {
   .input-wrapper {
     position: relative;
   }
   
   .input-hint {
     display: flex;
     align-items: center;
     gap: $spacing-1;
     margin-top: $spacing-1;
     font-size: 0.8rem;
     color: $gray;
     
     i {
       color: $primary;
     }
   }
 }

 .macro-distribution {
   margin-top: $spacing-6;
   padding-top: $spacing-4;
   border-top: 1px dashed $gray-lighter;
 
   h4 {
     margin-bottom: $spacing-3;
     color: $primary-dark;
   }
 
   .macro-chart {
     position: relative;
     height: 20px;
     background: $gray-lightest;
     border-radius: $border-radius;
     overflow: hidden;
     margin-bottom: $spacing-2;
   }
 
   .macro-bar {
     position: absolute;
     top: 0;
     left: 0;
     height: 100%;
     width: 100%;
     border-radius: $border-radius;
     display: flex;
   }
 
   .macro-segment {
     height: 100%;
     transition: width 0.3s ease-in-out;
 
     &.protein {
       background: #e74c3c;
     }
     &.carbs {
       background: #3498db;
     }
     &.fat {
       background: #f39c12;
     }
   }
 
   .macro-legend {
     display: flex;
     justify-content: space-around;
     font-size: 0.8rem;
     color: $gray;
 
     .legend-item {
       display: flex;
       align-items: center;
       gap: $spacing-1;
 
       .legend-color {
         display: inline-block;
         width: 10px;
         height: 10px;
         border-radius: 50%;
         
         &.protein {
           background: #e74c3c;
         }
         &.carbs {
           background: #3498db;
         }
         &.fat {
           background: #f39c12;
         }
       }
     }
   }
 }
</style>