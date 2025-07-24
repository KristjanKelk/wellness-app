<template>
  <div v-if="isVisible" class="service-status-overlay">
    <div class="service-status-modal">
      <div class="status-icon">
        <div v-if="status === 'waking'" class="spinner"></div>
        <div v-else-if="status === 'error'" class="error-icon">⚠️</div>
        <div v-else-if="status === 'success'" class="success-icon">✅</div>
        <div v-else class="info-icon">ℹ️</div>
      </div>
      
      <h3 class="status-title">{{ statusTitle }}</h3>
      <p class="status-message">{{ statusMessage }}</p>
      
      <div v-if="showProgress" class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>
      
      <div v-if="status === 'error'" class="error-actions">
        <button @click="retry" class="retry-btn">Try Again</button>
        <button @click="dismiss" class="dismiss-btn">Continue Anyway</button>
      </div>
      
      <div v-if="showDetails" class="status-details">
        <p><strong>Note:</strong> Our backend service uses a free hosting tier that goes to sleep after periods of inactivity. The first request after sleeping may take 30-60 seconds to respond while the service wakes up.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ServiceStatus',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    status: {
      type: String,
      default: 'checking', // checking, waking, success, error
      validator: value => ['checking', 'waking', 'success', 'error'].includes(value)
    },
    message: {
      type: String,
      default: ''
    },
    progress: {
      type: Number,
      default: 0
    },
    showDetails: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    isVisible() {
      return this.visible && this.status !== 'success';
    },
    statusTitle() {
      switch (this.status) {
        case 'checking':
          return 'Checking Service Status';
        case 'waking':
          return 'Waking Up Service';
        case 'error':
          return 'Service Connection Issue';
        case 'success':
          return 'Service Ready';
        default:
          return 'Connecting...';
      }
    },
    statusMessage() {
      if (this.message) {
        return this.message;
      }
      
      switch (this.status) {
        case 'checking':
          return 'Checking if the backend service is available...';
        case 'waking':
          return 'The service is sleeping and being woken up. This may take a minute...';
        case 'error':
          return 'Unable to connect to the backend service. Please check your internet connection.';
        case 'success':
          return 'Service is ready!';
        default:
          return 'Connecting to service...';
      }
    },
    showProgress() {
      return this.status === 'waking' && this.progress > 0;
    }
  },
  methods: {
    retry() {
      this.$emit('retry');
    },
    dismiss() {
      this.$emit('dismiss');
    }
  }
};
</script>

<style scoped>
.service-status-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.service-status-modal {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  text-align: center;
}

.status-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.status-title {
  color: #333;
  margin-bottom: 0.5rem;
  font-size: 1.5rem;
}

.status-message {
  color: #666;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transition: width 0.3s ease;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.retry-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s ease;
}

.retry-btn:hover {
  background: #2980b9;
}

.dismiss-btn {
  background: #95a5a6;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.3s ease;
}

.dismiss-btn:hover {
  background: #7f8c8d;
}

.status-details {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #666;
  text-align: left;
}

.status-details strong {
  color: #333;
}
</style>