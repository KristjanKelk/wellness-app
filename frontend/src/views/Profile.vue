<template>
  <div class="profile-container">
    <h1>Health Profile</h1>
    <p class="profile-description">Complete your health profile to receive personalized recommendations and insights.</p>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your profile data...</p>
    </div>

    <form v-else @submit.prevent="saveProfile" class="profile-form">
      <!-- Personal Information Section -->
      <section class="form-section">
        <h2>Personal Information</h2>
        <p class="section-description">Basic information helps us personalize your experience.</p>

        <div class="form-row">
          <div class="form-group">
            <label for="age">Age</label>
            <input
              type="number"
              id="age"
              v-model.number="profile.age"
              placeholder="Your age"
              min="13"
              max="120"
            >
            <small v-if="validationErrors.age" class="error-text">{{ validationErrors.age }}</small>
          </div>

          <div class="form-group">
            <label for="gender">Gender</label>
            <select id="gender" v-model="profile.gender">
              <option value="">Select gender</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Physical Metrics Section -->
      <section class="form-section">
        <h2>Physical Metrics</h2>
        <p class="section-description">Your height and weight help us calculate important health indicators like BMI.</p>

        <div class="form-row">
          <div class="form-group">
            <label for="height">Height (cm)</label>
            <input
              type="number"
              id="height"
              v-model.number="profile.height_cm"
              placeholder="Your height in cm"
              min="100"
              max="250"
              step="0.1"
            >
            <small v-if="validationErrors.height_cm" class="error-text">{{ validationErrors.height_cm }}</small>
          </div>

          <div class="form-group">
            <label for="weight">Weight (kg)</label>
            <input
              type="number"
              id="weight"
              v-model.number="profile.weight_kg"
              placeholder="Your weight in kg"
              min="30"
              max="300"
              step="0.1"
            >
            <small v-if="validationErrors.weight_kg" class="error-text">{{ validationErrors.weight_kg }}</small>
          </div>
        </div>

        <div class="metrics-summary" v-if="profile.height_cm && profile.weight_kg">
          <div class="metric-item">
            <span class="metric-label">Current BMI:</span>
            <span class="metric-value">{{ calculateBMI().toFixed(1) }}</span>
            <span class="metric-category">{{ getBMICategory() }}</span>
          </div>
        </div>
      </section>

      <!-- Lifestyle & Goals Section -->
      <section class="form-section">
        <h2>Lifestyle & Goals</h2>
        <p class="section-description">Tell us about your lifestyle and what you want to achieve.</p>

        <div class="form-group">
          <label for="occupation">Occupation Type</label>
          <input
            type="text"
            id="occupation"
            v-model="profile.occupation_type"
            placeholder="e.g., Office worker, Construction, etc."
          >
        </div>

        <div class="form-group">
          <label for="activity">Activity Level</label>
          <select id="activity" v-model="profile.activity_level">
            <option value="sedentary">Sedentary (little or no exercise)</option>
            <option value="light">Lightly Active (light exercise 1-3 days/week)</option>
            <option value="moderate">Moderately Active (moderate exercise 3-5 days/week)</option>
            <option value="active">Active (hard exercise 6-7 days/week)</option>
            <option value="very_active">Very Active (very hard exercise & physical job)</option>
          </select>
          <small class="help-text">Choose the option that best describes your typical week.</small>
        </div>

        <div class="form-group">
          <label for="goal">Fitness Goal</label>
          <select id="goal" v-model="profile.fitness_goal">
            <option value="weight_loss">Weight Loss</option>
            <option value="muscle_gain">Muscle Gain</option>
            <option value="general_fitness">General Fitness</option>
            <option value="endurance">Endurance</option>
            <option value="flexibility">Flexibility</option>
          </select>
        </div>

        <div class="form-group" v-if="profile.fitness_goal === 'weight_loss' || profile.fitness_goal === 'muscle_gain'">
          <label for="target_weight">Target Weight (kg)</label>
          <input
            type="number"
            id="target_weight"
            v-model.number="profile.target_weight_kg"
            placeholder="Your target weight in kg"
            min="30"
            max="300"
            step="0.1"
          >
          <small v-if="validationErrors.target_weight_kg" class="error-text">{{ validationErrors.target_weight_kg }}</small>
        </div>

        <div v-if="isGoalAchieved" class="goal-achieved-message">
          <p><strong>Congratulations!</strong> You've reached your weight goal of {{ profile.target_weight_kg }}kg!</p>
        </div>
      </section>

      <!-- Fitness Assessment Section -->
      <section class="form-section">
        <h2>Fitness Assessment</h2>
        <p class="section-description">
          This information helps us provide more personalized fitness recommendations and track your progress.
        </p>

        <div class="subsection">
          <h3>Current Activity</h3>

          <div class="form-group">
            <label for="weeklyActivityDays">How many days per week do you currently exercise?</label>
            <input
              type="number"
              id="weeklyActivityDays"
              v-model.number="profile.weekly_activity_days"
              min="0"
              max="7"
              placeholder="0-7 days"
            >
            <small class="help-text">Enter a number between 0 and 7</small>
            <small v-if="validationErrors.weekly_activity_days" class="error-text">{{ validationErrors.weekly_activity_days }}</small>
          </div>

          <div class="form-group">
            <label>What types of exercise do you currently do?</label>
            <div class="checkbox-group">
              <div class="checkbox-item">
                <input type="checkbox" id="cardio" v-model="profile.does_cardio">
                <label for="cardio" class="checkbox-label">Cardio (running, cycling, swimming, etc.)</label>
              </div>
              <div class="checkbox-item">
                <input type="checkbox" id="strength" v-model="profile.does_strength">
                <label for="strength" class="checkbox-label">Strength Training (weights, resistance, etc.)</label>
              </div>
              <div class="checkbox-item">
                <input type="checkbox" id="flexibility" v-model="profile.does_flexibility">
                <label for="flexibility" class="checkbox-label">Flexibility (yoga, stretching, etc.)</label>
              </div>
              <div class="checkbox-item">
                <input type="checkbox" id="sports" v-model="profile.does_sports">
                <label for="sports" class="checkbox-label">Sports (team sports, racket sports, etc.)</label>
              </div>
            </div>
          </div>
        </div>

        <div class="subsection">
          <h3>Workout Details</h3>

          <div class="form-group">
            <label for="sessionDuration">Average workout duration</label>
            <select id="sessionDuration" v-model="profile.avg_session_duration">
              <option value="">Select duration</option>
              <option value="short">15-30 minutes</option>
              <option value="medium">30-60 minutes</option>
              <option value="long">60+ minutes</option>
            </select>
          </div>

          <div class="form-group">
            <label for="fitnessLevel">How would you rate your current fitness level?</label>
            <select id="fitnessLevel" v-model="profile.fitness_level">
              <option value="">Select level</option>
              <option value="beginner">Beginner - New to regular exercise</option>
              <option value="intermediate">Intermediate - Regularly active for 3+ months</option>
              <option value="advanced">Advanced - Consistently training for 1+ years</option>
            </select>
          </div>
        </div>

        <div class="subsection">
          <h3>Preferences</h3>

          <div class="form-row">
            <div class="form-group">
              <label for="environment">Preferred exercise environment</label>
              <select id="environment" v-model="profile.preferred_environment">
                <option value="">Select preference</option>
                <option value="home">Home</option>
                <option value="gym">Gym</option>
                <option value="outdoors">Outdoors</option>
              </select>
            </div>

            <div class="form-group">
              <label for="timePreference">Preferred time to exercise</label>
              <select id="timePreference" v-model="profile.time_preference">
                <option value="">Select time</option>
                <option value="morning">Morning</option>
                <option value="afternoon">Afternoon</option>
                <option value="evening">Evening</option>
              </select>
            </div>
          </div>
        </div>

        <div class="subsection">
          <h3>Physical Capacity</h3>

          <div class="form-row">
            <div class="form-group">
              <label for="endurance">How long can you walk/run continuously? (minutes)</label>
              <input
                type="number"
                id="endurance"
                v-model.number="profile.endurance_minutes"
                min="0"
                max="300"
                placeholder="Enter minutes"
              >
              <small v-if="validationErrors.endurance_minutes" class="error-text">{{ validationErrors.endurance_minutes }}</small>
            </div>

            <div class="form-group">
              <label for="pushups">Maximum pushups in one set</label>
              <input
                type="number"
                id="pushups"
                v-model.number="profile.pushup_count"
                min="0"
                max="200"
                placeholder="Enter count"
              >
              <small v-if="validationErrors.pushup_count" class="error-text">{{ validationErrors.pushup_count }}</small>
            </div>
          </div>

          <div class="form-group">
            <label for="squats">Maximum bodyweight squats in one set</label>
            <input
              type="number"
              id="squats"
              v-model.number="profile.squat_count"
              min="0"
              max="200"
              placeholder="Enter count"
            >
            <small v-if="validationErrors.squat_count" class="error-text">{{ validationErrors.squat_count }}</small>
          </div>
        </div>
      </section>

      <!-- Dietary Preferences Section -->
      <section class="form-section">
        <h2>Dietary Preferences</h2>
        <p class="section-description">
          This helps us tailor nutritional recommendations to your dietary needs and preferences.
        </p>

        <div class="form-group">
          <label for="dietaryPreference">Primary dietary preference</label>
          <select id="dietaryPreference" v-model="profile.dietary_preference">
            <option value="">Select preference</option>
            <option value="omnivore">Omnivore (Eats Everything)</option>
            <option value="vegetarian">Vegetarian</option>
            <option value="vegan">Vegan</option>
            <option value="pescatarian">Pescatarian</option>
            <option value="keto">Keto</option>
            <option value="paleo">Paleo</option>
          </select>
        </div>

        <div class="form-group">
          <label>Food restrictions or allergies</label>
          <div class="checkbox-group">
            <div class="checkbox-item">
              <input type="checkbox" id="glutenFree" v-model="profile.is_gluten_free">
              <label for="glutenFree" class="checkbox-label">Gluten-Free</label>
            </div>
            <div class="checkbox-item">
              <input type="checkbox" id="dairyFree" v-model="profile.is_dairy_free">
              <label for="dairyFree" class="checkbox-label">Dairy-Free</label>
            </div>
            <div class="checkbox-item">
              <input type="checkbox" id="nutFree" v-model="profile.is_nut_free">
              <label for="nutFree" class="checkbox-label">Nut-Free</label>
            </div>
            <div class="checkbox-item">
              <input type="checkbox" id="otherRestrictions" v-model="profile.has_other_restrictions">
              <label for="otherRestrictions" class="checkbox-label">Other Restrictions</label>
            </div>
          </div>
        </div>

        <div class="form-group" v-if="profile.has_other_restrictions">
          <label for="otherRestrictionsNote">Please describe your other dietary restrictions</label>
          <textarea
            id="otherRestrictionsNote"
            v-model="profile.other_restrictions_note"
            rows="3"
            placeholder="Enter any other dietary restrictions or allergies"
          ></textarea>
        </div>
      </section>

      <!-- Privacy Setting -->
      <section class="form-section">
        <h2>Privacy Settings</h2>
        <p class="section-description">
          We take your privacy seriously. You control how your data is used.
        </p>

        <div class="form-group">
          <div class="checkbox-item privacy-checkbox">
            <input type="checkbox" id="data_sharing" v-model="profile.data_sharing_consent">
            <label for="data_sharing" class="checkbox-label">
              I consent to share my health data for personalized recommendations
            </label>
          </div>
          <small class="help-text">Your data privacy is important to us. We use this information only to provide personalized wellness recommendations.</small>
        </div>
      </section>

      <!-- Submit Section -->
      <div v-if="message" class="alert" :class="successful ? 'alert-success' : 'alert-danger'">
        <span v-if="successful">✓</span>
        <span v-else>!</span>
        {{ message }}
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-secondary" @click="resetForm" :disabled="saveLoading">
          Reset
        </button>
        <button type="submit" class="btn btn-primary" :disabled="saveLoading || Object.keys(validationErrors).length > 0">
          <span v-if="saveLoading">
            <span class="spinner"></span>
            Saving...
          </span>
          <span v-else>Save Profile</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import HealthProfileService from '../services/health-profile_service';

