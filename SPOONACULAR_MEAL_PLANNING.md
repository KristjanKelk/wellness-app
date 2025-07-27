# Enhanced Spoonacular Meal Planning System

This document describes the new streamlined meal planning system that integrates Spoonacular API with OpenAI analysis for optimal user experience.

## Overview

The enhanced meal planning system combines:
- **Spoonacular API**: For recipe search, meal plan generation, and shopping lists
- **OpenAI GPT**: For nutritional analysis and personalized recommendations
- **Seamless Integration**: Automatic user connection and preference mapping

## Key Features

### 1. Native Spoonacular Meal Plans
- Uses Spoonacular's built-in meal plan generator
- Automatically maps user dietary preferences and restrictions
- Generates daily or weekly meal plans based on calorie targets

### 2. AI-Enhanced Analysis
- OpenAI analyzes generated meal plans for nutritional balance
- Provides specific recommendations and insights
- Calculates nutritional scores and identifies gaps

### 3. Streamlined User Experience
- Automatic user connection to Spoonacular
- No manual recipe creation needed
- Direct shopping list generation from meal plans

## API Endpoints

### Core Meal Planning

#### Generate Smart Meal Plan
```http
POST /meal-planning/api/nutrition-profile/generate_smart_meal_plan/
Content-Type: application/json

{
  "days": 7
}
```

**Response:**
```json
{
  "days": [
    {
      "day": "monday",
      "meals": {
        "breakfast": [...],
        "lunch": [...],
        "dinner": [...]
      },
      "nutrition": {
        "calories": 2000,
        "protein": 150,
        "carbs": 200,
        "fat": 70
      },
      "recommendations": [...]
    }
  ],
  "ai_insights": {
    "summary": "This meal plan provides excellent nutritional balance...",
    "recommendations": [...],
    "healthiness_score": 8.5
  },
  "scores": {
    "balance_score": 8.5,
    "variety_score": 7.8,
    "preference_match_score": 9.2,
    "overall_score": 8.5
  }
}
```

#### Get Spoonacular Meal Plan
```http
GET /meal-planning/api/nutrition-profile/spoonacular_meal_plan/?start_date=2025-01-27
```

**Response:**
```json
{
  "week": {
    "monday": {
      "meals": [...],
      "nutrients": {...}
    }
  },
  "ai_insights": {...}
}
```

#### Get Shopping List
```http
GET /meal-planning/api/nutrition-profile/spoonacular_shopping_list/
```

**Response:**
```json
{
  "aisles": [
    {
      "aisle": "Produce",
      "items": [
        {
          "name": "2 lbs apples",
          "original": "2 lbs apples"
        }
      ]
    }
  ]
}
```

### Analysis and Insights

#### Analyze Meal Plan
```http
POST /meal-planning/api/nutrition-profile/analyze_meal_plan/
Content-Type: application/json

{
  "meal_plan_data": {
    "meals": {...},
    "nutrition": {...}
  }
}
```

**Response:**
```json
{
  "ai_analysis": {
    "summary": "Nutritional analysis...",
    "recommendations": [...],
    "nutritional_gaps": [...],
    "meal_prep_tips": [...],
    "healthiness_score": 8.0
  },
  "scores": {...},
  "recommendations": [...]
}
```

### User Connection

#### Connect to Spoonacular
```http
POST /meal-planning/api/nutrition-profile/connect_spoonacular/
```

**Response:**
```json
{
  "message": "Successfully connected to Spoonacular",
  "connected": true,
  "spoonacular_username": "user_123"
}
```

#### Check Connection Status
```http
GET /meal-planning/api/nutrition-profile/spoonacular_status/
```

**Response:**
```json
{
  "connected": true,
  "spoonacular_username": "user_123"
}
```

## Service Architecture

### EnhancedSpoonacularService
Located: `meal_planning/services/enhanced_spoonacular_service.py`

**Key Methods:**
- `search_recipes()` - Advanced recipe search with filters
- `generate_meal_plan()` - Native Spoonacular meal plan generation
- `create_personalized_meal_plan()` - User-specific meal plans
- `connect_user()` - Connect user to Spoonacular
- `get_meal_plan_week()` - Retrieve weekly meal plans
- `get_shopping_list()` - Get/generate shopping lists

### AIEnhancedMealService
Located: `meal_planning/services/ai_enhanced_meal_service.py`

