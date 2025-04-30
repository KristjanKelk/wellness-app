<template>
  <div class="login-container">
    <form @submit.prevent="handleLogin" class="login-form">
      <h2>Login</h2>

      <div v-if="!showTwoFactorForm">
        <div class="form-group">
          <label for="username">Username</label>
          <input
              type="text"
              id="username"
              v-model="username"
              required
              placeholder="Enter your username"
              :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
              type="password"
              id="password"
              v-model="password"
              required
              placeholder="Enter your password"
              :disabled="loading"
          />
        </div>

        <div class="form-group">
          <div class="remember-me">
            <input type="checkbox" id="remember" v-model="remember" />
            <label for="remember" class="checkbox-label">Remember me</label>
          </div>
        </div>
      </div>

      <div v-else class="two-factor-form">
        <p>Please enter the verification code from your authenticator app.</p>
        <div class="form-group">
          <label for="twoFactorCode">Verification Code</label>
          <input
              type="text"
              id="twoFactorCode"
              v-model="twoFactorCode"
              required
              placeholder="000000"
              maxlength="6"
              pattern="[0-9]*"
              inputmode="numeric"
              :disabled="loading"
              ref="twoFactorInput"
          />
        </div>
      </div>

      <div v-if="message" class="alert" :class="successful ? 'alert-success' : 'alert-danger'">
        {{ message }}
      </div>

      <div class="form-group">
        <button class="btn btn-primary btn-block" :disabled="loading">
          <span v-if="loading">
            <span class="loading-spinner-sm"></span>
            {{ showTwoFactorForm ? 'Verifying...' : 'Signing in...' }}
          </span>
          <span v-else>{{ showTwoFactorForm ? 'Verify' : 'Sign In' }}</span>
        </button>
      </div>

      <div v-if="showTwoFactorForm" class="form-group text-center">
        <button type="button" class="btn-text" @click="cancelTwoFactor">
          Cancel
        </button>
      </div>

      <div class="form-group text-center">
        <p>
          <router-link to="/reset-password">Forgot Password?</router-link>
        </p>
        <p>
          Don't have an account?
          <router-link to="/register">Register here</router-link>
        </p>
      </div>
    </form>

    <!-- Add Google login section here -->
    <div class="social-login">
      <div class="divider">
        <span>OR</span>
      </div>

      <button
        type="button"
        class="btn btn-google"
        @click="loginWithGoogle"
        :disabled="loading"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 48 48">
          <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"></path>
          <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"></path>
          <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"></path>
          <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"></path>
        </svg>
        <span>Continue with Google</span>
      </button>
    </div>
  </div>
</template>

<script>
import OAuthService from '../services/oauth.service';

