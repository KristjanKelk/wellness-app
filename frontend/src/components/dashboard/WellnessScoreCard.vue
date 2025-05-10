<!-- src/components/dashboard/WellnessScoreCard.vue -->
<template>
  <dashboard-card
    title="Wellness Score"
    :isEmpty="!hasProfileData"
  >
    <template v-slot:empty>
      <p>Your wellness score will be calculated once you've completed your health profile.</p>
      <router-link to="/profile" class="btn btn-primary">Complete Profile</router-link>
    </template>

    <div class="score-card">
      <div class="score-circle" :class="scoreClass">
        <span class="score-number">{{ score }}</span>
      </div>
      <div class="score-breakdown">
        <div class="score-component">
          <div class="component-info">
            <span class="component-label">BMI Score</span>
            <span class="component-value">{{ bmiScore }}% ({{ (bmiScore * 0.3).toFixed(1) }}pts)</span>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: bmiScore + '%' }"></div>
          </div>
        </div>

        <div class="score-component">
          <div class="component-info">
            <span class="component-label">Activity</span>
            <span class="component-value">{{ activityScore }}% ({{ (activityScore * 0.3).toFixed(1) }}pts)</span>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: activityScore + '%' }"></div>
          </div>
        </div>

        <div class="score-component">
          <div class="component-info">
            <span class="component-label">Progress</span>
            <span class="component-value">{{ progressScore }}% ({{ (progressScore * 0.2).toFixed(1) }}pts)</span>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: progressScore + '%' }"></div>
          </div>
        </div>

        <div class="score-component">
          <div class="component-info">
            <span class="component-label">Habits</span>
            <span class="component-value">{{ habitsScore }}% ({{ (habitsScore * 0.2).toFixed(1) }}pts)</span>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: habitsScore + '%' }"></div>
          </div>
        </div>
      </div>
    </div>
  </dashboard-card>
</template>

<script>
import DashboardCard from './DashboardCard.vue';
import WellnessService from '../../services/wellness-service';

export default {
  name: 'WellnessScoreCard',
  components: {
    DashboardCard
  },
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

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';

.score-card {
  .score-component {
    margin-bottom: $spacing-3;

    &:last-child {
      margin-bottom: 0;
    }

    .component-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-1;

      .component-label {
        font-weight: $font-weight-medium;
        color: $secondary;
        font-size: $font-size-sm;
      }

      .component-value {
        color: $gray-dark;
        font-size: $font-size-sm;
      }
    }

    .progress-bar {
      height: 6px;
      background-color: $gray-lighter;
      border-radius: 3px;
      overflow: hidden;

      .progress {
        height: 100%;
        border-radius: 3px;
        background-color: $primary;
        transition: width 0.6s ease-in-out;
      }
    }
  }
}
</style>