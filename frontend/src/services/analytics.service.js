// src/services/analytics.service.js - Enhanced Version
import apiClient from './http.service';

/**
 * Service for analytics-related data fetching and operations
 */
class AnalyticsService {
    /**
     * Get wellness scores for the current user
     * @param {Object} params - Query parameters for filtering
     * @returns {Promise} - Promise resolving to wellness scores data
     */
    getWellnessScores(params = {}) {
        return apiClient.get('analytics/wellness-scores/', { params });
    }

    /**
     * Calculate a new wellness score based on current health profile
     * @param {Object} additionalData - Additional data for calculation (e.g., weekly_activity_days)
     * @returns {Promise} - Promise resolving to the new wellness score with breakdown
     */
    calculateWellnessScore(additionalData = {}) {
        return apiClient.post('analytics/wellness-score/calculate/', additionalData);
    }

    /**
     * Get the latest wellness score with detailed breakdown
     * @returns {Promise} - Promise resolving to latest wellness score
     */
    getLatestWellnessScore() {
        return apiClient.get('analytics/wellness-score/latest/');
    }

    /**
     * Get wellness score trends over time
     * @param {number} days - Number of days to look back (default: 30)
     * @returns {Promise} - Promise resolving to trend data
     */
    getWellnessScoreTrends(days = 30) {
        return apiClient.get('analytics/wellness-score/trends/', {
            params: { days }
        });
    }

    /**
     * Get AI-generated insights based on user health data
     * @returns {Promise} - Promise resolving to insights data
     */
    getInsights() {
        return apiClient.get('analytics/aiinsight/');
    }

    /**
     * Generate new AI insights based on current health data
     * @param {Object} userData - User health data for context
     * @param {boolean} force - Force regeneration even if daily limit reached
     * @returns {Promise} - Promise resolving to generated insights with metadata
     */
    generateInsights(userData = {}, force = false) {
        const url = force ? 'analytics/aiinsight/generate/?force=true' : 'analytics/aiinsight/generate/';
        return apiClient.post(url, userData);
    }

    /**
     * Get all milestones for the current user
     * @param {Object} params - Query parameters (days, milestone_type, etc.)
     * @returns {Promise} - Promise resolving to milestones data
     */
    getMilestones(params = {}) {
        return apiClient.get('analytics/milestones/', { params });
    }

    /**
     * Get recent milestones within specified timeframe
     * @param {number} days - Number of days to look back (default: 30)
     * @returns {Promise} - Promise resolving to recent milestones
     */
    getRecentMilestones(days = 30) {
        return apiClient.get('analytics/milestones/recent/', {
            params: { days }
        });
    }

    /**
     * Get milestone summary statistics
     * @returns {Promise} - Promise resolving to milestone summary
     */
    getMilestoneSummary() {
        return apiClient.get('analytics/milestones/summary/');
    }

    /**
     * Track a habit streak and check for milestones
     * @param {string} habitName - Name of the habit
     * @param {number} streakDays - Current streak in days
     * @returns {Promise} - Promise resolving to milestone if achieved
     */
    trackHabitStreak(habitName, streakDays) {
        return apiClient.post('analytics/milestones/track_habit/', {
            habit_name: habitName,
            streak_days: streakDays
        });
    }

    /**
     * Get progress metrics for the current user
     * This includes milestone tracking, goal progress, etc.
     * @param {Object} params - Query parameters for filtering
     * @returns {Promise} - Promise resolving to progress metrics data
     */
    getProgressMetrics(params = {}) {
        return apiClient.get('analytics/progress-metrics/', { params });
    }

