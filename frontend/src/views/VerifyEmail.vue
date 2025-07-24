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
        <p>Welcome to Wellness Platform! Your email has been verified and your account is now active.</p>
        <div class="features-preview">
          <h3>You now have access to:</h3>
          <ul>
            <li>🏋️‍♀️ Personalized fitness tracking</li>
            <li>🥗 Smart meal planning</li>
            <li>🤖 AI-powered health insights</li>
            <li>📊 Comprehensive analytics</li>
          </ul>
        </div>
        <div class="actions">
          <router-link to="/login" class="btn btn-primary">Get Started - Login</router-link>
          <router-link to="/register" class="btn btn-secondary">Create Another Account</router-link>
        </div>
      </div>

      <div v-else-if="error" class="error">
        <div class="icon">!</div>
        <h2>Verification Failed</h2>
        <p>{{ error }}</p>
        
        <div v-if="showResendOption" class="resend-section">
          <h3>Need a new verification link?</h3>
          <p>Enter your email address to receive a new verification email:</p>
          <div class="email-input-group">
            <input
              v-model="resendEmail"
              type="email"
              placeholder="Enter your email address"
              class="email-input"
              :disabled="resending"
            />
            <button
              @click="resendVerification"
              class="btn btn-primary"
              :disabled="resending || !resendEmail"
            >
              {{ resending ? 'Sending...' : 'Send New Link' }}
            </button>
          </div>
        </div>
        
        <div class="actions">
          <router-link to="/login" class="btn btn-secondary">Back to Login</router-link>
          <router-link to="/register" class="btn btn-outline">Register New Account</router-link>
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
      resending: false,
      resendEmail: '',
      showResendOption: false
    };
  },
  mounted() {
    this.token = this.$route.params.token;
    if (!this.token) {
      this.loading = false;
      this.error = 'Invalid verification link. Please check your email and try again.';
      this.showResendOption = true;
      return;
    }

    this.verifyEmail();
  },
  methods: {
    async verifyEmail() {
      try {
        const response = await UserService.verifyEmail(this.token);
        this.verified = true;
        
        // Show success message with user info if available
        if (response.data.user) {
          this.$toast.success(
            `Welcome ${response.data.user.username}! Your email has been verified.`,
            {
              position: 'top-right',
              duration: 5000
            }
          );
        }
      } catch (error) {
        console.error('Email verification failed:', error);
        
        if (error.response && error.response.data && error.response.data.detail) {
          this.error = error.response.data.detail;
          
          // Show resend option for certain error types
          if (this.error.includes('expired') || this.error.includes('invalid')) {
            this.showResendOption = true;
          }
        } else {
          this.error = 'Failed to verify your email. The link may have expired or is invalid.';
          this.showResendOption = true;
        }
      } finally {
        this.loading = false;
      }
    },
    
    async resendVerification() {
      if (!this.resendEmail) {
        this.$toast.error('Please enter your email address.', {
          position: 'top-right',
          duration: 3000
        });
        return;
      }

      this.resending = true;
      try {
        await UserService.resendVerificationEmail(this.resendEmail);
        this.$toast.success(
          'Verification email sent! Please check your inbox and spam folder.',
          {
            position: 'top-right',
            duration: 8000
          }
        );
        this.resendEmail = '';
      } catch (error) {
        console.error('Failed to resend verification email:', error);
        
        if (error.response && error.response.data && error.response.data.detail) {
          this.$toast.error(error.response.data.detail, {
            position: 'top-right',
            duration: 5000
          });
        } else {
          this.$toast.error(
            'Failed to send verification email. Please try again later.',
            {
              position: 'top-right',
              duration: 5000
            }
          );
        }
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
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.verify-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  padding: 3rem;
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.loading, .success, .error {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-spinner {
  border: 4px solid rgba(76, 175, 80, 0.1);
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.icon {
  font-size: 64px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  font-weight: bold;
}

.success .icon {
  background: linear-gradient(135deg, #d4edda, #c3e6cb);
  color: #155724;
  box-shadow: 0 4px 15px rgba(21, 87, 36, 0.2);
}

.error .icon {
  background: linear-gradient(135deg, #f8d7da, #f1b0b7);
  color: #721c24;
  box-shadow: 0 4px 15px rgba(114, 28, 36, 0.2);
}

h2 {
  margin-bottom: 1rem;
  color: #333;
  font-size: 2rem;
  font-weight: 600;
}

p {
  margin-bottom: 1.5rem;
  color: #666;
  line-height: 1.6;
  font-size: 1.1rem;
}

.features-preview {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  margin: 2rem 0;
  text-align: left;
}

.features-preview h3 {
  color: #4CAF50;
  margin-bottom: 1rem;
  text-align: center;
}

.features-preview ul {
  list-style: none;
  padding: 0;
}

.features-preview li {
  padding: 0.5rem 0;
  font-size: 1rem;
  color: #555;
}

.resend-section {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem 0;
}

.resend-section h3 {
  color: #856404;
  margin-bottom: 0.5rem;
}

.email-input-group {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.email-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  min-width: 200px;
}

.email-input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 2rem;
}

.btn {
  cursor: pointer;
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  display: inline-block;
  transition: all 0.3s ease;
  min-width: 140px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

.btn-outline {
  background: transparent;
  color: #4CAF50;
  border: 2px solid #4CAF50;
}

.btn-outline:hover {
  background: #4CAF50;
  color: white;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 600px) {
  .verify-card {
    padding: 2rem;
    margin: 1rem;
  }
  
  .email-input-group {
    flex-direction: column;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>