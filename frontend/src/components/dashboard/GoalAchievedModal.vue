<!-- src/components/dashboard/GoalAchievedModal.vue -->
<template>
  <div class="goal-achieved-modal" v-if="show">
    <div class="modal-content">
      <div class="confetti-container">
        <div v-for="n in 50" :key="n" class="confetti" :style="randomConfettiStyle()"></div>
      </div>
      <div class="achievement-content">
        <div class="achievement-icon">🏆</div>
        <h2>Goal Achieved!</h2>
        <p>Congratulations! You've reached your weight goal of {{ goalWeight }}kg.</p>
        <div class="achievement-details">
          <div class="detail-item">
            <span class="detail-label">Starting Weight:</span>
            <span class="detail-value">{{ startWeight }}kg</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Current Weight:</span>
            <span class="detail-value">{{ currentWeight }}kg</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Total Change:</span>
            <span class="detail-value">{{ (startWeight - currentWeight).toFixed(1) }}kg</span>
          </div>
        </div>
        <button @click="$emit('close')" class="btn-primary">Continue</button>
      </div>
    </div>
  </div>
</template>

<script>
import AnalyticsService from '../../services/analytics.service';

export default {
  name: 'GoalAchievedModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    goalWeight: {
      type: Number,
      required: true
    },
    currentWeight: {
      type: Number,
      required: true
    },
    startWeight: {
      type: Number,
      required: true
    }
  },
  created() {
    // Send the goal achievement to the backend
    this.recordGoalAchievement();
  },
  methods: {
    async recordGoalAchievement() {
      try {
        // Trigger a wellness score calculation to record the milestone
        await AnalyticsService.calculateWellnessScore();
      } catch (error) {
        console.error('Failed to record goal achievement:', error);
      }
    },
    randomConfettiStyle() {
      const colors = ['#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B', '#FFC107', '#FF9800', '#FF5722'];

      return {
        backgroundColor: colors[Math.floor(Math.random() * colors.length)],
        left: Math.random() * 100 + 'vw',
        top: (Math.random() * -10 - 10) + 'vh',
        transform: 'rotate(' + Math.random() * 360 + 'deg)',
        width: (Math.random() + 0.5) + 'rem',
        height: (Math.random() * 0.3 + 0.1) + 'rem',
        animationDelay: Math.random() * 5 + 's',
        animationDuration: (Math.random() * 3 + 3) + 's'
      };
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.goal-achieved-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.5s ease-out;
}

.modal-content {
  position: relative;
  background-color: white;
  border-radius: $border-radius-lg;
  padding: $spacing-8;
  width: 90%;
  max-width: 500px;
  overflow: hidden;
  z-index: 1001;
}

.confetti-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.confetti {
  position: absolute;
  animation: confettiFall linear forwards;
}

.achievement-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.achievement-icon {
  font-size: 4rem;
  margin-bottom: $spacing-4;
  animation: bounce 2s infinite;
}

.achievement-details {
  margin: $spacing-6 0;
  background-color: $gray-lighter;
  border-radius: $border-radius;
  padding: $spacing-4;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: $spacing-2;

  &:last-child {
    margin-bottom: 0;
    font-weight: $font-weight-bold;
  }
}

.btn-primary {
  //@include button-primary;
  margin-top: $spacing-4;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes confettiFall {
  from {
    transform: translateY(-10vh) rotate(0deg);
  }
  to {
    transform: translateY(100vh) rotate(360deg);
  }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-20px);
  }
  60% {
    transform: translateY(-10px);
  }
}
</style>