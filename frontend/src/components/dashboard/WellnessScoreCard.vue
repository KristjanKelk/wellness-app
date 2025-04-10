<template>
  <div class="card">
    <h2>Wellness Score</h2>
    <div v-if="hasProfileData" class="score-container">
      <div class="score-circle" :class="scoreClass">
        <span class="score-number">{{ score }}</span>
      </div>
      <div class="score-breakdown">
        <div class="score-component">
          <span>BMI: {{ bmiScore }} ({{ (bmiScore * 0.3).toFixed(1) }} pts)</span>
          <div class="progress-bar">
            <div class="progress" :style="{ width: bmiScore + '%' }"></div>
          </div>
        </div>
        <div class="score-component">
          <span>Activity: {{ activityScore }} ({{ (activityScore * 0.3).toFixed(1) }} pts)</span>
          <div class="progress-bar">
            <div class="progress" :style="{ width: activityScore + '%' }"></div>
          </div>
        </div>
        <div class="score-component">
          <span>Progress: {{ progressScore }} ({{ (progressScore * 0.2).toFixed(1) }} pts)</span>
          <div class="progress-bar">
            <div class="progress" :style="{ width: progressScore + '%' }"></div>
          </div>
        </div>
        <div class="score-component">
          <span>Habits: {{ habitsScore }} ({{ (habitsScore * 0.2).toFixed(1) }} pts)</span>
          <div class="progress-bar">
            <div class="progress" :style="{ width: habitsScore + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
    <div v-else>
      <p>Your wellness score will be calculated once you've completed your health profile.</p>
      <router-link to="/profile" class="btn btn-primary">Complete Profile</router-link>
    </div>
  </div>
</template>

<script>
import WellnessService from '../../services/wellness-service';

export default {
  name: 'WellnessScoreCard',
  props: {
    profile: {
      type: Object,
      default: null
    },
    score: {
      type: Number,
      default: 0
    },
    bmiScore: {
      type: Number,
      default: 0
    },
    activityScore: {
      type: Number,
      default: 0
    },
    progressScore: {
      type: Number,
      default: 0
    },
    habitsScore: {
      type: Number,
      default: 0
    }
  },
  computed: {
    hasProfileData() {
      return this.profile && this.profile.height_cm && this.profile.weight_kg;
    },
    scoreClass() {
      return WellnessService.getScoreCategory(this.score);
    }
  }
};
</script>