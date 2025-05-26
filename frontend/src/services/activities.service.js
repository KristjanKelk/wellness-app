// src/services/activities.service.js
import apiClient from './http.service';

/**
 * Service for managing user activities
 */
class ActivitiesService {
    /**
     * Get all activities for the current user
     * @param {Object} params - Query parameters for filtering
     * @returns {Promise} - Promise resolving to activities data
     */
    getAllActivities(params = {}) {
        return apiClient.get('activities/', { params });
    }

    /**
     * Get activities filtered by date range
     * @param {string} startDate - Start date (YYYY-MM-DD format)
     * @param {string} endDate - End date (YYYY-MM-DD format)
     * @returns {Promise} - Promise resolving to filtered activities
     */
    getActivitiesByDateRange(startDate, endDate) {
        return apiClient.get('activities/', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
    }

    /**
     * Get activities by type
     * @param {string} activityType - Type of activity to filter by
     * @returns {Promise} - Promise resolving to filtered activities
     */
    getActivitiesByType(activityType) {
        return apiClient.get('activities/', {
            params: {
                activity_type: activityType
            }
        });
    }

    /**
     * Get a single activity by ID
     * @param {number} activityId - ID of the activity
     * @returns {Promise} - Promise resolving to activity data
     */
    getActivity(activityId) {
        return apiClient.get(`activities/${activityId}/`);
    }

    /**
     * Create a new activity
     * @param {Object} activityData - Activity data to create
     * @returns {Promise} - Promise resolving to created activity
     */
    createActivity(activityData) {
        return apiClient.post('activities/', activityData);
    }

    /**
     * Update an existing activity
     * @param {number} activityId - ID of the activity to update
     * @param {Object} activityData - Updated activity data
     * @returns {Promise} - Promise resolving to updated activity
     */
    updateActivity(activityId, activityData) {
        return apiClient.put(`activities/${activityId}/`, activityData);
    }

    /**
     * Delete an activity
     * @param {number} activityId - ID of the activity to delete
     * @returns {Promise} - Promise resolving to deletion status
     */
    deleteActivity(activityId) {
        return apiClient.delete(`activities/${activityId}/`);
    }

    /**
     * Get activity summary statistics
     * @returns {Promise} - Promise resolving to summary data
     */
    getActivitySummary() {
        return apiClient.get('activities/summary/');
    }

    /**
     * Get activities grouped by type
     * @returns {Promise} - Promise resolving to grouped activities
     */
    getActivitiesByTypeGrouped() {
        return apiClient.get('activities/by_type/');
    }

    /**
     * Get recent activities (last 10)
     * @returns {Promise} - Promise resolving to recent activities
     */
    getRecentActivities() {
        return apiClient.get('activities/recent/');
    }

    /**
     * Get calendar data for activities
     * @param {string} startDate - Start date for calendar view
     * @param {string} endDate - End date for calendar view
     * @returns {Promise} - Promise resolving to calendar data
     */
    getCalendarData(startDate, endDate) {
        return apiClient.get('activities/calendar_data/', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
    }

    /**
     * Calculate estimated calories for an activity
     * @param {string} activityType - Type of activity
     * @param {number} durationMinutes - Duration in minutes
     * @param {number} weight - User weight in kg (optional)
     * @returns {number} - Estimated calories burned
     */
    estimateCalories(activityType, durationMinutes, weight = 70) {
        // MET (Metabolic Equivalent of Task) values for activities
        const metValues = {
            cardio: 7.0,      // Running at moderate pace
            strength: 6.0,    // Weight lifting
            flexibility: 2.5, // Stretching
            sports: 8.0,      // General sports
            hiit: 8.0,        // High-intensity interval training
            yoga: 2.5,        // Hatha yoga
            other: 4.0        // Moderate activity
        };

        const met = metValues[activityType] || 4.0;

        // Formula: Calories = MET * weight(kg) * time(hours)
        const caloriesBurned = met * weight * (durationMinutes / 60);

        return Math.round(caloriesBurned);
    }

    /**
     * Get activity statistics for a specific period
     * @param {string} period - Period to get stats for ('week', 'month', 'year')
     * @returns {Promise} - Promise resolving to statistics
     */
    async getActivityStats(period = 'week') {
        const now = new Date();
        let startDate = new Date();

        switch (period) {
            case 'week':
                startDate.setDate(now.getDate() - 7);
                break;
            case 'month':
                startDate.setMonth(now.getMonth() - 1);
                break;
            case 'year':
                startDate.setFullYear(now.getFullYear() - 1);
                break;
        }

        const response = await this.getActivitiesByDateRange(
            startDate.toISOString().split('T')[0],
            now.toISOString().split('T')[0]
        );

        const activities = response.data;

        // Calculate statistics
        return {
            totalActivities: activities.length,
            totalDuration: activities.reduce((sum, a) => sum + a.duration_minutes, 0),
            totalDistance: activities.reduce((sum, a) => sum + (a.distance_km || 0), 0),
            totalCalories: activities.reduce((sum, a) => sum + (a.calories_burned || 0), 0),
            activeDays: this.calculateActiveDays(activities),
            activityDistribution: this.calculateActivityDistribution(activities)
        };
    }

    /**
     * Calculate number of active days from activities
     * @param {Array} activities - Array of activity objects
     * @returns {number} - Number of unique active days
     */
    calculateActiveDays(activities) {
        const uniqueDays = new Set(
            activities.map(activity =>
                new Date(activity.performed_at).toLocaleDateString()
            )
        );
        return uniqueDays.size;
    }

    /**
     * Calculate distribution of activities by type
     * @param {Array} activities - Array of activity objects
     * @returns {Object} - Distribution of activities by type
     */
    calculateActivityDistribution(activities) {
        const distribution = {};

        activities.forEach(activity => {
            if (!distribution[activity.activity_type]) {
                distribution[activity.activity_type] = 0;
            }
            distribution[activity.activity_type]++;
        });

        return distribution;
    }
}

export default new ActivitiesService();