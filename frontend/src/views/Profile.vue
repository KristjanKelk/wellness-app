<template>
  <div class="profile-container">
    <!-- Profile Header -->
    <div class="profile-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="profile-title">Your Profile</h1>
          <p class="profile-subtitle">Complete your profile to unlock personalized recommendations and insights</p>
        </div>
        <div class="profile-completion">
          <div class="completion-circle">
            <svg class="progress-ring" width="60" height="60">
              <circle class="progress-ring-circle" stroke="currentColor" stroke-width="4" fill="transparent" r="26" cx="30" cy="30" :style="{ strokeDasharray: `${completionPercentage * 1.63} 163`, strokeDashoffset: 0 }"/>
            </svg>
            <span class="completion-text">{{ completionPercentage }}%</span>
          </div>
          <span class="completion-label">Complete</span>
        </div>
      </div>
    </div>

    <!-- Enhanced Tab Navigation -->
    <div class="profile-tabs-container">
      <nav class="profile-tabs" role="tablist">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="tab-item"
          :class="{ 'active': activeTab === tab.id }"
          :aria-selected="activeTab === tab.id"
          role="tab"
        >
          <div class="tab-icon">
            <i :class="tab.icon"></i>
          </div>
          <div class="tab-content">
            <span class="tab-title">{{ tab.title }}</span>
            <span class="tab-description">{{ tab.description }}</span>
          </div>
          <div class="tab-indicator" v-if="activeTab === tab.id"></div>
        </button>
      </nav>
    </div>

    <!-- Tab Content -->
    <div class="tab-panels">
      <!-- General Profile Tab -->
      <div v-if="activeTab === 'general'" class="tab-panel" role="tabpanel">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p class="loading-text">Loading your profile data...</p>
        </div>

        <form v-else @submit.prevent="saveProfile" class="profile-form">
          <!-- Personal Information Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-user-circle"></i>
              </div>
              <div class="card-title">
                <h3>Personal Information</h3>
                <p>Basic information to personalize your experience</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-grid">
                <div class="form-group">
                  <label for="age" class="form-label">
                    <span class="label-text">Age</span>
                    <span class="label-required">*</span>
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      id="age"
                      v-model.number="profile.age"
                      placeholder="Enter your age"
                      min="13"
                      max="120"
                      class="form-input"
                      :class="{ 'error': validationErrors.age }"
                    >
                    <div class="input-suffix">years</div>
                  </div>
                  <span v-if="validationErrors.age" class="error-message">{{ validationErrors.age }}</span>
                </div>

                <div class="form-group">
                  <label for="gender" class="form-label">
                    <span class="label-text">Gender</span>
                  </label>
                  <FormSelect
                    id="gender"
                    v-model="profile.gender"
                    placeholder="Select gender"
                    :options="[
                      { value: 'M', label: 'Male' },
                      { value: 'F', label: 'Female' },
                      { value: 'O', label: 'Other' }
                    ]"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Physical Metrics Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-weight"></i>
              </div>
              <div class="card-title">
                <h3>Physical Metrics</h3>
                <p>Height and weight for health calculations</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-grid">
                <div class="form-group">
                  <label for="height" class="form-label">
                    <span class="label-text">Height</span>
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      id="height"
                      v-model.number="profile.height_cm"
                      placeholder="170"
                      min="100"
                      max="250"
                      step="0.1"
                      class="form-input"
                      :class="{ 'error': validationErrors.height_cm }"
                    >
                    <div class="input-suffix">cm</div>
                  </div>
                  <span v-if="validationErrors.height_cm" class="error-message">{{ validationErrors.height_cm }}</span>
                </div>

                <div class="form-group">
                  <label for="weight" class="form-label">
                    <span class="label-text">Weight</span>
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      id="weight"
                      v-model.number="profile.weight_kg"
                      placeholder="70"
                      min="30"
                      max="300"
                      step="0.1"
                      class="form-input"
                      :class="{ 'error': validationErrors.weight_kg }"
                    >
                    <div class="input-suffix">kg</div>
                  </div>
                  <span v-if="validationErrors.weight_kg" class="error-message">{{ validationErrors.weight_kg }}</span>
                </div>
              </div>

              <!-- BMI Display -->
              <div class="metrics-display" v-if="profile.height_cm && profile.weight_kg">
                <div class="metric-card">
                  <div class="metric-icon">
                    <i class="fas fa-chart-line"></i>
                  </div>
                  <div class="metric-info">
                    <span class="metric-label">Body Mass Index</span>
                    <div class="metric-value">
                      <span class="value">{{ calculateBMI().toFixed(1) }}</span>
                      <span class="category" :class="getBMICategoryClass()">{{ getBMICategory() }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Form Actions -->
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="resetForm" :disabled="saveLoading">
              <i class="fas fa-undo"></i>
              Reset Changes
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saveLoading || Object.keys(validationErrors).length > 0">
              <span v-if="saveLoading" class="btn-loading">
                <i class="fas fa-spinner fa-spin"></i>
                Saving...
              </span>
              <span v-else class="btn-content">
                <i class="fas fa-save"></i>
                Save Profile
              </span>
            </button>
          </div>
        </form>
      </div>

             <!-- Nutrition Profile Tab -->
       <div v-if="activeTab === 'nutrition'" class="tab-panel" role="tabpanel">
         <div class="nutrition-wrapper">
           <div class="nutrition-intro">
             <div class="intro-card">
               <div class="intro-icon">
                 <i class="fas fa-leaf"></i>
               </div>
               <div class="intro-content">
                 <h3>Nutrition Profile</h3>
                 <p>Set up your nutrition preferences to get personalized meal recommendations and track your dietary goals.</p>
               </div>
             </div>
           </div>
           <nutrition-profile-setup
             :profile="nutritionProfile"
             :loading="nutritionProfileLoading"
             @profile-updated="onNutritionProfileUpdated"
           />
         </div>
       </div>

      <!-- Activity Tab -->
      <div v-if="activeTab === 'activity'" class="tab-panel" role="tabpanel">
        <form @submit.prevent="saveProfile" class="profile-form">
          <!-- Current Activity Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-running"></i>
              </div>
              <div class="card-title">
                <h3>Current Activity Level</h3>
                <p>Tell us about your current exercise routine</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-group">
                <label for="weeklyActivityDays" class="form-label">
                  <span class="label-text">Exercise days per week</span>
                </label>
                <div class="number-input-container">
                  <input
                    type="number"
                    id="weeklyActivityDays"
                    v-model.number="profile.weekly_activity_days"
                    min="0"
                    max="7"
                    placeholder="0"
                    class="form-input number-input"
                  >
                  <div class="number-slider">
                    <input
                      type="range"
                      min="0"
                      max="7"
                      v-model.number="profile.weekly_activity_days"
                      class="slider"
                    >
                    <div class="slider-labels">
                      <span>0</span>
                      <span>7</span>
                    </div>
                  </div>
                </div>
                <small class="form-help">Select how many days per week you currently exercise</small>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <span class="label-text">Types of exercise you do</span>
                </label>
                <div class="activity-grid">
                  <div class="activity-card" :class="{ active: profile.does_cardio }">
                    <input type="checkbox" id="cardio" v-model="profile.does_cardio" class="activity-checkbox">
                    <label for="cardio" class="activity-label">
                      <div class="activity-icon">
                        <i class="fas fa-heartbeat"></i>
                      </div>
                      <div class="activity-info">
                        <span class="activity-name">Cardio</span>
                        <span class="activity-desc">Running, cycling, swimming</span>
                      </div>
                    </label>
                  </div>

                  <div class="activity-card" :class="{ active: profile.does_strength }">
                    <input type="checkbox" id="strength" v-model="profile.does_strength" class="activity-checkbox">
                    <label for="strength" class="activity-label">
                      <div class="activity-icon">
                        <i class="fas fa-dumbbell"></i>
                      </div>
                      <div class="activity-info">
                        <span class="activity-name">Strength</span>
                        <span class="activity-desc">Weights, resistance</span>
                      </div>
                    </label>
                  </div>

                  <div class="activity-card" :class="{ active: profile.does_flexibility }">
                    <input type="checkbox" id="flexibility" v-model="profile.does_flexibility" class="activity-checkbox">
                    <label for="flexibility" class="activity-label">
                      <div class="activity-icon">
                        <i class="fas fa-leaf"></i>
                      </div>
                      <div class="activity-info">
                        <span class="activity-name">Flexibility</span>
                        <span class="activity-desc">Yoga, stretching</span>
                      </div>
                    </label>
                  </div>

                  <div class="activity-card" :class="{ active: profile.does_sports }">
                    <input type="checkbox" id="sports" v-model="profile.does_sports" class="activity-checkbox">
                    <label for="sports" class="activity-label">
                      <div class="activity-icon">
                        <i class="fas fa-futbol"></i>
                      </div>
                      <div class="activity-info">
                        <span class="activity-name">Sports</span>
                        <span class="activity-desc">Team & racket sports</span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Workout Details Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-clock"></i>
              </div>
              <div class="card-title">
                <h3>Workout Details</h3>
                <p>Information about your typical workouts</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-grid">
                <div class="form-group">
                  <label for="sessionDuration" class="form-label">
                    <span class="label-text">Average workout duration</span>
                  </label>
                  <select id="sessionDuration" v-model="profile.avg_session_duration" class="form-select">
                    <option value="">Select duration</option>
                    <option value="short">15-30 minutes</option>
                    <option value="medium">30-60 minutes</option>
                    <option value="long">60+ minutes</option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="fitnessLevel" class="form-label">
                    <span class="label-text">Current fitness level</span>
                  </label>
                  <select id="fitnessLevel" v-model="profile.fitness_level" class="form-select">
                    <option value="">Select level</option>
                    <option value="beginner">Beginner - New to exercise</option>
                    <option value="intermediate">Intermediate - 3+ months active</option>
                    <option value="advanced">Advanced - 1+ years training</option>
                  </select>
                </div>
              </div>

              <div class="form-grid">
                <div class="form-group">
                  <label for="environment" class="form-label">
                    <span class="label-text">Preferred environment</span>
                  </label>
                  <select id="environment" v-model="profile.preferred_environment" class="form-select">
                    <option value="">Select preference</option>
                    <option value="home">Home</option>
                    <option value="gym">Gym</option>
                    <option value="outdoors">Outdoors</option>
                  </select>
                </div>

                <div class="form-group">
                  <label for="timePreference" class="form-label">
                    <span class="label-text">Preferred time</span>
                  </label>
                  <select id="timePreference" v-model="profile.time_preference" class="form-select">
                    <option value="">Select time</option>
                    <option value="morning">Morning</option>
                    <option value="afternoon">Afternoon</option>
                    <option value="evening">Evening</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <!-- Physical Capacity Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-tachometer-alt"></i>
              </div>
              <div class="card-title">
                <h3>Physical Capacity</h3>
                <p>Help us understand your current fitness level</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-grid">
                <div class="form-group">
                  <label for="endurance" class="form-label">
                    <span class="label-text">Continuous walk/run duration</span>
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      id="endurance"
                      v-model.number="profile.endurance_minutes"
                      placeholder="15"
                      min="0"
                      max="300"
                      class="form-input"
                    >
                    <div class="input-suffix">minutes</div>
                  </div>
                </div>

                <div class="form-group">
                  <label for="pushups" class="form-label">
                    <span class="label-text">Maximum pushups</span>
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      id="pushups"
                      v-model.number="profile.pushup_count"
                      placeholder="10"
                      min="0"
                      max="200"
                      class="form-input"
                    >
                    <div class="input-suffix">reps</div>
                  </div>
                </div>
              </div>

              <div class="form-group">
                <label for="squats" class="form-label">
                  <span class="label-text">Maximum bodyweight squats</span>
                </label>
                <div class="input-group">
                  <input
                    type="number"
                    id="squats"
                    v-model.number="profile.squat_count"
                    placeholder="20"
                    min="0"
                    max="200"
                    class="form-input"
                  >
                  <div class="input-suffix">reps</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Form Actions -->
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="resetForm" :disabled="saveLoading">
              <i class="fas fa-undo"></i>
              Reset Changes
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saveLoading || Object.keys(validationErrors).length > 0">
              <span v-if="saveLoading" class="btn-loading">
                <i class="fas fa-spinner fa-spin"></i>
                Saving...
              </span>
              <span v-else class="btn-content">
                <i class="fas fa-save"></i>
                Save Profile
              </span>
            </button>
          </div>
        </form>
      </div>

      <!-- Goals Tab -->
      <div v-if="activeTab === 'goals'" class="tab-panel" role="tabpanel">
        <form @submit.prevent="saveProfile" class="profile-form">
          <!-- Lifestyle Goals Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-bullseye"></i>
              </div>
              <div class="card-title">
                <h3>Lifestyle & Goals</h3>
                <p>Tell us about your lifestyle and what you want to achieve</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-group">
                <label for="occupation" class="form-label">
                  <span class="label-text">Occupation type</span>
                </label>
                <input
                  type="text"
                  id="occupation"
                  v-model="profile.occupation_type"
                  placeholder="e.g., Office worker, Teacher, Construction"
                  class="form-input"
                >
              </div>

              <div class="form-group">
                <label for="activity" class="form-label">
                  <span class="label-text">Overall activity level</span>
                </label>
                <select id="activity" v-model="profile.activity_level" class="form-select">
                  <option value="sedentary">Sedentary (little or no exercise)</option>
                  <option value="light">Lightly Active (light exercise 1-3 days/week)</option>
                  <option value="moderate">Moderately Active (moderate exercise 3-5 days/week)</option>
                  <option value="active">Active (hard exercise 6-7 days/week)</option>
                  <option value="very_active">Very Active (very hard exercise & physical job)</option>
                </select>
                <small class="form-help">Choose the option that best describes your typical week</small>
              </div>

              <div class="form-group">
                <label for="goal" class="form-label">
                  <span class="label-text">Primary fitness goal</span>
                </label>
                <select id="goal" v-model="profile.fitness_goal" class="form-select">
                  <option value="weight_loss">Weight Loss</option>
                  <option value="muscle_gain">Muscle Gain</option>
                  <option value="general_fitness">General Fitness</option>
                  <option value="endurance">Endurance</option>
                  <option value="flexibility">Flexibility</option>
                </select>
              </div>

              <div class="form-group" v-if="profile.fitness_goal === 'weight_loss' || profile.fitness_goal === 'muscle_gain'">
                <label for="target_weight" class="form-label">
                  <span class="label-text">Target weight</span>
                </label>
                <div class="input-group">
                  <input
                    type="number"
                    id="target_weight"
                    v-model.number="profile.target_weight_kg"
                    placeholder="70"
                    min="30"
                    max="300"
                    step="0.1"
                    class="form-input"
                  >
                  <div class="input-suffix">kg</div>
                </div>
              </div>

              <div v-if="isGoalAchieved" class="achievement-card">
                <div class="achievement-icon">
                  <i class="fas fa-trophy"></i>
                </div>
                <div class="achievement-content">
                  <h4>Congratulations!</h4>
                  <p>You've reached your weight goal of {{ profile.target_weight_kg }}kg!</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Dietary Preferences Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-utensils"></i>
              </div>
              <div class="card-title">
                <h3>Dietary Preferences</h3>
                <p>Help us tailor nutritional recommendations to your needs</p>
              </div>
            </div>
            <div class="card-content">
              <div class="form-group">
                <label for="dietaryPreference" class="form-label">
                  <span class="label-text">Primary dietary preference</span>
                </label>
                <select id="dietaryPreference" v-model="profile.dietary_preference" class="form-select">
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
                <label class="form-label">
                  <span class="label-text">Food restrictions & allergies</span>
                </label>
                <div class="restriction-grid">
                  <div class="restriction-card" :class="{ active: profile.is_gluten_free }">
                    <input type="checkbox" id="glutenFree" v-model="profile.is_gluten_free" class="restriction-checkbox">
                    <label for="glutenFree" class="restriction-label">
                      <i class="fas fa-wheat"></i>
                      Gluten-Free
                    </label>
                  </div>

                  <div class="restriction-card" :class="{ active: profile.is_dairy_free }">
                    <input type="checkbox" id="dairyFree" v-model="profile.is_dairy_free" class="restriction-checkbox">
                    <label for="dairyFree" class="restriction-label">
                      <i class="fas fa-cheese"></i>
                      Dairy-Free
                    </label>
                  </div>

                  <div class="restriction-card" :class="{ active: profile.is_nut_free }">
                    <input type="checkbox" id="nutFree" v-model="profile.is_nut_free" class="restriction-checkbox">
                    <label for="nutFree" class="restriction-label">
                      <i class="fas fa-seedling"></i>
                      Nut-Free
                    </label>
                  </div>

                  <div class="restriction-card" :class="{ active: profile.has_other_restrictions }">
                    <input type="checkbox" id="otherRestrictions" v-model="profile.has_other_restrictions" class="restriction-checkbox">
                    <label for="otherRestrictions" class="restriction-label">
                      <i class="fas fa-plus"></i>
                      Other
                    </label>
                  </div>
                </div>
              </div>

              <div class="form-group" v-if="profile.has_other_restrictions">
                <label for="otherRestrictionsNote" class="form-label">
                  <span class="label-text">Describe your other restrictions</span>
                </label>
                <textarea
                  id="otherRestrictionsNote"
                  v-model="profile.other_restrictions_note"
                  rows="3"
                  placeholder="Please describe any other dietary restrictions or allergies"
                  class="form-textarea"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Privacy Settings Card -->
          <div class="form-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-shield-alt"></i>
              </div>
              <div class="card-title">
                <h3>Privacy Settings</h3>
                <p>Control how your data is used</p>
              </div>
            </div>
            <div class="card-content">
              <div class="privacy-setting">
                <div class="privacy-toggle">
                  <input type="checkbox" id="data_sharing" v-model="profile.data_sharing_consent" class="toggle-checkbox">
                  <label for="data_sharing" class="toggle-label">
                    <span class="toggle-switch"></span>
                  </label>
                </div>
                <div class="privacy-content">
                  <h4>Share data for personalized recommendations</h4>
                  <p>We use this information only to provide personalized wellness recommendations. Your privacy is important to us.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Form Actions -->
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="resetForm" :disabled="saveLoading">
              <i class="fas fa-undo"></i>
              Reset Changes
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saveLoading || Object.keys(validationErrors).length > 0">
              <span v-if="saveLoading" class="btn-loading">
                <i class="fas fa-spinner fa-spin"></i>
                Saving...
              </span>
              <span v-else class="btn-content">
                <i class="fas fa-save"></i>
                Save Profile
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Status Messages -->
    <div v-if="message" class="status-message" :class="successful ? 'success' : 'error'">
      <div class="status-icon">
        <i :class="successful ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
      </div>
      <div class="status-content">
        <p>{{ message }}</p>
      </div>
      <button @click="message = ''" class="status-close">
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>

<script>
import HealthProfileService from '../services/health-profile_service';
import AnalyticsService from "../services/analytics.service";
import FormSelect from '@/components/ui/FormSelect.vue';
import NutritionProfileSetup from '@/components/meal-planning/NutritionProfileSetup.vue';

export default {
  name: 'Profile',
  components: {
    FormSelect,
    NutritionProfileSetup
  },
  data() {
    return {
      tabs: [
        {
          id: 'general',
          title: 'General',
          description: 'Basic info',
          icon: 'fas fa-user'
        },
        {
          id: 'nutrition',
          title: 'Nutrition',
          description: 'Diet & meals',
          icon: 'fas fa-utensils'
        },
        {
          id: 'activity',
          title: 'Activity',
          description: 'Fitness & exercise',
          icon: 'fas fa-dumbbell'
        },
        {
          id: 'goals',
          title: 'Goals',
          description: 'Targets & preferences',
          icon: 'fas fa-target'
        }
      ],
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
      validationErrors: {},
      activeTab: 'general', // Default to general profile tab
      nutritionProfile: {
        // Placeholder for nutrition profile data
        // This will be populated by the NutritionProfileSetup component
      },
      nutritionProfileLoading: false,
    };
  },
  mounted() {
    this.fetchProfile();
    this.loadNutritionProfile();
  },
  computed: {
    isGoalAchieved() {
      return this.profile?.target_weight_kg &&
             this.profile?.weight_kg &&
             Math.abs(parseFloat(this.profile.weight_kg) - parseFloat(this.profile.target_weight_kg)) <= 0.5;
    },
    completionPercentage() {
      const requiredFields = [
        'age', 'gender', 'height_cm', 'weight_kg', 'activity_level', 
        'fitness_goal', 'weekly_activity_days', 'avg_session_duration', 
        'fitness_level', 'dietary_preference'
      ];
      const filledFields = requiredFields.filter(field => {
        const value = this.profile[field];
        return value !== null && value !== '' && value !== undefined;
      }).length;
      return Math.round((filledFields / requiredFields.length) * 100);
    }
  },
  methods: {
    fetchProfile() {
      this.loading = true;
      this.message = '';

      HealthProfileService.getHealthProfile()
        .then(response => {
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

    getBMICategoryClass() {
      const bmi = this.calculateBMI();
      if (bmi < 18.5) return 'underweight';
      if (bmi < 25) return 'normal';
      if (bmi < 30) return 'overweight';
      return 'obese';
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
            const alertElement = document.querySelector('.status-message');
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

       AnalyticsService.calculateWellnessScore()
         .then(response => {
           console.log('Wellness score updated:', response.data);
         })
         .catch(error => {
           console.error('Error updating wellness score:', error);
         });
    },

         async loadNutritionProfile() {
       this.nutritionProfileLoading = true;
       try {
         // Import the API service
         const { mealPlanningApi } = await import('@/services/mealPlanningApi');
         const response = await mealPlanningApi.getNutritionProfile();
         this.nutritionProfile = response.data;
       } catch (error) {
         console.error('Failed to load nutrition profile:', error);
         // Create default profile if none exists
         this.nutritionProfile = {
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
         };
       } finally {
         this.nutritionProfileLoading = false;
       }
     },

     onNutritionProfileUpdated(updatedProfile) {
       this.nutritionProfile = updatedProfile;
       this.nutritionProfileLoading = false;
       this.message = 'Nutrition profile updated successfully!';
       this.successful = true;
       // Refresh the component
       this.$nextTick(() => {
         this.$forceUpdate();
       });
     }
  }
};
</script>

<style lang="scss" scoped>
@import '../assets/styles/_variables.scss';
@import '../assets/styles/_utilities.scss';

// Additional variables for this component
$warning-light: #fef5e7;
$info-light: #bee3f8;

.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-6;
  padding: $spacing-4;
  background-color: $primary-light;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-sm;

  .header-content {
    display: flex;
    align-items: center;
    gap: $spacing-4;
  }

  .header-text {
    flex-grow: 1;
  }

  .profile-title {
    font-size: 2.5rem;
    color: $primary-dark;
    margin-bottom: $spacing-1;
  }

  .profile-subtitle {
    font-size: 1.1rem;
    color: $gray;
  }

  .profile-completion {
    display: flex;
    align-items: center;
    gap: $spacing-2;
    color: $primary;
    font-weight: $font-weight-bold;
    font-size: 1.1rem;

    .completion-circle {
      position: relative;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background-color: $white;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: $shadow-sm;
    }

    .progress-ring {
      transform: rotate(-90deg); /* Start from the top */
      transform-origin: 50% 50%;
    }

    .progress-ring-circle {
      fill: none;
      stroke-width: 4;
      stroke-linecap: round;
      stroke-dasharray: 163; /* Circumference of the circle */
      stroke-dashoffset: 0;
      transition: stroke-dashoffset 0.3s ease-in-out;
    }

    .completion-text {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 1.5rem;
      font-weight: $font-weight-bold;
    }
  }
}

.profile-tabs-container {
  margin-bottom: $spacing-6;
  background-color: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-lg;
  overflow: hidden;
  border: 1px solid $gray-lighter;
}

.profile-tabs {
  display: flex;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 3px solid $primary;
  padding: $spacing-3 $spacing-4;
  gap: $spacing-1;
  justify-content: flex-start;
  width: 100%;
  flex-wrap: nowrap;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    bottom: -3px;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, $primary 0%, lighten($primary, 15%) 100%);
  }
}

.tab-item {
  flex: 0 0 auto;
  min-width: 120px;
  max-width: 160px;
  padding: $spacing-3 $spacing-4;
  border: 2px solid transparent;
  background: $white;
  color: $gray-dark;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-2;
  border-radius: $border-radius-lg $border-radius-lg 0 0;
  white-space: nowrap;
  position: relative;
  margin-bottom: -3px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);

  &.active {
    background: $primary;
    color: $white;
    border-color: $primary;
    box-shadow: 0 4px 12px rgba($primary, 0.3);
    transform: translateY(-3px);
    z-index: 10;
    
    &::after {
      content: '';
      position: absolute;
      bottom: -3px;
      left: 0;
      right: 0;
      height: 3px;
      background: $primary;
    }
  }

  &:hover:not(.active) {
    background: lighten($primary, 45%);
    color: $primary-dark;
    border-color: lighten($primary, 30%);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  }

  .tab-icon {
    font-size: 1rem;
    margin-right: $spacing-1;
  }

  .tab-content {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .tab-title {
    font-size: 1rem;
    font-weight: 600;
    color: $primary-dark;
  }

  .tab-description {
    font-size: 0.8rem;
    color: $gray;
    margin-top: $spacing-1;
  }

  .tab-indicator {
    position: absolute;
    bottom: -3px;
    left: 0;
    right: 0;
    height: 3px;
    background: $primary;
    border-radius: $border-radius-sm;
  }
}

.tab-panels {
  min-height: 600px;
  width: 100%;
  clear: both;
}

.tab-panel {
  padding: 0;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background-color: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  padding: $spacing-4;
}

.loading-spinner {
  @include spinner;
  margin-bottom: $spacing-2;
}

.loading-text {
  color: $gray;
  font-size: 1rem;
}

.profile-form {
  background-color: white;
  border-radius: $border-radius-lg;
  padding: $spacing-4;
  box-shadow: $shadow;
  margin-top: $spacing-4;
}

.form-card {
  background-color: #f8f9fa;
  border-radius: $border-radius;
  padding: $spacing-3;
  margin-bottom: $spacing-3;
  border: 1px solid $gray-lighter;
  box-shadow: $shadow-sm;
}

.card-header {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  margin-bottom: $spacing-2;
  padding-bottom: $spacing-2;
  border-bottom: 1px solid $gray-lighter;

  .card-icon {
    font-size: 1.5rem;
    color: $primary;
  }

  .card-title {
    h3 {
      font-size: 1.2rem;
      color: $primary-dark;
      margin-bottom: $spacing-1;
    }

    p {
      font-size: 0.9rem;
      color: $gray;
    }
  }
}

.card-content {
  .form-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: $spacing-2;

    @include responsive('md') {
      grid-template-columns: 1fr 1fr;
    }
  }

  .form-group {
    .form-label {
      display: flex;
      align-items: center;
      gap: $spacing-1;
      font-size: 0.9rem;
      color: $gray-dark;
      font-weight: $font-weight-semibold;

      .label-text {
        flex-grow: 1;
      }

      .label-required {
        color: $error;
      }
    }

    .input-group {
      display: flex;
      align-items: center;
      gap: $spacing-1;
      margin-top: $spacing-1;

      .form-input {
        width: 100%;
        padding: $spacing-2;
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

        &.error {
          border-color: $error;
          box-shadow: 0 0 0 3px rgba($error, 0.1);
        }
      }

      .input-suffix {
        font-size: 0.9rem;
        color: $gray;
      }
    }

    .number-input-container {
      position: relative;
      margin-top: $spacing-1;

      .number-input {
        width: 100%;
        padding: $spacing-2;
        padding-right: $spacing-6; /* Make space for slider */
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
      }

      .number-slider {
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        width: $spacing-6;
        pointer-events: none;
        display: flex;
        align-items: center;
        justify-content: center;

        .slider {
          -webkit-appearance: none;
          width: 100%;
          height: 4px;
          background: $gray-light;
          border-radius: 2px;
          outline: none;
          opacity: 0.7;
          transition: opacity 0.2s;

          &:hover {
            opacity: 1;
          }

          &::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            background: $primary;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 2px rgba(0,0,0,0.2);
          }

          &::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: $primary;
            border-radius: 50%;
            cursor: pointer;
            box-shadow: 0 0 2px rgba(0,0,0,0.2);
          }
        }

        .slider-labels {
          position: absolute;
          top: -20px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          justify-content: space-between;
          width: 100%;
          font-size: 0.8rem;
          color: $gray;
        }
      }
    }

    .activity-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: $spacing-2;

      @include responsive('md') {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .activity-card {
      display: flex;
      align-items: center;
      gap: $spacing-2;
      padding: $spacing-2;
      background-color: $white;
      border: 1px solid $gray-lighter;
      border-radius: $border-radius;
      cursor: pointer;
      transition: all 0.2s ease;

      &:hover {
        background-color: $primary-light;
        border-color: $primary;
        box-shadow: $shadow-sm;
      }

      &.active {
        background-color: $primary;
        border-color: $primary;
        color: $white;

        .activity-checkbox {
          background-color: $white;
          border-color: $white;
        }

        .activity-label {
          color: $white;
        }
      }

      .activity-checkbox {
        flex-shrink: 0;
        width: 18px;
        height: 18px;
        border: 2px solid $gray-light;
        border-radius: 4px;
        background-color: $white;
        transition: all 0.2s ease;

        &:checked {
          background-color: $primary;
          border-color: $primary;
        }
      }

      .activity-label {
        display: flex;
        align-items: center;
        gap: $spacing-1;
        flex-grow: 1;
        font-size: 0.95rem;
        color: $gray-dark;
        cursor: pointer;
      }

      .activity-icon {
        font-size: 1rem;
        color: $primary;
      }

      .activity-info {
        display: flex;
        flex-direction: column;
      }

      .activity-name {
        font-weight: $font-weight-semibold;
        color: $primary-dark;
      }

      .activity-desc {
        font-size: 0.8rem;
        color: $gray;
      }
    }

    .metrics-display {
      margin-top: $spacing-2;
      background-color: #f8fcfc;
      padding: $spacing-2;
      border-radius: $border-radius;
      border-left: 4px solid $primary;

      .metric-card {
        display: flex;
        align-items: center;
        gap: $spacing-1;

        .metric-icon {
          font-size: 1.2rem;
          color: $primary;
        }

        .metric-info {
          .metric-label {
            font-size: 0.9rem;
            color: $gray;
          }

          .metric-value {
            display: flex;
            align-items: baseline;
            gap: $spacing-1;
            font-size: 1.2rem;
            font-weight: $font-weight-bold;
            color: $primary-dark;

            .value {
              font-size: 1.5rem;
            }

            .category {
              padding: $spacing-1 $spacing-2;
              border-radius: $border-radius-sm;
              font-size: 0.8rem;
              font-weight: $font-weight-semibold;
            }

            .underweight {
              background-color: $success-light;
              color: $success;
            }
            .normal {
              background-color: $info-light;
              color: $info;
            }
            .overweight {
              background-color: $warning-light;
              color: $warning;
            }
            .obese {
              background-color: $error-light;
              color: $error;
            }
          }
        }
      }
    }

    .achievement-card {
      margin-top: $spacing-3;
      padding: $spacing-2;
      background-color: #d4edda;
      border-radius: $border-radius;
      border-left: 4px solid $success;
      display: flex;
      align-items: center;
      gap: $spacing-2;

      .achievement-icon {
        font-size: 1.5rem;
        color: $success;
      }

      .achievement-content {
        h4 {
          font-size: 1.1rem;
          color: darken($success, 10%);
          margin-bottom: $spacing-1;
        }

        p {
          font-size: 0.9rem;
          color: darken($success, 10%);
          margin-bottom: 0;
        }
      }
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: $spacing-1;
    margin-top: $spacing-3;
  }

  .btn {
    padding: $spacing-2 $spacing-3;
    border-radius: $border-radius;
    font-weight: $font-weight-semibold;
    display: flex;
    align-items: center;
    gap: $spacing-1;
    transition: all 0.2s ease;

    &.btn-outline {
      background-color: $white;
      color: $primary;
      border: 1px solid $primary;

      &:hover:not(:disabled) {
        background-color: $primary-light;
        color: $primary;
        border-color: $primary;
      }

      &:disabled {
        background-color: $gray-lighter;
        color: $gray;
        border-color: $gray-light;
        cursor: not-allowed;
      }
    }

    &.btn-primary {
      background-color: $primary;
      color: $white;
      border: none;

      &:hover:not(:disabled) {
        background-color: darken($primary, 10%);
      }

      &:disabled {
        background-color: $gray-lighter;
        color: $gray;
        cursor: not-allowed;
      }

      .btn-loading {
        display: flex;
        align-items: center;
        gap: $spacing-1;

        .spinner {
          display: inline-block;
          width: 1rem;
          height: 1rem;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-radius: 50%;
          border-top-color: white;
          animation: spin 1s ease-in-out infinite;
        }
      }
    }
  }

  .error-message {
    color: $error;
    font-size: 0.875rem;
    margin-top: $spacing-1;
    display: block;
  }

  .help-text {
    color: $gray;
    font-size: 0.875rem;
    margin-top: $spacing-1;
    display: block;
  }

  .form-select, .form-textarea {
    width: 100%;
    padding: $spacing-2;
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
  }

  .form-textarea {
    min-height: $spacing-6;
    padding-top: $spacing-2;
    padding-bottom: $spacing-2;
  }

  .checkbox-group {
    display: grid;
    grid-template-columns: 1fr;
    gap: $spacing-1;
    margin-top: $spacing-1;

    @include responsive('md') {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .checkbox-item {
    display: flex;
    align-items: center;
    position: relative;
    margin-bottom: $spacing-1;
  }

  .checkbox-item input[type="checkbox"] {
    position: absolute;
    opacity: 0;
    cursor: pointer;
    height: 0;
    width: 0;
  }

  .checkbox-label {
    padding-left: $spacing-3;
    cursor: pointer;
    font-weight: normal;
    position: relative;
    display: inline-block;
    user-select: none;
    font-size: 0.9rem;
    color: $gray-dark;

    &:hover {
      color: $primary;
    }
  }

  .checkbox-label:before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: $spacing-2;
    height: $spacing-2;
    border: 2px solid $gray-light;
    background-color: $white;
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
    left: $spacing-1;
    top: $spacing-1;
    width: $spacing-1;
    height: $spacing-1;
    border: solid $white;
    border-width: 0 $spacing-1 $spacing-1 0;
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

  .restriction-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: $spacing-1;
    margin-top: $spacing-1;

    @include responsive('md') {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .restriction-card {
    display: flex;
    align-items: center;
    gap: $spacing-1;
    padding: $spacing-1;
    background-color: $white;
    border: 1px solid $gray-lighter;
    border-radius: $border-radius;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      background-color: $primary-light;
      border-color: $primary;
      box-shadow: $shadow-sm;
    }

    &.active {
      background-color: $primary;
      border-color: $primary;
      color: $white;

      .restriction-checkbox {
        background-color: $white;
        border-color: $white;
      }

      .restriction-label {
        color: $white;
      }
    }

    .restriction-checkbox {
      flex-shrink: 0;
      width: $spacing-2;
      height: $spacing-2;
      border: 2px solid $gray-light;
      border-radius: 4px;
      background-color: $white;
      transition: all 0.2s ease;

      &:checked {
        background-color: $primary;
        border-color: $primary;
      }
    }

    .restriction-label {
      display: flex;
      align-items: center;
      gap: $spacing-1;
      flex-grow: 1;
      font-size: 0.9rem;
      color: $gray-dark;
      cursor: pointer;

      .restriction-icon {
        font-size: 0.9rem;
        color: $primary;
      }
    }
  }

  .privacy-setting {
    display: flex;
    align-items: center;
    gap: $spacing-2;
    margin-top: $spacing-2;
    padding: $spacing-2;
    background-color: #f8f9fa;
    border: 1px solid $gray-lighter;
    border-radius: $border-radius;
    box-shadow: $shadow-sm;

    .privacy-toggle {
      position: relative;
      width: 40px;
      height: 20px;
      margin-right: $spacing-1;

      .toggle-checkbox {
        position: absolute;
        opacity: 0;
        width: 0;
        height: 0;
      }

      .toggle-label {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: $gray-light;
        border-radius: 20px;
        cursor: pointer;
        transition: background-color 0.3s ease;

        .toggle-switch {
          position: absolute;
          width: 16px;
          height: 16px;
          background-color: $white;
          border-radius: 50%;
          border: 1px solid $gray-light;
          box-shadow: $shadow-sm;
          transition: transform 0.3s ease;
          left: 2px;
          top: 2px;
        }
      }

      .toggle-checkbox:checked + .toggle-label .toggle-switch {
        transform: translateX(20px);
      }
    }

    .privacy-content {
      h4 {
        font-size: 1rem;
        color: $primary-dark;
        margin-bottom: $spacing-1;
      }

      p {
        font-size: 0.85rem;
        color: $gray;
        margin-bottom: 0;
      }
    }
  }
}

.status-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: $white;
  border-radius: $border-radius;
  box-shadow: $shadow-lg;
  padding: $spacing-2 $spacing-3;
  display: flex;
  align-items: center;
  gap: $spacing-1;
  z-index: 1000;
  border-left: 4px solid;

  &.success {
    border-left-color: $success;
    color: darken($success, 10%);
    background-color: lighten($success, 45%);
  }

  &.error {
    border-left-color: $error;
    color: darken($error, 10%);
    background-color: lighten($error, 45%);
  }

  .status-icon {
    font-size: 1.2rem;
    color: $primary;
  }

  .status-content {
    flex-grow: 1;
  }

  .status-close {
    background: none;
    border: none;
    font-size: 1.2rem;
    color: $gray;
    cursor: pointer;
    padding: 0;
    line-height: 1;

    &:hover {
      color: $gray-dark;
    }
  }
}

// Enhanced Responsive Design
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-2;
    padding: $spacing-3;
    
    .header-content {
      flex-direction: column;
      align-items: flex-start;
      width: 100%;
    }
    
    .profile-title {
      font-size: 2rem;
    }
    
    .profile-completion {
      align-self: flex-end;
      margin-top: $spacing-2;
    }
  }

  .profile-tabs {
    margin-bottom: $spacing-4;
    border-radius: $border-radius;
    padding: $spacing-2 $spacing-3;
    gap: $spacing-1;
    justify-content: flex-start;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    -ms-overflow-style: none;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }

  .tab-item {
    padding: $spacing-2 $spacing-3;
    font-size: 0.85rem;
    min-width: 100px;
    max-width: 130px;
    flex-shrink: 0;
    
    .tab-icon {
      font-size: 0.85rem;
    }
    
    .tab-content {
      align-items: flex-start;
    }
    
    .tab-description {
      display: none; // Hide descriptions on mobile
    }
    
    &:hover:not(.active) {
      transform: translateY(-1px);
    }
    
    &.active {
      transform: translateY(-2px);
    }
  }

  .profile-form {
    padding: $spacing-3;
  }

  .form-card {
    padding: $spacing-2;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-1;
    
    .card-icon {
      font-size: 1.3rem;
    }
  }

  .form-grid {
    grid-template-columns: 1fr !important;
    gap: $spacing-2;
  }

  .activity-grid,
  .restriction-grid {
    grid-template-columns: 1fr !important;
  }

  .form-actions {
    flex-direction: column;
    gap: $spacing-2;
    
    .btn {
      width: 100%;
      justify-content: center;
    }
  }

  .profile-container {
    padding: $spacing-2;
  }
}

