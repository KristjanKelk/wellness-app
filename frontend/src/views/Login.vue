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
  </div>
</template>

<script>
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
            this.handleLoginError(error);
            // Don't reset the form on 2FA failure to allow retries
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
    }
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>