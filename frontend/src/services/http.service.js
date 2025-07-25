// src/services/http.service.js
import axios from 'axios';
import AuthService from './auth.service';
import store from '../store';

// Compute base-URL once, either from your VUE_APP_API_URL or fallback to Render:
const API_URL = (
  process.env.VUE_APP_API_URL ||
  'https://wellness-app-tx2c.onrender.com/api'
)
  .replace(/\/+$/, '') + '/';

// Create axios instance
const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 60000,  // Increased timeout to 60 seconds for service wake-up and login
    withCredentials: true,   // if you need cookies/CORS creds
});

// Function to handle service hibernation (503 errors on Render.com)
async function handleServiceHibernation(originalRequest) {
    console.log('Service appears to be hibernating. Attempting to wake up...');
    
    // Show user-friendly message
    if (store?.commit) {
        store.commit('ui/setLoading', {
            isLoading: true,
            message: 'Service is starting up... This may take up to 60 seconds on the first request.'
        });
    }

    // Multiple wake-up attempts with increasing delays
    const maxAttempts = 4;
    const delays = [5000, 10000, 15000, 20000]; // 5s, 10s, 15s, 20s
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            console.log(`Wake-up attempt ${attempt + 1}/${maxAttempts}...`);
            
            if (store?.commit) {
                store.commit('ui/setLoading', {
                    isLoading: true,
                    message: `Waking up service... Attempt ${attempt + 1}/${maxAttempts}`
                });
            }
            
            await new Promise(resolve => setTimeout(resolve, delays[attempt]));
            
            // Attempt to wake up the service
            await axios.get(API_URL.replace('/api/', '/'), { 
                timeout: 30000,
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            
            // Service responded, wait a bit for full initialization
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            console.log('Service wake-up successful, retrying original request...');
            
            // Retry original request
            return apiClient(originalRequest);
            
        } catch (wakeupError) {
            console.log(`Wake-up attempt ${attempt + 1} failed:`, wakeupError.message);
            
            if (attempt === maxAttempts - 1) {
                // Last attempt failed, try the original request anyway
                console.log('All wake-up attempts failed, trying original request...');
                break;
            }
        }
    }
    
    // Final attempt with the original request
    try {
        return await apiClient(originalRequest);
    } catch (finalError) {
        if (store?.commit) {
            store.commit('ui/setError', {
                message: 'Service is currently unavailable. Please try again in a few minutes.',
                details: 'The backend service may be starting up or experiencing issues.'
            });
        }
        throw finalError;
    } finally {
        if (store?.commit) {
            store.commit('ui/setLoading', { isLoading: false });
        }
    }
}

// Add request interceptor
apiClient.interceptors.request.use(
    config => {
        const token = getAccessToken();
        if (token) {
            config.headers['Authorization'] = 'Bearer ' + token;
        }

        return config;
    },
    error => {
        console.error('API request error:', error);
        return Promise.reject(error);
    }
);

apiClient.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;

        // Handle service hibernation (503 errors)
        if (error.response?.status === 503 && !originalRequest._hibernation_retry) {
            originalRequest._hibernation_retry = true;
            return handleServiceHibernation(originalRequest);
        }

        // Handle 502 errors (bad gateway, often during service startup)
        if (error.response?.status === 502 && !originalRequest._gateway_retry) {
            originalRequest._gateway_retry = true;
            console.log('Service gateway error, retrying in 5 seconds...');
            await new Promise(resolve => setTimeout(resolve, 5000));
            return apiClient(originalRequest);
        }

        // Handle timeout errors specifically for authentication requests
        if (error.code === 'ECONNABORTED' && !originalRequest._timeout_retry) {
            const isAuthRequest = originalRequest.url?.includes('token/') || originalRequest.url?.includes('register/');
            
            if (isAuthRequest) {
                originalRequest._timeout_retry = true;
                console.log('Authentication request timed out, retrying with longer timeout...');
                
                // Retry with extended timeout
                const retryConfig = {
                    ...originalRequest,
                    timeout: 120000, // 2 minutes for auth requests
                };
                
                return apiClient(retryConfig);
            }
        }

        // Handle authentication errors
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const response = await AuthService.refreshToken();
                if (response?.access) {
                    originalRequest.headers['Authorization'] = 'Bearer ' + response.access;

                    if (store?.state?.auth?.status?.loggedIn) {
                        await store.dispatch('auth/refreshToken', response.access);
                    }
                    return apiClient(originalRequest);
                }
            } catch (refreshError) {
                AuthService.logout();

                if (store?.state?.auth?.status?.loggedIn) {
                    store.commit('auth/logout');
                }
                setTimeout(() => {
                    window.location.href = '/login';
                }, 100);
                return Promise.reject(refreshError);
            }
        }

        // Enhanced error logging and user-friendly messages
        if (error.response) {
            const errorInfo = {
                status: error.response.status,
                statusText: error.response.statusText,
                url: error.config?.url,
                method: error.config?.method,
                data: error.response.data,
                headers: error.response.headers
            };
            
            if (error.response.status === 503) {
                console.error('Service hibernation detected:', errorInfo);
            } else if (error.response.status === 502) {
                console.error('Service gateway error:', errorInfo);
            } else {
                console.error('API Error:', errorInfo);
            }
        } else if (error.code === 'ECONNABORTED') {
            console.error('API Request timeout:', error.message);
            
            // Add user-friendly timeout message for login requests
            if (error.config?.url?.includes('token/')) {
                console.warn('Login request timed out - service may be hibernating');
            }
        } else {
            console.error('API Network error:', error.message);
            
            // Network error handling for login requests
            if (error.config?.url?.includes('token/')) {
                console.warn('Network error during login request');
            }
        }

        return Promise.reject(error);
    }
);

/**
 * Get the current access token from store or storage
 * @returns {string|null} Access token or null
 */
function getAccessToken() {
    // Try to get token from store
    if (store?.state?.auth?.user?.access) {
        return store.state.auth.user.access;
    }
    const user = AuthService.getCurrentUser();
    return user?.access || null;
}

export default apiClient;