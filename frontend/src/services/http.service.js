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
    timeout: 10000,
    withCredentials: true,   // if you need cookies/CORS creds
});

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
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const response = await AuthService.refreshToken();
                if (response?.access) {
                    originalRequest.headers['Authorization'] = 'Bearer ' + response.access;

                    if (store?.state?.auth?.status?.loggedIn) {
                        await store.dispatch('auth/refreshToken', response.access);
                    }
                    return axios(originalRequest);
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
        if (error.response) {
            console.error(
                `API Error: ${error.response.status} ${error.response.statusText}`,
                error.response.data
            );
        } else {
            console.error('API Error:', error.message);
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