@media (max-width: 480px) {
  .profile-title {
    font-size: 1.8rem;
  }
  
  .profile-subtitle {
    font-size: 1rem;
  }
  
  .completion-circle {
    width: 50px !important;
    height: 50px !important;
    
    .progress-ring {
      width: 50px;
      height: 50px;
    }
    
    .completion-text {
      font-size: 1.2rem;
    }
  }
  
  .tab-item {
    min-width: 80px;
    max-width: 100px;
    padding: $spacing-1 $spacing-2;
    
    .tab-title {
      font-size: 0.8rem;
    }
  }
  
  .form-card {
    margin-bottom: $spacing-2;
  }
  
  .status-message {
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    width: auto;
     }
 }

 .nutrition-wrapper {
   .nutrition-intro {
     margin-bottom: $spacing-4;
     
     .intro-card {
       background: linear-gradient(135deg, $primary-light 0%, $primary 100%);
       border-radius: $border-radius-lg;
       padding: $spacing-4;
       color: $white;
       display: flex;
       align-items: center;
       gap: $spacing-3;
       box-shadow: $shadow-lg;
       
       .intro-icon {
         font-size: 2.5rem;
         opacity: 0.9;
       }
       
       .intro-content {
         flex-grow: 1;
         
         h3 {
           font-size: 1.5rem;
           font-weight: $font-weight-bold;
           margin-bottom: $spacing-2;
         }
         
         p {
           font-size: 1rem;
           opacity: 0.9;
           line-height: 1.5;
           margin: 0;
         }
       }
     }
   }
 }
 
 @keyframes spin {
  to { transform: rotate(360deg); }
}
</style>