**Key Methods:**
- `generate_smart_meal_plan()` - Spoonacular + AI analysis
- `analyze_meal_plan_with_ai()` - Standalone AI analysis
- `get_spoonacular_meal_plan()` - Enhanced meal plan retrieval
- `_add_ai_analysis()` - Add OpenAI insights to meal plans
- `_calculate_nutritional_scores()` - Calculate quality metrics

## Configuration

### Environment Variables
```env
SPOONACULAR_API_KEY=your_spoonacular_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Rate Limiting
- **Spoonacular**: 150 requests/day (free tier), 1 request/second
- **OpenAI**: Based on your plan
- Automatic rate limiting with caching

## User Flow

### 1. Initial Setup
1. User creates nutrition profile
2. System automatically connects user to Spoonacular
3. User preferences are mapped to Spoonacular parameters

### 2. Meal Plan Generation
1. User requests meal plan (1-14 days)
2. System generates plan using Spoonacular API
3. OpenAI analyzes the plan for nutritional quality
4. Combined result with insights is returned

### 3. Shopping and Preparation
1. User can generate shopping list from meal plan
2. AI provides meal prep tips and recommendations
3. User can modify plans and get re-analysis

## Dietary Preference Mapping

| User Preference | Spoonacular Diet |
|----------------|------------------|
| vegetarian | vegetarian |
| vegan | vegan |
| pescatarian | pescatarian |
| keto | ketogenic |
| paleo | paleo |
| mediterranean | mediterranean |
| low_carb | ketogenic |
| gluten_free | gluten free |
| dairy_free | dairy free |

## Allergy/Intolerance Mapping

| User Allergy | Spoonacular Intolerance |
|-------------|------------------------|
| nuts | tree nuts |
| peanuts | peanuts |
| dairy | dairy |
| gluten | gluten |
| eggs | eggs |
| fish | fish |
| shellfish | shellfish |
| soy | soy |
| sesame | sesame |

## Benefits Over Previous System

### 1. Reduced API Usage
- Use Spoonacular's native meal planning instead of multiple recipe searches
- Cached results and intelligent rate limiting
- Fallback mechanisms for API failures

### 2. Better User Experience
- Automatic user connection (no manual setup)
- Consistent recipe data from Spoonacular
- Real shopping lists instead of just ingredients

### 3. Enhanced Intelligence
- OpenAI provides nutritional analysis
- Personalized recommendations
- Quality scoring system

### 4. Simplified Maintenance
- Less custom logic for meal planning
- Leverages Spoonacular's expertise
- Modular service architecture

## Migration Notes

### Removed Components
- `ai_meal_planning_service.py` - Replaced by AIEnhancedMealService
- `enhanced_meal_planning_service.py` - Consolidated functionality
- Complex recipe search logic - Now uses Spoonacular's search

### Updated Components
- `views.py` - New endpoints for enhanced features
- `models.py` - Spoonacular connection fields already existed
- Frontend calls - Updated to use new endpoints

## Error Handling

### Spoonacular API Failures
- Automatic fallback to basic meal plans
- Graceful degradation of features
- Clear error messages to users

### OpenAI API Failures
- Meal plans still generated without AI insights
- Basic recommendations provided
- System continues to function

## Testing

### Test Spoonacular Connection
```bash
python test_spoonacular.py
```

### Manual Testing Endpoints
1. Connect user: `/nutrition-profile/connect_spoonacular/`
2. Generate plan: `/nutrition-profile/generate_smart_meal_plan/`
3. Get shopping list: `/nutrition-profile/spoonacular_shopping_list/`

## Performance Optimizations

### Caching Strategy
- API responses cached for appropriate durations
- Rate limiting prevents quota exhaustion
- Intelligent request batching

### Background Processing
- Large meal plan generations can be async
- Shopping list generation from meal plans
- AI analysis can be queued for non-critical paths

## Future Enhancements

### Planned Features
- Recipe rating and feedback integration
- Custom recipe additions to Spoonacular meal plans
- Advanced meal prep scheduling
- Family meal planning (multiple profiles)

### Potential Improvements
- Machine learning for preference refinement
- Integration with grocery delivery services
- Nutritionist dashboard for plan review
- Social features for meal plan sharing

This system provides a robust, scalable foundation for meal planning that leverages the best of both Spoonacular's recipe database and OpenAI's analytical capabilities.