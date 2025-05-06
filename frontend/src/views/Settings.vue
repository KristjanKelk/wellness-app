<template>
  <div class="settings-container">
    <h1>Account Settings</h1>

    <div class="settings-card">
      <h2>Security Settings</h2>

      <!-- Email Verification Status -->
      <div class="setting-item">
        <div class="setting-info">
          <h3>Email Verification</h3>
          <p>Verify your email address to access all platform features</p>
        </div>
        <div class="setting-status">
          <span :class="{'status-verified': user.email_verified, 'status-unverified': !user.email_verified}">
            {{ user.email_verified ? 'Verified' : 'Unverified' }}
          </span>
          <button v-if="!user.email_verified" @click="resendVerificationEmail" class="btn btn-secondary" :disabled="loading.verification">
            {{ loading.verification ? 'Sending...' : 'Resend Email' }}
          </button>
        </div>
      </div>

      <!-- Two-Factor Authentication -->
      <div class="setting-item">
        <div class="setting-info">
          <h3>Two-Factor Authentication</h3>
          <p>Add an extra layer of security to your account</p>
        </div>
        <div class="setting-status">
          <span :class="{'status-enabled': user.two_factor_enabled, 'status-disabled': !user.two_factor_enabled}">
            {{ user.two_factor_enabled ? 'Enabled' : 'Disabled' }}
          </span>
          <button v-if="!user.two_factor_enabled" @click="setupTwoFactor" class="btn btn-primary" :disabled="loading.twoFactor">
            {{ loading.twoFactor ? 'Setting up...' : 'Enable' }}
          </button>
          <button v-else @click="disableTwoFactor" class="btn btn-danger" :disabled="loading.twoFactor">
            {{ loading.twoFactor ? 'Disabling...' : 'Disable' }}
          </button>
        </div>
      </div>

      <!-- Two-Factor Authentication Setup Modal -->
      <div v-if="showTwoFactorModal" class="modal">
        <div class="modal-content">
          <span class="close-button" @click="showTwoFactorModal = false">&times;</span>
          <h2>Set Up Two-Factor Authentication</h2>

          <div v-if="setupStep === 1" class="setup-qr">
            <p>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
            <div class="qr-container">
              <img :src="qrCodeUrl" alt="QR Code for 2FA setup" v-if="qrCodeUrl" />
              <div v-else class="loading-spinner"></div>
            </div>
            <p class="manual-key" v-if="secretKey">
              Or enter this key manually: <strong>{{ secretKey }}</strong>
            </p>
            <button @click="setupStep = 2" class="btn btn-primary" :disabled="!qrCodeUrl">
              Next
            </button>
          </div>

          <div v-if="setupStep === 2" class="verify-code">
            <p>Enter the 6-digit code from your authenticator app to verify setup</p>
            <div class="code-input">
              <input
                  type="text"
                  v-model="verificationCode"
                  placeholder="000000"
                  maxlength="6"
                  pattern="[0-9]*"
                  inputmode="numeric"
              />
            </div>
            <div v-if="twoFactorError" class="error-message">
              {{ twoFactorError }}
            </div>
            <div class="form-actions">
              <button @click="setupStep = 1" class="btn btn-secondary">
                Back
              </button>
              <button @click="verifyTwoFactor" class="btn btn-primary" :disabled="verificationCode.length !== 6 || loading.verification">
                {{ loading.verification ? 'Verifying...' : 'Verify & Enable' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Change Password -->
      <div class="setting-item">
        <div class="setting-info">
          <h3>Password</h3>
          <p>Update your password regularly to keep your account secure</p>
        </div>
        <div class="setting-status">
          <button @click="showPasswordModal = true" class="btn btn-secondary">
            Change Password
          </button>
        </div>
      </div>

      <!-- Change Password Modal -->
      <div v-if="showPasswordModal" class="modal">
        <div class="modal-content">
          <span class="close-button" @click="showPasswordModal = false">&times;</span>
          <h2>Change Password</h2>
          <form @submit.prevent="changePassword">
            <div class="form-group">
              <label for="currentPassword">Current Password</label>
              <input
                  type="password"
                  id="currentPassword"
                  v-model="passwordForm.currentPassword"
                  required
              />
            </div>

            <div class="form-group">
              <label for="newPassword">New Password</label>
              <input
                  type="password"
                  id="newPassword"
                  v-model="passwordForm.newPassword"
                  required
                  minlength="8"
              />
              <small>Password must be at least 8 characters long</small>
            </div>

            <div class="form-group">
              <label for="confirmPassword">Confirm New Password</label>
              <input
                  type="password"
                  id="confirmPassword"
                  v-model="passwordForm.confirmPassword"
                  required
              />
            </div>

            <div v-if="passwordError" class="error-message">
              {{ passwordError }}
            </div>

            <div v-if="passwordSuccess" class="success-message">
              {{ passwordSuccess }}
            </div>

            <div class="form-actions">
              <button type="button" class="btn btn-secondary" @click="showPasswordModal = false">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="loading.password">
                {{ loading.password ? 'Updating...' : 'Update Password' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Data Privacy Settings -->
    <div class="settings-card">
      <h2>Data Privacy</h2>

      <div class="setting-item">
        <div class="setting-info">
          <h3>Data Sharing Consent</h3>
          <p>Control how your health data is used for personalized recommendations</p>
        </div>
        <div class="setting-status">
          <label class="toggle-switch">
            <input type="checkbox" v-model="privacySettings.dataSharingConsent" @change="updatePrivacySettings">
            <span class="slider"></span>
          </label>
          <span class="toggle-label">{{ privacySettings.dataSharingConsent ? 'Enabled' : 'Disabled' }}</span>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-info">
          <h3>Export Your Data</h3>
          <p>Download all your health data in a portable format</p>
        </div>
        <div class="setting-status">
          <button @click="exportData" class="btn btn-secondary" :disabled="loading.export">
            {{ loading.export ? 'Preparing...' : 'Export Data' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Notification Settings -->
    <div class="settings-card">
      <h2>Notifications</h2>

      <div class="setting-item">
        <div class="setting-info">
          <h3>Email Notifications</h3>
          <p>Receive updates, insights, and recommendations via email</p>
        </div>
        <div class="setting-status">
          <label class="toggle-switch">
            <input type="checkbox" v-model="notificationSettings.emailEnabled" @change="updateNotificationSettings">
            <span class="slider"></span>
          </label>
          <span class="toggle-label">{{ notificationSettings.emailEnabled ? 'Enabled' : 'Disabled' }}</span>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-info">
          <h3>Weekly Summary</h3>
          <p>Receive a weekly summary of your health metrics and progress</p>
        </div>
        <div class="setting-status">
          <label class="toggle-switch">
            <input type="checkbox" v-model="notificationSettings.weeklySummary" @change="updateNotificationSettings" :disabled="!notificationSettings.emailEnabled">
            <span class="slider"></span>
          </label>
          <span class="toggle-label">{{ notificationSettings.weeklySummary ? 'Enabled' : 'Disabled' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import UserService from '../services/user.service';
import HealthProfileService from '../services/health-profile_service';

export default {
  name: 'Settings',
  data() {
    return {
      user: {
        email_verified: false,
        two_factor_enabled: false
      },
      privacySettings: {
        dataSharingConsent: false
      },
      notificationSettings: {
        emailEnabled: true,
        weeklySummary: true
      },
      loading: {
        verification: false,
        twoFactor: false,
        password: false,
        export: false
      },
      showTwoFactorModal: false,
      showPasswordModal: false,
      setupStep: 1,
      qrCodeUrl: '',
      secretKey: '',
      verificationCode: '',
      twoFactorError: '',
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      passwordError: '',
      passwordSuccess: ''
    };
  },
  computed: {
    //TODO isnt in use yet
    currentUser() {
      return this.$store.getters['auth/currentUser'];
    },
    hasTwoFactorEnabled() {
      return this.$store.getters['auth/hasTwoFactorEnabled'];
    }
  },
  mounted() {
    this.loadUserData();
    this.loadPrivacySettings();
    this.loadNotificationSettings();
  },
  methods: {
    async loadUserData() {
      try {
        const response = await UserService.getCurrentUser();
        this.user = response.data;
      } catch (error) {
        console.error('Error loading user data:', error);
      }
    },
    async loadPrivacySettings() {
      try {
        const response = await HealthProfileService.getHealthProfile();
        if (response.data) {
          this.privacySettings.dataSharingConsent = response.data.data_sharing_consent || false;
        }
      } catch (error) {
        console.error('Error loading privacy settings:', error);
      }
    },
    async loadNotificationSettings() {
      try {
        const response = await UserService.getNotificationSettings();
        this.notificationSettings = response.data;
      } catch (error) {
        console.error('Error loading notification settings:', error);
        // Default settings if API fails
        this.notificationSettings = {
          emailEnabled: true,
          weeklySummary: true
        };
      }
    },
    async resendVerificationEmail() {
      this.loading.verification = true;
      try {
        await UserService.resendVerificationEmail();
        this.$toast.success('Verification email sent successfully. Please check your inbox.', {
          position: 'top-right',
          duration: 5000
        });
      } catch (error) {
        console.error('Error sending verification email:', error);
        this.$toast.error('Failed to send verification email. Please try again later.', {
          position: 'top-right',
          duration: 5000
        });
      } finally {
        this.loading.verification = false;
      }
    },
    async setupTwoFactor() {
      this.loading.twoFactor = true;
      try {
        const response = await UserService.generateTwoFactorSecret();
        this.qrCodeUrl = response.data.qr_code;
        this.secretKey = response.data.secret_key;
        this.showTwoFactorModal = true;
        this.setupStep = 1;
        this.twoFactorError = '';
        this.verificationCode = '';
      } catch (error) {
        console.error('Error setting up 2FA:', error);
        this.$toast.error('Failed to set up two-factor authentication. Please try again later.', {
          position: 'top-right',
          duration: 5000
        });
      } finally {
        this.loading.twoFactor = false;
      }
    },
    async verifyTwoFactor() {
      if (this.verificationCode.length !== 6) {
        this.twoFactorError = 'Please enter a valid 6-digit code';
        return;
      }

      this.loading.verification = true;
      try {
        await UserService.verifyTwoFactor(this.verificationCode);
        this.user.two_factor_enabled = true;
        this.showTwoFactorModal = false;
        this.$toast.success('Two-factor authentication enabled successfully.', {
          position: 'top-right',
          duration: 5000
        });
      } catch (error) {
        console.error('Error verifying 2FA code:', error);
        this.twoFactorError = 'Invalid verification code. Please try again.';
      } finally {
        this.loading.verification = false;
      }
    },
     async disableTwoFactor() {
      if (!confirm('Are you sure you want to disable two-factor authentication? This will make your account less secure.')) {
        return;
      }

      this.loading.twoFactor = true;

      try {
        await UserService.disableTwoFactor();
        this.user.two_factor_enabled = false;

        if (this.$toast) {
          this.$toast.success('Two-factor authentication disabled.', {
            position: 'top-right',
            duration: 5000
          });
        }
      } catch (err) {
        if (this.$toast) {
          this.$toast.error('Failed to disable two-factor authentication. Please try again later.', {
            position: 'top-right',
            duration: 5000
          });
        }
      } finally {
        this.loading.twoFactor = false;
      }
    },
    async changePassword() {
      this.passwordError = '';
      this.passwordSuccess = '';

      if (this.passwordForm.newPassword !== this.passwordForm.confirmPassword) {
        this.passwordError = 'New passwords do not match';
        return;
      }

      if (this.passwordForm.newPassword.length < 8) {
        this.passwordError = 'Password must be at least 8 characters long';
        return;
      }

      this.loading.password = true;
      try {
        await UserService.changePassword(
            this.passwordForm.currentPassword,
            this.passwordForm.newPassword
        );
        this.passwordSuccess = 'Password updated successfully';

        // Clear form
        this.passwordForm = {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        };

        // Close modal after a delay
        setTimeout(() => {
          this.showPasswordModal = false;
          this.passwordSuccess = '';
        }, 2000);
      } catch (error) {
        console.error('Error changing password:', error);
        if (error.response && error.response.data && error.response.data.detail) {
          this.passwordError = error.response.data.detail;
        } else {
          this.passwordError = 'Failed to update password. Please try again.';
        }
      } finally {
        this.loading.password = false;
      }
    },
    async updatePrivacySettings() {
      try {
        const profile = await HealthProfileService.getHealthProfile();
        const updatedProfile = {
          ...profile.data,
          data_sharing_consent: this.privacySettings.dataSharingConsent
        };

        await HealthProfileService.updateHealthProfile(updatedProfile);
        this.$toast.success('Privacy settings updated successfully.', {
          position: 'top-right',
          duration: 3000
        });
      } catch (error) {
        console.error('Error updating privacy settings:', error);
        this.$toast.error('Failed to update privacy settings.', {
          position: 'top-right',
          duration: 3000
        });
        // Revert the toggle if update fails
        this.loadPrivacySettings();
      }
    },
    async updateNotificationSettings() {
      try {
        await UserService.updateNotificationSettings(this.notificationSettings);
        this.$toast.success('Notification settings updated successfully.', {
          position: 'top-right',
          duration: 3000
        });
      } catch (error) {
        console.error('Error updating notification settings:', error);
        this.$toast.error('Failed to update notification settings.', {
          position: 'top-right',
          duration: 3000
        });
        // Revert toggles if update fails
        this.loadNotificationSettings();
      }
    },
    async exportData() {
      this.loading.export = true;
      try {
        const response = await UserService.exportUserData();

        // Create a download link
        const url = window.URL.createObjectURL(new Blob([JSON.stringify(response.data, null, 2)]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'my_wellness_data.json');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.$toast.success('Data exported successfully.', {
          position: 'top-right',
          duration: 3000
        });
      } catch (error) {
        console.error('Error exporting data:', error);
        this.$toast.error('Failed to export data. Please try again later.', {
          position: 'top-right',
          duration: 3000
        });
      } finally {
        this.loading.export = false;
      }
    }
  }
};
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
}

.settings-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.settings-card h2 {
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #eee;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid #f5f5f5;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex: 1;
}

.setting-info h3 {
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.setting-info p {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.setting-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-verified, .status-enabled {
  color: #4CAF50;
  font-weight: bold;
}

.status-unverified, .status-disabled {
  color: #F44336;
  font-weight: bold;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #4CAF50;
}

input:disabled + .slider {
  opacity: 0.5;
  cursor: not-allowed;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.toggle-label {
  font-size: 0.9rem;
  min-width: 70px;
}

/* Modal Styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  position: relative;
}

.close-button {
  position: absolute;
  top: 1rem;
  right: 1rem;
  font-size: 1.5rem;
  cursor: pointer;
}

/* Form Styles */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group small {
  display: block;
  color: #666;
  margin-top: 0.25rem;
  font-size: 0.8rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.error-message {
  color: #F44336;
  margin-top: 1rem;
}

.success-message {
  color: #4CAF50;
  margin-top: 1rem;
}

/* Two-Factor Setup Styles */
.setup-qr, .verify-code {
  text-align: center;
}

.qr-container {
  display: flex;
  justify-content: center;
  margin: 1.5rem 0;
  min-height: 200px;
  align-items: center;
}

.qr-container img {
  max-width: 200px;
}

.manual-key {
  margin-bottom: 1.5rem;
  word-break: break-all;
  background: #f5f5f5;
  padding: 0.5rem;
  border-radius: 4px;
}

.code-input input {
  font-size: 1.5rem;
  letter-spacing: 0.5rem;
  text-align: center;
  max-width: 200px;
  margin: 1rem auto;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* Button Styles */
.btn {
  cursor: pointer;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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

.btn-danger {
  background-color: #F44336;
  color: white;
}

/* Loading Spinner */
.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 2rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>