# AI-Powered Nutrition Profile System

## Overview

This document describes the comprehensive AI-powered nutrition profile system that automatically generates personalized nutrition recommendations based on user goals, health profiles, and preferences using OpenAI integration.

## Features Implemented

### 1. AI Nutrition Profile Service (`AINutritionProfileService`)

**Location:** `meal_planning/services/ai_nutrition_profile_service.py`

**Core Functionality:**
- Generates personalized nutrition profiles using OpenAI GPT-4
- Calculates precise calorie and macronutrient targets based on user goals
- Provides goal-specific dietary recommendations
- Adapts recommendations based on progress and feedback
- Supports all fitness goals: weight loss, muscle gain, endurance, general fitness

**Key Methods:**
- `generate_ai_nutrition_profile()` - Main profile generation with OpenAI function calling
- `update_profile_based_on_progress()` - Adaptive recommendations based on user feedback
- `get_nutrition_insights()` - Daily nutrition analysis and insights

### 2. Enhanced Nutrition Profile Model

**Location:** `meal_planning/models.py`

**New Methods Added:**
- `get_goal_based_preferences()` - Returns goal-specific dietary preferences
- `get_ai_generation_context()` - Comprehensive context for AI generation
- Enhanced `calculate_targets_from_health_profile()` with goal-based logic

**Goal-Based Macro Calculations:**
- **Weight Loss**: 15% calorie deficit, higher protein (30%), moderate carbs (35%), healthy fats (35%)
- **Muscle Gain**: 15% calorie surplus, high protein (25%), higher carbs (50%), moderate fats (25%)
- **Endurance**: 10% calorie surplus, moderate protein (20%), high carbs (60%), lower fats (20%)
- **General Fitness**: Maintenance calories, balanced macros (25%/45%/30%)

### 3. API Endpoints

**Base URL:** `/api/nutrition-profiles/`

#### New Endpoints:

**POST `/generate-ai-profile/`**
- Generates AI-powered nutrition profile
- Parameters: `force_regenerate` (optional boolean)
- Returns: Complete profile with AI insights and recommendations

**POST `/update-with-progress/`**
- Updates profile based on user progress and feedback
- Parameters: `feedback`, `goal_achievement`, `challenges`, `weight_change`, `energy_levels`, `satisfaction`
- Returns: Updated profile with new recommendations

**POST `/get-daily-insights/`**
- Provides AI insights about daily nutrition intake
- Parameters: `calories`, `protein`, `carbs`, `fat`, `meals`, `date`
- Returns: Personalized insights and recommendations

**GET `/ai-recommendations/`**
- Retrieves stored AI recommendations from profile
- Returns: Complete AI recommendations including foods to emphasize/limit, supplements, strategy

**GET `/goal-based-preferences/`**
- Gets goal-specific dietary preferences
- Returns: Preferences based on current fitness goal

### 4. Enhanced Serializers

**Location:** `meal_planning/serializers.py`

**New Fields in NutritionProfileSerializer:**
- `ai_generated` - Boolean indicating if profile was AI-generated
- `ai_insights` - Complete AI recommendations and insights
- `goal_based_preferences` - Goal-specific dietary guidance
- `fitness_goal` - Current fitness goal from health profile
- `nutrition_strategy` - AI-generated nutrition strategy

## Integration with OpenAI

### Function Calling Schema

The system uses OpenAI's function calling feature to generate structured nutrition profiles:

```json
{
  "name": "generate_nutrition_profile",
  "description": "Generate a comprehensive nutrition profile based on user's health data and fitness goals",
  "parameters": {
    "calorie_target": "Daily calorie target (1200-4000 kcal)",
    "protein_target": "Daily protein target (50-300g)",
    "carb_target": "Daily carbohydrate target (50-500g)",
    "fat_target": "Daily fat target (30-200g)",
    "recommended_dietary_preferences": "Recommended dietary approaches",
    "meal_timing_recommendations": "Meal timing and frequency suggestions",
    "hydration_target": "Daily water intake in liters",
    "supplement_recommendations": "Recommended supplements if any",
    "foods_to_emphasize": "Foods to prioritize based on goals",
    "foods_to_limit": "Foods to limit or avoid",
    "nutrition_strategy": "Overall nutrition strategy explanation",
    "progress_monitoring": "Key metrics and monitoring guidance"
  }
}
```

