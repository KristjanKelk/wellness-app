<template>
  <div class="home">
    <!-- Hero section -->
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">Track your wellness journey with AI-powered insights</h1>
          <p class="hero-description">Monitor your health metrics, receive personalized recommendations, and visualize your progress with our intelligent wellness platform.</p>
          <div class="hero-actions">
            <router-link v-if="!isLoggedIn" to="/register" class="btn-primary">Get Started</router-link>
            <router-link v-if="!isLoggedIn" to="/login" class="btn-secondary">Sign In</router-link>
            <router-link v-if="isLoggedIn" to="/dashboard" class="btn-primary">Go to Dashboard</router-link>
          </div>
        </div>
        <div class="hero-image">
          <!-- Hero illustration -->
          <img src="@/assets/images/hero-illustration.svg" alt="Wellness tracking illustration" />
        </div>
      </div>
    </section>

    <!-- Features section -->
    <section class="features">
      <div class="container">
        <h2 class="section-title">Why choose our platform?</h2>

        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 8V20.993C21 21.549 20.55 22 19.993 22H4.007C3.451 22 3 21.55 3 20.993V8M21 8H3M21 8L12 3L3 8" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 16H15" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                <path d="M12 13L12 19" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <h3 class="feature-title">Track Your Health Metrics</h3>
            <p class="feature-description">Monitor key health indicators like weight, BMI, activity levels, and more in one unified dashboard.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 3.5V2M5.5 5.5H4M14.5 5.5H16M5.5 14.5H4M14.5 14.5H16" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                <path d="M9 21.5V20M9 14.5V9.5" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                <circle cx="9" cy="7" r="2.5" stroke="#30C1B1" stroke-width="2"/>
                <circle cx="9" cy="17" r="2.5" stroke="#30C1B1" stroke-width="2"/>
              </svg>
            </div>
            <h3 class="feature-title">AI-Powered Insights</h3>
            <p class="feature-description">Receive personalized recommendations and health insights based on your unique profile and goals.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 8L7 4M7 4L11 8M7 4V20" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 16L17 20M17 20L13 16M17 20V4" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3 class="feature-title">Visualize Your Progress</h3>
            <p class="feature-description">See your health journey with clear, intuitive charts and visualizations that help you stay motivated.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works section -->
    <section class="how-it-works">
      <div class="container">
        <h2 class="section-title">How It Works</h2>

        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <h3 class="step-title">Create Your Profile</h3>
            <p class="step-description">Sign up and enter your health information, goals, and preferences to get started.</p>
          </div>

          <div class="step">
            <div class="step-number">2</div>
            <h3 class="step-title">Track Your Journey</h3>
            <p class="step-description">Regularly update your metrics and activities to build a comprehensive health picture.</p>
          </div>

          <div class="step">
            <div class="step-number">3</div>
            <h3 class="step-title">Get Smart Insights</h3>
            <p class="step-description">Receive AI-generated recommendations tailored to your specific health profile and goals.</p>
          </div>

          <div class="step">
            <div class="step-number">4</div>
            <h3 class="step-title">Achieve Your Goals</h3>
            <p class="step-description">Follow your personalized plan and watch as you make progress toward better health.</p>
          </div>
        </div>

        <div class="cta-container">
          <router-link v-if="!isLoggedIn" to="/register" class="btn-primary">Start Your Journey</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useStore } from 'vuex';

