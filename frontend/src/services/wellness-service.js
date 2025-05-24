// src/services/wellness.service.js

/**
 * Service for wellness-related calculations and utilities
 */
class WellnessService {
    /**
     * Calculate BMI based on height and weight
     * @param {number} heightCm - Height in centimeters
     * @param {number} weightKg - Weight in kilograms
     * @returns {number|null} - BMI value or null if inputs are invalid
     */
    calculateBMI(heightCm, weightKg) {
        if (!heightCm || !weightKg || heightCm <= 0 || weightKg <= 0) {
            return null;
        }

        const heightM = heightCm / 100;
        return weightKg / (heightM * heightM);
    }

    /**
     * Get BMI category based on BMI value
     * @param {number} bmi - BMI value
     * @returns {string} - BMI category
     */
    getBMICategory(bmi) {
        if (bmi === null || bmi === undefined) return '';

        if (bmi < 18.5) return 'Underweight';
        if (bmi < 25) return 'Normal Weight';
        if (bmi < 30) return 'Overweight';
        return 'Obese';
    }

    /**
     * Calculate BMI score component (0-100)
     * @param {number} bmi - BMI value
     * @returns {number} - Score from 0-100
     */
    calculateBMIScore(bmi) {
        if (!bmi) return 0;
        let score = 0;
        if (bmi >= 18.5 && bmi <= 25) {
            score = 100;
        } else if (bmi < 18.5) {
            score = 100 - (18.5 - bmi) * 10;
        } else {
            score = 100 - (bmi - 25) * 5;
        }
        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate activity score from profile (deprecated)
     * @param {string} activityLevel - Activity level from profile
     * @returns {number} - Score from 0-100
     */
    calculateActivityScore(activityLevel) {
        console.warn('Deprecated: use calculateActivityScoreFromActivities instead');
        const map = { sedentary: 20, light: 40, moderate: 70, active: 90, very_active: 100 };
        return map[activityLevel] ?? 50;
    }

    /**
     * Calculate activity score based on actual activity logs
     * @param {Array<Object>} activities - Array of activity objects { performed_at: ISOString, duration_minutes: number }
     * @returns {number} - Score from 0 to 100
     */
    calculateActivityScoreFromActivities(activities = []) {
        if (!Array.isArray(activities) || activities.length === 0) return 0;

        const now = new Date();
        const weekAgo = new Date(now);
        weekAgo.setDate(now.getDate() - 7);

        // Filter only last 7 days
        const recent = activities.filter(a => {
            const d = new Date(a.performed_at);
            return d >= weekAgo && d <= now;
        });

        // Count unique days
        const daysCount = new Set(recent.map(a => new Date(a.performed_at).toDateString())).size;
        const dayScore = Math.min(daysCount / 7, 1) * 100;

        // Sum durations
        const totalMin = recent.reduce((sum, a) => sum + (a.duration_minutes || 0), 0);
        const maxMin = 7 * 60;
        const durationScore = Math.min(totalMin / maxMin, 1) * 100;

        // Combine day and duration equally
        return Math.round((dayScore + durationScore) / 2);
    }

    /**
     * Calculate overall wellness score using activity logs
     * @param {number} bmiScore
     * @param {Array<Object>} activities
     * @param {number} progressScore
     * @param {number} habitsScore
     * @returns {number} - Overall wellness score (0-100)
     */
    calculateWellnessScoreFromActivities(bmiScore, activities, progressScore, habitsScore) {
        const activityScore = this.calculateActivityScoreFromActivities(activities);
        return this.calculateWellnessScore(bmiScore, activityScore, progressScore, habitsScore);
    }

    /**
     * Calculate wellness score based on components
     * @param {number} bmiScore
     * @param {number} activityScore
     * @param {number} progressScore
     * @param {number} habitsScore
     * @returns {number}
     */
    calculateWellnessScore(bmiScore, activityScore, progressScore, habitsScore) {
        return Math.round(
            (bmiScore * 0.3) +
            (activityScore * 0.3) +
            (progressScore * 0.2) +
            (habitsScore * 0.2)
        );
    }

    /**
     * Get wellness score category
     * @param {number} score - Wellness score (0-100)
     * @returns {string} - Category (excellent, good, fair, poor)
     */
    getScoreCategory(score) {
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'fair';
        return 'poor';
    }

    /**
     * Get activity level display name
     * @param {string} activityLevel - Activity level code
     * @returns {string} - Human readable activity level
     */
    getActivityLevelDisplay(activityLevel) {
        const activityMap = {
            sedentary: 'Sedentary',
            light: 'Lightly Active',
            moderate: 'Moderately Active',
            active: 'Active',
            very_active: 'Very Active'
        };
        return activityMap[activityLevel] || 'Unknown';
    }

    /**
     * Get activity level description
     * @param {string} activityLevel - Activity level code
     * @returns {string} - Description of activity level
     */
    getActivityDescription(activityLevel) {
        const descriptions = {
            sedentary: 'Little to no regular exercise',
            light: 'Light exercise 1-3 days per week',
            moderate: 'Moderate exercise 3-5 days per week',
            active: 'Hard exercise 6-7 days per week',
            very_active: 'Very hard exercise & physical job or twice daily training'
        };
        return descriptions[activityLevel] || '';
    }

    /**
     * Get suggestions based on activity level
     * @param {string} activityLevel - Activity level code
     * @returns {string[]} - Array of suggestions
     */
    getActivitySuggestions(activityLevel) {
        const suggestions = {
            sedentary: [
                'Start with a 10-minute daily walk',
                'Take breaks to stretch every hour',
                'Try using stairs instead of elevators'
            ],
            light: [
                'Aim for 20-30 minute walks 4-5 days/week',
                'Consider adding 1-2 strength sessions weekly',
                'Try a beginner yoga or flexibility routine'
            ],
            moderate: [
                'Increase intensity in 1-2 workouts per week',
                'Add variety with different exercise types',
                'Consider tracking heart rate during exercise'
            ],
            active: [
                'Focus on recovery between intense sessions',
                'Consider periodization in your training',
                'Add mobility work to prevent injuries'
            ],
            very_active: [
                'Ensure adequate recovery and sleep',
                'Consider professional guidance for programming',
                'Focus on nutrition to support your activity level'
            ]
        };
        return suggestions[activityLevel] || [];
    }

    /**
     * Get priority display name
     * @param {string} priority - Priority code (high, medium, low)
     * @returns {string} - Human readable priority name
     */
    getPriorityDisplay(priority) {
        const map = { high: 'High Priority', medium: 'Medium Priority', low: 'Low Priority' };
        return map[priority] || '';
    }

    /**
     * Calculate weight change evaluation based on goal
     * @param {number} change - Weight change value
     * @param {string} goal - Fitness goal
     * @returns {string} - Evaluation class (positive, negative, neutral)
     */
    evaluateWeightChange(change, goal) {
        if (change === 0) return 'neutral';
        if (goal === 'weight_loss') {
            return change < 0 ? 'positive' : 'negative';
        } else if (goal === 'muscle_gain') {
            return change > 0 ? 'positive' : 'negative';
        }
        return 'neutral';
    }
}

export default new WellnessService();