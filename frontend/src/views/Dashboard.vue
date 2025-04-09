<template>
  <div class="dashboard">
    <h1>Health Dashboard</h1>
    <p>Welcome, {{ currentUser && currentUser.username }}!</p>

    <div class="dashboard-content">
      <div class="card">
        <h2>Wellness Score</h2>
        <p>Your wellness score will appear here once you've completed your health profile.</p>
        <router-link to="/profile" class="btn btn-primary">Complete Profile</router-link>
      </div>

      <div class="card">
        <h2>BMI Status</h2>
        <p>Your BMI information will appear here once you've added your height and weight.</p>
      </div>

      <div class="card">
        <h2>Activity Level</h2>
        <p>Your activity tracking will appear here.</p>
      </div>

      <div class="card">
        <h2>AI Insights</h2>
        <p>Personalized health recommendations will appear here.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dashboard',
  computed: {
    currentUser() {
      return this.$store.state.auth.user;
    }
  },
  mounted() {
    if (!this.currentUser) {
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 1rem;
}

.dashboard-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card h2 {
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-weight: bold;
  text-decoration: none;
  margin-top: 1rem;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}
</style>