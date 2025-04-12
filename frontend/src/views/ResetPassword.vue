<template>
  <div class="reset-password-container">
    <div v-if="!token" class="reset-card">
      <h2>Reset Password</h2>
      <p>Enter your email address and we'll send you a link to reset your password.</p>

      <form @submit.prevent="requestReset">
        <div class="form-group">
          <label for="email">Email Address</label>
          <input
              type="email"
              id="email"
              v-model="email"
              required
              placeholder="Enter your email"
          />
        </div>

        <div v-if="requestMessage" class="alert" :class="requestSuccess ? 'alert-success' : 'alert-danger'">
          {{ requestMessage }}
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
          {{ loading ? 'Sending...' : 'Send Reset Link' }}
        </button>

        <div class="form-footer">
          <router-link to="/login">Back to Login</router-link>
        </div>
      </form>
    </div>

    <div v-else class="reset-card">
      <h2>Create New Password</h2>
      <p>Please enter your new password below.</p>

      <form @submit.prevent="resetPassword">
        <div class="form-group">
          <label for="newPassword">New Password</label>
          <input
              type="password"
              id="newPassword"
              v-model="newPassword"
              required
              minlength="8"
              placeholder="Enter new password"
          />
          <small>Password must be at least 8 characters long</small>
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
              type="password"
              id="confirmPassword"
              v-model="confirmPassword"
              required
              placeholder="Confirm new password"
          />
        </div>

        <div v-if="resetMessage" class="alert" :class="resetSuccess ? 'alert-success' : 'alert-danger'">
          {{ resetMessage }}
        </div>

        <button type="submit" class="btn btn-primary btn-block" :disabled="loading || resetSuccess">
          {{ loading ? 'Updating...' : 'Reset Password' }}
        </button>

        <div v-if="resetSuccess" class="form-footer">
          <router-link to="/login" class="btn btn-secondary">Go to Login</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import UserService from '../services/user.service';

export default {
  name: 'ResetPassword',
  data() {
    return {
      token: '',
      email: '',
      newPassword: '',
      confirmPassword: '',
      loading: false,
      requestMessage: '',
      requestSuccess: false,
      resetMessage: '',
      resetSuccess: false
    };
  },
  created() {
    // Check if we have a token in the URL
    this.token = this.$route.params.token || '';
  },
  methods: {
    async requestReset() {
      if (!this.email) {
        this.requestMessage = 'Please enter your email address';
        this.requestSuccess = false;
        return;
      }

      this.loading = true;
      this.requestMessage = '';

      try {
        await UserService.resetPassword(this.email);
        this.requestSuccess = true;
        this.requestMessage = 'If your email is registered, you will receive a password reset link shortly.';
        this.email = ''; // Clear email field
      } catch (error) {
        console.error('Failed to request password reset:', error);
        // Show same message for security (prevents email enumeration)
        this.requestSuccess = true;
        this.requestMessage = 'If your email is registered, you will receive a password reset link shortly.';
      } finally {
        this.loading = false;
      }
    },
    async resetPassword() {
      if (this.newPassword !== this.confirmPassword) {
        this.resetMessage = 'Passwords do not match';
        this.resetSuccess = false;
        return;
      }

      if (this.newPassword.length < 8) {
        this.resetMessage = 'Password must be at least 8 characters long';
        this.resetSuccess = false;
        return;
      }

      this.loading = true;
      this.resetMessage = '';

      try {
        await UserService.confirmResetPassword(this.token, this.newPassword);
        this.resetSuccess = true;
        this.resetMessage = 'Your password has been reset successfully!';

        // Clear form
        this.newPassword = '';
        this.confirmPassword = '';
      } catch (error) {
        console.error('Failed to reset password:', error);
        this.resetSuccess = false;

        if (error.response && error.response.data && error.response.data.detail) {
          this.resetMessage = error.response.data.detail;
        } else {
          this.resetMessage = 'Failed to reset your password. The link may have expired or is invalid.';
        }
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.reset-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.reset-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  padding: 2rem;
  max-width: 500px;
  width: 100%;
}

h2 {
  margin-bottom: 1rem;
  text-align: center;
}

p {
  margin-bottom: 1.5rem;
  color: #666;
  text-align: center;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

small {
  display: block;
  color: #666;
  margin-top: 0.25rem;
  font-size: 0.8rem;
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

.btn {
  cursor: pointer;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
}

.btn-block {
  width: 100%;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

.btn-secondary {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.form-footer {
  margin-top: 1.5rem;
  text-align: center;
}

.form-footer a {
  color: #4CAF50;
  text-decoration: none;
}
</style>