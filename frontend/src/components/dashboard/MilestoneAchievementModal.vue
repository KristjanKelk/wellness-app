<!-- src/components/dashboard/MilestoneAchievementModal.vue -->
<template>
  <div class="milestone-modal-overlay" @click.self="$emit('close')">
    <div class="milestone-modal">
      <!-- Confetti Animation -->
      <div class="confetti-container">
        <div v-for="n in 50" :key="n" class="confetti" :style="getConfettiStyle(n)"></div>
      </div>

      <!-- Modal Content -->
      <div class="modal-content">
        <div class="achievement-header">
          <div class="achievement-icon">🏆</div>
          <h2>{{ getModalTitle() }}</h2>
          <p class="achievement-subtitle">{{ getModalSubtitle() }}</p>
        </div>

        <!-- Milestones List -->
        <div class="milestones-list">
          <div
            v-for="(milestone, index) in milestones"
            :key="index"
            class="milestone-card"
            :style="{ animationDelay: `${index * 0.2}s` }"
          >
            <div class="milestone-icon">
              {{ getMilestoneIcon(milestone.milestone_type) }}
            </div>
            <div class="milestone-content">
              <h3>{{ milestone.description }}</h3>
              <div class="milestone-details">
                <span class="milestone-type">{{ getMilestoneTypeLabel(milestone.milestone_type) }}</span>
                <span v-if="milestone.progress_value" class="milestone-value">
                  {{ formatProgressValue(milestone) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Progress Impact -->
        <div v-if="showProgressImpact" class="progress-impact">
          <h4>Impact on Your Wellness Score</h4>
          <div class="impact-details">
            <div class="impact-item">
              <span class="impact-label">Progress Score Boost:</span>
              <span class="impact-value">+{{ milestones.length * 5 }} points</span>
            </div>
            <div class="impact-item">
              <span class="impact-label">Total Milestones:</span>
              <span class="impact-value">{{ totalMilestones }} achieved</span>
            </div>
          </div>
        </div>

        <!-- Social Sharing (Optional) -->
        <div v-if="showSharing" class="sharing-section">
          <h4>Share Your Achievement</h4>
          <div class="sharing-buttons">
            <button @click="shareToSocial('twitter')" class="share-btn twitter">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
              </svg>
              Tweet
            </button>
            <button @click="shareToSocial('facebook')" class="share-btn facebook">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/>
              </svg>
              Share
            </button>
            <button @click="copyToClipboard" class="share-btn copy">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              Copy
            </button>
          </div>
        </div>

        <!-- Actions -->
        <div class="modal-actions">
          <button @click="$emit('close')" class="btn btn-primary">
            Continue Your Journey
          </button>
          <button @click="viewAllMilestones" class="btn btn-secondary">
            View All Achievements
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MilestoneAchievementModal',
  props: {
    milestones: {
      type: Array,
      required: true
    },
    showProgressImpact: {
      type: Boolean,
      default: true
    },
    showSharing: {
      type: Boolean,
      default: true
    },
    totalMilestones: {
      type: Number,
      default: 0
    }
  },
  emits: ['close'],
  methods: {
    getModalTitle() {
      if (this.milestones.length === 1) {
        return 'Achievement Unlocked!';
      } else {
        return `${this.milestones.length} New Achievements!`;
      }
    },

    getModalSubtitle() {
      if (this.milestones.length === 1) {
        return 'Congratulations on reaching this milestone!';
      } else {
        return 'You\'re making incredible progress on your wellness journey!';
      }
    },

    getMilestoneIcon(type) {
      const icons = {
        weight: '⚖️',
        activity: '🏃',
        habit: '🔄',
        goal: '🎯',
        streak: '🔥'
      };
      return icons[type] || '🏆';
    },

    getMilestoneTypeLabel(type) {
      const labels = {
        weight: 'Weight Goal',
        activity: 'Activity Milestone',
        habit: 'Habit Streak',
        goal: 'Goal Achievement',
        streak: 'Streak Milestone'
      };
      return labels[type] || 'Achievement';
    },

    formatProgressValue(milestone) {
      if (!milestone.progress_value) return '';

      switch (milestone.milestone_type) {
        case 'weight':
          return `${milestone.progress_value} kg`;
        case 'activity':
          return `${milestone.progress_value} days/week`;
        case 'habit':
          return `${milestone.progress_value} day streak`;
        default:
          return milestone.progress_value;
      }
    },

    getConfettiStyle(index) {
      const colors = [
        '#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1',
        '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF'
      ];

      return {
        backgroundColor: colors[index % colors.length],
        left: Math.random() * 100 + 'vw',
        animationDelay: Math.random() * 3 + 's',
        animationDuration: (Math.random() * 3 + 2) + 's'
      };
    },

    shareToSocial(platform) {
      const text = this.getShareText();
      const url = window.location.origin;

      let shareUrl = '';

      switch (platform) {
        case 'twitter':
          shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
          break;
        case 'facebook':
          shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(text)}`;
          break;
      }

      if (shareUrl) {
        window.open(shareUrl, '_blank', 'width=600,height=400');
      }
    },

    async copyToClipboard() {
      const text = this.getShareText();
      try {
        await navigator.clipboard.writeText(text);
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
      }
    },

    getShareText() {
      if (this.milestones.length === 1) {
        return `Just achieved a new milestone: ${this.milestones[0].description} 🏆 #WellnessJourney #HealthGoals`;
      } else {
        return `Just unlocked ${this.milestones.length} new achievements on my wellness journey! 🏆 #WellnessJourney #HealthGoals`;
      }
    },

    viewAllMilestones() {
      this.$emit('close');
      this.$router.push('/achievements');
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.milestone-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: $spacing-4;
}

.milestone-modal {
  position: relative;
  background-color: $white;
  border-radius: $border-radius-lg;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalAppear 0.3s ease-out;
}

.confetti-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
}

.confetti {
  position: absolute;
  width: 10px;
  height: 10px;
  top: -10px;
  animation: confettiFall linear infinite;
}

.modal-content {
  padding: $spacing-6;
}

.achievement-header {
  text-align: center;
  margin-bottom: $spacing-6;

  .achievement-icon {
    font-size: 4rem;
    margin-bottom: $spacing-4;
    animation: bounce 2s infinite;
  }

  h2 {
    color: $secondary;
    margin-bottom: $spacing-2;
  }

  .achievement-subtitle {
    color: $gray;
    font-size: $font-size-lg;
  }
}

.milestones-list {
  margin-bottom: $spacing-6;
}

.milestone-card {
  display: flex;
  align-items: center;
  gap: $spacing-4;
  padding: $spacing-4;
  background: linear-gradient(135deg, $primary, lighten($primary, 10%));
  color: $white;
  border-radius: $border-radius;
  margin-bottom: $spacing-3;
  animation: slideInLeft 0.5s ease-out;
  box-shadow: $shadow-lg;

  &:last-child {
    margin-bottom: 0;
  }

  .milestone-icon {
    font-size: 2rem;
    min-width: 60px;
    text-align: center;
  }

  .milestone-content {
    flex: 1;

    h3 {
      margin: 0 0 $spacing-2 0;
      font-size: $font-size-lg;
    }

    .milestone-details {
      display: flex;
      gap: $spacing-3;
      align-items: center;

      .milestone-type {
        background-color: rgba($white, 0.2);
        padding: $spacing-1 $spacing-2;
        border-radius: $border-radius-sm;
        font-size: $font-size-sm;
      }

      .milestone-value {
        font-weight: $font-weight-bold;
        font-size: $font-size-sm;
      }
    }
  }
}

.progress-impact {
  background-color: $bg-light;
  padding: $spacing-4;
  border-radius: $border-radius;
  margin-bottom: $spacing-6;

  h4 {
    margin: 0 0 $spacing-3 0;
    color: $secondary;
  }

  .impact-details {
    display: flex;
    flex-direction: column;
    gap: $spacing-2;
  }

  .impact-item {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .impact-label {
      color: $gray;
    }

    .impact-value {
      font-weight: $font-weight-bold;
      color: $success;
    }
  }
}

.sharing-section {
  margin-bottom: $spacing-6;

  h4 {
    margin: 0 0 $spacing-3 0;
    color: $secondary;
    text-align: center;
  }

  .sharing-buttons {
    display: flex;
    justify-content: center;
    gap: $spacing-3;
  }

  .share-btn {
    display: flex;
    align-items: center;
    gap: $spacing-2;
    padding: $spacing-2 $spacing-4;
    border: none;
    border-radius: $border-radius;
    font-weight: $font-weight-medium;
    cursor: pointer;
    transition: $transition-base;

    &.twitter {
      background-color: #1DA1F2;
      color: $white;

      &:hover {
        background-color: darken(#1DA1F2, 10%);
      }
    }

    &.facebook {
      background-color: #4267B2;
      color: $white;

      &:hover {
        background-color: darken(#4267B2, 10%);
      }
    }

    &.copy {
      background-color: $gray-light;
      color: $secondary;

      &:hover {
        background-color: $gray;
        color: $white;
      }
    }
  }
}

.modal-actions {
  display: flex;
  flex-direction: column;
  gap: $spacing-3;
  align-items: center;

  @include responsive('sm') {
    flex-direction: row;
    justify-content: center;
  }

  .btn {
    min-width: 200px;
  }
}

// Animations
@keyframes modalAppear {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes confettiFall {
  to {
    transform: translateY(100vh) rotate(360deg);
  }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-30px);
  }
  60% {
    transform: translateY(-15px);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

// Responsive adjustments
@include responsive('sm') {
  .milestone-modal {
    margin: $spacing-4;
  }

  .modal-content {
    padding: $spacing-4;
  }

  .milestone-card {
    flex-direction: column;
    text-align: center;

    .milestone-content {
      .milestone-details {
        justify-content: center;
      }
    }
  }
}
</style>