### AI Prompt Strategy

The system creates comprehensive prompts that include:
- Complete user demographic data (age, gender, weight, height, BMI)
- Activity level and training details
- Current fitness goals and target weight
- Dietary preferences and restrictions
- Goal-specific guidance based on fitness objectives

## Usage Examples

### 1. Generate AI Nutrition Profile

```javascript
// Frontend API call
const response = await fetch('/api/nutrition-profiles/generate-ai-profile/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    force_regenerate: false  // Set to true to regenerate existing profile
  })
});

const result = await response.json();
// Returns: profile data, AI insights, recommendations, status
```

### 2. Update Profile with Progress

```javascript
const progressData = {
  feedback: "I've been feeling more energetic but struggling with late-night cravings",
  goal_achievement: {
    weight_loss: 0.7,  // 70% of goal achieved
    energy_levels: 0.9
  },
  challenges: ["late_night_cravings", "meal_prep_time"],
  weight_change: -2.5,  // kg lost
  energy_levels: 8,  // 1-10 scale
  satisfaction: 7  // 1-10 scale
};

const response = await fetch('/api/nutrition-profiles/update-with-progress/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(progressData)
});
```

### 3. Get Daily Insights

```javascript
const dailyData = {
  calories: 1847,
  protein: 142,
  carbs: 158,
  fat: 67,
  meals: [
    { name: "Breakfast", calories: 350 },
    { name: "Lunch", calories: 520 },
    { name: "Dinner", calories: 680 },
    { name: "Snacks", calories: 297 }
  ],
  date: "2024-01-15"
};

const response = await fetch('/api/nutrition-profiles/get-daily-insights/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(dailyData)
});
```

## Goal-Based Recommendations

### Weight Loss
- **Emphasized Foods**: Lean protein, vegetables, fruits, whole grains
- **Limited Foods**: Refined sugars, processed foods, high-fat dairy
- **Meal Timing**: Regular intervals to maintain metabolism
- **Portion Control**: Strict portion control with calorie tracking

### Muscle Gain
- **Emphasized Foods**: Protein-rich foods, complex carbs, healthy fats, dairy
- **Limited Foods**: Empty calories, excessive cardio-focused foods
- **Meal Timing**: Frequent meals (4-6 per day) with pre/post-workout nutrition
- **Portion Control**: Generous portions to support muscle growth

### Endurance
- **Emphasized Foods**: Complex carbs, lean protein, antioxidant-rich foods
- **Limited Foods**: High-fat foods pre-workout, excessive fiber before training
- **Meal Timing**: Strategic carb timing around workouts
- **Portion Control**: Moderate with emphasis on carb loading strategies

### General Fitness
- **Emphasized Foods**: Balanced nutrition, variety, whole foods
- **Limited Foods**: Processed foods, excessive sweets
- **Meal Timing**: Flexible based on lifestyle
- **Portion Control**: Moderate with focus on portion awareness

## AI Insights and Recommendations

The system provides comprehensive insights including:

### Nutrition Strategy
- Personalized explanation of the recommended approach
- Scientific rationale for macro distribution
- Timeline and expectations for results

### Foods to Emphasize
- Specific food recommendations based on goals
- Nutrient-dense options prioritized
- Cultural and preference considerations

### Foods to Limit
- Goal-specific foods to avoid or minimize
- Explanation of why certain foods don't align with goals
- Healthy alternatives provided

