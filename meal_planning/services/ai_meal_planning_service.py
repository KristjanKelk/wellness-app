# nutrition/services/ai_meal_planning_service.py
import openai
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from meal_planning.models import NutritionProfile, Recipe, MealPlan, Ingredient
from .nutrition_calculation_service import NutritionCalculationService

logger = logging.getLogger('nutrition.ai')
User = get_user_model()


class AIMealPlanningService:
    """
    AI-powered meal planning service using sequential prompting and function calling
    """

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.nutrition_calculator = NutritionCalculationService()
        self.model_config = settings.OPENAI_MODEL_CONFIG['meal_planning']

        # Function definitions for OpenAI function calling
        self.functions = [
            {
                "type": "function",
                "function": {
                    "name": "calculate_meal_nutrition",
                    "description": "Calculate nutritional information for a meal with specific ingredients",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ingredients": {
                                "type": "array",
                                "description": "List of ingredients with quantities",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "quantity": {"type": "number"},
                                        "unit": {"type": "string"}
                                    },
                                    "required": ["name", "quantity", "unit"]
                                }
                            },
                            "servings": {
                                "type": "number",
                                "description": "Number of servings this meal makes"
                            }
                        },
                        "required": ["ingredients", "servings"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_dietary_restrictions",
                    "description": "Check if a meal meets user's dietary restrictions and allergies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ingredients": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of ingredient names"
                            },
                            "dietary_preferences": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "User's dietary preferences"
                            },
                            "allergies": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "User's allergies and intolerances"
                            }
                        },
                        "required": ["ingredients", "dietary_preferences", "allergies"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_similar_recipes",
                    "description": "Find similar recipes from the database based on criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "meal_type": {"type": "string"},
                            "cuisine": {"type": "string"},
                            "dietary_tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "max_calories": {"type": "number"},
                            "exclude_allergens": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["meal_type"]
                    }
                }
            }
        ]

    def generate_meal_plan(self, user: User, plan_type: str = 'daily',
                           start_date: datetime = None, **kwargs) -> MealPlan:
        """
        Generate AI-powered meal plan using sequential prompting

        Args:
            user: User instance
            plan_type: 'daily' or 'weekly'
            start_date: Start date for the meal plan
            **kwargs: Additional parameters (target_calories, use_preferences, etc.)

        Returns:
            Generated MealPlan instance
        """
        try:
            # Get user's nutrition profile
            nutrition_profile = self._get_nutrition_profile(user)

            # Set default start date
            if not start_date:
                start_date = timezone.now().date()

            # Calculate end date based on plan type
            if plan_type == 'weekly':
                end_date = start_date + timedelta(days=6)
            else:
                end_date = start_date

            # STEP 1: Generate meal planning strategy
            strategy = self._generate_meal_strategy(nutrition_profile, **kwargs)

            # STEP 2: Create meal structure
            meal_structure = self._generate_meal_structure(
                strategy, nutrition_profile, start_date, end_date
            )

            # STEP 3: Generate detailed recipes for each meal
            detailed_meal_plan = self._generate_detailed_recipes(
                meal_structure, nutrition_profile
            )

            # STEP 4: Validate and optimize nutrition
            optimized_meal_plan = self._optimize_nutrition_balance(
                detailed_meal_plan, nutrition_profile
            )

            # Calculate nutritional totals
            nutrition_totals = self._calculate_plan_nutrition(optimized_meal_plan)

            # Create MealPlan instance
            meal_plan = MealPlan.objects.create(
                user=user,
                plan_type=plan_type,
                start_date=start_date,
                end_date=end_date,
                meal_plan_data=optimized_meal_plan,
                **nutrition_totals,
                ai_model_used=self.model_config['model'],
                generation_version='1.0'
            )

            logger.info(f"Generated {plan_type} meal plan for user {user.id}")
            return meal_plan

        except Exception as e:
            logger.error(f"Failed to generate meal plan: {e}")
            raise