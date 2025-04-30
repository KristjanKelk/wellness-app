// src/services/oauth.service.js

/**
 * Service for OAuth authentication methods
 */
class OauthService {
  /**
   * Initiate Google OAuth login
   */
  loginWithGoogle() {
    window.location.href = 'http://localhost:8000/api/auth/google/';
  }

  /**
   * Initiate GitHub OAuth login
   */
  loginWithGitHub() {
    window.location.href = 'http://localhost:8000/api/auth/github/';
  }

  /**
   * Process OAuth callback response
   * @param {Object} urlParams - URL parameters from callback
   * @returns {Promise} Promise resolving to user data
   */
  processCallback(urlParams) {
    const tokens = urlParams.get('tokens');

    if (tokens) {
      try {
        const tokenData = JSON.parse(tokens);
        return Promise.resolve(tokenData);
      } catch (error) {
        console.error('Error parsing token data:', error);
        return Promise.reject(error);
      }
    }

    const error = urlParams.get('error');
    if (error) {
      return Promise.reject(new Error(error));
    }

    return Promise.reject(new Error('Invalid callback response'));
  }
}

export default new OauthService();