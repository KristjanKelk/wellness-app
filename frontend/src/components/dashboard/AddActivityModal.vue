<!-- src/components/dashboard/AddActivityModal.vue -->
<template>
  <div class="modal is-active" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Log New Activity</h2>
        <button class="close-button" @click="$emit('close')" aria-label="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="activity-form">
        <!-- Activity Type Selection -->
        <div class="form-group">
          <label class="form-label">Activity Type</label>
          <div class="activity-type-grid">
            <button
              v-for="type in activityTypes"
              :key="type.value"
              type="button"
              @click="activity.activity_type = type.value"
              :class="{ active: activity.activity_type === type.value }"
              class="activity-type-btn"
            >
              <span class="activity-type-icon">{{ type.icon }}</span>
              <span class="activity-type-label">{{ type.label }}</span>
            </button>
          </div>
        </div>

        <!-- Activity Name -->
        <div class="form-group">
          <label for="activityName" class="form-label">Activity Name</label>
          <input
            type="text"
            id="activityName"
            v-model="activity.name"
            class="form-control"
            placeholder="e.g., Morning Run, Yoga Session"
            required
          />
        </div>

        <!-- Duration -->
        <div class="form-group">
          <label for="duration" class="form-label">Duration (minutes)</label>
          <div class="duration-input">
            <input
              type="number"
              id="duration"
              v-model.number="activity.duration_minutes"
              class="form-control"
              min="1"
              max="480"
              required
            />
            <div class="duration-presets">
              <button
                v-for="preset in durationPresets"
                :key="preset"
                type="button"
                @click="activity.duration_minutes = preset"
                class="preset-btn"
              >
                {{ preset }}m
              </button>
            </div>
          </div>
        </div>

        <!-- Distance (conditional) -->
        <div v-if="showDistanceField" class="form-group">
          <label for="distance" class="form-label">Distance (km)</label>
          <input
            type="number"
            id="distance"
            v-model.number="activity.distance_km"
            class="form-control"
            min="0"
            step="0.1"
            placeholder="Optional"
          />
        </div>

        <!-- Location -->
        <div class="form-group">
          <label for="location" class="form-label">Location</label>
          <select
            id="location"
            v-model="activity.location"
            class="form-control"
          >
            <option value="home">Home</option>
            <option value="gym">Gym</option>
            <option value="outdoors">Outdoors</option>
            <option value="other">Other</option>
          </select>
        </div>

        <!-- Calories Burned (optional) -->
        <div class="form-group">
          <label for="calories" class="form-label">
            Calories Burned (optional)
            <button
              type="button"
              @click="estimateCalories"
              class="estimate-btn"
              v-if="activity.activity_type && activity.duration_minutes"
            >
              Estimate
            </button>
          </label>
          <input
            type="number"
            id="calories"
            v-model.number="activity.calories_burned"
            class="form-control"
            min="0"
            placeholder="Optional"
          />
        </div>

        <!-- Notes -->
        <div class="form-group">
          <label for="notes" class="form-label">Notes (optional)</label>
          <textarea
            id="notes"
            v-model="activity.notes"
            class="form-control"
            rows="3"
            placeholder="How did you feel? Any achievements?"
          ></textarea>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button
            type="button"
            class="btn btn-secondary"
            @click="$emit('close')"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading || !isFormValid"
          >
            <span v-if="loading" class="loading-spinner"></span>
            {{ loading ? 'Saving...' : 'Save Activity' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AddActivityModal',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      activity: {
        name: '',
        activity_type: 'cardio',
        duration_minutes: null,
        location: 'home',
        distance_km: null,
        calories_burned: null,
        notes: ''
      },
      activityTypes: [
        { value: 'cardio', label: 'Cardio', icon: '🏃' },
        { value: 'strength', label: 'Strength', icon: '💪' },
        { value: 'flexibility', label: 'Flexibility', icon: '🧘' },
        { value: 'sports', label: 'Sports', icon: '⚽' },
        { value: 'hiit', label: 'HIIT', icon: '⚡' },
        { value: 'yoga', label: 'Yoga', icon: '🧘' },
        { value: 'other', label: 'Other', icon: '🏋️' }
      ],
      durationPresets: [15, 30, 45, 60, 90, 120]
    };
  },
  computed: {
    showDistanceField() {
      return ['cardio', 'sports'].includes(this.activity.activity_type);
    },
    isFormValid() {
      return this.activity.name &&
             this.activity.activity_type &&
             this.activity.duration_minutes > 0;
    }
  },
  methods: {
    handleSubmit() {
      if (!this.isFormValid) return;

      // Clean up null values and ensure proper data types
      const activityData = {
        name: this.activity.name,
        activity_type: this.activity.activity_type,
        duration_minutes: parseInt(this.activity.duration_minutes),
        location: this.activity.location,
        distance_km: this.activity.distance_km ? parseFloat(this.activity.distance_km) : null,
        calories_burned: this.activity.calories_burned ? parseInt(this.activity.calories_burned) : null,
        notes: this.activity.notes || null
      };

      this.$emit('save', activityData);
    },
    estimateCalories() {
      // Simple calorie estimation based on activity type and duration
      const caloriesPerMinute = {
        cardio: 10,
        strength: 8,
        flexibility: 3,
        sports: 9,
        hiit: 12,
        yoga: 4,
        other: 6
      };

      const rate = caloriesPerMinute[this.activity.activity_type] || 6;
      this.activity.calories_burned = Math.round(this.activity.duration_minutes * rate);
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.modal {
  @include modal-container;
}

.modal-content {
  @include modal-content;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-6;

  h2 {
    margin: 0;
    font-size: $font-size-xl;
  }
}

.close-button {
  background: none;
  border: none;
  color: $gray;
  cursor: pointer;
  padding: $spacing-2;
  border-radius: $border-radius;
  transition: $transition-base;

  &:hover {
    background-color: $gray-lighter;
    color: $secondary;
  }
}

.activity-form {
  .form-group {
    margin-bottom: $spacing-6;
  }

  .form-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-2;
    font-weight: $font-weight-medium;
    color: $secondary;
  }

  .form-control {
    width: 100%;
    padding: $spacing-3;
    border: 1px solid $gray-light;
    border-radius: $border-radius;
    font-size: $font-size-base;
    transition: $transition-base;

    &:focus {
      outline: none;
      border-color: $primary;
      box-shadow: 0 0 0 3px rgba($primary, 0.1);
    }
  }

  textarea.form-control {
    resize: vertical;
    min-height: 80px;
  }
}

.activity-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: $spacing-3;
}

