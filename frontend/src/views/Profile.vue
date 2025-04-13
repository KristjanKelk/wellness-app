<template>
  <div class="profile-container">
    <h1>Health Profile</h1>

    <form @submit.prevent="saveProfile" class="profile-form">
      <!-- Personal Information Section -->
      <h2>Personal Information</h2>

      <div class="form-group">
        <label for="age">Age</label>
        <input type="number" id="age" v-model="profile.age" placeholder="Your age">
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

      <!-- Physical Metrics Section -->
      <h2>Physical Metrics</h2>

      <div class="form-group">
        <label for="height">Height (cm)</label>
        <input type="number" id="height" v-model="profile.height_cm" placeholder="Your height in cm">
      </div>

      <div class="form-group">
        <label for="weight">Weight (kg)</label>
        <input type="number" id="weight" v-model="profile.weight_kg" placeholder="Your weight in kg">
      </div>

      <!-- Lifestyle & Goals Section -->
      <h2>Lifestyle & Goals</h2>

      <div class="form-group">
        <label for="occupation">Occupation Type</label>
        <input type="text" id="occupation" v-model="profile.occupation_type" placeholder="e.g., Office worker, Construction, etc.">
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

      <div class="form-group">
        <label for="target_weight">Target Weight (kg, if applicable)</label>
        <input type="number" id="target_weight" v-model="profile.target_weight_kg" placeholder="Your target weight in kg">
      </div>

      <!-- Fitness Assessment Section -->
      <h2>Fitness Assessment</h2>
      <p class="section-description">
        This information helps us provide more personalized fitness recommendations and track your progress.
      </p>

      <div class="form-section">
        <h3>Current Activity</h3>

        <div class="form-group">
          <label for="weeklyActivityDays">How many days per week do you currently exercise?</label>
          <input
            type="number"
            id="weeklyActivityDays"
            v-model="profile.weekly_activity_days"
            min="0"
            max="7"
            placeholder="0-7 days"
          >
          <small>Enter a number between 0 and 7</small>
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

      <div class="form-section">
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

      <div class="form-section">
        <h3>Preferences</h3>

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

      <div class="form-section">
        <h3>Physical Capacity</h3>

        <div class="form-group">
          <label for="endurance">How long can you walk/run continuously? (minutes)</label>
          <input
            type="number"
            id="endurance"
            v-model="profile.endurance_minutes"
            min="0"
            placeholder="Enter minutes"
          >
        </div>

        <div class="form-group">
          <label for="pushups">Maximum number of pushups you can do in one set</label>
          <input
            type="number"
            id="pushups"
            v-model="profile.pushup_count"
            min="0"
            placeholder="Enter count"
          >
        </div>

        <div class="form-group">
          <label for="squats">Maximum number of bodyweight squats you can do in one set</label>
          <input
            type="number"
            id="squats"
            v-model="profile.squat_count"
            min="0"
            placeholder="Enter count"
          >
        </div>
      </div>

      <!-- Dietary Preferences Section -->
      <h2>Dietary Preferences</h2>
      <p class="section-description">
        This helps us tailor nutritional recommendations to your dietary needs and preferences.
      </p>

      <div class="form-section">
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
      </div>

      <!-- Privacy Setting -->
      <h2>Privacy Settings</h2>

      <div class="form-section">
        <div class="form-group">
          <div class="checkbox-item privacy-checkbox">
            <input type="checkbox" id="data_sharing" v-model="profile.data_sharing_consent">
            <label for="data_sharing" class="checkbox-label">
              I consent to share my health data for personalized recommendations
            </label>
          </div>
          <small>Your data privacy is important to us. We use this information only to provide personalized wellness recommendations.</small>
        </div>
      </div>

      <!-- Submit Section -->
      <div v-if="message" class="alert" :class="successful ? 'alert-success' : 'alert-danger'">
        <span v-if="successful">✓</span>
        <span v-else>!</span>
        {{ message }}
      </div>

      <div class="form-group submit-button">
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <span v-if="loading">
            <span class="loading-spinner"></span>
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
import '../assets/Profile.css';

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
      loading: false,
      message: '',
      successful: false
    };
  },
  mounted() {
    this.fetchProfile();
  },
  methods: {
    fetchProfile() {
      this.loading = true;
      this.message = '';

      HealthProfileService.getHealthProfile()
        .then(response => {
          console.log('Profile data received:', response.data);
          if (response.data) {
            Object.keys(this.profile).forEach(key => {
              if (key in response.data) {
                this.profile[key] = response.data[key];
              }
            });
          }
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching profile:', error);
          this.loading = false;
          if (error.response && error.response.status === 404) {
            console.log('No profile found, using default values');
          } else {
            this.message = 'Failed to load profile. Please try again.';
            this.successful = false;
          }
        });
    },
    saveProfile() {
      this.loading = true;
      this.message = '';

      // Convert string number values to actual numbers
      const profileData = { ...this.profile };

      // Handle numeric fields separately to ensure they're properly formatted
      ['age', 'height_cm', 'weight_kg', 'target_weight_kg',
       'weekly_activity_days', 'endurance_minutes', 'pushup_count', 'squat_count'].forEach(field => {
        if (profileData[field] !== null && profileData[field] !== '') {
          profileData[field] = Number(profileData[field]);
        }
      });

      HealthProfileService.updateHealthProfile(profileData)
        .then(response => {
          console.log('Profile saved successfully:', response.data);
          this.successful = true;
          this.message = 'Profile saved successfully!';
          this.loading = false;

          Object.keys(this.profile).forEach(key => {
            if (key in response.data) {
              this.profile[key] = response.data[key];
            }
          });
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

          this.loading = false;
        });
    }
  }
};
</script>