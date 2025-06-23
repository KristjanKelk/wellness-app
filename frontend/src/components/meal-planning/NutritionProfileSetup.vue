<!-- src/components/meal-planning/NutritionProfileSetup.vue -->
<template>
  <div class="nutrition-profile-setup">
    <div class="profile-card">
      <div class="card-header">
        <h2>Your Nutrition Profile</h2>
        <p>Set up your dietary preferences and nutrition goals</p>
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
        <!-- Nutrition Targets -->
        <div class="form-section">
          <h3>Daily Nutrition Targets</h3>
          <div class="targets-grid">
            <div class="form-group">
              <label for="calorie_target">Daily Calories</label>
              <input
                id="calorie_target"
                v-model.number="formData.calorie_target"
                type="number"
                min="1000"
                max="5000"
                class="form-input"
                required
              />
              <span class="form-help">Recommended: 1800-2500 kcal</span>
            </div>

            <div class="form-group">
              <label for="protein_target">Protein (g)</label>
              <input
                id="protein_target"
                v-model.number="formData.protein_target"
                type="number"
                min="0"
                max="500"
                class="form-input"
                required
              />
            </div>

            <div class="form-group">
              <label for="carb_target">Carbs (g)</label>
              <input
                id="carb_target"
                v-model.number="formData.carb_target"
                type="number"
                min="0"
                max="1000"
                class="form-input"
                required
              />
            </div>

            <div class="form-group">
              <label for="fat_target">Fat (g)</label>
              <input
                id="fat_target"
                v-model.number="formData.fat_target"
                type="number"
                min="0"
                max="300"
                class="form-input"
                required
              />
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
      ]
    }
  },
  computed: {
    hasValidationErrors() {
      return this.validationErrors.length > 0 || this.dietaryConflicts.length > 0
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
</style>