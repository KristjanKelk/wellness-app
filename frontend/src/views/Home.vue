<template>
  <div class="home">
    <div class="hero">
      <h1>Wellness Platform</h1>
      <p>Track your health metrics and get personalized insights</p>
      <div class="hero-actions">
        <router-link v-if="!isLoggedIn" to="/register" class="btn btn-primary">Get Started</router-link>
        <router-link v-if="!isLoggedIn" to="/login" class="btn btn-secondary">Login</router-link>
        <router-link v-if="isLoggedIn" to="/dashboard" class="btn btn-primary">My Dashboard</router-link>
      </div>
    </div>
    <div class="features">
      <div class="feature">
        <h3>Track Health Metrics</h3>
        <p>Monitor your weight, activity level, and other health indicators</p>
      </div>
      <div class="feature">
        <h3>AI-Powered Insights</h3>
        <p>Get personalized recommendations based on your data</p>
      </div>
      <div class="feature">
        <h3>Visualize Progress</h3>
        <p>See your progress over time with clear charts and graphs</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  computed: {
    isLoggedIn() {
      return this.$store.getters['auth/isLoggedIn'];
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.hero {
  text-align: center;
  padding: 3rem 1rem;
  margin-bottom: 2rem;
}

.hero h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.hero p {
  font-size: 1.25rem;
  margin-bottom: 2rem;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-weight: bold;
  text-decoration: none;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

.btn-secondary {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature {
  padding: 1.5rem;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.feature h3 {
  margin-bottom: 1rem;
}
</style>