// src/utils/oauth-debug.js

/**
 * Utility functions for debugging OAuth flows
 */
export const OAuthDebug = {
  /**
   * Log OAuth response information
   * @param {URLSearchParams} params - URL query parameters
   */
  logAuthResponse(params) {
    const debugInfo = {
      hasCode: params.has('code'),
      codeLength: params.get('code')?.length || 0,
      hasState: params.has('state'),
      stateValue: params.get('state'),
      hasError: params.has('error'),
      errorValue: params.get('error'),
      hasErrorDescription: params.has('error_description'),
      errorDescription: params.get('error_description'),
      allParams: Object.fromEntries(params.entries())
    };

    // Remove sensitive data for logging
    if (debugInfo.allParams.code) {
      debugInfo.allParams.code = `${debugInfo.allParams.code.substring(0, 10)}... [truncated]`;
    }

    return debugInfo;
  },

  /**
   * Validate OAuth configuration
   * @returns {Object} - Validation results
   */
  validateConfig() {
    // Check for required environment variables
    const results = {
      hasGoogleClientId: !!process.env.VUE_APP_GOOGLE_CLIENT_ID,
      redirectUriConfigured: true, // Assume true, check from logs
      routeConfigured: true, // Assume true, check from router
      issues: []
    };

    if (!results.hasGoogleClientId) {
      results.issues.push('Google Client ID not configured in environment variables');
    }

    // Do a rudimentary check that Axios is configured properly
    try {
      const axios = require('axios');
      results.axiosConfigured = !!axios.defaults.baseURL;
      if (!results.axiosConfigured) {
        results.issues.push('Axios base URL not configured');
      }
    } catch (e) {
      results.axiosConfigured = false;
      results.issues.push('Error loading Axios configuration');
    }

    console.log('OAuth Configuration Validation:', results);
    return results;
  },

  /**
   * Check browser storage for OAuth-related items
   */
  checkStorage() {
    const storage = {
      localStorage: {
        user: localStorage.getItem('user') ? 'Present' : 'Not present',
        oauth_state: localStorage.getItem('oauth_state')
      },
      sessionStorage: {
        auth_in_progress: sessionStorage.getItem('auth_in_progress')
      }
    };

    return storage;
  }
};

export default OAuthDebug;