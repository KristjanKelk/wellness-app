#!/usr/bin/env python3
import os
import django
import sys

# Setup Django
sys.path.insert(0, '/workspace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fittrack_project.settings')
django.setup()

from meal_planning.models import MealPlan
from meal_planning.services.shopping_list_service import ShoppingListService

# Get the first meal plan
meal_plan = MealPlan.objects.first()
if meal_plan:
    print(f"Testing shopping list for meal plan: {meal_plan.id}")
    print(f"Meal plan data structure: {meal_plan.meal_plan_data}")
    
    service = ShoppingListService()
    try:
        shopping_list = service.generate_shopping_list_from_meal_plan(str(meal_plan.id))
        print(f"\nGenerated shopping list: {shopping_list}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No meal plans found in database")