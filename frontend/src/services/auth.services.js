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
                    localStorage.setItem('user', JSON.stringify(response.data));
                }
                return response.data;
            });
    }

    logout() {
        localStorage.removeItem('user');
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
        const user = JSON.parse(localStorage.getItem('user'));

        if (!user || !user.refresh) {
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
                }
                return response.data;
            });
    }
}

export default new AuthService();