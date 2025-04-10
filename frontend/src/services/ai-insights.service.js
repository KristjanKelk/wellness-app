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
        return apiClient.get('insights/');
    }

    /**
     * Generate new insights based on user data
     * This would connect to an LLM API in production
     * For development, we return mock insights
     * @param {Object} userData - User health data
     * @returns {Promise} - Promise resolving to generated insights
     */
    generateInsights(userData) {
        // In production, this would send data to an LLM API
        // For development, we're returning mock data
        console.log('Generating insights based on user data:', userData);
        // Mock API delay
        return new Promise((resolve) => {
            setTimeout(() => {
                const mockInsights = this.generateMockInsights(userData);
                resolve({ data: mockInsights });
            }, 200);
        });
    }

    /**
     * Generate mock insights based on user data for development
     * @param {Object} userData - User health data
     * @returns {Array} - Array of insight objects
     */
    generateMockInsights(userData) {
        const insights = [];
        const now = new Date();

        // BMI-based insights
        if (userData.bmi) {
            if (userData.bmi < 18.5) {
                insights.push({
                    content: "Your BMI indicates you're underweight. Focus on nutrient-dense foods and consider consulting with a nutritionist for healthy weight gain strategies.",
                    priority: "high",
                    created_at: new Date(now.getTime() - 86400000) // 1 day ago
                });
            } else if (userData.bmi >= 25 && userData.bmi < 30) {
                insights.push({
                    content: "Your BMI indicates you're overweight. Consider increasing your daily activity and focusing on nutrient-dense, lower-calorie foods.",
                    priority: "medium",
                    created_at: new Date(now.getTime() - 86400000) // 1 day ago
                });
            } else if (userData.bmi >= 30) {
                insights.push({
                    content: "Your BMI indicates obesity, which increases risk for several health conditions. Consider consulting with a healthcare provider for a personalized plan.",
                    priority: "high",
                    created_at: new Date(now.getTime() - 86400000) // 1 day ago
                });
            } else {
                insights.push({
                    content: "Your BMI is within the healthy range. Focus on maintaining your current weight through balanced nutrition and regular physical activity.",
                    priority: "low",
                    created_at: new Date(now.getTime() - 86400000) // 1 day ago
                });
            }
        }

        // Activity-based insights
        if (userData.activity_level) {
            switch (userData.activity_level) {
                case 'sedentary':
                    insights.push({
                        content: "Your activity level is sedentary. Try to incorporate at least 30 minutes of walking daily to improve your health metrics.",
                        priority: "high",
                        created_at: new Date(now.getTime() - 172800000) // 2 days ago
                    });
                    break;
                case 'light':
                    insights.push({
                        content: "You're lightly active. Consider adding 1-2 more active days per week to reach the recommended activity levels for optimal health.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 172800000) // 2 days ago
                    });
                    break;
                case 'moderate':
                    insights.push({
                        content: "You have a moderate activity level, which is great. For additional benefits, try adding variety to your workouts.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 172800000) // 2 days ago
                    });
                    break;
                case 'active':
                case 'very_active':
                    insights.push({
                        content: "Your activity level is excellent. Focus on recovery and proper nutrition to support your high activity level.",
                        priority: "low",
                        created_at: new Date(now.getTime() - 172800000) // 2 days ago
                    });
                    break;
            }
        }

        // Goal-based insights
        if (userData.fitness_goal) {
            switch (userData.fitness_goal) {
                case 'weight_loss':
                    insights.push({
                        content: "For your weight loss goals, try incorporating more protein in your diet to increase satiety and preserve lean muscle mass.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 259200000) // 3 days ago
                    });
                    break;
                case 'muscle_gain':
                    insights.push({
                        content: "For muscle gain, ensure you're in a slight caloric surplus and consider a progressive overload approach in your strength training.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 259200000) // 3 days ago
                    });
                    break;
                case 'general_fitness':
                    insights.push({
                        content: "For general fitness, aim for a balanced approach including cardio, strength training, and flexibility work throughout the week.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 259200000) // 3 days ago
                    });
                    break;
                case 'endurance':
                    insights.push({
                        content: "For endurance goals, gradually increase your training duration by no more than 10% per week to avoid overtraining.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 259200000) // 3 days ago
                    });
                    break;
                case 'flexibility':
                    insights.push({
                        content: "For flexibility, consider adding daily stretching routines, focusing on holding each stretch for 30-60 seconds.",
                        priority: "medium",
                        created_at: new Date(now.getTime() - 259200000) // 3 days ago
                    });
                    break;
            }
        }

        // General health insight
        insights.push({
            content: "Staying hydrated is critical for overall health. Aim for at least 8 glasses of water daily, more when exercising.",
            priority: "low",
            created_at: new Date(now.getTime() - 345600000) // 4 days ago
        });

        return insights;
    }
}

export default new AIInsightsService();