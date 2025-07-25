<template>
  <div v-if="showModal" class="service-status-overlay">
    <div class="service-status-modal">
      <div class="modal-header">
        <h3>
          <span v-if="status === 'checking'" class="icon">🔍</span>
          <span v-else-if="status === 'waking'" class="icon">🔄</span>
          <span v-else-if="status === 'ready'" class="icon">✅</span>
          <span v-else-if="status === 'error'" class="icon">❌</span>
          <span v-else class="icon">⏸️</span>
          {{ statusMessage }}
        </h3>
      </div>

      <div class="modal-body">
        <div v-if="status === 'hibernating' || status === 'waking'" class="hibernation-info">
          <p class="explanation">
            Our app is hosted on a free service that goes to sleep after 15 minutes of inactivity. 
            This helps keep our costs down while providing you with a great wellness tracking experience!
          </p>
          
          <div v-if="progress.current > 0" class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: progress.percentage + '%' }"
              ></div>
            </div>
            <p class="progress-text">
              {{ progress.message }} ({{ progress.current }}/{{ progress.total }})
            </p>
          </div>

          <div class="tips">
            <h4>💡 While you wait:</h4>
            <ul>
              <li>This usually takes 30-60 seconds on the first visit</li>
              <li>Once awake, the app will be fast and responsive</li>
              <li>Consider bookmarking your dashboard for quick access</li>
            </ul>
          </div>
        </div>

        <div v-else-if="status === 'error'" class="error-info">
          <p class="error-message">{{ errorMessage }}</p>
          <div class="error-actions">
            <button @click="retryConnection" class="retry-btn">
              🔄 Try Again
            </button>
            <button @click="continueAnyway" class="continue-btn">
              ⏭️ Continue Anyway
            </button>
          </div>
        </div>

        <div v-else-if="status === 'ready'" class="success-info">
          <p>✅ Service is ready! Your app should work normally now.</p>
          <button @click="closeModal" class="close-btn">
            Continue to App
          </button>
        </div>
      </div>

      <div class="modal-footer">
        <p class="help-text">
          Having issues? The service might be experiencing high load. 
          <a href="mailto:support@wellnessapp.com">Contact support</a> if problems persist.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { serviceWakeup } from '../utils/serviceWakeup';

export default {
  name: 'ServiceStatus',
  data() {
    return {
      showModal: false,
      status: 'checking', // checking, hibernating, waking, ready, error
      progress: {
        current: 0,
        total: 0,
        percentage: 0,
        message: ''
      },
      errorMessage: '',
      autoCloseTimer: null
    };
  },
  computed: {
    statusMessage() {
      switch (this.status) {
        case 'checking':
          return 'Checking Service Status';
        case 'hibernating':
          return 'Service is Sleeping';
        case 'waking':
          return 'Waking Up Service';
        case 'ready':
          return 'Service is Ready!';
        case 'error':
          return 'Connection Issues';
        default:
          return 'Service Status';
      }
    }
  },
  async mounted() {
    this.setupProgressListener();
    await this.checkServiceStatus();
  },
  beforeUnmount() {
    this.removeProgressListener();
    if (this.autoCloseTimer) {
      clearTimeout(this.autoCloseTimer);
    }
  },
  methods: {
    async checkServiceStatus() {
      this.status = 'checking';
      this.showModal = true;

      try {
        const health = await serviceWakeup.checkServiceHealth();
        
        if (health.isHealthy) {
          this.status = 'ready';
          this.autoCloseModal();
        } else if (health.isHibernating) {
          this.status = 'hibernating';
          await this.wakeUpService();
        } else {
          this.status = 'error';
          this.errorMessage = health.error || 'Service is currently unavailable';
        }
      } catch (error) {
        console.error('Error checking service status:', error);
        this.status = 'error';
        this.errorMessage = 'Failed to connect to service';
      }
    },

    async wakeUpService() {
      this.status = 'waking';
      
      try {
        const result = await serviceWakeup.wakeupService(true);
        
        if (result.success) {
          this.status = 'ready';
          this.autoCloseModal();
        } else {
          this.status = 'error';
          this.errorMessage = `Failed to wake up service after ${result.attempts} attempts: ${result.lastError}`;
        }
      } catch (error) {
        console.error('Error waking up service:', error);
        this.status = 'error';
        this.errorMessage = error.message || 'Failed to wake up service';
      }
    },

    setupProgressListener() {
      this.progressHandler = (event) => {
        this.progress = event.detail;
      };
      window.addEventListener('service-wakeup-progress', this.progressHandler);
    },

    removeProgressListener() {
      if (this.progressHandler) {
        window.removeEventListener('service-wakeup-progress', this.progressHandler);
      }
    },

    async retryConnection() {
      await this.checkServiceStatus();
    },

    continueAnyway() {
      this.closeModal();
      // Emit event to parent that user wants to continue
      this.$emit('continue-anyway');
    },

    closeModal() {
      this.showModal = false;
      this.$emit('closed');
    },

    autoCloseModal() {
      // Auto close after 3 seconds when ready
      this.autoCloseTimer = setTimeout(() => {
        this.closeModal();
      }, 3000);
    }
  }
};
</script>

<style scoped>
.service-status-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.service-status-modal {
  background: white;
  border-radius: 12px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px 12px 0 0;
}

.modal-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
}

.icon {
  font-size: 24px;
  margin-right: 12px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.modal-body {
  padding: 24px;
}

.hibernation-info, .error-info, .success-info {
  text-align: center;
}

.explanation {
  color: #6b7280;
  margin-bottom: 24px;
  line-height: 1.6;
}

.progress-container {
  margin: 24px 0;
}

.progress-bar {
  background-color: #f3f4f6;
  border-radius: 8px;
  height: 8px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  height: 100%;
  border-radius: 8px;
  transition: width 0.3s ease;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: 200px 0; }
}

.progress-text {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

.tips {
  background-color: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  margin-top: 24px;
  text-align: left;
}

.tips h4 {
  margin: 0 0 12px;
  color: #374151;
  font-size: 16px;
}

.tips ul {
  margin: 0;
  padding-left: 20px;
  color: #6b7280;
}

.tips li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.error-message {
  color: #dc2626;
  margin-bottom: 24px;
  padding: 16px;
  background-color: #fef2f2;
  border-radius: 8px;
  border: 1px solid #fecaca;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.retry-btn, .continue-btn, .close-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.retry-btn {
  background-color: #3b82f6;
  color: white;
}

.retry-btn:hover {
  background-color: #2563eb;
  transform: translateY(-1px);
}

.continue-btn {
  background-color: #6b7280;
  color: white;
}

.continue-btn:hover {
  background-color: #4b5563;
  transform: translateY(-1px);
}

.close-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 16px 32px;
  font-size: 16px;
}

.close-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.modal-footer {
  padding: 16px 24px;
  background-color: #f9fafb;
  border-top: 1px solid #e5e7eb;
  border-radius: 0 0 12px 12px;
}

.help-text {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}

.help-text a {
  color: #3b82f6;
  text-decoration: none;
}

.help-text a:hover {
  text-decoration: underline;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .service-status-modal {
    background: #1f2937;
    color: #f9fafb;
  }

  .modal-header {
    border-bottom-color: #374151;
  }

  .explanation, .progress-text, .tips li {
    color: #9ca3af;
  }

  .tips {
    background-color: #374151;
  }

  .tips h4 {
    color: #f3f4f6;
  }

  .modal-footer {
    background-color: #374151;
    border-top-color: #4b5563;
  }

  .help-text {
    color: #9ca3af;
  }
}
</style>