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
            // Normal weight
            score = 100;
        } else if (bmi < 18.5) {
            // Underweight
            score = 100 - (18.5 - bmi) * 10;
        } else {
            // Overweight/obese
            score = 100 - (bmi - 25) * 5;
        }
        return Math.max(0, Math.min(100, score));
    }

    /**
     * Calculate activity score component (0-100)
     * @param {string} activityLevel - Activity level from profile
     * @returns {number} - Score from 0-100
     */
    calculateActivityScore(activityLevel) {
        switch (activityLevel) {
            case 'sedentary':
                return 20;
            case 'light':
                return 40;
            case 'moderate':
                return 70;
            case 'active':
                return 90;
            case 'very_active':
                return 100;
            default:
                return 50;
        }
    }

    /**
     * Calculate wellness score based on all components
     * @param {number} bmiScore - BMI score component (0-100)
     * @param {number} activityScore - Activity score component (0-100)
     * @param {number} progressScore - Progress score component (0-100)
     * @param {number} habitsScore - Habits score component (0-100)
     * @returns {number} - Overall wellness score (0-100)
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
            'sedentary': 'Sedentary',
            'light': 'Lightly Active',
            'moderate': 'Moderately Active',
            'active': 'Active',
            'very_active': 'Very Active'
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
            'sedentary': 'Little to no regular exercise',
            'light': 'Light exercise 1-3 days per week',
            'moderate': 'Moderate exercise 3-5 days per week',
            'active': 'Hard exercise 6-7 days per week',
            'very_active': 'Very hard exercise & physical job or twice daily training'
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
            'sedentary': [
                'Start with a 10-minute daily walk',
                'Take breaks to stretch every hour',
                'Try using stairs instead of elevators'
            ],
            'light': [
                'Aim for 20-30 minute walks 4-5 days/week',
                'Consider adding 1-2 strength sessions weekly',
                'Try a beginner yoga or flexibility routine'
            ],
            'moderate': [
                'Increase intensity in 1-2 workouts per week',
                'Add variety with different exercise types',
                'Consider tracking heart rate during exercise'
            ],
            'active': [
                'Focus on recovery between intense sessions',
                'Consider periodization in your training',
                'Add mobility work to prevent injuries'
            ],
            'very_active': [
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
        const map = {
            'high': 'High Priority',
            'medium': 'Medium Priority',
            'low': 'Low Priority'
        };
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