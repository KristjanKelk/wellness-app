// src/services/auth.service.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

class AuthService {
    login(username, password, remember = false) {
        return axios
            .post(API_URL + 'token/', {
                username,
                password
            })
            .then(response => {
                if (response.data.access) {
                    // Extract user info from token
                    const tokenParts = response.data.access.split('.');
                    const payload = JSON.parse(atob(tokenParts[1]));

                    // Prepare user data, which might include 2FA status
                    const userData = {
                        ...response.data,
                        username: username,
                        user_id: payload.user_id,
                        email_verified: payload.email_verified,
                        two_factor_enabled: payload.two_factor_enabled
                    };

                    // If 2FA is not required, store user data in localStorage
                    if (!userData.two_factor_enabled) {
                        if (remember) {
                            localStorage.setItem('user', JSON.stringify(userData));
                        } else {
                            sessionStorage.setItem('user', JSON.stringify(userData));
                        }
                        console.log('User data stored, 2FA not required:', userData);
                    } else {
                        console.log('2FA required for login, temporary auth data created');
                    }

                    return userData;
                }
                return response.data;
            });
    }

    verifyTwoFactorLogin(code, tempAuthData) {
        return axios
            .post(API_URL + 'token/2fa-verify/', {
                token: tempAuthData.access,
                code: code
            })
            .then(response => {
                if (response.data.access) {
                    const userData = {
                        ...tempAuthData,
                        ...response.data,
                        two_factor_verified: true
                    };

                    // Store user data after 2FA verification
                    localStorage.setItem('user', JSON.stringify(userData));
                    console.log('User data stored after 2FA verification:', userData);

                    return userData;
                }
                return response.data;
            });
    }

    logout() {
        localStorage.removeItem('user');
        sessionStorage.removeItem('user');
        console.log('User data removed from storage');
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
        // Try to get user from localStorage, then from sessionStorage
        let userStr = localStorage.getItem('user') || sessionStorage.getItem('user');

        if (!userStr) {
            console.error('No user found in storage');
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

                        // Update in the same storage that had the user
                        if (localStorage.getItem('user')) {
                            localStorage.setItem('user', JSON.stringify(updatedUser));
                        } else if (sessionStorage.getItem('user')) {
                            sessionStorage.setItem('user', JSON.stringify(updatedUser));
                        }

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
        // Try localStorage first, then sessionStorage
        const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
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