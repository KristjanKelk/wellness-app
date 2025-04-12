<!-- App.vue -->
<template>
  <div id="app">
    <AppHeader />
    <router-view></router-view>
  </div>
</template>

<script>
import AppHeader from './components/AppHeader.vue'

export default {
  name: 'App',
  components: {
    AppHeader
  },
  created() {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    const storeHasUser = this.$store.state.auth &&
                         this.$store.state.auth.status &&
                         this.$store.state.auth.status.loggedIn;

    if (userStr && !storeHasUser) {
      console.log('Inconsistent auth state detected, attempting to restore session');
      this.$store.dispatch('auth/checkAuth')
        .catch(() => {
          console.log('Failed to restore session, continuing as unauthenticated');
        });
    } else if (storeHasUser) {
      this.$store.dispatch('auth/checkAuth')
        .catch(() => {
          console.log('Session validation failed, logging out');
          this.$store.dispatch('auth/logout');
          this.$router.push('/login');
        });
    }
  }
}
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: Arial, sans-serif;
  background-color: #f5f5f5;
  color: #333;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}
</style>