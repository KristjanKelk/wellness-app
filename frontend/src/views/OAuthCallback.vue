<!-- src/views/OAuthCallback.vue -->
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
        <div v-if="debugInfo" class="debug-info">
          <details>
            <summary>Technical Details (For Developers)</summary>
            <pre>{{ debugInfo }}</pre>
          </details>
        </div>
        <div class="action-buttons">
          <button @click="retryAuthentication" class="btn btn-primary">
            Try Again
          </button>
          <router-link to="/login" class="btn btn-secondary">
            Return to Login
          </router-link>
        </div>
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
import OAuthDebug from '../utils/oauth-debug';

export default {
  name: 'OAuthCallback',
  props: {
    provider: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      loading: true,
      error: null,
      debugInfo: null
    };
  },
  mounted() {
    OAuthDebug.checkStorage();
    this.processCallback();
  },
  methods: {
    processCallback() {
      try {
        // Extract query parameters
        const queryParams = new URLSearchParams(window.location.search);

        // Debug OAuth response
        const debugData = OAuthDebug.logAuthResponse(queryParams);

        // Determine provider from route, URL path, or default
        let provider = this.provider || this.$route.params.provider;

        // Extract provider from URL path if not in params
        if (!provider) {
          const pathParts = window.location.pathname.split('/');
          if (pathParts.includes('callback')) {
            const providerIndex = pathParts.indexOf('callback') - 1;
            if (providerIndex >= 0 && pathParts[providerIndex]) {
              provider = pathParts[providerIndex];
            }
          }
        }

        // Default to google if still not found
        provider = provider || 'google';

        // Create debug info
        this.debugInfo = JSON.stringify({
          url: window.location.href,
          search: window.location.search,
          pathname: window.location.pathname,
          debugData,
          provider: provider,
          routeParams: this.$route.params,
          timestamp: new Date().toISOString()
        }, null, 2);

        if (queryParams.get('error')) {
          const errorMsg = queryParams.get('error_description') || queryParams.get('error');
          this.error = `Authentication error: ${errorMsg}`;
          this.loading = false;
          return;
        }

        if (!queryParams.get('code')) {
          this.error = 'No authorization code received. Please try again.';
          this.loading = false;
          return;
        }

        OAuthService.processCallback(queryParams, provider)
          .then(userData => {

            this.$store.commit('auth/loginSuccess', userData);

            this.loading = false;

            setTimeout(() => {
              this.$router.push('/dashboard');
            }, 1000);
          })
          .catch(error => {
            console.error('OAuth callback error:', error);
            this.error = error.message || 'Failed to complete authentication. Please try again.';
            this.loading = false;
          });
      } catch (err) {
        console.error('Error in processCallback:', err);
        this.error = `Authentication processing error: ${err.message}`;
        this.loading = false;
      }
    },

    retryAuthentication() {
      // Clear any error state
      localStorage.removeItem('oauth_error');
      sessionStorage.removeItem('auth_in_progress');

      const pathParts = window.location.pathname.split('/');
      let provider = 'google'; // Default

      if (pathParts.includes('callback')) {
        const providerIndex = pathParts.indexOf('callback') - 1;
        if (providerIndex >= 0 && pathParts[providerIndex]) {
          provider = pathParts[providerIndex];
        }
      }


      if (provider === 'github') {
        OAuthService.loginWithGitHub()
          .catch(error => {
            console.error('Failed to restart GitHub authentication:', error);
            this.error = `Failed to restart authentication: ${error.message}`;
          });
      } else {
        OAuthService.loginWithGoogle()
          .catch(error => {
            console.error('Failed to restart Google authentication:', error);
            this.error = `Failed to restart authentication: ${error.message}`;
          });
      }
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

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.debug-info {
  margin: 1rem 0;
  width: 100%;
  text-align: left;
}

.debug-info details {
  margin-bottom: 1rem;
}

.debug-info summary {
  cursor: pointer;
  color: #007bff;
  font-size: 0.9rem;
}

.debug-info pre {
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
  overflow-x: auto;
  text-align: left;
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

.btn-secondary {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>