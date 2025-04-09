// src/services/http.service.js
import axios from 'axios';

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
        const userStr = localStorage.getItem('user');
        if (userStr) {
            const user = JSON.parse(userStr);
            if (user && user.access) {
                config.headers['Authorization'] = 'Bearer ' + user.access;
            }
        }
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

        if (error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const userStr = localStorage.getItem('user');
                if (userStr) {
                    const user = JSON.parse(userStr);
                    const response = await axios.post('http://localhost:8000/api/token/refresh/', {
                        refresh: user.refresh
                    });

                    if (response.data.access) {
                        localStorage.setItem('user', JSON.stringify({
                            ...user,
                            access: response.data.access
                        }));

                        apiClient.defaults.headers.common['Authorization'] = 'Bearer ' + response.data.access;
                        return apiClient(originalRequest);
                    }
                }
            } catch (_error) {
                localStorage.removeItem('user');
                window.location = '/login';
                return Promise.reject(_error);
            }
        }

        return Promise.reject(error);
    }
);

export default apiClient;