export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      twoFactorCode: '',
      showTwoFactorForm: false,
      remember: false,
      loading: false,
      message: '',
      successful: false,
      tempAuthData: null
    };
  },
  computed: {
    loggedIn() {
      return this.$store.getters['auth/isLoggedIn'];
    }
  },
  created() {
    console.log('Login component created, checking logged in status');
    if (this.loggedIn) {
      console.log('Already logged in, redirecting to dashboard');
      this.$router.push('/dashboard');
    }
  },
  watch: {
    showTwoFactorForm(newVal) {
      if (newVal) {
        // Focus on the 2FA input when the form appears
        this.$nextTick(() => {
          if (this.$refs.twoFactorInput) {
            this.$refs.twoFactorInput.focus();
          }
        });
      }
    }
  },
  methods: {
    handleLogin() {
      if (this.showTwoFactorForm) {
        this.verifyTwoFactor();
        return;
      }

      if (!this.username || !this.password) {
        this.message = 'Please enter both username and password';
        this.successful = false;
        return;
      }

      this.loading = true;
      this.message = '';

      console.log(`Attempting to login with username: ${this.username}`);

      this.$store.dispatch('auth/login', {
        username: this.username,
        password: this.password,
        remember: this.remember
      }).then(
          (userData) => {
            // Check if 2FA is required
            if (userData.two_factor_enabled) {
              this.showTwoFactorForm = true;
              this.tempAuthData = userData;
              this.loading = false;
            } else {
              // No 2FA, proceed with login
              this.loginSuccess(userData);
            }
          },
          error => {
            this.handleLoginError(error);
          }
      );
    },

    verifyTwoFactor() {
      if (!this.twoFactorCode || this.twoFactorCode.length !== 6 || !/^\d+$/.test(this.twoFactorCode)) {
        this.message = 'Please enter a valid 6-digit verification code';
        this.successful = false;
        return;
      }

      this.loading = true;
      this.message = '';

      this.$store.dispatch('auth/verifyTwoFactor', {
        code: this.twoFactorCode,
        tempAuthData: this.tempAuthData
      }).then(
          (userData) => {
            this.loginSuccess(userData);
          },
          error => {
            this.loading = false;
            this.successful = false;
            console.error('Login error:', error);

            if (error.response && error.response.data) {
              if (error.response.data.detail) {
                this.message = error.response.data.detail;
              } else {
                this.message = 'Invalid verification code. Please try again.';
              }
            } else {
              this.message = 'Failed to verify code. Please try again.';
            }
          }
      );
    },

    // In Login.vue, update the loginSuccess method:
    loginSuccess(userData) {
      console.log('Login successful in component, user data:', userData);

      // Make sure we commit the login success if it hasn't been done yet
      if (!this.$store.getters['auth/isLoggedIn']) {
        this.$store.commit('auth/loginSuccess', userData);
      }

      this.successful = true;
      this.message = 'Login successful! Redirecting...';

      // Short delay before redirect for better UX
      setTimeout(() => {
        this.$router.push('/dashboard');
      }, 500);
    },

    handleLoginError(error) {
      this.loading = false;
      this.successful = false;
      console.error('Login error:', error);

      if (error.response && error.response.data) {
        if (error.response.data.detail) {
          this.message = error.response.data.detail;
        } else if (error.response.data.non_field_errors) {
          this.message = error.response.data.non_field_errors.join(' ');
        } else {
          // Try to extract first error message
          const firstError = Object.values(error.response.data)[0];
          if (Array.isArray(firstError)) {
            this.message = firstError[0];
          } else {
            this.message = 'Failed to login. Please check your credentials.';
          }
        }
      } else {
        this.message = 'Failed to login. Please check your credentials.';
      }
    },

    cancelTwoFactor() {
      this.showTwoFactorForm = false;
      this.twoFactorCode = '';
      this.tempAuthData = null;
    },

    // OAuth login methods
    async loginWithGoogle() {
      try {
        this.message = '';
        this.loading = true;

        localStorage.removeItem('oauth_error');

        console.log('Starting Google authentication flow');
        await OAuthService.loginWithGoogle();
        this.loading = false;
      } catch (error) {
        console.error('Google login initialization error:', error);
        this.loading = false;
        this.successful = false;
        this.message = error.message || 'Failed to start Google authentication. Please try again.';
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.login-form {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #333;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.checkbox-label {
  display: inline;
  margin-left: 0.5rem;
  font-weight: normal;
}

.remember-me {
  display: flex;
  align-items: center;
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

input[type="checkbox"] {
  margin: 0;
}

.btn {
  cursor: pointer;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

.btn-text {
  background: none;
  border: none;
  color: #4CAF50;
  padding: 0;
  font: inherit;
  cursor: pointer;
  text-decoration: underline;
}

.btn-block {
  width: 100%;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.alert {
  padding: 0.75rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

.alert-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.alert-success {
  background-color: #d4edda;
  color: #155724;
}

.text-center {
  text-align: center;
}

.two-factor-form p {
  text-align: center;
  margin-bottom: 1.5rem;
  color: #555;
}

input[id="twoFactorCode"] {
  text-align: center;
  letter-spacing: 0.5rem;
  font-size: 1.5rem;
  padding: 0.75rem 0.5rem;
}

.loading-spinner-sm {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
  margin-right: 0.5rem;
  vertical-align: middle;
}

/* Social login styles */
.social-login {
  margin-top: 2rem;
  width: 100%;
  max-width: 400px;
}

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin: 1.5rem 0;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #ddd;
}

.divider span {
  padding: 0 1rem;
  color: #999;
  font-size: 0.9rem;
}

.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  background-color: white;
  color: #333;
  border: 1px solid #ddd;
  transition: background-color 0.2s, box-shadow 0.2s;
}

.btn-google:hover {
  background-color: #f9f9f9;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn-google:active {
  background-color: #f0f0f0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>