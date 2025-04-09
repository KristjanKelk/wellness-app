<!-- AppHeader.vue -->
<template>
  <header class="app-header">
    <div class="container">
      <router-link to="/" class="logo">Wellness Platform</router-link>
      <nav class="nav-menu">
        <template v-if="isLoggedIn">
          <router-link to="/dashboard">Dashboard</router-link>
          <router-link to="/profile">Profile</router-link>
          <button @click="logout" class="btn btn-danger">Logout</button>
        </template>
        <template v-else>
          <router-link to="/login">Login</router-link>
          <router-link to="/register">Register</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppHeader',
  computed: {
    isLoggedIn() {
      const authState = this.$store.state.auth;
      console.log('Auth state:', authState);
      return authState && authState.status && authState.status.loggedIn;
    }
  },
  created() {
    console.log('AppHeader created, loggedIn status:', this.isLoggedIn);
  },
  methods: {
    logout() {
      this.$store.dispatch('auth/logout');
      this.$router.push('/login');
    }
  }
}
</script>

<style scoped>
.app-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 1rem 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: #4CAF50;
  text-decoration: none;
}

.nav-menu {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-menu a {
  color: #333;
  text-decoration: none;
  padding: 0.5rem 0;
  font-weight: 500;
}

.nav-menu a:hover {
  color: #4CAF50;
}

.nav-menu a.router-link-exact-active {
  color: #4CAF50;
  border-bottom: 2px solid #4CAF50;
}

.btn {
  cursor: pointer;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}
</style>