### Supplement Recommendations
- Evidence-based supplement suggestions
- Only recommended when beneficial for specific goals
- Dosage and timing guidance included

### Progress Monitoring
- Key metrics to track for goal achievement
- Recommended frequency of measurements
- Success indicators and milestone markers

## Technical Implementation

### Database Schema

The system stores AI recommendations in the `advanced_preferences` JSONField:

```json
{
  "ai_generated": true,
  "ai_generation_date": "2024-01-15T10:30:00Z",
  "ai_recommendations": {
    "nutrition_strategy": "...",
    "calorie_target": 1850,
    "protein_target": 140,
    "carb_target": 170,
    "fat_target": 65,
    "ai_confidence": 0.87
  },
  "foods_to_emphasize": ["lean_protein", "vegetables", "fruits"],
  "foods_to_limit": ["refined_sugars", "processed_foods"],
  "hydration_target": 2.5,
  "supplement_recommendations": ["vitamin_d", "omega_3"],
  "progress_monitoring": {
    "key_metrics": ["weight", "body_composition", "energy_levels"],
    "adjustment_frequency": "bi_weekly",
    "success_indicators": ["steady_weight_loss", "maintained_energy"]
  }
}
```

### Error Handling

The system includes comprehensive error handling:
- OpenAI API failures fallback to rule-based calculations
- Graceful degradation when AI features are unavailable
- Detailed logging for debugging and monitoring
- User-friendly error messages

### Security and Privacy

- OpenAI API key securely stored in environment variables
- User data encrypted and anonymized before sending to OpenAI
- No personally identifiable information included in AI prompts
- All recommendations stored locally in user's profile

## Configuration

### Environment Variables Required

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Django Settings

```python
# OpenAI Model Configuration
OPENAI_MODEL_CONFIG = {
    'nutrition_analysis': {
        'model': 'gpt-4-turbo-preview',
        'temperature': 0.3,
        'max_tokens': 1000,
    }
}
```

## Frontend Integration

### Profile Display
- Show AI-generated status with confidence indicator
- Display nutrition strategy in user-friendly format
- Present recommendations in organized sections
- Provide easy access to regeneration options

### Progress Tracking
- Integrate progress feedback forms
- Show adaptation recommendations
- Track goal achievement metrics
- Display progress-based insights

### Daily Nutrition
- Real-time insights based on daily intake
- Goal progress indicators
- Personalized recommendations for meal adjustments
- Smart notifications for nutrition goals

## Future Enhancements

### Planned Features
1. **Meal Plan Integration**: Automatically generate meal plans based on AI nutrition profiles
2. **Recipe Recommendations**: AI-powered recipe suggestions aligned with nutrition goals
3. **Progress Adaptation**: Automatic profile adjustments based on tracked progress
4. **Community Insights**: Anonymized insights from similar user profiles
5. **Seasonal Adjustments**: Nutrition recommendations adapted for training seasons

### Technical Improvements
1. **Caching**: Implement intelligent caching for AI responses
2. **Batch Processing**: Optimize API calls for multiple users
3. **Model Fine-tuning**: Train custom models on nutrition data
4. **Real-time Updates**: WebSocket integration for live recommendations

## Conclusion

The AI-powered nutrition profile system provides a comprehensive, personalized approach to nutrition guidance. By integrating OpenAI's advanced language models with evidence-based nutrition science, users receive tailored recommendations that adapt to their specific goals, preferences, and progress.

The system is designed to be:
- **Intelligent**: Uses advanced AI for personalized recommendations
- **Adaptive**: Adjusts based on user progress and feedback
- **Goal-oriented**: Specifically designed for different fitness objectives
- **User-friendly**: Easy-to-understand recommendations and insights
- **Scalable**: Efficient implementation supporting multiple users
- **Secure**: Privacy-focused with secure API integration

This implementation significantly enhances the nutrition tracking capabilities of the wellness platform, providing users with professional-level nutrition guidance powered by artificial intelligence.