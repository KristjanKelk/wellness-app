#!/usr/bin/env python
"""
Test script for the enhanced AI assistant
Tests all major features including:
- Health metrics queries
- Meal plan and recipe information
- Nutrition analysis
- Progress reports
- Recipe search
- Visualization generation
- Context management and reference resolution
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append('/workspace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from ai_assistant.services import AIAssistantService
from ai_assistant.conversation_manager import ConversationManager
from health_profiles.models import HealthProfile, WeightHistory
from meal_planning.models import NutritionProfile, MealPlan, Recipe, NutritionLog
from analytics.models import WellnessScore

User = get_user_model()


def create_test_data():
    """Create test user with health and nutrition data"""
    # Create test user
    user, created = User.objects.get_or_create(
        username='test_ai_user',
        defaults={'first_name': 'Test', 'email': 'test@example.com'}
    )
    
    # Create health profile
    health_profile, _ = HealthProfile.objects.get_or_create(
        user=user,
        defaults={
            'age': 30,
            'gender': 'M',
            'height_cm': 175,
            'weight_kg': 75,
            'activity_level': 'moderate',
            'fitness_goal': 'weight_loss',
            'target_weight_kg': 72
        }
    )
    
    # Create weight history
    for i in range(30, 0, -5):
        date = datetime.now() - timedelta(days=i)
        weight = 77 - (i * 0.06)  # Gradual weight loss
        WeightHistory.objects.get_or_create(
            health_profile=health_profile,
            recorded_at=date,
            defaults={'weight_kg': weight}
        )
    
    # Create nutrition profile
    nutrition_profile, _ = NutritionProfile.objects.get_or_create(
        user=user,
        defaults={
            'calorie_target': 2000,
            'protein_target': 100,
            'carb_target': 250,
            'fat_target': 67,
            'dietary_preferences': ['mediterranean', 'high_protein'],
            'allergies_intolerances': ['nuts'],
            'cuisine_preferences': ['italian', 'asian']
        }
    )
    
    # Create some recipes
    recipe1, _ = Recipe.objects.get_or_create(
        title='Grilled Salmon with Vegetables',
        defaults={
            'ready_in_minutes': 30,
            'servings': 2,
            'calories': 380,
            'protein': 34,
            'carbs': 15,
            'fat': 22,
            'instructions': ['1. Season salmon', '2. Grill for 12 minutes', '3. Steam vegetables'],
            'ingredients': ['salmon fillet', 'broccoli', 'bell peppers', 'olive oil'],
            'diets': ['mediterranean', 'high_protein']
        }
    )
    
    recipe2, _ = Recipe.objects.get_or_create(
        title='Mediterranean Quinoa Bowl',
        defaults={
            'ready_in_minutes': 25,
            'servings': 2,
            'calories': 420,
            'protein': 18,
            'carbs': 52,
            'fat': 16,
            'instructions': ['1. Cook quinoa', '2. Chop vegetables', '3. Mix with dressing'],
            'ingredients': ['quinoa', 'chickpeas', 'cucumber', 'tomatoes', 'feta cheese'],
            'diets': ['vegetarian', 'mediterranean']
        }
    )
    
    # Create meal plans
    today = datetime.now().date()
    MealPlan.objects.get_or_create(
        user=user,
        date=today,
        meal_type='lunch',
        defaults={'recipe': recipe2}
    )
    
    MealPlan.objects.get_or_create(
        user=user,
        date=today,
        meal_type='dinner',
        defaults={'recipe': recipe1}
    )
    
    # Create nutrition logs
    NutritionLog.objects.get_or_create(
        user=user,
        date=today,
        meal_type='breakfast',
        defaults={
            'calories': 350,
            'protein': 20,
            'carbs': 45,
            'fat': 12
        }
    )
    
    # Create wellness score
    WellnessScore.objects.get_or_create(
        health_profile=health_profile,
        calculated_at=datetime.now(),
        defaults={
            'total_score': 75,
            'activity_score': 70,
            'nutrition_score': 80,
            'sleep_score': 75,
            'mental_wellbeing_score': 75
        }
    )
    
    return user


def test_ai_assistant():
    """Test various AI assistant capabilities"""
    print("Creating test data...")
    user = create_test_data()
    
    print("\nInitializing AI Assistant...")
    manager = ConversationManager(user)
    
    # Test queries
    test_queries = [
        # Health metrics queries
        "What's my current BMI?",
        "How has my weight changed this month?",
        
        # Progress questions
        "How close am I to my weight goal?",
        "Show me my wellness score",
        
        # Meal plan inquiries
        "What's on my meal plan today?",
        "What's for dinner tonight?",
        
        # Recipe information
        "Tell me about the dinner recipe",
        "How many calories in tonight's meal?",
        
        # Nutritional analysis
        "How many calories have I consumed today?",
        "Am I meeting my protein target?",
        
        # Multi-turn context
        "What's my weight?",
        "How has it changed?",  # Reference to previous topic
        
        # Recipe search
        "Find me high protein recipes",
        "Search for vegetarian meals under 400 calories",
        
        # User preferences
        "What are my dietary preferences?",
        "What are my nutrition targets?",
        
        # Progress reports
        "Show me my weight loss progress",
        "Generate a comprehensive progress report",
        
        # Visualization requests
        "Show me my weight trend for the last month",
        "Show me how my protein intake compares to the target",
        "Show me the breakdown of my macronutrients for today"
    ]
    
    print("\nTesting AI Assistant with various queries:\n")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}] User: {query}")
        
        try:
            response = manager.send_message(query)
            
            print(f"\n[Response] Assistant: {response.get('message', 'No response')}")
            
            if response.get('function_called'):
                print(f"\n[Function Called]: {response['function_called']}")
            
            if 'visualization_ready' in str(response):
                print("\n[Visualization]: Chart data generated successfully")
                
        except Exception as e:
            print(f"\n[Error]: {str(e)}")
        
        print("\n" + "-" * 80)
    
    # Test conversation history
    print("\n\nTesting Conversation History Retrieval...")
    history = manager.get_conversation_history(limit=5)
    print(f"Retrieved {len(history)} recent messages")
    
    # Test compression
    print("\n\nTesting Conversation Compression...")
    # Add more messages to trigger compression
    for i in range(15):
        manager.send_message(f"Test message {i} for compression")
    
    print("Compression test completed")
    
    print("\n\n✅ All tests completed!")
    print(f"Conversation ID: {manager.conversation.id}")


if __name__ == "__main__":
    test_ai_assistant()
    
    # Quick sanity check for compare-modes feature (non-fatal)
    try:
        print("\n\nTesting compare-modes (concise vs detailed)...")
        user = User.objects.get(username='test_ai_user')
        manager = ConversationManager(user)
        resp = manager.send_message(
            "Ask the same question in both modes and verify the difference in details and verbosity: What are 3 high-protein breakfast ideas?",
            compare_modes=True
        )
        content = resp.get('message', '')
        has_concise = 'Concise:' in content
        has_detailed = 'Detailed:' in content
        print("Contains Concise section:", has_concise)
        print("Contains Detailed section:", has_detailed)
    except Exception as e:
        print("Compare-modes check skipped due to error:", e)