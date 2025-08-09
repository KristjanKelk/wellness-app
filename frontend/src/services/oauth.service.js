// src/services/oauth.service.js
import axios from 'axios';
import AuthService from './auth.service';

export const API_URL = (
  process.env.VUE_APP_API_URL ||
  'https://wellness-app-tx2c.onrender.com/api'
).replace(/\/+$/, '') + '/';

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
      sessionStorage.setItem('auth_in_progress', 'true');
      sessionStorage.setItem('oauth_provider', provider);

      const response = await axios.get(`${API_URL}oauth/${provider}/`, {
        withCredentials: true,
      });

      const { authorization_url, state } = response.data || {};

      if (authorization_url) {
        if (state) {
          localStorage.setItem('oauth_state', state);
        }
        // Redirect browser to provider's OAuth page
        window.location.href = authorization_url;
        return true;
      }

      console.error('Invalid OAuth response:', response.data);
      throw new Error(`Failed to start ${provider} authentication`);
    } catch (err) {
      console.error(`OAuth login error for ${provider}:`, err);
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.removeItem('oauth_provider');
      throw err;
    }
  }

  /** Redirect to Google OAuth */
  async loginWithGoogle() {
    return this.initiateOAuth('google');
  }

  /** Redirect to GitHub OAuth */
  async loginWithGitHub() {
    return this.initiateOAuth('github');
  }

  /**
   * Process OAuth callback
   * @param {URLSearchParams} queryParams - URL query parameters
   * @returns {Promise<Object>} user data (tokens, profile, etc)
   */
  async processCallback(queryParams) {
    try {
      const provider = sessionStorage.getItem('oauth_provider') || 'google';
      const code = queryParams.get('code');
      if (!code) {
        throw new Error('Missing authorization code in callback');
      }

      const returnedState = queryParams.get('state');
      const storedState = localStorage.getItem('oauth_state');
      if (storedState !== returnedState) {
        throw new Error('OAuth state mismatch – possible CSRF attack');
      }

      const response = await axios.post(
        `${API_URL}oauth/${provider}/`,
        { code, state: returnedState },
        { withCredentials: true }
      );

      const data = response.data || {};
      if (!data.access) {
        console.error('Invalid backend response:', response.data);
        throw new Error('Invalid authentication response from server');
      }

      // Store full user payload so flags are available
      AuthService.storeUser(data, true);

      // Cleanup
      localStorage.removeItem('oauth_state');
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.removeItem('oauth_provider');

      return data;
    } catch (err) {
      console.error('OAuth callback processing error:', err);
      localStorage.removeItem('oauth_state');
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.removeItem('oauth_provider');
      // Bubble up either backend detail or generic message
      throw new Error(
        err.response?.data?.detail || err.message || 'Authentication failed'
      );
    }
  }
}

export default new OAuthService();
