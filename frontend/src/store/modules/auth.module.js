// src/store/auth.module.js
import AuthService from '../../services/auth.services'

// Check if the token in localStorage is still valid
const validateToken = () => {
    const user = JSON.parse(localStorage.getItem('user'))
    if (!user) return false

    // Check if token exists
    if (!user.access) return false

    try {
        // Simple check if it looks like a JWT token
        const parts = user.access.split('.')
        if (parts.length !== 3) return false

        return true
    } catch (e) {
        return false
    }
}

const initialState = validateToken()
    ? { status: { loggedIn: true }, user: JSON.parse(localStorage.getItem('user')) }
    : { status: { loggedIn: false }, user: null }

export default {
    namespaced: true,
    state: initialState,
    actions: {
        login({ commit }, user) {
            return AuthService.login(user.username, user.password).then(
                user => {
                    commit('loginSuccess', user)
                    return Promise.resolve(user)
                },
                error => {
                    commit('loginFailure')
                    return Promise.reject(error)
                }
            )
        },
        logout({ commit }) {
            AuthService.logout()
            commit('logout')
        },
        register({ commit }, user) {
            return AuthService.register(user.username, user.email, user.password, user.password2).then(
                response => {
                    commit('registerSuccess')
                    return Promise.resolve(response.data)
                },
                error => {
                    commit('registerFailure')
                    return Promise.reject(error)
                }
            )
        },
        refreshToken({ commit }, accessToken) {
            commit('refreshToken', accessToken)
        }
    },
    mutations: {
        loginSuccess(state, user) {
            state.status.loggedIn = true
            state.user = user
        },
        loginFailure(state) {
            state.status.loggedIn = false
            state.user = null
        },
        logout(state) {
            state.status.loggedIn = false
            state.user = null
        },
        registerSuccess(state) {
            state.status.loggedIn = false
        },
        registerFailure(state) {
            state.status.loggedIn = false
        },
        refreshToken(state, accessToken) {
            state.status.loggedIn = true
            state.user = { ...state.user, accessToken: accessToken }
        }
    }
}