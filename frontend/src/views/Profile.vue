<template>
  <div class="profile-container">
    <h1>Health Profile</h1>

    <form @submit.prevent="saveProfile" class="profile-form">
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

      <h2>Physical Metrics</h2>

      <div class="form-group">
        <label for="height">Height (cm)</label>
        <input type="number" id="height" v-model="profile.height_cm" placeholder="Your height in cm">
      </div>

      <div class="form-group">
        <label for="weight">Weight (kg)</label>
        <input type="number" id="weight" v-model="profile.weight_kg" placeholder="Your weight in kg">
      </div>

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

      <div class="form-group">
        <label for="data_sharing">
          <input type="checkbox" id="data_sharing" v-model="profile.data_sharing_consent">
          I consent to share my health data for personalized recommendations
        </label>
      </div>

      <div v-if="message" class="alert" :class="successful ? 'alert-success' : 'alert-danger'">
        {{ message }}
      </div>

      <div class="form-group">
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <span v-if="loading">Saving...</span>
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
        age: null,
        gender: '',
        height_cm: null,
        weight_kg: null,
        occupation_type: '',
        activity_level: 'moderate',
        fitness_goal: 'general_fitness',
        target_weight_kg: null,
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
      HealthProfileService.getHealthProfile()
          .then(response => {
            if (response.data && response.data.length > 0) {
              this.profile = response.data[0];
            }
            this.loading = false;
          })
          .catch(error => {
            console.error('Error fetching profile:', error);
            this.loading = false;
          });
    },
    saveProfile() {
      this.loading = true;
      this.message = '';

      HealthProfileService.updateHealthProfile(this.profile)
          .then(() => {
            this.successful = true;
            this.message = 'Profile saved successfully!';
            this.loading = false;
          })
          .catch(error => {
            this.successful = false;
            this.message = 'Failed to save profile. Please try again.';
            console.error('Error saving profile:', error);
            this.loading = false;
          });
    }
  }
};
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
}

h2 {
  margin: 2rem 0 1rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

.profile-form {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

input[type="text"],
input[type="number"],
select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

input[type="checkbox"] {
  margin-right: 0.5rem;
}

.btn {
  cursor: pointer;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

.alert {
  padding: 0.75rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

.alert-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.alert-success {
  background-color: #d4edda;
  color: #155724;
}
</style>