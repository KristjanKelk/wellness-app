// src/services/oauth.service.js
import axios from 'axios';
import AuthService from './auth.service';

const API_URL = 'http://localhost:8000/api/';

/**
 * Handles OAuth authentication operations
 */
class OAuthService {
  /**
   * Initiate OAuth flow for a provider
   * @param {string} provider - OAuth provider name (google, github)
   */
  async initiateOAuth(provider) {
    try {
      // Clear any previous OAuth data
      localStorage.removeItem('oauth_state');
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.setItem('auth_in_progress', 'true');
      sessionStorage.setItem('oauth_provider', provider);

      // Get authorization URL from our backend
      const response = await axios.get(`${API_URL}oauth/${provider}/`);

      if (response.data && response.data.authorization_url) {
        console.log(`Redirecting to ${provider} authorization URL`);

        // Store state parameter for CSRF protection
        if (response.data.state) {
          localStorage.setItem('oauth_state', response.data.state);
        }

        // Redirect to authorization page
        window.location.href = response.data.authorization_url;
        return true;
      } else {
        console.error('Invalid OAuth response:', response.data);
        throw new Error(`Failed to start ${provider} authentication`);
      }
    } catch (error) {
      console.error(`OAuth login error for ${provider}:`, error);
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.removeItem('oauth_provider');
      throw error;
    }
  }

  /**
   * Redirect to Google OAuth
   */
  async loginWithGoogle() {
    return this.initiateOAuth('google');
  }

  /**
   * Redirect to GitHub OAuth
   */
  async loginWithGitHub() {
    return this.initiateOAuth('github');
  }

  /**
   * Process OAuth callback
   * @param {URLSearchParams} queryParams - URL query parameters
   * @returns {Promise} Promise resolving to user data
   */
  async processCallback(queryParams) {
    try {
      // Get the provider from sessionStorage or default to 'google'
      const provider = sessionStorage.getItem('oauth_provider') || 'google';

      // Get authorization code
      const code = queryParams.get('code');
      if (!code) {
        throw new Error('Missing authorization code in callback');
      }

      // Get state and validate with stored state
      const state = queryParams.get('state');
      const storedState = localStorage.getItem('oauth_state');

      if (storedState && state !== storedState) {
        throw new Error('OAuth state mismatch - possible CSRF attack');
      }

      // Exchange code for tokens via our backend
      console.log(`Exchanging code for tokens via ${provider} endpoint...`);

      const response = await axios.post(`${API_URL}oauth/${provider}/`, {
        code,
        state
      });

      // Check if we have the expected data
      if (!response.data || !response.data.access) {
        console.error('Invalid backend response:', response.data);
        throw new Error('Invalid authentication response from server');
      }

      // Store user data
      AuthService.storeUser(response.data, true);

      // Clean up
      localStorage.removeItem('oauth_state');
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.removeItem('oauth_provider');

      return response.data;
    } catch (error) {
      console.error('OAuth callback processing error:', error);

      // Clean up
      localStorage.removeItem('oauth_state');
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.removeItem('oauth_provider');

      // Handle specific OAuth errors
      if (error.response && error.response.data) {
        console.log('Backend error response:', error.response.data);

        if (error.response.data.detail) {
          throw new Error(error.response.data.detail);
        }
      }

      // Generic error handling
      throw new Error(error.message || 'Authentication failed');
    }
  }
}

export default new OAuthService();