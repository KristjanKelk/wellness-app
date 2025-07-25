// src/utils/serviceWakeup.js
import axios from 'axios';

export class ServiceWakeupManager {
  constructor() {
    this.isWakingUp = false;
    this.wakeupPromise = null;
    this.baseUrl = 'https://wellness-app-tx2c.onrender.com';
  }

  async wakeupService(showProgress = true) {
    // If already waking up, return the existing promise
    if (this.isWakingUp && this.wakeupPromise) {
      return this.wakeupPromise;
    }

    this.isWakingUp = true;
    
    this.wakeupPromise = this._performWakeup(showProgress);
    
    try {
      const result = await this.wakeupPromise;
      return result;
    } finally {
      this.isWakingUp = false;
      this.wakeupPromise = null;
    }
  }

  async _performWakeup(showProgress) {
    console.log('🔄 Starting service wake-up sequence...');
    
    const maxAttempts = 6;
    const delays = [2000, 5000, 8000, 12000, 18000, 25000]; // Progressive delays
    
    let lastError = null;
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        if (showProgress) {
          this._updateProgress(attempt + 1, maxAttempts, 'Pinging service...');
        }
        
        console.log(`🔄 Wake-up attempt ${attempt + 1}/${maxAttempts}...`);
        
        // Wait before each attempt (except the first)
        if (attempt > 0) {
          await this._delay(delays[attempt - 1]);
        }
        
        // Try to ping the service
        const response = await axios.get(`${this.baseUrl}/`, {
          timeout: 20000,
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'X-Wake-Up': 'true'
          }
        });
        
        if (response.status === 200) {
          console.log('✅ Service is awake!');
          
          if (showProgress) {
            this._updateProgress(maxAttempts, maxAttempts, 'Service is ready!');
          }
          
          // Give the service a moment to fully initialize
          await this._delay(2000);
          
          return { success: true, attempts: attempt + 1 };
        }
        
      } catch (error) {
        console.log(`❌ Wake-up attempt ${attempt + 1} failed:`, error.message);
        lastError = error;
        
        if (showProgress) {
          this._updateProgress(
            attempt + 1, 
            maxAttempts, 
            `Attempt ${attempt + 1} failed, retrying...`
          );
        }
        
        // If it's a 503, the service is definitely hibernating, continue trying
        if (error.response?.status === 503) {
          continue;
        }
        
        // For other errors, still continue but adjust strategy
        if (error.response?.status && error.response.status !== 502) {
          // Service is responding but with an error, it might be starting up
          continue;
        }
      }
    }
    
    // All attempts failed
    console.error('❌ Failed to wake up service after all attempts');
    
    if (showProgress) {
      this._updateProgress(maxAttempts, maxAttempts, 'Wake-up failed, service may be offline');
    }
    
    return { 
      success: false, 
      attempts: maxAttempts, 
      lastError: lastError?.message || 'Unknown error' 
    };
  }

  async checkServiceHealth() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/health/`, {
        timeout: 10000,
        headers: {
          'Cache-Control': 'no-cache'
        }
      });
      
      return {
        isHealthy: response.status === 200,
        status: response.status,
        data: response.data
      };
    } catch (error) {
      return {
        isHealthy: false,
        status: error.response?.status || 0,
        error: error.message,
        isHibernating: error.response?.status === 503
      };
    }
  }

  _updateProgress(current, total, message) {
    // Emit a custom event that components can listen to
    const event = new CustomEvent('service-wakeup-progress', {
      detail: {
        current,
        total,
        message,
        percentage: Math.round((current / total) * 100)
      }
    });
    
    window.dispatchEvent(event);
    
    // Also log to console for debugging
    console.log(`🔄 [${current}/${total}] ${message}`);
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Utility method to handle 503 errors in any API call
  static async handleHibernationError(originalRequest, api) {
    const manager = new ServiceWakeupManager();
    
    console.log('🔄 Detected service hibernation, attempting wake-up...');
    
    const result = await manager.wakeupService(true);
    
    if (result.success) {
      console.log('✅ Service awakened, retrying original request...');
      // Retry the original request
      return api(originalRequest);
    } else {
      console.error('❌ Failed to wake up service, original request will likely fail');
      // Still try the original request, it might work
      throw new Error(`Service wake-up failed after ${result.attempts} attempts: ${result.lastError}`);
    }
  }
}

// Singleton instance
export const serviceWakeup = new ServiceWakeupManager();

// Utility functions for common use cases
export const wakeupService = (showProgress = true) => serviceWakeup.wakeupService(showProgress);
export const checkServiceHealth = () => serviceWakeup.checkServiceHealth();

export default serviceWakeup;