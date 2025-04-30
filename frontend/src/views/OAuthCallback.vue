<template>
  <div class="oauth-callback">
    <div class="callback-container">
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <p>Processing login... Please wait.</p>
      </div>
      <div v-else-if="error" class="error">
        <div class="error-icon">!</div>
        <h2>Authentication Failed</h2>
        <p>{{ error }}</p>
        <router-link to="/login" class="btn btn-primary">Return to Login</router-link>
      </div>
      <div v-else class="success">
        <div class="success-icon">✓</div>
        <h2>Authentication Successful</h2>
        <p>Redirecting to dashboard...</p>
      </div>
    </div>
  </div>
</template>

<script>
import OAuthService from '../services/oauth.service';

export default {
  name: 'OAuthCallback',
  data() {
    return {
      loading: true,
      error: null
    };
  },
  mounted() {
    this.processCallback();
  },
  methods: {
    processCallback() {
      const queryParams = new URLSearchParams(window.location.search);

      OAuthService.processCallback(queryParams)
        .then(userData => {
          console.log('OAuth login successful:', userData);

          // Store the user data
          this.$store.commit('auth/loginSuccess', userData);

          this.loading = false;

          // Redirect to dashboard after a short delay
          setTimeout(() => {
            this.$router.push('/dashboard');
          }, 1500);
        })
        .catch(error => {
          console.error('OAuth callback error:', error);
          this.error = error.message || 'Failed to complete authentication. Please try again.';
          this.loading = false;
        });
    }
  }
};
</script>

<style scoped>
.oauth-callback {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.callback-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  padding: 2rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.loading, .success, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.success-icon, .error-icon {
  font-size: 48px;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  font-weight: bold;
}

.success-icon {
  background-color: #d4edda;
  color: #155724;
}

.error-icon {
  background-color: #f8d7da;
  color: #721c24;
}

h2 {
  margin-bottom: 1rem;
}

p {
  margin-bottom: 1.5rem;
  color: #666;
}

.btn {
  cursor: pointer;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
  text-decoration: none;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>