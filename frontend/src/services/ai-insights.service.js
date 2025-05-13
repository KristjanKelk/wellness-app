// src/services/ai-insights.service.js
import apiClient from './http.service';

/**
 * Service for AI insights generation and management
 */
class AIInsightsService {
    /**
     * Fetch AI insights for the current user
     * @returns {Promise} - Promise resolving to insights data
     */
    getInsights() {
        // Updated to match Django route prefix
        return apiClient
            .get('analytics/aiinsight/')
            .then(res => res.data);
    }

    /**
     * Generate new insights based on user data
     * @param {Object} userData - User health data
     * @returns {Promise} - Promise resolving to generated insights
     */
    generateInsights(userData) {
        // Updated to match Django route prefix including custom action
        return apiClient
            .post('analytics/aiinsight/generate/', userData)
            .then(res => res.data);
    }
}

export default new AIInsightsService();