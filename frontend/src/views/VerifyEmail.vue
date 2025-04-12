<template>
  <div class="verify-email-container">
    <div class="verify-card">
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <p>Verifying your email...</p>
      </div>

      <div v-else-if="verified" class="success">
        <div class="icon">✓</div>
        <h2>Email Verified Successfully!</h2>
        <p>Your email has been verified. You can now access all features of the Wellness Platform.</p>
        <router-link to="/login" class="btn btn-primary">Login</router-link>
      </div>

      <div v-else-if="error" class="error">
        <div class="icon">!</div>
        <h2>Verification Failed</h2>
        <p>{{ error }}</p>
        <div class="actions">
          <router-link to="/login" class="btn btn-secondary">Back to Login</router-link>
          <button @click="resendVerification" class="btn btn-primary" :disabled="resending">
            {{ resending ? 'Sending...' : 'Resend Verification Email' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import UserService from '../services/user.service';

export default {
  name: 'VerifyEmail',
  data() {
    return {
      loading: true,
      verified: false,
      error: null,
      token: null,
      resending: false
    };
  },
  mounted() {
    this.token = this.$route.params.token;
    if (!this.token) {
      this.loading = false;
      this.error = 'Invalid verification link. Please check your email and try again.';
      return;
    }

    this.verifyEmail();
  },
  methods: {
    async verifyEmail() {
      try {
        await UserService.verifyEmail(this.token);
        this.verified = true;
      } catch (error) {
        console.error('Email verification failed:', error);
        if (error.response && error.response.data && error.response.data.detail) {
          this.error = error.response.data.detail;
        } else {
          this.error = 'Failed to verify your email. The link may have expired or is invalid.';
        }
      } finally {
        this.loading = false;
      }
    },
    async resendVerification() {
      this.resending = true;
      try {
        await UserService.resendVerificationEmail(this.$route.query.email);
        this.$toast.success('Verification email sent. Please check your inbox.', {
          position: 'top-right',
          duration: 5000
        });
      } catch (error) {
        console.error('Failed to resend verification email:', error);
        this.$toast.error('Failed to send verification email. Please try again later.', {
          position: 'top-right',
          duration: 5000
        });
      } finally {
        this.resending = false;
      }
    }
  }
};
</script>

<style scoped>
.verify-email-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.verify-card {
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

.icon {
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

.success .icon {
  background-color: #d4edda;
  color: #155724;
}

.error .icon {
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

.actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
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