export default {
  name: 'Profile',
  data() {
    return {
      profile: {
        // Basic information
        age: null,
        gender: '',
        height_cm: null,
        weight_kg: null,
        occupation_type: '',
        activity_level: 'moderate',
        fitness_goal: 'general_fitness',
        target_weight_kg: null,

        // Fitness assessment
        weekly_activity_days: null,
        does_cardio: false,
        does_strength: false,
        does_flexibility: false,
        does_sports: false,
        avg_session_duration: '',
        fitness_level: '',
        preferred_environment: '',
        time_preference: '',
        endurance_minutes: null,
        pushup_count: null,
        squat_count: null,

        // Dietary preferences
        dietary_preference: '',
        is_gluten_free: false,
        is_dairy_free: false,
        is_nut_free: false,
        has_other_restrictions: false,
        other_restrictions_note: '',

        // Privacy settings
        data_sharing_consent: false
      },
      originalProfile: null,
      loading: true,
      saveLoading: false,
      message: '',
      successful: false,
      validationErrors: {}
    };
  },
  mounted() {
    this.fetchProfile();
  },
  computed: {
    isGoalAchieved() {
      return this.profile?.target_weight_kg &&
             this.profile?.weight_kg &&
             Math.abs(parseFloat(this.profile.weight_kg) - parseFloat(this.profile.target_weight_kg)) <= 0.5;
    }
  },
  methods: {
    fetchProfile() {
      this.loading = true;
      this.message = '';

      HealthProfileService.getHealthProfile()
        .then(response => {
          console.log('Profile data received:', response.data);
          if (response.data) {
            // Populate profile data
            Object.keys(this.profile).forEach(key => {
              if (key in response.data) {
                this.profile[key] = response.data[key];
              }
            });

            // Save original profile data for later comparison
            this.originalProfile = JSON.parse(JSON.stringify(this.profile));
          }
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching profile:', error);
          this.loading = false;

          if (error.response && error.response.status === 404) {
            console.log('No profile found, using default values');
            // Save original profile data (default values)
            this.originalProfile = JSON.parse(JSON.stringify(this.profile));
          } else {
            this.message = 'Failed to load profile. Please try again.';
            this.successful = false;
          }
        });
    },

    resetGoal() {
      // Clear the current target weight
      this.profile.target_weight_kg = null;

      // Save the updated profile
      this.saveProfile();
    },

    calculateBMI() {
      if (!this.profile.height_cm || !this.profile.weight_kg) return 0;

      const heightInMeters = this.profile.height_cm / 100;
      return this.profile.weight_kg / (heightInMeters * heightInMeters);
    },

    getBMICategory() {
      const bmi = this.calculateBMI();
      if (bmi < 18.5) return 'Underweight';
      if (bmi < 25) return 'Normal weight';
      if (bmi < 30) return 'Overweight';
      return 'Obese';
    },

    validateForm() {
      this.validationErrors = {};

      // Age validation
      if (this.profile.age !== null) {
        if (this.profile.age < 13) {
          this.validationErrors.age = 'Age must be at least 13';
        } else if (this.profile.age > 120) {
          this.validationErrors.age = 'Age must be below 120';
        }
      }

      // Height validation
      if (this.profile.height_cm !== null) {
        if (this.profile.height_cm < 100) {
          this.validationErrors.height_cm = 'Height must be at least 100 cm';
        } else if (this.profile.height_cm > 250) {
          this.validationErrors.height_cm = 'Height must be below 250 cm';
        }
      }

      // Weight validation
      if (this.profile.weight_kg !== null) {
        if (this.profile.weight_kg < 30) {
          this.validationErrors.weight_kg = 'Weight must be at least 30 kg';
        } else if (this.profile.weight_kg > 300) {
          this.validationErrors.weight_kg = 'Weight must be below 300 kg';
        }
      }

      // Target weight validation
      if (this.profile.target_weight_kg !== null) {
        if (this.profile.target_weight_kg < 30) {
          this.validationErrors.target_weight_kg = 'Target weight must be at least 30 kg';
        } else if (this.profile.target_weight_kg > 300) {
          this.validationErrors.target_weight_kg = 'Target weight must be below 300 kg';
        }
      }

      // Weekly activity days validation
      if (this.profile.weekly_activity_days !== null) {
        if (this.profile.weekly_activity_days < 0) {
          this.validationErrors.weekly_activity_days = 'Activity days cannot be negative';
        } else if (this.profile.weekly_activity_days > 7) {
          this.validationErrors.weekly_activity_days = 'Activity days cannot exceed 7';
        }
      }

      // Other validations for endurance, pushups, and squats
      if (this.profile.endurance_minutes !== null && this.profile.endurance_minutes > 300) {
        this.validationErrors.endurance_minutes = 'Please enter a value below 300 minutes';
      }

      if (this.profile.pushup_count !== null && this.profile.pushup_count > 200) {
        this.validationErrors.pushup_count = 'Please enter a realistic value';
      }

      if (this.profile.squat_count !== null && this.profile.squat_count > 200) {
        this.validationErrors.squat_count = 'Please enter a realistic value';
      }

      return Object.keys(this.validationErrors).length === 0;
    },

    saveProfile() {
      // First validate the form
      if (!this.validateForm()) {
        this.message = 'Please correct the validation errors before saving.';
        this.successful = false;
        return;
      }

      this.saveLoading = true;
      this.message = '';

      // Check if anything has changed to avoid unnecessary API calls
      if (JSON.stringify(this.profile) === JSON.stringify(this.originalProfile)) {
        this.message = 'No changes to save.';
        this.successful = true;
        this.saveLoading = false;
        return;
      }

      // Clone the profile to avoid modifying the original during processing
      const profileData = { ...this.profile };

      // Handle numeric fields to ensure they're properly formatted
      ['age', 'height_cm', 'weight_kg', 'target_weight_kg',
       'weekly_activity_days', 'endurance_minutes', 'pushup_count', 'squat_count'].forEach(field => {
        if (profileData[field] !== null && profileData[field] !== '') {
          profileData[field] = Number(profileData[field]);
        }
      });

      // Call the API service to update the profile
      HealthProfileService.updateHealthProfile(profileData)
        .then(response => {
          console.log('Profile saved successfully:', response.data);
          this.successful = true;
          this.message = 'Profile saved successfully!';

          // Update original profile to reflect the saved changes
          this.originalProfile = JSON.parse(JSON.stringify(this.profile));

          // Trigger wellness score calculation
          this.triggerWellnessScoreUpdate();
        })
        .catch(error => {
          console.error('Error saving profile:', error);
          this.successful = false;

          if (error.response && error.response.data) {
            const errorData = error.response.data;
            if (typeof errorData === 'object') {
              const errorMessages = Object.entries(errorData)
                .map(([field, errors]) => {
                  if (Array.isArray(errors)) {
                    return `${field}: ${errors.join(', ')}`;
                  }
                  return `${field}: ${errors}`;
                })
                .join('; ');

              this.message = `Failed to save profile: ${errorMessages}`;
            } else {
              this.message = 'Failed to save profile. Please check your inputs and try again.';
            }
          } else {
            this.message = 'Failed to save profile. Please try again.';
          }
        })
        .finally(() => {
          this.saveLoading = false;

          // Scroll to the message
          setTimeout(() => {
            const alertElement = document.querySelector('.alert');
            if (alertElement) {
              alertElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }, 100);
        });
    },

    resetForm() {
      if (confirm('Are you sure you want to reset all changes?')) {
        if (this.originalProfile) {
          // Reset to original values
          this.profile = JSON.parse(JSON.stringify(this.originalProfile));
        } else {
          // If no original profile (shouldn't happen), use default values
          this.profile = {
            age: null,
            gender: '',
            height_cm: null,
            weight_kg: null,
            occupation_type: '',
            activity_level: 'moderate',
            fitness_goal: 'general_fitness',
            target_weight_kg: null,
            weekly_activity_days: null,
            does_cardio: false,
            does_strength: false,
            does_flexibility: false,
            does_sports: false,
            avg_session_duration: '',
            fitness_level: '',
            preferred_environment: '',
            time_preference: '',
            endurance_minutes: null,
            pushup_count: null,
            squat_count: null,
            dietary_preference: '',
            is_gluten_free: false,
            is_dairy_free: false,
            is_nut_free: false,
            has_other_restrictions: false,
            other_restrictions_note: '',
            data_sharing_consent: false
          };
        }

        this.message = 'Form has been reset.';
        this.successful = true;
        this.validationErrors = {};
      }
    },

    triggerWellnessScoreUpdate() {
      // Call the wellness score calculation API (if available)
      // This would typically happen after saving the profile
      // For now, we'll just log that it would be triggered
      console.log('Would trigger wellness score update');

      // In a real implementation, you would call a service like:
      // AnalyticsService.calculateWellnessScore()
      //   .then(response => {
      //     console.log('Wellness score updated:', response.data);
      //   })
      //   .catch(error => {
      //     console.error('Error updating wellness score:', error);
      //   });
    }
  }
};
</script>

<style lang="scss" scoped>
@import '../assets/styles/_variables.scss';
@import '../assets/styles/_utilities.scss';

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.profile-description {
  margin-bottom: 2rem;
  color: $gray;
}

/* Apply consistent styling to form selects and inputs */
select, input[type="text"], input[type="number"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid $gray-light;
  border-radius: $border-radius;
  font-size: 1rem;
  background-color: $white;
  transition: all 0.2s ease;

  &:focus {
    border-color: $primary;
    outline: none;
    box-shadow: 0 0 0 3px rgba($primary, 0.1);
  }

  &:disabled {
    background-color: $gray-lighter;
    cursor: not-allowed;
  }
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.loading-spinner {
  @include spinner;
  margin-bottom: 1rem;
}

.profile-form {
  background-color: white;
  border-radius: $border-radius-lg;
  padding: 2rem;
  box-shadow: $shadow;
}

.form-section {
  margin-bottom: 2.5rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid $gray-lighter;

  &:last-child {
    margin-bottom: 1.5rem;
    padding-bottom: 0;
    border-bottom: none;
  }
}

.subsection {
  margin-bottom: 1.5rem;
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: $border-radius;

  h3 {
    margin-bottom: 1rem;
    font-size: 1.1rem;
    color: $primary-dark;
  }
}

.section-description {
  color: $gray;
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;

  @include responsive('md') {
    grid-template-columns: 1fr 1fr;
  }
}

.error-text {
  color: $error;
  font-size: 0.875rem;
  margin-top: 0.375rem;
  display: block;
}

.help-text {
  color: $gray;
  font-size: 0.875rem;
  margin-top: 0.375rem;
  display: block;
}

.metrics-summary {
  margin-top: 1.5rem;
  background-color: #f8fcfc;
  padding: 1rem;
  border-radius: $border-radius;
  border-left: 4px solid $primary;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.metric-label {
  color: $gray;
}

.metric-value {
  font-weight: $font-weight-bold;
  font-size: 1.2rem;
}

.metric-category {
  font-size: 0.9rem;
  padding: 0.25rem 0.5rem;
  border-radius: $border-radius-sm;
  color: white;
  background-color: $primary;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: $border-radius;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.alert-success {
  background-color: lighten($success, 45%);
  color: darken($success, 10%);
  border-left: 4px solid $success;
}

.alert-danger {
  background-color: lighten($error, 45%);
  color: darken($error, 10%);
  border-left: 4px solid $error;
}

textarea {
  width: 100%;
  min-height: 100px;
  border: 1px solid $gray-light;
  border-radius: $border-radius;
  padding: 0.75rem;

  &:focus {
    border-color: $primary;
    outline: none;
    box-shadow: 0 0 0 3px rgba($primary, 0.1);
  }
}

.checkbox-group {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;
  margin-top: 0.75rem;

  @include responsive('md') {
    grid-template-columns: repeat(2, 1fr);
  }
}

.checkbox-item {
  display: flex;
  align-items: center;
  position: relative;
  margin-bottom: 0.5rem;
}

.checkbox-item input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkbox-label {
  padding-left: 2rem;
  cursor: pointer;
  font-weight: normal;
  position: relative;
  display: inline-block;
  user-select: none;
}

.checkbox-label:before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 1.25rem;
  height: 1.25rem;
  border: 2px solid $gray-light;
  background-color: white;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.checkbox-item input[type="checkbox"]:checked + .checkbox-label:before {
  background-color: $primary;
  border-color: $primary;
}

.checkbox-label:after {
  content: '';
  position: absolute;
  left: 0.45rem;
  top: 0.25rem;
  width: 0.35rem;
  height: 0.7rem;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  opacity: 0;
  transition: opacity 0.2s;
}

.checkbox-item input[type="checkbox"]:checked + .checkbox-label:after {
  opacity: 1;
}

.checkbox-item:hover .checkbox-label:before {
  border-color: $primary;
}

/* Add this to your <style> section */
.goal-achieved-message {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #d4edda;
  border-radius: $border-radius;
  border-left: 4px solid $success;
}

.goal-achieved-message p {
  margin-bottom: 0.5rem;
  color: darken($success, 10%);
}
</style>