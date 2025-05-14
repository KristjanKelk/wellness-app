<template>
  <transition name="modal-fade">
    <div v-if="show" class="two-factor-modal-backdrop" @click="$emit('close')">
      <div class="two-factor-modal-content" @click.stop>
        <button class="two-factor-modal-close" @click="$emit('close')">&times;</button>

        <h2>Set Up Two-Factor Authentication</h2>

        <div v-if="step === 1" class="setup-qr">
          <p>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
          <div class="qr-container">
            <img :src="qrCode" alt="QR Code for 2FA setup" v-if="qrCode" />
            <div v-else class="loading-spinner"></div>
          </div>
          <p class="manual-key" v-if="secret">
            Or enter this key manually: <strong>{{ secret }}</strong>
          </p>
          <button @click="$emit('step', 2)" class="btn btn-primary" :disabled="!qrCode">
            Next
          </button>
        </div>

        <div v-if="step === 2" class="verify-code">
          <p>Enter the 6-digit code from your authenticator app to verify setup</p>
          <div class="code-input">
            <input
                type="text"
                :value="code"
                @input="$emit('update:code', $event.target.value)"
                placeholder="000000"
                maxlength="6"
                pattern="[0-9]*"
                inputmode="numeric"
            />
          </div>
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
          <div class="form-actions">
            <button @click="$emit('step', 1)" class="btn btn-secondary">
              Back
            </button>
            <button @click="$emit('verify')"
                    class="btn btn-primary"
                    :disabled="code.length !== 6 || verifying">
              {{ verifying ? 'Verifying...' : 'Verify & Enable' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'TwoFactorModal',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    step: {
      type: Number,
      default: 1
    },
    qrCode: {
      type: String,
      default: ''
    },
    secret: {
      type: String,
      default: ''
    },
    code: {
      type: String,
      default: ''
    },
    error: {
      type: String,
      default: ''
    },
    verifying: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'step', 'update:code', 'verify']
}
</script>

<style scoped>
.two-factor-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.two-factor-modal-content {
  background-color: white;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  padding: 2rem;
  position: relative;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.two-factor-modal-close {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

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
  border: 1px solid #eee;
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

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 2rem auto;
}

.error-message {
  color: #F44336;
  margin-top: 1rem;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>