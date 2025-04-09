// src/services/auth.service.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

class AuthService {
    login(username, password) {
        return axios
            .post(API_URL + 'token/', {
                username,
                password
            })
            .then(response => {
                if (response.data.access) {
                    const userData = {
                        ...response.data,
                        username: username
                    };
                    localStorage.setItem('user', JSON.stringify(userData));
                    console.log('User data stored in localStorage:', userData);
                    return userData;
                }
                return response.data;
            });
    }

    logout() {
        localStorage.removeItem('user');
        console.log('User data removed from localStorage');
    }

    register(username, email, password, password2) {
        return axios.post(API_URL + 'register/', {
            username,
            email,
            password,
            password2
        });
    }

    refreshToken() {
        const userStr = localStorage.getItem('user');

        if (!userStr) {
            console.error('No user found in localStorage');
            return Promise.reject('No refresh token available');
        }

        try {
            const user = JSON.parse(userStr);

            if (!user.refresh) {
                console.error('No refresh token found in user data');
                return Promise.reject('No refresh token available');
            }

            return axios
                .post(API_URL + 'token/refresh/', {
                    refresh: user.refresh
                })
                .then(response => {
                    if (response.data.access) {
                        const updatedUser = {
                            ...user,
                            access: response.data.access
                        };
                        localStorage.setItem('user', JSON.stringify(updatedUser));
                        console.log('Token refreshed and stored:', updatedUser);
                        return response.data;
                    }
                    return Promise.reject('Failed to refresh token');
                });
        } catch (e) {
            console.error('Error parsing user data:', e);
            return Promise.reject('Invalid user data');
        }
    }

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        if (!userStr) return null;

        try {
            return JSON.parse(userStr);
        } catch (e) {
            console.error('Error parsing current user:', e);
            return null;
        }
    }
}

export default new AuthService();