.activity-type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-2;
  padding: $spacing-3;
  background-color: $white;
  border: 2px solid $gray-lighter;
  border-radius: $border-radius;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    border-color: $primary;
    background-color: rgba($primary, 0.05);
  }

  &.active {
    border-color: $primary;
    background-color: rgba($primary, 0.1);
    color: $primary;
  }

  .activity-type-icon {
    font-size: 1.5rem;
  }

  .activity-type-label {
    font-size: $font-size-sm;
    font-weight: $font-weight-medium;
  }
}

.duration-input {
  display: flex;
  gap: $spacing-3;
  align-items: center;

  .form-control {
    flex: 1;
  }

  .duration-presets {
    display: flex;
    gap: $spacing-2;
  }
}

.preset-btn {
  padding: $spacing-2 $spacing-3;
  background-color: $gray-lighter;
  border: none;
  border-radius: $border-radius-sm;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    background-color: $primary;
    color: $white;
  }
}

.estimate-btn {
  padding: $spacing-1 $spacing-2;
  background-color: $primary;
  color: $white;
  border: none;
  border-radius: $border-radius-sm;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    background-color: $primary-dark;
  }
}

.alert {
  padding: $spacing-3;
  border-radius: $border-radius;
  margin-bottom: $spacing-4;

  &.alert-error {
    background-color: rgba($error, 0.1);
    color: $error;
    border: 1px solid rgba($error, 0.3);
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-3;
  margin-top: $spacing-6;
  padding-top: $spacing-6;
  border-top: 1px solid $gray-lighter;
}

.loading-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
  margin-right: $spacing-2;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>