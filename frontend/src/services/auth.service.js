// src/services/auth.service.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';
const TOKEN_KEY = 'user';

/**
 * Handles authentication-related operations
 */
class AuthService {
  /**
   * Get storage method based on remember preference
   * @param {boolean} remember - Whether to use localStorage or sessionStorage
   * @returns {Storage} - Storage object
   */
  getStorage(remember = false) {
    return remember ? localStorage : sessionStorage;
  }

  /**
   * Get current user data from storage
   * @returns {Object|null} User data or null if not found
   */
  getCurrentUser() {
    const userStr = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch (e) {
      console.error('Error parsing user data:', e);
      return null;
    }
  }

  /**
   * Store user data in the appropriate storage
   * @param {Object} userData - User data including tokens
   * @param {boolean} remember - Whether to use localStorage
   */
  storeUser(userData, remember = false) {
    const storage = this.getStorage(remember);
    storage.setItem(TOKEN_KEY, JSON.stringify(userData));
  }

  /**
   * Remove user data from all storages
   */
  clearUser() {
    localStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TOKEN_KEY);
  }

  /**
   * Validate the current token
   * @returns {boolean} Whether token is valid
   */
  validateToken() {
    const userStr = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
    if (!userStr) return false;

    try {
      const user = JSON.parse(userStr);
      if (!user.access) return false;

      const parts = user.access.split('.');
      if (parts.length !== 3) return false;

      // Check if token is expired
      const payload = JSON.parse(atob(parts[1]));
      const now = Math.floor(Date.now() / 1000);

      // Make sure to return true if the token is NOT expired
      return !(payload.exp && payload.exp < now);
    } catch (e) {
      console.error('Error validating token:', e);
      return false;
    }
  }

  /**
   * Log in a user
   * @param {string} username - Username
   * @param {string} password - Password
   * @param {boolean} remember - Whether to remember user
   * @returns {Promise} Promise resolving to user data
   */
  async login(username, password, remember = false) {
    try {
      const response = await axios.post(API_URL + 'token/', { username, password });
      const userData = response.data;

      // If 2FA is not required, store user data
      if (!userData.two_factor_enabled) {
        this.storeUser(userData, remember);
      }

      return userData;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Verify two-factor authentication
   * @param {string} code - 2FA verification code
   * @param {Object} tempAuthData - Temporary auth data from login
   * @returns {Promise} Promise resolving to user data
   */
  async verifyTwoFactorLogin(code, tempAuthData) {
    try {
      // Make sure we have all required data
      if (!code || !tempAuthData || !tempAuthData.access) {
        return Promise.reject(new Error('Missing required 2FA verification data'));
      }

      const response = await axios.post(API_URL + 'token/2fa-verify/', {
        token: tempAuthData.access,
        code: code
      });

      if (response.data && response.data.access) {
        const userData = {
          ...tempAuthData,
          ...response.data,
          two_factor_verified: true
        };

        // Store the complete user data
        this.storeUser(userData, true);
        return userData;
      } else {
        console.error('Incomplete 2FA response:', response.data);
        return Promise.reject(new Error('Invalid 2FA verification response'));
      }
    } catch (error) {
      console.error('2FA verification error:', error);
      return Promise.reject(error);
    }
  }

  /**
   * Log out the current user
   */
  logout() {
    this.clearUser();
  }

  /**
   * Register a new user
   * @param {string} username - Username
   * @param {string} email - Email
   * @param {string} password - Password
   * @param {string} password2 - Password confirmation
   * @returns {Promise} Promise resolving to registration response
   */
  register(username, email, password, password2) {
    return axios.post(API_URL + 'register/', {
      username,
      email,
      password,
      password2
    });
  }

  /**
   * Refresh the access token
   * @returns {Promise} Promise resolving to new tokens
   */
  async refreshToken() {
    const user = this.getCurrentUser();

    if (!user || !user.refresh) {
      return Promise.reject('No refresh token available');
    }

    try {
      const response = await axios.post(API_URL + 'token/refresh/', {
        refresh: user.refresh
      });

      if (response.data.access) {
        const updatedUser = {
          ...user,
          access: response.data.access
        };

        // Update token in the same storage that had the user
        if (localStorage.getItem(TOKEN_KEY)) {
          localStorage.setItem(TOKEN_KEY, JSON.stringify(updatedUser));
        } else if (sessionStorage.getItem(TOKEN_KEY)) {
          sessionStorage.setItem(TOKEN_KEY, JSON.stringify(updatedUser));
        }

        return response.data;
      }

      return Promise.reject('Failed to refresh token');
    } catch (error) {
      console.error('Token refresh error:', error);
      throw error;
    }
  }
}

export default new AuthService();