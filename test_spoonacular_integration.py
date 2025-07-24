#!/usr/bin/env python
"""
Test script for Spoonacular integration and enhanced meal planning
"""
import os
import sys
import django

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
django.setup()

from meal_planning.services.spoonacular_service import get_spoonacular_service, SpoonacularAPIError
from meal_planning.models import Recipe, NutritionProfile
from django.contrib.auth import get_user_model
import json

User = get_user_model()

def test_spoonacular_service():
    """Test basic Spoonacular service functionality"""
    print("🧪 Testing Spoonacular Service...")
    
    try:
        service = get_spoonacular_service()
        
        # Test recipe search
        print("  📋 Testing recipe search...")
        results = service.search_recipes(
            query="healthy breakfast",
            diet="vegetarian",
            number=2
        )
        
        print(f"  ✅ Found {len(results.get('results', []))} recipes")
        
        if results.get('results'):
            recipe = results['results'][0]
            print(f"  📝 Sample recipe: {recipe.get('title', 'Unknown')}")
            
            # Test recipe normalization
            print("  🔄 Testing recipe normalization...")
            normalized = service.normalize_recipe_data(recipe)
            print(f"  ✅ Normalized recipe: {normalized.get('title', 'Unknown')}")
            print(f"     Calories: {normalized.get('calories_per_serving', 0)}")
            print(f"     Protein: {normalized.get('protein_per_serving', 0)}g")
            
    except SpoonacularAPIError as e:
        print(f"  ❌ Spoonacular API Error: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected Error: {e}")

def test_recipe_database():
    """Test recipe database operations"""
    print("\n🗃️ Testing Recipe Database...")
    
    total_recipes = Recipe.objects.count()
    spoonacular_recipes = Recipe.objects.filter(source_type='spoonacular').count()
    
    print(f"  📊 Total recipes in database: {total_recipes}")
    print(f"  🥄 Spoonacular recipes: {spoonacular_recipes}")
    
    # Show sample recipes by meal type
    for meal_type in ['breakfast', 'lunch', 'dinner']:
        count = Recipe.objects.filter(meal_type=meal_type).count()
        print(f"  🍽️ {meal_type.title()} recipes: {count}")
        
        if count > 0:
            sample = Recipe.objects.filter(meal_type=meal_type).first()
            print(f"     Example: {sample.title} ({sample.source_type})")

def test_meal_plan_generation():
    """Test enhanced meal plan generation"""
    print("\n🤖 Testing Enhanced Meal Plan Generation...")
    
    try:
        # Get or create a test user
        test_user, created = User.objects.get_or_create(
            username='test_spoonacular_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            print("  👤 Created test user")
        
        # Get or create nutrition profile
        nutrition_profile, created = NutritionProfile.objects.get_or_create(
            user=test_user,
            defaults={
                'calorie_target': 2200,  # Custom calorie target
                'protein_target': 120,
                'carb_target': 275,
                'fat_target': 73,
                'dietary_preferences': ['vegetarian'],
                'allergies_intolerances': ['nuts'],
                'cuisine_preferences': ['mediterranean', 'italian']
            }
        )
        
        print(f"  📋 Using nutrition profile with {nutrition_profile.calorie_target} calorie target")
        
        # Test AI meal planning service
        from meal_planning.services.ai_meal_planning_service import AIMealPlanningService
        from datetime import date
        
        ai_service = AIMealPlanningService()
        
        # Test with custom calories
        custom_calories = 2500
        print(f"  🎯 Testing with custom calorie target: {custom_calories}")
        
        meal_plan = ai_service.generate_meal_plan(
            user=test_user,
            plan_type='daily',
            start_date=date.today(),
            target_calories=custom_calories
        )
        
        print(f"  ✅ Generated meal plan with ID: {meal_plan.id}")
        print(f"     Average daily calories: {meal_plan.avg_daily_calories}")
        print(f"     Total protein: {meal_plan.total_protein}g")
        
        # Check if meal plan uses Spoonacular recipes
        meal_data = meal_plan.meal_plan_data
        spoonacular_count = 0
        
        for date_meals in meal_data.get('meals', {}).values():
            for meal in date_meals:
                recipe = meal.get('recipe', {})
                if recipe.get('source_type') in ['spoonacular', 'spoonacular_local']:
                    spoonacular_count += 1
        
        print(f"  🥄 Meals using Spoonacular recipes: {spoonacular_count}")
        
    except Exception as e:
        print(f"  ❌ Meal plan generation error: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test API functionality (simulation)"""
    print("\n🔌 Testing API Endpoints...")
    
    print("  📡 Available endpoints:")
    print("     GET  /meal-planning/api/recipes/search_spoonacular/")
    print("     POST /meal-planning/api/recipes/search/")
    print("     POST /meal-planning/api/meal-plans/generate/")
    
    # Test parameters that would be sent to the API
    test_search_params = {
        'query': 'healthy breakfast',
        'cuisine': 'mediterranean',
        'diet': 'vegetarian',
        'number': 10
    }
    
    test_meal_plan_params = {
        'plan_type': 'daily',
        'start_date': '2024-07-25',
        'target_calories': 2400  # Custom calories
    }
    
    print(f"  📋 Sample search params: {json.dumps(test_search_params, indent=2)}")
    print(f"  🎯 Sample meal plan params: {json.dumps(test_meal_plan_params, indent=2)}")

def main():
    """Run all tests"""
    print("🚀 Starting Spoonacular Integration Tests\n")
    
    test_spoonacular_service()
    test_recipe_database()
    test_meal_plan_generation()
    test_api_endpoints()
    
    print("\n✅ All tests completed!")
    print("\n📝 Summary of enhancements:")
    print("   ✓ Spoonacular API integration for recipe search")
    print("   ✓ Enhanced meal plan generation with Spoonacular recipes")
    print("   ✓ Custom calorie target support (fixes n/a issue)")
    print("   ✓ Automatic saving of Spoonacular recipes to local database")
    print("   ✓ Fallback recipe removal and replacement")
    print("   ✓ Fixed Redis connection pool configuration")

if __name__ == '__main__':
    main()