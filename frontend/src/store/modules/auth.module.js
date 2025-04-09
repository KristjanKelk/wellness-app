// src/store/modules/auth.module.js
import AuthService from '../../services/auth.services'

// Check if the token in localStorage is still valid
const validateToken = () => {
    const userStr = localStorage.getItem('user');
    if (!userStr) return false;

    try {
        const user = JSON.parse(userStr);
        if (!user.access) return false;

        const parts = user.access.split('.');
        if (parts.length !== 3) return false;

        return true;
    } catch (e) {
        console.error('Error validating token:', e);
        return false;
    }
}

const userStr = localStorage.getItem('user');
const initialState = validateToken()
    ? { status: { loggedIn: true }, user: JSON.parse(userStr) }
    : { status: { loggedIn: false }, user: null };
console.log('Auth module initial state:', initialState);

export default {
    namespaced: true,
    state: initialState,
    actions: {
        login({ commit }, user) {
            return AuthService.login(user.username, user.password).then(
                userData => {
                    commit('loginSuccess', userData);
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
            state.user = { ...state.user, accessToken: accessToken };
        }
    }
}