<!-- AppHeader.vue -->
<button @click="logout" class="btn btn-danger">Logout</button>
<script>
export default {
  name: 'AppHeader',
  computed: {
    isLoggedIn() {
      return this.$store.getters.isAuthenticated
    }
  },
  methods: {
    logout() {
      this.$store.dispatch('auth/logout')
      this.$router.push('/login')
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
</style>