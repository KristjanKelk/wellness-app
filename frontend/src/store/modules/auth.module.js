// src/store/modules/auth.module.js
import AuthService from '../../services/auth.service';
import OAuthService from '../../services/oauth.service';

const initialState = (() => {
  if (AuthService.validateToken()) {
    return {
      status: { loggedIn: true },
      user: AuthService.getCurrentUser()
    };
  }
  return {
    status: { loggedIn: false },
    user: null
  };
})();

export default {
  namespaced: true,
  state: initialState,
  getters: {
    isLoggedIn: state => state.status.loggedIn,
    currentUser: state => state.user,
    isEmailVerified: state => state.user?.email_verified || false,
    hasTwoFactorEnabled: state => state.user?.two_factor_enabled || false
  },

  actions: {
    /**
     * Login action
     */
    login({ commit }, { username, password, remember }) {
      return AuthService.login(username, password, remember)
        .then(userData => {
          if (!userData.two_factor_enabled) {
            commit('loginSuccess', userData);
          }
          return userData;
        })
        .catch(error => {
          commit('loginFailure');
          return Promise.reject(error);
        });
    },

    /**
     * Verify 2FA code during login
     */
    verifyTwoFactor({ commit }, { code, tempAuthData }) {
      return AuthService.verifyTwoFactorLogin(code, tempAuthData)
        .then(userData => {
          commit('loginSuccess', userData);
          return userData;
        })
        .catch(error => {
          return Promise.reject(error);
        });
    },

    /**
     * OAuth login actions
     */
    loginWithGoogle() {
      return OAuthService.loginWithGoogle();
    },

    loginWithGitHub() {
      return OAuthService.loginWithGitHub();
    },

    /**
     * Logout action
     */
    logout({ commit }) {
      AuthService.logout();
      commit('logout');
    },

    /**
     * User registration
     */
    register({ commit }, { username, email, password, password2 }) {
      return AuthService.register(username, email, password, password2)
        .then(response => {
          commit('registerSuccess');
          return response.data;
        })
        .catch(error => {
          commit('registerFailure');
          return Promise.reject(error);
        });
    },

    /**
     * Update the access token
     */
    refreshToken({ commit }, accessToken) {
      commit('refreshToken', accessToken);
    },

    /**
     * Check authentication state
     */
    checkAuth({ commit, state }) {
      if (!state.status.loggedIn) {
        // Check if we have a valid token in storage
        if (AuthService.validateToken()) {
          const userData = AuthService.getCurrentUser();
          if (userData) {
            commit('loginSuccess', userData);
            return Promise.resolve(userData);
          }
        }
        return Promise.reject(new Error('Not authenticated'));
      }

      if (!AuthService.validateToken()) {
        return AuthService.refreshToken()
          .then(response => {
            if (response?.access) {
              const user = { ...state.user, access: response.access };
              commit('loginSuccess', user);
              return user;
            } else {
              commit('logout');
              return Promise.reject(new Error('Failed to refresh token'));
            }
          })
          .catch(error => {
            commit('logout');
            return Promise.reject(error);
          });
      }

      return Promise.resolve(state.user);
    },
  },

  mutations: {
    loginSuccess(state, user) {
      state.status.loggedIn = true;
      state.user = user;
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
      if (state.user) {
        state.user = { ...state.user, access: accessToken };
      }
    },
    updateUser(state, userData) {
      if (state.user) {
        state.user = { ...state.user, ...userData };

        if (localStorage.getItem('user')) {
          const storedUser = JSON.parse(localStorage.getItem('user'));
          localStorage.setItem('user', JSON.stringify({ ...storedUser, ...userData }));
        } else if (sessionStorage.getItem('user')) {
          const storedUser = JSON.parse(sessionStorage.getItem('user'));
          sessionStorage.setItem('user', JSON.stringify({ ...storedUser, ...userData }));
        }
      }
    }
  }
};