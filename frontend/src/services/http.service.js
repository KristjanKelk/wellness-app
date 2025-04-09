// src/services/http.service.js
import axios from 'axios';
import AuthService from './auth.services';

// Create axios instance
const apiClient = axios.create({
    baseURL: 'http://localhost:8000/api/',
    headers: {
        'Content-Type': 'application/json',
    }
});

// Add request interceptor
apiClient.interceptors.request.use(
    config => {
        const user = JSON.parse(localStorage.getItem('user'));
        if (user && user.access) {
            config.headers['Authorization'] = 'Bearer ' + user.access;
        }
        console.log('API Request:', config.method.toUpperCase(), config.url);
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Add response interceptor
apiClient.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshResult = await AuthService.refreshToken();

                if (refreshResult && refreshResult.access) {
                    originalRequest.headers['Authorization'] = 'Bearer ' + refreshResult.access;
                    return axios(originalRequest);
                }
            } catch (refreshError) {
                console.error('Token refresh failed:', refreshError);
                AuthService.logout();
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;