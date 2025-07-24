<template>
  <div v-if="isWarming" class="service-warming-overlay">
    <div class="warming-modal">
      <div class="warming-header">
        <div class="warming-icon">
          <div class="pulse-icon">🏥</div>
        </div>
        <h3>Starting Wellness Service</h3>
        <p class="warming-message">{{ currentMessage }}</p>
      </div>
      
      <div class="warming-progress">
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
        <div class="progress-text">{{ progressText }}</div>
      </div>
      
      <div class="warming-details">
        <div class="detail-item">
          <span class="detail-icon">⏰</span>
          <span>This is normal on first load (free hosting)</span>
        </div>
        <div class="detail-item">
          <span class="detail-icon">🚀</span>
          <span>Service will be faster once started</span>
        </div>
        <div class="detail-item" v-if="attempt > 1">
          <span class="detail-icon">🔄</span>
          <span>Attempt {{ attempt }}/{{ maxAttempts }}</span>
        </div>
      </div>
      
      <div v-if="showError" class="warming-error">
        <p>❌ Service startup is taking longer than expected</p>
        <button @click="retryWarming" class="retry-button">
          Try Again
        </button>
        <button @click="skipWarming" class="skip-button">
          Continue Anyway
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { initializeService } from '../utils/serviceWakeup.js';

export default {
  name: 'ServiceWarming',
  data() {
    return {
      isWarming: false,
      currentMessage: '',
      progress: 0,
      attempt: 1,
      maxAttempts: 4,
      showError: false,
      startTime: null
    };
  },
  computed: {
    progressPercent() {
      return Math.min(this.progress, 100);
    },
    progressText() {
      if (this.progress >= 100) {
        return 'Service Ready!';
      } else if (this.progress >= 80) {
        return 'Almost ready...';
      } else if (this.progress >= 50) {
        return 'Starting up...';
      } else {
        return 'Connecting...';
      }
    }
  },
  methods: {
    async startWarming() {
      this.isWarming = true;
      this.showError = false;
      this.startTime = Date.now();
      this.attempt = 1;
      this.progress = 10;
      
      try {
        const success = await initializeService((message) => {
          this.updateProgress(message);
        });
        
        if (success) {
          this.currentMessage = 'Service is ready!';
          this.progress = 100;
          
          // Wait a moment to show success, then hide
          setTimeout(() => {
            this.isWarming = false;
            this.$emit('service-ready');
          }, 1500);
        } else {
          this.showWarmingError();
        }
      } catch (error) {
        console.error('Service warming failed:', error);
        this.showWarmingError();
      }
    },
    
    updateProgress(message) {
      this.currentMessage = message;
      
      if (message.includes('Checking')) {
        this.progress = 20;
      } else if (message.includes('sleeping') || message.includes('hibernating')) {
        this.progress = 30;
      } else if (message.includes('Attempting to wake')) {
        this.progress = 50;
        this.attempt = 1;
      } else if (message.includes('Attempt')) {
        const attemptMatch = message.match(/Attempt (\d+)/);
        if (attemptMatch) {
          this.attempt = parseInt(attemptMatch[1]);
          this.progress = 50 + (this.attempt * 15);
        }
      } else if (message.includes('ready')) {
        this.progress = 95;
      }
      
      // Auto-increment progress based on time
      if (this.startTime) {
        const elapsed = Date.now() - this.startTime;
        const timeProgress = Math.min(elapsed / 60000 * 70, 70); // 70% max from time
        this.progress = Math.max(this.progress, timeProgress);
      }
    },
    
    showWarmingError() {
      this.currentMessage = 'Service startup is taking longer than expected';
      this.showError = true;
    },
    
    async retryWarming() {
      this.showError = false;
      this.progress = 10;
      await this.startWarming();
    },
    
    skipWarming() {
      this.isWarming = false;
      this.$emit('service-skipped');
    }
  },
  
  mounted() {
    // Auto-start warming on component mount
    this.startWarming();
  }
};
</script>

<style scoped>
.service-warming-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(5px);
}

.warming-modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  max-width: 480px;
  width: 90%;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalAppear 0.3s ease-out;
}

@keyframes modalAppear {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.warming-header {
  margin-bottom: 24px;
}

.warming-icon {
  margin-bottom: 16px;
}

.pulse-icon {
  font-size: 48px;
  animation: pulse 2s infinite;
  display: inline-block;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.warming-header h3 {
  color: #2c3e50;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.warming-message {
  color: #666;
  margin: 0;
  font-size: 16px;
  min-height: 24px;
}

.warming-progress {
  margin: 24px 0;
}

.progress-bar {
  background: #f0f0f0;
  border-radius: 12px;
  height: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  background: linear-gradient(90deg, #3498db, #2ecc71);
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 12px;
}

.progress-text {
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.warming-details {
  margin: 24px 0;
  text-align: left;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.detail-icon {
  margin-right: 8px;
  font-size: 16px;
  width: 20px;
}

.warming-error {
  margin-top: 24px;
  padding: 16px;
  background: #fef5e7;
  border-radius: 8px;
  border: 1px solid #f39c12;
}

.warming-error p {
  color: #d68910;
  margin: 0 0 16px 0;
  font-weight: 500;
}

.retry-button, .skip-button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  margin: 0 4px;
  transition: all 0.2s ease;
}

.retry-button {
  background: #3498db;
  color: white;
}

.retry-button:hover {
  background: #2980b9;
}

.skip-button {
  background: #95a5a6;
  color: white;
}

.skip-button:hover {
  background: #7f8c8d;
}

/* Mobile responsiveness */
@media (max-width: 640px) {
  .warming-modal {
    padding: 24px;
    margin: 16px;
  }
  
  .warming-header h3 {
    font-size: 20px;
  }
  
  .pulse-icon {
    font-size: 40px;
  }
}
</style>