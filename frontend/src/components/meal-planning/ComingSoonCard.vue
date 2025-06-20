<!-- src/components/meal-planning/ComingSoonCard.vue -->
<template>
  <div class="coming-soon-card">
    <div class="card-content">
      <div class="icon-container">
        <i :class="icon"></i>
      </div>

      <h2>{{ title }}</h2>
      <p>{{ description }}</p>

      <div class="features-preview">
        <h3>Coming Features:</h3>
        <ul>
          <li v-for="feature in features" :key="feature">
            <i class="fas fa-check-circle"></i>
            {{ feature }}
          </li>
        </ul>
      </div>

      <div class="progress-indicator">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <span class="progress-text">{{ progress }}% Complete</span>
      </div>

      <div class="cta-section">
        <p class="cta-text">Want to be notified when this feature launches?</p>
        <button class="btn btn-primary" @click="subscribeToUpdates">
          <i class="fas fa-bell"></i>
          Notify Me
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ComingSoonCard',
  props: {
    title: {
      type: String,
      required: true
    },
    description: {
      type: String,
      required: true
    },
    icon: {
      type: String,
      default: 'fas fa-rocket'
    },
    progress: {
      type: Number,
      default: 75
    }
  },
  computed: {
    features() {
      // Different features based on the title
      const featureMap = {
        'Meal Plans': [
          'AI-generated daily meal plans',
          'Weekly meal planning',
          'Personalized recipe suggestions',
          'Automatic shopping lists',
          'Nutritional balance optimization'
        ],
        'Nutrition Analytics': [
          'Daily nutrition tracking',
          'Macro breakdown charts',
          'Progress towards goals',
          'Trend analysis',
          'AI-powered insights'
        ]
      }

      return featureMap[this.title] || [
        'Personalized recommendations',
        'Smart AI integration',
        'Beautiful visualizations',
        'Easy-to-use interface'
      ]
    }
  },
  methods: {
    subscribeToUpdates() {
      // In a real app, this would open a modal or send an API request
      alert('Thanks for your interest! We\'ll notify you when this feature is ready.')
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.coming-soon-card {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  overflow: hidden;
  max-width: 600px;
  margin: 0 auto;
}

.card-content {
  padding: $spacing-8;
  text-align: center;
}

.icon-container {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, $primary, lighten($primary, 20%));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto $spacing-6;
  box-shadow: $shadow-lg;

  i {
    font-size: 2rem;
    color: $white;
  }
}

h2 {
  margin: 0 0 $spacing-3 0;
  color: $primary-dark;
  font-size: 2rem;
  font-weight: 600;
}

p {
  color: $gray;
  font-size: 1.1rem;
  line-height: 1.6;
  margin: 0 0 $spacing-6 0;
}

.features-preview {
  text-align: left;
  margin-bottom: $spacing-6;
  padding: $spacing-4;
  background: rgba($primary, 0.05);
  border-radius: $border-radius;
  border-left: 4px solid $primary;

  h3 {
    margin: 0 0 $spacing-3 0;
    color: $primary-dark;
    font-size: 1.1rem;
    font-weight: 600;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  li {
    display: flex;
    align-items: center;
    gap: $spacing-2;
    padding: $spacing-1 0;
    color: $primary-dark;

    i {
      color: $success;
      font-size: 0.9rem;
    }
  }
}

.progress-indicator {
  margin-bottom: $spacing-6;

  .progress-bar {
    width: 100%;
    height: 8px;
    background: $gray-lighter;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: $spacing-2;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, $primary, lighten($primary, 15%));
    border-radius: 4px;
    transition: width 0.5s ease;
  }

  .progress-text {
    font-size: 0.9rem;
    color: $gray;
    font-weight: 500;
  }
}

.cta-section {
  padding-top: $spacing-4;
  border-top: 1px solid $gray-lighter;

  .cta-text {
    margin: 0 0 $spacing-4 0;
    color: $primary-dark;
    font-weight: 500;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: $spacing-2;

    i {
      font-size: 0.9rem;
    }
  }
}

// Animation for the card
.coming-soon-card {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>