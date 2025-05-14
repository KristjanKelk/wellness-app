// src/services/analytics.service.js
import apiClient from './http.service';

/**
 * Service for analytics-related data fetching and operations
 */
class AnalyticsService {
    /**
     * Get wellness scores for the current user
     * @returns {Promise} - Promise resolving to wellness scores data
     */
    getWellnessScores() {
        return apiClient.get('wellness-scores/');
    }

    /**
     * Calculate a new wellness score based on current health profile
     * @returns {Promise} - Promise resolving to the new wellness score
     */
    calculateWellnessScore() {
        return apiClient.post('wellness-scores/calculate/');
    }

    /**
     * Get AI-generated insights based on user health data
     * @returns {Promise} - Promise resolving to insights data
     */
    getInsights() {
        return apiClient.get('insights/');
    }

    /**
     * Generate new AI insights based on current health data
     * @returns {Promise} - Promise resolving to generated insights
     */
    generateInsights() {
        return apiClient.post('insights/generate/');
    }

    /**
     * Get progress metrics for the current user
     * This would include milestone tracking, goal progress, etc.
     * @returns {Promise} - Promise resolving to progress metrics data
     */
    getProgressMetrics() {
        return apiClient.get('analytics/progress-metrics/');
    }

    /**
     * Export health data in CSV format
     * @param {Object} options - Export options (date range, metrics to include)
     * @returns {Promise} - Promise resolving to the exported data
     */
    exportHealthData(options = {}) {
        return apiClient.post('analytics/export/', options, {
            responseType: 'blob'
        });
    }

    /**
     * Get activity trends over time
     * @param {Object} params - Query parameters for filtering activity data
     * @returns {Promise} - Promise resolving to activity trend data
     */
    getActivityTrends(params = {}) {
        return apiClient.get('analytics/activity-trends/', { params });
    }

    /**
     * Get historical wellness scores with filtering options
     * @param {Object} params - Query parameters (timeRange, startDate, endDate)
     * @returns {Promise} - Promise resolving to filtered wellness scores
     */
    getWellnessScoreHistory(params = {}) {
        return apiClient.get('analytics/wellness-history/', { params });
    }

    /**
     * Track a milestone achievement
     * @param {Object} milestoneData - Data about the achieved milestone
     * @returns {Promise} - Promise resolving to the created milestone
     */
    trackMilestone(milestoneData) {
        return apiClient.post('analytics/milestones/', milestoneData);
    }
    

    /**
     * Get all milestones for the current user
     * @returns {Promise} - Promise resolving to milestones data
     */
    getMilestones() {
        return apiClient.get('analytics/milestones/');
    }
}

export default new AnalyticsService();