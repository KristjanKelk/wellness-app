# Spoonacular Integration & Enhanced Meal Planning

## 🚀 Overview

This update replaces fallback recipes with real Spoonacular API integration and fixes custom calorie target issues in meal planning. The system now provides access to thousands of real recipes with accurate nutritional information.

## ✨ New Features

### 1. **Spoonacular Recipe Search**
- Direct API integration with Spoonacular's recipe database
- Real-time recipe search with dietary filters
- Automatic caching and local storage of recipes
- Enhanced search with user preference matching

### 2. **Enhanced Meal Plan Generation**
- Prioritizes Spoonacular recipes in AI meal planning
- Custom calorie target support (fixes n/a issue)
- Multiple search strategies for better recipe matching
- Automatic fallback to local database when API is unavailable

### 3. **Improved Recipe Management**
- Automatic removal of placeholder/fallback recipes
- Population with real Spoonacular recipes
- Better nutritional accuracy
- Source tracking for all recipes

## 🔧 Technical Improvements

### Fixed Issues
- ✅ **Custom kcal not working** - Now properly handles `target_calories` parameter
- ✅ **Fallback recipes removal** - Replaced with real Spoonacular recipes
- ✅ **Redis connection error** - Fixed `CONNECTION_POOL_KWARGS` configuration
- ✅ **n/a values in meal plans** - Proper calorie target processing

### Enhanced APIs
- ✅ **New endpoint**: `/meal-planning/api/recipes/search_spoonacular/`
- ✅ **Enhanced**: Recipe search with Spoonacular integration
- ✅ **Enhanced**: Meal plan generation with custom calories

## 🛠️ Setup & Configuration

### Environment Variables
Ensure your `.env` file contains:
```bash
SPOONACULAR_API_KEY=your_api_key_here
```

### Database Population
Remove fallback recipes and populate with Spoonacular recipes:
```bash
python manage.py populate_spoonacular_recipes --remove-fallbacks --limit 100
```

## 📡 API Usage

### Recipe Search (Spoonacular)
```http
GET /meal-planning/api/recipes/search_spoonacular/?query=healthy breakfast&diet=vegetarian&number=10
```

**Parameters:**
- `query` - Search term
- `cuisine` - Cuisine type (italian, mexican, etc.)
- `diet` - Dietary preference (vegetarian, vegan, keto, etc.)
- `intolerances` - Allergies/intolerances (nuts, dairy, etc.)
- `meal_type` - breakfast, lunch, dinner, snack
- `max_calories` - Maximum calories per serving
- `number` - Number of results (default: 12)
- `offset` - Pagination offset

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "Mediterranean Breakfast Bowl",
      "cuisine": "mediterranean",
      "meal_type": "breakfast",
      "calories_per_serving": 380,
      "protein_per_serving": 15,
      "dietary_tags": ["vegetarian", "gluten_free"],
      "image_url": "https://...",
      "source_type": "spoonacular"
    }
  ],
  "total_results": 1250,
  "number": 12,
  "offset": 0,
  "source": "spoonacular"
}
```

### Enhanced Recipe Search
```http
POST /meal-planning/api/recipes/search/
Content-Type: application/json

{
  "search_query": "healthy breakfast",
  "dietary_preferences": ["vegetarian"],
  "allergies_to_avoid": ["nuts"],
  "cuisine_preferences": ["mediterranean"],
  "meal_type": "breakfast",
  "max_calories": 500,
  "number": 10
}
```

### Meal Plan Generation with Custom Calories
```http
POST /meal-planning/api/meal-plans/generate/
Content-Type: application/json

{
  "plan_type": "daily",
  "start_date": "2024-07-25",
  "target_calories": 2400
}
```

**Key Changes:**
- `target_calories` parameter now works correctly
- No more "n/a" values in generated meal plans
- Meal plans prioritize Spoonacular recipes

## 🔍 Recipe Sources

The system now uses multiple recipe sources in priority order:

1. **Spoonacular API** (Primary) - Fresh, real recipes with accurate nutrition
2. **Local Spoonacular Cache** - Previously fetched Spoonacular recipes
3. **AI Generated** (Fallback) - Only when Spoonacular is unavailable

## 🧪 Testing

Run the test script to verify functionality:
```bash
python test_spoonacular_integration.py
```

This will test:
- Spoonacular API connectivity
- Recipe search and normalization
- Database operations
- Enhanced meal plan generation
- Custom calorie target functionality

## 📊 Database Schema

### Recipe Model Enhancements
- `spoonacular_id` - Links to Spoonacular recipe
- `source_type` - Tracks recipe origin ('spoonacular', 'ai_generated', 'user_submitted')
- `is_verified` - Indicates data accuracy (True for Spoonacular)

### Nutrition Profile
- Supports custom calorie targets in meal plan generation
- Better integration with Spoonacular dietary filters

## 🔄 Migration Guide

### From Fallback System
1. **Remove old recipes**: `python manage.py populate_spoonacular_recipes --remove-fallbacks`
2. **Populate new recipes**: The command automatically fetches Spoonacular recipes
3. **Update frontend**: Use new search endpoints for better recipe discovery

### Frontend Integration
Update your frontend to use the new endpoints:

```javascript
// Enhanced recipe search
const searchRecipes = async (params) => {
  const response = await fetch('/meal-planning/api/recipes/search_spoonacular/', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Meal plan with custom calories
const generateMealPlan = async (calories) => {
  const response = await fetch('/meal-planning/api/meal-plans/generate/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      plan_type: 'daily',
      start_date: '2024-07-25',
      target_calories: calories  // Custom calorie target
    })
  });
  return response.json();
};
```

## 🚨 Rate Limiting

Spoonacular API has rate limits:
- **Free tier**: 150 requests/day
- **Paid tiers**: Higher limits available

The system implements:
- Request rate limiting
- Response caching
- Graceful fallbacks
- Local recipe storage to reduce API calls

## 🔧 Troubleshooting

### Common Issues

**API Key Issues**
```bash
# Test API key
python test_spoonacular.py
```

**No Recipes Found**
- Check if Spoonacular recipes are populated
- Verify dietary preferences aren't too restrictive
- Check API rate limits

**Custom Calories Not Working**
- Ensure `target_calories` is passed in request body
- Check logs for parameter validation
- Verify nutrition profile exists

**Redis Connection Errors**
- Fixed in this update (removed `CONNECTION_POOL_KWARGS`)
- Restart application after update

## 📈 Performance Optimizations

- **Caching**: Spoonacular responses cached for 24 hours
- **Local Storage**: Popular recipes stored locally
- **Batching**: Multiple search strategies for better results
- **Fallbacks**: Graceful degradation when API unavailable

## 🎯 Next Steps

### Planned Enhancements
1. **Advanced Filtering**: More granular search options
2. **User Preferences**: Learning from user behavior
3. **Ingredient Substitutions**: AI-powered recipe modifications
4. **Nutritional Analysis**: Enhanced macro/micro tracking
5. **Recipe Collections**: Curated recipe sets

### Integration Opportunities
- Shopping list generation from Spoonacular recipes
- Cooking instruction videos
- Nutritional fact verification
- Recipe rating and review system

---

## 🆘 Support

For issues with this integration:
1. Check the logs for specific error messages
2. Verify Spoonacular API key configuration
3. Run the test script for diagnostics
4. Check rate limiting status

The system is designed to be resilient - if Spoonacular is unavailable, it will fall back to local recipes and AI generation to ensure meal planning continues working.