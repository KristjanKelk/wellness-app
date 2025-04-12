// src/store/modules/auth.module.js
import AuthService from '../../services/auth.services'

// Check if the token in localStorage is still valid
const validateToken = () => {
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    if (!userStr) return false;

    try {
        const user = JSON.parse(userStr);
        if (!user.access) return false;

        const parts = user.access.split('.');
        if (parts.length !== 3) return false;

        // Check if token is expired
        const payload = JSON.parse(atob(parts[1]));
        const now = Math.floor(Date.now() / 1000);

        if (!(payload.exp && payload.exp < now)) {
            return true;
        }

        localStorage.removeItem('user');
        sessionStorage.removeItem('user');
        return false;
    } catch (e) {
        console.error('Error validating token:', e);
        return false;
    }
}

// Get user from both possible storage locations
const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
const initialState = validateToken()
    ? { status: { loggedIn: true }, user: JSON.parse(userStr) }
    : { status: { loggedIn: false }, user: null };
console.log('Auth module initial state:', initialState);

export default {
    namespaced: true,
    state: initialState,
    actions: {
        login({ commit }, user) {
            return AuthService.login(user.username, user.password, user.remember).then(
                userData => {
                    // If 2FA is not required, we commit loginSuccess
                    // Otherwise, the calling component will handle the 2FA flow
                    if (!userData.two_factor_enabled) {
                        commit('loginSuccess', userData);

                        // Force a small delay before continuing to allow the token to be properly set
                        return new Promise(resolve => {
                            setTimeout(() => {
                                console.log('Login successful, user data:', userData);
                                resolve(userData);
                            }, 50);
                        });
                    }

                    console.log('Login successful, user data:', userData);
                    return Promise.resolve(userData);
                },
                error => {
                    commit('loginFailure');
                    console.error('Login failed:', error);
                    return Promise.reject(error);
                }
            );
        },
        verifyTwoFactor({ commit }, { code, tempAuthData }) {
            return AuthService.verifyTwoFactorLogin(code, tempAuthData).then(
                userData => {
                    commit('loginSuccess', userData);

                    // Same delay after 2FA login success
                    return new Promise(resolve => {
                        setTimeout(() => {
                            console.log('Two-factor verification successful');
                            resolve(userData);
                        }, 50);
                    });
                },
                error => {
                    console.error('Two-factor verification failed:', error);
                    return Promise.reject(error);
                }
            );
        },
        logout({ commit }) {
            AuthService.logout();
            commit('logout');
            console.log('User logged out');
        },
        register({ commit }, user) {
            return AuthService.register(user.username, user.email, user.password, user.password2).then(
                response => {
                    commit('registerSuccess');
                    console.log('Registration successful');
                    return Promise.resolve(response.data);
                },
                error => {
                    commit('registerFailure');
                    console.error('Registration failed:', error);
                    return Promise.reject(error);
                }
            );
        },
        refreshToken({ commit }, accessToken) {
            commit('refreshToken', accessToken);
            console.log('Token refreshed');
        },
        checkAuth({ commit, state }) {
            // This action will check if the user is still authenticated
            // and can be called when the app initializes
            if (state.status.loggedIn && state.user) {
                if (!validateToken()) {
                    // Token is invalid, try to refresh
                    return AuthService.refreshToken().then(
                        response => {
                            if (response && response.access) {
                                const user = { ...state.user, access: response.access };
                                commit('loginSuccess', user);
                                return Promise.resolve(user);
                            } else {
                                commit('logout');
                                return Promise.reject(new Error('Failed to refresh token'));
                            }
                        },
                        error => {
                            commit('logout');
                            return Promise.reject(error);
                        }
                    );
                }
                return Promise.resolve(state.user);
            } else {
                // Check if we have a valid token in storage but not in state
                if (validateToken()) {
                    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
                    try {
                        const userData = JSON.parse(userStr);
                        commit('loginSuccess', userData);
                        return Promise.resolve(userData);
                    } catch (e) {
                        console.error('Error parsing user data:', e);
                    }
                }

                commit('logout');
                return Promise.reject(new Error('Not authenticated'));
            }
        }
    },
    mutations: {
        loginSuccess(state, user) {
            state.status.loggedIn = true;
            state.user = user;
            console.log('Login success mutation applied, new state:', state);
        },
        loginFailure(state) {
            state.status.loggedIn = false;
            state.user = null;
        },
        logout(state) {
            state.status.loggedIn = false;
            state.user = null;
        },
        registerSuccess(state) {
            state.status.loggedIn = false;
        },
        registerFailure(state) {
            state.status.loggedIn = false;
        },
        refreshToken(state, accessToken) {
            state.status.loggedIn = true;
            state.user = { ...state.user, access: accessToken };
        },
        updateUser(state, userData) {
            state.user = { ...state.user, ...userData };

            // Update in storage too
            const storageKey = localStorage.getItem('user') ? 'localStorage' : 'sessionStorage';
            const storage = window[storageKey];
            if (storage) {
                const storedUser = JSON.parse(storage.getItem('user') || '{}');
                storage.setItem('user', JSON.stringify({ ...storedUser, ...userData }));
            }
        }
    }
}