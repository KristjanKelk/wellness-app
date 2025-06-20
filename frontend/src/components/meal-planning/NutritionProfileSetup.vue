<!-- src/components/meal-planning/NutritionProfileSetup.vue -->
<template>
  <div class="nutrition-profile-setup">
    <div class="profile-card">
      <div class="card-header">
        <h2>Your Nutrition Profile</h2>
        <p>Set up your dietary preferences and nutrition goals</p>
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

        <!-- Dietary Preferences -->
        <div class="form-section">
          <h3>Dietary Preferences</h3>
          <div class="preferences-grid">
            <label
              v-for="preference in availableDietaryPreferences"
              :key="preference.value"
              class="checkbox-label"
            >
              <input
                v-model="formData.dietary_preferences"
                type="checkbox"
                :value="preference.value"
                class="checkbox-input"
              />
              <span class="checkbox-custom"></span>
              {{ preference.label }}
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
                <option value="America/New_York">New York</option>
                <option value="America/Los_Angeles">Los Angeles</option>
                <option value="Asia/Tokyo">Tokyo</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Save Button -->
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            <span v-if="saving">Saving...</span>
            <span v-else>Save Profile</span>
          </button>

          <button type="button" @click="calculateTargets" class="btn btn-secondary">
            Auto-Calculate Targets
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
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
      formData: {
        calorie_target: 2000,
        protein_target: 100,
        carb_target: 250,
        fat_target: 67,
        dietary_preferences: [],
        allergies_intolerances: [],
        cuisine_preferences: [],
        meals_per_day: 3,
        timezone: 'UTC'
      },
      availableDietaryPreferences: [
        { value: 'vegetarian', label: 'Vegetarian' },
        { value: 'vegan', label: 'Vegan' },
        { value: 'pescatarian', label: 'Pescatarian' },
        { value: 'keto', label: 'Ketogenic' },
        { value: 'paleo', label: 'Paleo' },
        { value: 'mediterranean', label: 'Mediterranean' },
        { value: 'low_carb', label: 'Low Carb' },
        { value: 'high_protein', label: 'High Protein' },
        { value: 'gluten_free', label: 'Gluten Free' },
        { value: 'dairy_free', label: 'Dairy Free' }
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
        { value: 'sesame', label: 'Sesame' }
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
        { value: 'chinese', label: 'Chinese' }
      ]
    }
  },
  watch: {
    profile: {
      immediate: true,
      handler(newProfile) {
        if (newProfile) {
          this.formData = { ...this.formData, ...newProfile }
        }
      }
    }
  },
  methods: {
    async saveProfile() {
      this.saving = true
      try {
        this.$emit('profile-updated', this.formData)
      } catch (error) {
        console.error('Error saving profile:', error)
      } finally {
        this.saving = false
      }
    },

    calculateTargets() {
      // Simple calculation based on activity level and goals
      // In a real app, this would use the health profile data
      const baseCalories = 2000
      const proteinRatio = 0.25
      const carbRatio = 0.45
      const fatRatio = 0.30

      this.formData.calorie_target = baseCalories
      this.formData.protein_target = Math.round((baseCalories * proteinRatio) / 4)
      this.formData.carb_target = Math.round((baseCalories * carbRatio) / 4)
      this.formData.fat_target = Math.round((baseCalories * fatRatio) / 9)
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

  &:hover {
    background-color: rgba($primary, 0.05);
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
</style>