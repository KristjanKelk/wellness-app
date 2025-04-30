<template>
  <div class="oauth-success">
    <div class="success-container">
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <p>Finalizing login... Please wait.</p>
      </div>
      <div v-else-if="error" class="error">
        <div class="error-icon">!</div>
        <h2>Authentication Error</h2>
        <p>{{ error }}</p>
        <router-link to="/login" class="btn btn-primary">Return to Login</router-link>
      </div>
      <div v-else class="success">
        <div class="success-icon">✓</div>
        <h2>Login Successful!</h2>
        <p>You have successfully logged in with your account.</p>
        <router-link to="/dashboard" class="btn btn-primary">Go to Dashboard</router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'OAuthSuccess',
  data() {
    return {
      loading: true,
      error: null
    };
  },
  created() {
    // Process the tokens from the URL
    this.processTokens();
  },
  methods: {
    processTokens() {
      try {
        const params = new URLSearchParams(window.location.search);
        const tokensParam = params.get('tokens');

        if (!tokensParam) {
          throw new Error('No authentication tokens provided');
        }

        // Parse the tokens
        const tokens = JSON.parse(decodeURIComponent(tokensParam));

        if (!tokens.access || !tokens.refresh) {
          throw new Error('Invalid authentication tokens');
        }

        // Store the tokens and log the user in
        const userData = {
          ...tokens,
          // Default values that will be updated when user profile is loaded
          username: 'User',
          email_verified: true
        };

        this.$store.commit('auth/loginSuccess', userData);

        // Successful login
        this.loading = false;

        // Automatically redirect to dashboard after a delay
        setTimeout(() => {
          this.$router.push('/dashboard');
        }, 1500);
      } catch (error) {
        console.error('Error processing OAuth tokens:', error);
        this.error = error.message || 'Failed to process authentication.';
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.oauth-success {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.success-container {
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