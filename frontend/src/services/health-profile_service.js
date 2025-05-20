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
}

export default new HealthProfileService();