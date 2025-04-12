// src/services/http.service.js
import axios from 'axios';
import AuthService from './auth.services';
import store from '../store';

// Create axios instance
const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api/',
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000
});

// Add request interceptor
apiClient.interceptors.request.use(
    config => {
        let token = null;
        if (store && store.state && store.state.auth && store.state.auth.user) {
            token = store.state.auth.user.access;
        }
        if (!token) {
            const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
            if (userStr) {
                try {
                    const user = JSON.parse(userStr);
                    if (user && user.access) {
                        token = user.access;
                    }
                } catch (e) {
                    console.error('Error parsing user data in HTTP interceptor:', e);
                }
            }
        }

        if (token) {
            config.headers['Authorization'] = 'Bearer ' + token;
        }

        console.log('API Request:', config.method.toUpperCase(), config.url);
        return config;
    },
    error => {
        console.error('Request error in interceptor:', error);
        return Promise.reject(error);
    }
);

apiClient.interceptors.response.use(
    response => {
        return response;
    },
    async error => {
        const originalRequest = error.config;
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            console.log('Token expired, attempting refresh...');
            originalRequest._retry = true;

            try {
                const refreshResult = await AuthService.refreshToken();

                if (refreshResult && refreshResult.access) {
                    console.log('Token refreshed successfully');
                    originalRequest.headers['Authorization'] = 'Bearer ' + refreshResult.access;
                    return axios(originalRequest);
                } else {
                    console.error('Token refresh response incomplete');
                    throw new Error('Token refresh failed');
                }
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                AuthService.logout();
                setTimeout(() => {
                    window.location.href = '/login';
                }, 100);
                return Promise.reject(refreshError);
            }
        }
        console.error('API Response Error:',
            error.response ? `${error.response.status} ${error.response.statusText}` : error.message);

        return Promise.reject(error);
    }
);

export default apiClient;