export default {
  name: 'Home',
  setup() {
    const store = useStore();

    const isLoggedIn = computed(() => store.getters['auth/isLoggedIn']);

    return {
      isLoggedIn
    };
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

// Hero section
.hero {
  padding: $spacing-12 0;
  background-color: #f8fcfc;
  overflow: hidden;

  @include responsive('lg') {
    padding: $spacing-16 0;
  }

  .container {
    display: flex;
    flex-direction: column;
    align-items: center;

    @include responsive('lg') {
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
    }
  }
}

.hero-content {
  max-width: 600px;
  text-align: center;
  margin-bottom: $spacing-8;

  @include responsive('lg') {
    text-align: left;
    margin-bottom: 0;
    flex: 1;
    padding-right: $spacing-8;
  }
}

.hero-title {
  font-size: 2rem;
  line-height: 1.2;
  margin-bottom: $spacing-4;
  color: $secondary;
  font-weight: $font-weight-bold;

  @include responsive('md') {
    font-size: 2.5rem;
  }

  @include responsive('lg') {
    font-size: 3rem;
  }
}

.hero-description {
  font-size: $font-size-lg;
  color: $gray;
  margin-bottom: $spacing-6;

  @include responsive('md') {
    font-size: 1.25rem;
  }
}

.hero-actions {
  display: flex;
  gap: $spacing-4;
  justify-content: center;

  @include responsive('lg') {
    justify-content: flex-start;
  }

  .btn-primary, .btn-secondary {
    @include button-base;
    padding: $spacing-3 $spacing-8;

    @include responsive('md') {
      padding: $spacing-4 $spacing-10;
    }
  }

  .btn-primary {
    background-color: $primary;
    color: $white;

    &:hover {
      background-color: $primary-dark;
    }
  }

  .btn-secondary {
    background-color: $white;
    color: $secondary;
    border: 1px solid $gray-lighter;

    &:hover {
      background-color: $gray-lighter;
    }
  }
}

.hero-image {
  max-width: 100%;
  height: auto;
  flex: 1;
  display: flex;
  justify-content: center;

  img {
    max-width: 100%;
    height: auto;
    max-height: 400px;

    @include responsive('lg') {
      max-height: 500px;
    }
  }
}

// Features section
.features {
  padding: $spacing-12 0;
  background-color: $white;

  @include responsive('lg') {
    padding: $spacing-16 0;
  }
}

.section-title {
  text-align: center;
  margin-bottom: $spacing-12;
  position: relative;
  font-size: 2rem;

  &:after {
    content: '';
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 3px;
    background-color: $primary;
  }
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: $spacing-8;

  @include responsive('md') {
    grid-template-columns: repeat(2, 1fr);
  }

  @include responsive('lg') {
    grid-template-columns: repeat(3, 1fr);
  }
}

.feature-card {
  background-color: $white;
  border-radius: $border-radius-lg;
  padding: $spacing-6;
  box-shadow: $shadow;
  text-align: center;
  transition: $transition-base;

  &:hover {
    box-shadow: $shadow-lg;
    transform: translateY(-5px);
  }
}

.feature-icon {
  margin-bottom: $spacing-4;
  display: flex;
  justify-content: center;

  svg {
    width: 48px;
    height: 48px;
  }
}

.feature-title {
  margin-bottom: $spacing-3;
  font-size: $font-size-xl;
}

.feature-description {
  color: $gray;
}

// How it works section
.how-it-works {
  padding: $spacing-12 0;
  background-color: #f8fcfc;

  @include responsive('lg') {
    padding: $spacing-16 0;
  }
}

.steps {
  display: grid;
  grid-template-columns: 1fr;
  gap: $spacing-8;
  margin-bottom: $spacing-12;

  @include responsive('md') {
    grid-template-columns: repeat(2, 1fr);
  }

  @include responsive('lg') {
    grid-template-columns: repeat(4, 1fr);
  }
}

.step {
  text-align: center;
  position: relative;

  &:not(:last-child) {
    &:after {
      content: '';
      position: absolute;
      top: 2rem;
      right: -50%;
      width: 100%;
      height: 2px;
      background-color: $gray-lighter;
      display: none;

      @include responsive('lg') {
        display: block;
      }
    }
  }
}

.step-number {
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  background-color: $primary;
  color: $white;
  font-weight: $font-weight-bold;
  font-size: $font-size-xl;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto $spacing-4;
  position: relative;
  z-index: 1;
}

.step-title {
  margin-bottom: $spacing-3;
  font-size: $font-size-lg;
}

.step-description {
  color: $gray;
}

.cta-container {
  text-align: center;
  margin-top: $spacing-8;

  .btn-primary {
    @include button-primary;
    padding: $spacing-4 $spacing-10;
    font-size: $font-size-lg;
  }
}
</style>