<template>
  <div id="app">
    <AppHeader />
    <main class="main-content">
      <router-view></router-view>
    </main>
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
      if (process.env.NODE_ENV === 'development') {
        console.log('🔄 Inconsistent auth state detected, attempting to restore session');
      }
      this.$store.dispatch('auth/checkAuth')
        .catch(() => {
          if (process.env.NODE_ENV === 'development') {
            console.log('🔓 Failed to restore session, continuing as unauthenticated');
          }
        });
    } else if (storeHasUser) {
      this.$store.dispatch('auth/checkAuth')
        .catch(() => {
          if (process.env.NODE_ENV === 'development') {
            console.log('🔐 Session validation failed, logging out');
          }
          this.$store.dispatch('auth/logout');
          this.$router.push('/login');
        });
    }
  }
}
</script>

<style lang="scss">
@import '@/assets/styles/main.scss';

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}
</style>