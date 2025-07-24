// src/utils/serviceWakeup.js
import axios from 'axios';

const BACKEND_URL = process.env.VUE_APP_API_URL || 'https://wellness-app-tx2c.onrender.com';

/**
 * Wake up the backend service if it's hibernating
 * @returns {Promise<boolean>} True if service is awake, false otherwise
 */
export async function wakeUpService() {
    console.log('Attempting to wake up backend service...');
    
    try {
        // Try to ping the service root endpoint
        const response = await axios.get(BACKEND_URL + '/', {
            timeout: 60000, // 60 seconds timeout for wake-up
            headers: {
                'Accept': 'text/html,application/json',
            }
        });
        
        // If we get any response (200, 404, etc.), the service is awake
        if (response.status >= 200 && response.status < 600) {
            console.log('Service is awake!');
            return true;
        }
    } catch (error) {
        if (error.response) {
            // Service responded with an error, but it's awake
            console.log('Service is awake (responded with error):', error.response.status);
            return true;
        } else {
            console.error('Failed to wake up service:', error.message);
            return false;
        }
    }
    
    return false;
}

/**
 * Check if the error indicates service hibernation
 * @param {Error} error - The error to check
 * @returns {boolean} True if error indicates hibernation
 */
export function isHibernationError(error) {
    if (!error.response) return false;
    
    const status = error.response.status;
    const headers = error.response.headers || {};
    
    // Check for Render.com specific hibernation indicators
    return (
        status === 503 ||
        status === 502 ||
        headers['x-render-routing']?.includes('hibernate') ||
        headers['x-render-routing']?.includes('dynamic-user-server-502')
    );
}

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Function to retry
 * @param {number} maxAttempts - Maximum number of attempts
 * @param {number} baseDelay - Base delay in milliseconds
 * @returns {Promise} Promise resolving to function result
 */
export async function retryWithBackoff(fn, maxAttempts = 3, baseDelay = 1000) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (error) {
            lastError = error;
            
            if (attempt === maxAttempts) {
                break;
            }
            
            // Calculate delay with exponential backoff
            const delay = baseDelay * Math.pow(2, attempt - 1);
            console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    throw lastError;
}

/**
 * Enhanced service health check
 * @returns {Promise<Object>} Health check result
 */
export async function checkServiceHealth() {
    try {
        const response = await axios.get(BACKEND_URL + '/api/health/', {
            timeout: 10000,
            headers: {
                'Accept': 'application/json',
            }
        });
        
        return {
            isHealthy: true,
            status: response.status,
            data: response.data
        };
    } catch (error) {
        return {
            isHealthy: false,
            status: error.response?.status || 0,
            error: error.message,
            isHibernating: isHibernationError(error)
        };
    }
}

/**
 * Initialize service connection on app startup
 * @param {Function} onProgress - Progress callback
 * @returns {Promise<boolean>} True if successful
 */
export async function initializeService(onProgress = () => {}) {
    console.log('Initializing service connection...');
    onProgress('Checking service status...');
    
    const health = await checkServiceHealth();
    
    if (health.isHealthy) {
        onProgress('Service is ready!');
        return true;
    }
    
    if (health.isHibernating) {
        onProgress('Service is sleeping, waking up...');
        console.log('Service is hibernating, attempting wake-up...');
        
        const success = await retryWithBackoff(async () => {
            onProgress('Attempting to wake up service...');
            const wakeResult = await wakeUpService();
            if (!wakeResult) {
                throw new Error('Failed to wake up service');
            }
            return wakeResult;
        }, 3, 2000);
        
        if (success) {
            onProgress('Service is ready!');
            return true;
        }
    }
    
    onProgress('Service connection failed');
    console.error('Failed to initialize service connection');
    return false;
}