#!/usr/bin/env python3
"""
Setup script for Spoonacular API integration
This script helps configure the meal planning app with Spoonacular API
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
django.setup()

from meal_planning.services.spoonacular_service import get_spoonacular_service
from meal_planning.models import Recipe

def print_banner():
    """Print a welcome banner"""
    print("=" * 60)
    print("🍽️  MEAL PLANNER - SPOONACULAR SETUP")
    print("=" * 60)
    print()

def check_api_key():
    """Check if Spoonacular API key is configured"""
    from django.conf import settings
    
    api_key = getattr(settings, 'SPOONACULAR_API_KEY', '')
    
    if not api_key or api_key == 'demo_key_replace_with_real_key':
        print("❌ Spoonacular API key not configured!")
        print()
        print("To get a free API key:")
        print("1. Visit https://spoonacular.com/food-api")
        print("2. Sign up for a free account")
        print("3. Get your API key from the dashboard")
        print("4. Add it to your .env.local file:")
        print("   SPOONACULAR_API_KEY=your_actual_api_key_here")
        print()
        return False
    
    print(f"✅ API key configured: {api_key[:8]}...")
    return True

def test_api_connection():
    """Test the API connection"""
    try:
        print("🔍 Testing API connection...")
        service = get_spoonacular_service()
        
        # Test with a simple search
        results = service.search_recipes(
            query="pasta",
            number=1
        )
        
        if results and results.get('results'):
            print("✅ API connection successful!")
            print(f"   Found {results.get('totalResults', 0)} pasta recipes")
            return True
        else:
            print("⚠️  API connected but no results returned")
            return False
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def populate_sample_recipes():
    """Populate database with sample recipes from Spoonacular"""
    try:
        print("📥 Loading sample recipes from Spoonacular...")
        service = get_spoonacular_service()
        
        # Search for different types of recipes
        searches = [
            ("healthy breakfast", 5),
            ("easy dinner", 5),
            ("vegetarian lunch", 3),
            ("low carb snacks", 2)
        ]
        
        total_added = 0
        
        for query, limit in searches:
            print(f"   Searching for: {query}")
            results = service.search_recipes(query=query, number=limit)
            
            for recipe_data in results.get('results', []):
                # Check if recipe already exists
                if Recipe.objects.filter(spoonacular_id=recipe_data.get('id')).exists():
                    continue
                
                try:
                    # Get detailed recipe info
                    detailed_recipe = service.get_recipe_information(recipe_data['id'])
                    
                    # Normalize and save
                    normalized_data = service.normalize_recipe_data(detailed_recipe)
                    
                    recipe = Recipe.objects.create(
                        title=normalized_data['title'],
                        summary=normalized_data.get('summary', ''),
                        cuisine=normalized_data.get('cuisine', ''),
                        meal_type=normalized_data.get('meal_type', 'lunch'),
                        servings=normalized_data.get('servings', 4),
                        prep_time_minutes=normalized_data.get('prep_time_minutes', 0),
                        cook_time_minutes=normalized_data.get('cook_time_minutes', 0),
                        total_time_minutes=normalized_data.get('total_time_minutes', 30),
                        difficulty_level=normalized_data.get('difficulty_level', 'medium'),
                        spoonacular_id=normalized_data.get('spoonacular_id'),
                        ingredients_data=normalized_data.get('ingredients_data', []),
                        instructions_data=normalized_data.get('instructions_data', []),
                        image_url=normalized_data.get('image_url', ''),
                        source_url=normalized_data.get('source_url', ''),
                        source_name='spoonacular',
                        calories_per_serving=normalized_data.get('calories_per_serving', 0),
                        protein_per_serving=normalized_data.get('protein_per_serving', 0),
                        carbs_per_serving=normalized_data.get('carbs_per_serving', 0),
                        fat_per_serving=normalized_data.get('fat_per_serving', 0),
                        dietary_tags=normalized_data.get('dietary_tags', []),
                        allergens=normalized_data.get('allergens', [])
                    )
                    
                    total_added += 1
                    print(f"   ✅ Added: {recipe.title}")
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to add recipe {recipe_data.get('title', 'Unknown')}: {e}")
                    continue
        
        print(f"✅ Added {total_added} new recipes to database")
        return True
        
    except Exception as e:
        print(f"❌ Failed to populate recipes: {e}")
        return False

def check_database_status():
    """Check current database status"""
    recipe_count = Recipe.objects.count()
    spoonacular_count = Recipe.objects.filter(source_name='spoonacular').count()
    
    print(f"📊 Database Status:")
    print(f"   Total recipes: {recipe_count}")
    print(f"   Spoonacular recipes: {spoonacular_count}")
    print()

def main():
    """Main setup function"""
    print_banner()
    
    # Check API key
    if not check_api_key():
        print("Please configure your API key and run this script again.")
        return
    
    print()
    
    # Test API connection
    if not test_api_connection():
        print("Please check your API key and internet connection.")
        return
    
    print()
    
    # Check current database status
    check_database_status()
    
    # Ask user if they want to populate recipes
    populate = input("Would you like to populate the database with sample recipes? (y/n): ").lower().strip()
    
    if populate == 'y':
        print()
        if populate_sample_recipes():
            print()
            check_database_status()
    
    print()
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print("1. Start your Django server: python manage.py runserver")
    print("2. Start your Vue frontend: cd frontend && npm run serve")
    print("3. Go to the Meal Planning Dashboard")
    print("4. Try the Recipe Browser with Spoonacular search")
    print()

if __name__ == "__main__":
    main()