    /**
     * Export health data in various formats
     * @param {Object} options - Export options (date range, metrics to include, format)
     * @returns {Promise} - Promise resolving to the exported data
     */
    exportHealthData(options = {}) {
        return apiClient.post('analytics/export/', options, {
            responseType: options.format === 'csv' ? 'blob' : 'json'
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
     * Get comprehensive dashboard analytics
     * Combines multiple analytics calls for dashboard display
     * @returns {Promise} - Promise resolving to combined analytics data
     */
    async getDashboardAnalytics() {
        try {
            const [
                latestScore,
                recentMilestones,
                milestoneSummary,
                insights
            ] = await Promise.allSettled([
                this.getLatestWellnessScore(),
                this.getRecentMilestones(30),
                this.getMilestoneSummary(),
                this.getInsights()
            ]);

            return {
                wellnessScore: latestScore.status === 'fulfilled' ? latestScore.value.data : null,
                milestones: recentMilestones.status === 'fulfilled' ? recentMilestones.value.data : [],
                milestoneSummary: milestoneSummary.status === 'fulfilled' ? milestoneSummary.value.data : null,
                insights: insights.status === 'fulfilled' ? insights.value.data : []
            };
        } catch (error) {
            console.error('Error fetching dashboard analytics:', error);
            throw error;
        }
    }

    /**
     * Calculate and check for new milestones after profile updates
     * @param {Object} profileData - Updated profile data
     * @returns {Promise} - Promise resolving to any new milestones achieved
     */
    async checkForNewMilestones(profileData = {}) {
        try {
            // Trigger wellness score calculation which checks for milestones
            const scoreResponse = await this.calculateWellnessScore(profileData);

            // Return any milestones that were achieved
            return scoreResponse.data?.milestones_achieved || [];
        } catch (error) {
            console.error('Error checking for milestones:', error);
            return [];
        }
    }

    /**
     * Get wellness score component explanations
     * @returns {Object} - Explanations for each wellness score component
     */
    getWellnessScoreExplanations() {
        return {
            bmi_score: {
                name: "BMI Score",
                weight: 25,
                description: "Based on your Body Mass Index relative to healthy ranges",
                optimal: "BMI between 18.5-24.9 for maximum points"
            },
            activity_score: {
                name: "Activity Score",
                weight: 25,
                description: "Based on your logged activities and declared activity level",
                optimal: "Regular activities logged with good variety and consistency"
            },
            progress_score: {
                name: "Progress Score",
                weight: 15,
                description: "Based on milestone achievements and goal progress",
                optimal: "Regular milestones and steady progress toward goals"
            },
            habits_score: {
                name: "Habits Score",
                weight: 15,
                description: "Based on consistency in logging and profile completeness",
                optimal: "Regular weight logging and complete health profile"
            },
            nutrition_score: {
                name: "Nutrition Score",
                weight: 20,
                description: "Based on nutrition profile setup, goal adherence, and logging consistency",
                optimal: "Complete nutrition profile with regular food logging and meeting nutrition goals"
            }
        };
    }

    /**
     * Format wellness score for display
     * @param {Object} scoreData - Raw score data from API
     * @returns {Object} - Formatted score data for UI
     */
    formatWellnessScore(scoreData) {
        if (!scoreData) return null;

        const explanations = this.getWellnessScoreExplanations();

        return {
            total: Math.round(scoreData.total_score || 0),
            components: {
                bmi: {
                    score: Math.round(scoreData.bmi_score || 0),
                    points: Math.round((scoreData.bmi_score || 0) * 0.25),
                    ...explanations.bmi_score
                },
                activity: {
                    score: Math.round(scoreData.activity_score || 0),
                    points: Math.round((scoreData.activity_score || 0) * 0.25),
                    ...explanations.activity_score
                },
                progress: {
                    score: Math.round(scoreData.progress_score || 0),
                    points: Math.round((scoreData.progress_score || 0) * 0.15),
                    ...explanations.progress_score
                },
                habits: {
                    score: Math.round(scoreData.habits_score || 0),
                    points: Math.round((scoreData.habits_score || 0) * 0.15),
                    ...explanations.habits_score
                },
                nutrition: {
                    score: Math.round(scoreData.nutrition_score || 0),
                    points: Math.round((scoreData.nutrition_score || 0) * 0.20),
                    ...explanations.nutrition_score
                }
            },
            breakdown: scoreData.score_breakdown || null,
            lastUpdated: scoreData.created_at || new Date().toISOString()
        };
    }
}

export default new AnalyticsService();