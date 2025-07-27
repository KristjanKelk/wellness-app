# Meal Planning API Fixes

## Issues Identified and Fixed

### 1. CORS and API Access Issues

**Problem**: Frontend couldn't access meal planning APIs due to CORS configuration issues.

**Solutions Implemented**:
- Added CSRF exemption decorators to ViewSets
- Enhanced CORS settings in `wellness_project/settings.py`
- Added localhost:8000 to allowed origins for development

### 2. Empty Recipe Database

**Problem**: No recipes were being displayed because the database was empty and Spoonacular integration wasn't working properly.

**Solutions Implemented**:

#### A. Enhanced Recipe ViewSet with Spoonacular Integration
- Modified `RecipeViewSet` to automatically fetch from Spoonacular when database is empty
- Added fallback to database search when Spoonacular fails
- Implemented proper error handling for API failures

#### B. Sample Recipe Population Command
Created `populate_sample_recipes.py` management command that adds 5 sample recipes:
1. Classic Grilled Chicken Salad (lunch, high-protein)
2. Vegetarian Buddha Bowl (dinner, vegan)
3. Overnight Oats with Berries (breakfast, vegetarian)
4. Spaghetti Aglio e Olio (dinner, Italian)
5. Green Smoothie Bowl (breakfast, vegan)

### 3. Model Enhancements

**Added to Recipe Model**:
- `image_url` field for Spoonacular images
- `source_url` field for recipe sources
- Better integration with Spoonacular data structure

### 4. API Endpoint Improvements

**New Features Added**:
- Automatic Spoonacular search when database is empty
- Better error handling and user feedback
- Recipe saving functionality from Spoonacular to database
- Enhanced search with dietary preferences integration

## How to Use the Fixes

### 1. Populate Sample Recipes (Immediate Fix)

Run this command to add sample recipes immediately:

```bash
python manage.py populate_sample_recipes
```

This will give you 5 high-quality sample recipes to display in your app right away.

### 2. Configure Spoonacular API (Long-term Solution)

1. Get a Spoonacular API key from https://spoonacular.com/food-api
2. Add it to your environment variables:
   ```
   SPOONACULAR_API_KEY=your_api_key_here
   ```
3. The app will automatically use Spoonacular when:
   - Database is empty
   - User searches for specific recipes
   - `fetch_new=true` parameter is passed

### 3. Test the API Endpoints

Test these endpoints to verify functionality:

**Get Recipes**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/meal-planning/api/recipes/
```

**Search Recipes**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"query":"chicken","dietary_preferences":["high_protein"]}' \
     http://localhost:8000/meal-planning/api/recipes/search/
```

**Get Nutrition Profile**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/meal-planning/api/nutrition-profile/current/
```

## Performance Improvements

### 1. Spoonacular Integration
- Implements proper rate limiting (150 requests/day for free tier)
- Caches API responses for 1 hour
- Falls back to database when API fails

### 2. Recipe Loading Strategy
1. **First**: Check local database
2. **If empty**: Fetch from Spoonacular API
3. **If API fails**: Show helpful error message
4. **Cache results**: Store in database for future use

### 3. Error Handling
- Graceful degradation when Spoonacular is unavailable
- User-friendly error messages
- Proper HTTP status codes

## Frontend Integration

The fixed endpoints now return consistent data structures:

```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid-or-spoonacular-id",
      "title": "Recipe Name",
      "description": "Recipe description",
      "prep_time_minutes": 15,
      "cook_time_minutes": 20,
      "servings": 4,
      "calories_per_serving": 380,
      "protein_per_serving": 35,
      "carb_per_serving": 12,
      "fat_per_serving": 18,
      "dietary_tags": ["high_protein", "gluten_free"],
      "image_url": "https://example.com/image.jpg",
      "source": "spoonacular" // or "database"
    }
  ],
  "source": "spoonacular" // indicates data source
}
```

## Testing Checklist

- [ ] Recipe list loads successfully
- [ ] Search functionality works
- [ ] Nutrition profile loads/updates
- [ ] Meal plan generation works
- [ ] CORS errors are resolved
- [ ] Sample recipes display correctly
- [ ] API responses are properly formatted

## Troubleshooting

### If recipes still don't load:
1. Run `python manage.py populate_sample_recipes`
2. Check that CORS settings include your frontend URL
3. Verify authentication tokens are being sent properly

### If Spoonacular integration fails:
1. Check API key is set correctly
2. Verify you haven't exceeded rate limits (150/day)
3. Check network connectivity to Spoonacular API

### If CORS errors persist:
1. Verify `CORS_ALLOW_ALL_ORIGINS = True` in settings
2. Check that `corsheaders.middleware.CorsMiddleware` is first in MIDDLEWARE
3. Clear browser cache and try again

## Next Steps

1. **Immediate**: Run the sample recipe command to get the app working
2. **Short-term**: Set up proper Spoonacular API key
3. **Long-term**: Implement recipe caching and user favorites
4. **Future**: Add recipe rating and recommendation system

The meal planning functionality should now work correctly with both sample data and live Spoonacular integration!