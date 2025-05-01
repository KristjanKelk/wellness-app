// src/services/oauth.service.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

class OAuthService {
  /**
   * Redirect to Google OAuth
   */
  async loginWithGoogle() {
    try {
      localStorage.removeItem('oauth_state');
      sessionStorage.removeItem('auth_in_progress');
      sessionStorage.setItem('auth_in_progress', 'true');

      const response = await axios.get(`${API_URL}oauth/google/authorize/`);

      if (response.data && response.data.authorization_url) {
        console.log('Redirecting to Google authorization URL');

        // Store state parameter to prevent CSRF (if provided)
        if (response.data.state) {
          localStorage.setItem('oauth_state', response.data.state);
        }

        // Redirect to Google authorization page
        window.location.href = response.data.authorization_url;
        return true;
      } else {
        console.error('Invalid OAuth response:', response.data);
        throw new Error('Failed to start Google authentication');
      }
    } catch (error) {
      console.error('OAuth login error:', error);
      sessionStorage.removeItem('auth_in_progress');
      throw error;
    }
  }

  /**
   * Redirect to GitHub OAuth
   * This uses a direct window.location approach rather than axios
   * to avoid CORS issues with GitHub's OAuth flow
   */
  async loginWithGitHub() {
  try {
    localStorage.removeItem('oauth_state');
    sessionStorage.removeItem('auth_in_progress');
    sessionStorage.setItem('auth_in_progress', 'true');

    // Get the authorization URL from our backend
    const response = await axios.get(`${API_URL}oauth/github/authorize/`);

    if (response.data && response.data.authorization_url) {
      console.log('Redirecting to GitHub authorization URL');

      // Store state parameter to prevent CSRF (if provided)
      if (response.data.state) {
        localStorage.setItem('oauth_state', response.data.state);
      }

      // Redirect to GitHub authorization page
      window.location.href = response.data.authorization_url;
      return true;
    } else {
      console.error('Invalid OAuth response:', response.data);
      throw new Error('Failed to start GitHub authentication');
    }
  } catch (error) {
    console.error('GitHub OAuth login error:', error);
    sessionStorage.removeItem('auth_in_progress');
    throw error;
  }
}

  /**
   * Process OAuth callback
   * @param {URLSearchParams} queryParams - URL query parameters
   * @param {string} provider - OAuth provider name (default: 'google')
   * @returns {Promise} Promise resolving to user data
   */
  async processCallback(queryParams, provider = 'google') {
  try {
    // Log parameters for debugging
    console.log(`Processing ${provider} OAuth callback with params:`,
      Object.fromEntries(queryParams.entries()));

    // Get authorization code
    const code = queryParams.get('code');
    if (!code) {
      throw new Error('Missing authorization code in callback');
    }

    // Exchange code for tokens via our backend
    console.log(`Exchanging code for tokens via ${provider} endpoint...`);
    console.log(`Code: ${code.substring(0, 5)}...`); // Only log part of the code

    const response = await axios.post(`${API_URL}oauth/${provider}/callback/`, {
      code,
      state: queryParams.get('state')
    });

    // Check if we have the expected data
    if (!response.data || !response.data.access) {
      console.error('Invalid backend response:', response.data);
      throw new Error('Invalid authentication response from server');
    }

    // Store user data
    localStorage.setItem('user', JSON.stringify(response.data));

    return response.data;
  } catch (error) {
    console.error('OAuth callback processing error:', error);

      // Handle specific OAuth errors
      if (error.response && error.response.data) {
        console.log('Backend error response:', error.response.data);

        // Handle invalid_grant specifically
        if (error.response.data.detail &&
            error.response.data.detail.includes('invalid_grant')) {
          throw new Error(
            'Authentication code expired or already used. Please try logging in again.'
          );
        }

        // Get detailed error message
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