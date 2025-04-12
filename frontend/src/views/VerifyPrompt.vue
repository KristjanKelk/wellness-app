<template>
  <div class="verify-prompt-container">
    <div class="verify-card">
      <div class="icon">✉️</div>
      <h2>Verify Your Email</h2>
      <p>
        To access all features of the Wellness Platform, please verify your email address.
        We've sent a verification link to <strong>{{ userEmail }}</strong>.
      </p>

      <div class="instructions">
        <ol>
          <li>Check your email inbox (and spam folder)</li>
          <li>Click on the verification link in the email</li>
          <li>Return to this page after verification</li>
        </ol>
      </div>

      <div v-if="message" class="alert" :class="successful ? 'alert-success' : 'alert-danger'">
        {{ message }}
      </div>

      <div class="actions">
        <button @click="resendVerificationEmail" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Sending...' : 'Resend Verification Email' }}
        </button>
        <button @click="checkVerificationStatus" class="btn btn-secondary" :disabled="loading">
          I've Verified My Email
        </button>
      </div>

      <div class="help-text">
        <p>
          Having trouble? <a href="mailto:support@wellnessplatform.com">Contact Support</a>
        </p>
      </div>

      <div class="logout-link">
        <button @click="logout" class="btn-text">Sign Out</button>
      </div>
    </div>
  </div>
</template>

<script>
import UserService from '../services/user.service';

export default {
  name: 'VerifyPrompt',
  data() {
    return {
      loading: false,
      message: '',
      successful: false
    };
  },
  computed: {
    currentUser() {
      return this.$store.getters['auth/currentUser'];
    },
    //TODO isn in use yet
    isEmailVerified() {
      return this.$store.getters['auth/isEmailVerified'];
    },
    userEmail() {
      return this.currentUser?.email || 'your email address';
    }
  },
  created() {
    if (!this.currentUser) {
      this.$router.push('/login');
    }
  },
  methods: {
    async resendVerificationEmail() {
      this.loading = true;
      this.message = '';

      try {
        await UserService.resendVerificationEmail();
        this.successful = true;
        this.message = 'Verification email has been sent! Please check your inbox.';
      } catch (error) {
        console.error('Failed to resend verification email:', error);
        this.successful = false;

        if (error.response && error.response.data && error.response.data.detail) {
          this.message = error.response.data.detail;
        } else {
          this.message = 'Failed to send verification email. Please try again later.';
        }
      } finally {
        this.loading = false;
      }
    },

    async checkVerificationStatus() {
      this.loading = true;
      this.message = '';

      try {
        const response = await UserService.getCurrentUser();
        const user = response.data;

        if (user.email_verified) {
          this.$store.commit('auth/updateUser', { email_verified: true });

          this.successful = true;
          this.message = 'Email verified successfully! Redirecting...';

          setTimeout(() => {
            this.$router.push('/dashboard');
          }, 1500);

        } else {
          this.successful = false;
          this.message = 'Your email is not verified yet. Please check your inbox and click the verification link.';
        }
      } catch (error) {
        console.error('Failed to check verification status:', error);
        this.successful = false;
        this.message = 'Failed to check verification status. Please try again.';
      } finally {
        this.loading = false;
      }
    },

    logout() {
      this.$store.dispatch('auth/logout');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.verify-prompt-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.verify-card {
  width: 100%;
  max-width: 500px;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  text-align: center;
}

.icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

h2 {
  margin-bottom: 1rem;
  color: #333;
}

p {
  margin-bottom: 1.5rem;
  color: #666;
}

.instructions {
  text-align: left;
  margin: 1.5rem 0;
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 4px;
}

.instructions ol {
  margin: 0;
  padding-left: 1.5rem;
}

.instructions li {
  margin-bottom: 0.5rem;
}

.alert {
  padding: 0.75rem;
  margin-bottom: 1.5rem;
  border-radius: 4px;
  text-align: left;
}

.alert-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.alert-success {
  background-color: #d4edda;
  color: #155724;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
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

.btn-secondary {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.help-text {
  margin-top: 1.5rem;
  font-size: 0.9rem;
}

.help-text a {
  color: #4CAF50;
  text-decoration: none;
}

.logout-link {
  margin-top: 2rem;
}

.btn-text {
  background: none;
  border: none;
  color: #999;
  padding: 0;
  font: inherit;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.9rem;
}

@media (min-width: 640px) {
  .actions {
    flex-direction: row;
    justify-content: center;
  }
}
</style>