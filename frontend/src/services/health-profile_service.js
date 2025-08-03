// src/services/health-profile_service.js
import apiClient from './http.service';

class HealthProfileService {
    /**
     * Get the current user's health profile
     * @returns {Promise} - Promise resolving to health profile data
     */
    getHealthProfile() {
        return apiClient.get('health-profiles/my_profile/');
    }

    /**
     * Get the current user's health profile (alias for getHealthProfile)
     * @returns {Promise} - Promise resolving to health profile data
     */
    getProfile() {
        return this.getHealthProfile();
    }

    /**
     * Update the current user's health profile
     * @param {Object} profileData - Health profile data to update
     * @returns {Promise} - Promise resolving to updated profile data
     */
    updateHealthProfile(profileData) {
        return apiClient.put('health-profiles/my_profile/', profileData);
    }

    /**
     * Create a new health profile
     * @param {Object} profileData - Health profile data
     * @returns {Promise} - Promise resolving to created profile data
     */
    createHealthProfile(profileData) {
        return apiClient.post('health-profiles/', profileData);
    }

    /**
     * Add a new weight entry
     * @param {number} weight - Weight in kg
     * @returns {Promise} - Promise resolving to created weight entry
     */
    addWeightEntry(weight) {
        return apiClient.post('weight-history/', { weight_kg: weight });
    }

    /**
     * Get all weight history entries
     * @returns {Promise} - Promise resolving to weight history data
     */
    getWeightHistory() {
        return apiClient.get('weight-history/');
    }

    /**
     * Get weight history filtered by date range
     * @param {Object} dateRange - Date range filter parameters
     * @param {string} dateRange.start - Start date (ISO format)
     * @param {string} dateRange.end - End date (ISO format)
     * @returns {Promise} - Promise resolving to filtered weight history data
     */
    getWeightHistoryByDateRange(dateRange) {
        return apiClient.get('weight-history/', {
            params: {
                start_date: dateRange.start,
                end_date: dateRange.end
            }
        });
    }

    /**
     * Get weight history with weekly aggregation
     * @returns {Promise} - Promise resolving to weekly aggregated weight data
     */
    getWeeklyWeightSummary() {
        return apiClient.get('weight-history/weekly_summary/');
    }

    /**
     * Get weight history with monthly aggregation
     * @returns {Promise} - Promise resolving to monthly aggregated weight data
     */
    getMonthlyWeightSummary() {
        return apiClient.get('weight-history/monthly_summary/');
    }

    /**
     * Delete a weight entry
     * @param {number} entryId - ID of the weight entry to delete
     * @returns {Promise} - Promise resolving to deletion status
     */
    deleteWeightEntry(entryId) {
        return apiClient.delete(`weight-history/${entryId}/`);
    }

    // Nutrition Profile Methods

    /**
     * Get the current user's nutrition profile
     * @returns {Promise} - Promise resolving to nutrition profile data
     */
    getNutritionProfile() {
        return apiClient.get('meal-planning/api/nutrition-profile/my_profile/');
    }

    /**
     * Update the current user's nutrition profile
     * @param {Object} profileData - Nutrition profile data to update
     * @returns {Promise} - Promise resolving to updated nutrition profile data
     */
    updateNutritionProfile(profileData) {
        return apiClient.put('meal-planning/api/nutrition-profile/my_profile/', profileData);
    }

    /**
     * Create a new nutrition profile
     * @param {Object} profileData - Nutrition profile data
     * @returns {Promise} - Promise resolving to created nutrition profile data
     */
    createNutritionProfile(profileData) {
        return apiClient.post('meal-planning/api/nutrition-profile/', profileData);
    }

    // Nutrition Log Methods

    /**
     * Get nutrition log for a specific date
     * @param {string} date - Date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to nutrition log data
     */
    getNutritionLog(date) {
        return apiClient.get(`meal-planning/api/nutrition-logs/${date}/`);
    }

    /**
     * Get nutrition logs for a date range
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {string} endDate - End date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to nutrition logs data
     */
    getNutritionLogs(startDate, endDate) {
        return apiClient.get('meal-planning/api/nutrition-logs/', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
    }

    /**
     * Create or update nutrition log for a specific date
     * @param {string} date - Date in YYYY-MM-DD format
     * @param {Object} logData - Nutrition log data
     * @returns {Promise} - Promise resolving to created/updated nutrition log data
     */
    saveNutritionLog(date, logData) {
        return apiClient.post(`meal-planning/api/nutrition-logs/${date}/`, logData);
    }

    /**
     * Update nutrition log for a specific date
     * @param {string} date - Date in YYYY-MM-DD format
     * @param {Object} logData - Nutrition log data to update
     * @returns {Promise} - Promise resolving to updated nutrition log data
     */
    updateNutritionLog(date, logData) {
        return apiClient.put(`meal-planning/api/nutrition-logs/${date}/`, logData);
    }

    /**
     * Delete nutrition log for a specific date
     * @param {string} date - Date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to deletion status
     */
    deleteNutritionLog(date) {
        return apiClient.delete(`meal-planning/api/nutrition-logs/${date}/`);
    }

    // Progress Tracking Methods

    /**
     * Get nutrition progress summary for a date range
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {string} endDate - End date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to progress summary data
     */
    getNutritionProgressSummary(startDate, endDate) {
        return apiClient.get('meal-planning/api/nutrition-logs/progress_summary/', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
    }

    /**
     * Get weekly nutrition averages
     * @param {string} weekStart - Week start date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to weekly averages data
     */
    getWeeklyNutritionAverages(weekStart) {
        return apiClient.get('meal-planning/api/nutrition-logs/weekly_averages/', {
            params: {
                week_start: weekStart
            }
        });
    }

    /**
     * Get nutrition goal achievement statistics
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {string} endDate - End date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to goal achievement statistics
     */
    getNutritionGoalStats(startDate, endDate) {
        return apiClient.get('meal-planning/api/nutrition-logs/goal_stats/', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
    }

    /**
     * Get nutrition trends analysis
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {string} endDate - End date in YYYY-MM-DD format
     * @param {string} metric - Metric to analyze (calories, protein, carbs, fat)
     * @returns {Promise} - Promise resolving to trend analysis data
     */
    getNutritionTrends(startDate, endDate, metric = 'calories') {
        return apiClient.get('meal-planning/api/nutrition-logs/trends/', {
            params: {
                start_date: startDate,
                end_date: endDate,
                metric: metric
            }
        });
    }

    // Activity Methods (if needed for integration)

    /**
     * Get activity history
     * @returns {Promise} - Promise resolving to activity history data
     */
    getActivityHistory() {
        return apiClient.get('health-profiles/activities/');
    }

    /**
     * Add new activity entry
     * @param {Object} activityData - Activity data
     * @returns {Promise} - Promise resolving to created activity entry
     */
    addActivity(activityData) {
        return apiClient.post('health-profiles/activities/', activityData);
    }

    /**
     * Get activities for a date range
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {string} endDate - End date in YYYY-MM-DD format
     * @returns {Promise} - Promise resolving to filtered activities data
     */
    getActivitiesByDateRange(startDate, endDate) {
        return apiClient.get('health-profiles/activities/', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
    }
}

export default new HealthProfileService();