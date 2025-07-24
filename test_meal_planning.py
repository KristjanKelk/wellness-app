#!/usr/bin/env python3
"""
Test script for meal planning system
Run this to verify the new features work properly
"""

import os
import sys
import django
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
django.setup()

from meal_planning.services.ai_meal_planning_service import AIMealPlanningService
from meal_planning.services.rag_service import RAGService
from meal_planning.models import NutritionProfile, Recipe, Ingredient
from django.contrib.auth import get_user_model

User = get_user_model()

def test_rag_service():
    """Test RAG service functionality"""
    print("Testing RAG Service...")
    
    try:
        rag_service = RAGService()
        
        # Test recipe search
        recipes = rag_service.search_similar_recipes(
            query="healthy chicken dinner",
            dietary_preferences=["high_protein"],
            top_k=3
        )
        
        print(f"✅ RAG recipe search returned {len(recipes)} results")
        if recipes:
            print(f"   - Example: {recipes[0].get('title', 'Unknown')}")
    
    except Exception as e:
        print(f"❌ RAG service test failed: {e}")

def test_ai_meal_planning():
    """Test AI meal planning service"""
    print("\nTesting AI Meal Planning Service...")
    
    try:
        # Try to get or create a test user
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Create or get nutrition profile
        nutrition_profile, created = NutritionProfile.objects.get_or_create(
            user=user,
            defaults={
                'calorie_target': 2000,
                'protein_target': 100,
                'carb_target': 250,
                'fat_target': 67,
                'dietary_preferences': ['high_protein'],
                'allergies_intolerances': [],
                'cuisine_preferences': ['mediterranean']
            }
        )
        
        # Test meal plan generation
        ai_service = AIMealPlanningService()
        meal_plan = ai_service.generate_meal_plan(
            user=user,
            plan_type='daily',
            start_date=date.today()
        )
        
        print(f"✅ AI meal plan generated successfully")
        print(f"   - Plan type: {meal_plan.plan_type}")
        print(f"   - Total calories: {meal_plan.total_calories}")
        print(f"   - Generation method: {getattr(meal_plan, 'validation_method', 'standard')}")
        
    except Exception as e:
        print(f"❌ AI meal planning test failed: {e}")

def test_database_population():
    """Test database population"""
    print("\nTesting Database Population...")
    
    try:
        recipe_count = Recipe.objects.count()
        ingredient_count = Ingredient.objects.count()
        
        print(f"✅ Current database state:")
        print(f"   - Recipes: {recipe_count}")
        print(f"   - Ingredients: {ingredient_count}")
        
        if recipe_count == 0 or ingredient_count == 0:
            print("   🔄 Run: python manage.py populate_nutrition_database")
            print("      to populate the database with sample data")
    
    except Exception as e:
        print(f"❌ Database test failed: {e}")

def test_sequential_prompting():
    """Test 3-step sequential prompting"""
    print("\nTesting Sequential Prompting...")
    
    try:
        ai_service = AIMealPlanningService()
        
        # Test if the new methods exist
        methods_to_check = [
            '_generate_meal_recipes_with_rag',
            '_refine_nutritional_balance_with_functions',
            '_validate_recipe_nutrition_with_functions'
        ]
        
        for method_name in methods_to_check:
            if hasattr(ai_service, method_name):
                print(f"   ✅ {method_name} - Available")
            else:
                print(f"   ❌ {method_name} - Missing")
        
        print("✅ Sequential prompting methods check complete")
        
    except Exception as e:
        print(f"❌ Sequential prompting test failed: {e}")

def test_function_calling():
    """Test AI function calling implementation"""
    print("\nTesting Function Calling...")
    
    try:
        ai_service = AIMealPlanningService()
        
        # Check if functions are defined
        if hasattr(ai_service, 'functions') and ai_service.functions:
            print(f"✅ Function definitions available: {len(ai_service.functions)} functions")
            
            for func in ai_service.functions:
                func_name = func.get('function', {}).get('name', 'Unknown')
                print(f"   - {func_name}")
        else:
            print("❌ No function definitions found")
        
    except Exception as e:
        print(f"❌ Function calling test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Meal Planning System Test Suite")
    print("=" * 50)
    
    test_database_population()
    test_rag_service()
    test_sequential_prompting()
    test_function_calling()
    test_ai_meal_planning()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\nTo use the enhanced features:")
    print("1. Set OPENAI_API_KEY in your environment")
    print("2. Run: python manage.py populate_nutrition_database")
    print("3. Generate meal plans through the API or admin interface")

if __name__ == "__main__":
    main()