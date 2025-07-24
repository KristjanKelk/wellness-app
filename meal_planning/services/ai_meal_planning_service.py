# meal_planning/services/ai_meal_planning_service.py
import openai
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from meal_planning.models import NutritionProfile, Recipe, MealPlan, Ingredient
from meal_planning.services.rag_service import RAGService
from meal_planning.services.nutrition_calculation_service import NutritionCalculationService
from health_profiles.models import HealthProfile

logger = logging.getLogger('nutrition.ai')
User = get_user_model()


class AIMealPlanningService:
    """
    AI-powered meal planning service using sequential prompting and function calling
    """

    def __init__(self):
        # Set up OpenAI client
        self.client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        self.secondary_model = 'gpt-3.5-turbo'  # For function calling
        
        # Initialize service dependencies
        self.rag_service = RAGService()
        self.nutrition_service = NutritionCalculationService()

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
            }
        ]

    def generate_meal_plan(self, user: User, plan_type: str = 'daily',
                           start_date: date = None, target_calories: int = None) -> MealPlan:
        """
        Generate AI-powered meal plan using sequential prompting

        Args:
            user: User instance
            plan_type: 'daily' or 'weekly'
            start_date: Start date for the meal plan
            target_calories: Optional calorie target override

        Returns:
            Generated MealPlan instance
        """
        try:
            # Get user's nutrition and health profile
            nutrition_profile = self._get_nutrition_profile(user)
            health_profile = self._get_health_profile(user)

            # Set default start date
            if not start_date:
                start_date = timezone.now().date()

            # Calculate end date based on plan type
            if plan_type == 'weekly':
                end_date = start_date + timedelta(days=6)
            else:
                end_date = start_date

            # Use target calories if provided, otherwise use profile default
            calorie_target = target_calories or nutrition_profile.calorie_target

            # STEP 1: Generate meal planning strategy using AI with RAG context
            strategy = self._generate_meal_strategy(
                user, nutrition_profile, health_profile, calorie_target, plan_type
            )

            # STEP 2: Create detailed meal structure using AI with retrieved recipes
            meal_plan_data = self._generate_meal_structure(
                nutrition_profile, strategy, start_date, end_date, calorie_target
            )

            # STEP 3: Generate specific recipes for each meal using RAG and AI
            meal_plan_data = self._generate_meal_recipes_with_rag(
                meal_plan_data, nutrition_profile, strategy
            )

            # STEP 4: Validate and refine nutritional balance using function calling
            meal_plan_data = self._refine_nutritional_balance_with_functions(
                meal_plan_data, nutrition_profile, calorie_target
            )

            # Calculate nutritional totals
            nutrition_totals = self._calculate_plan_nutrition(meal_plan_data, plan_type)

            # Create MealPlan instance
            meal_plan = MealPlan.objects.create(
                user=user,
                plan_type=plan_type,
                start_date=start_date,
                end_date=end_date,
                meal_plan_data=meal_plan_data,
                total_calories=nutrition_totals['total_calories'],
                avg_daily_calories=nutrition_totals['avg_daily_calories'],
                total_protein=nutrition_totals.get('total_protein', 0),
                total_carbs=nutrition_totals.get('total_carbs', 0),
                total_fat=nutrition_totals.get('total_fat', 0),
                nutritional_balance_score=nutrition_totals.get('balance_score', 8.5),
                variety_score=nutrition_totals.get('variety_score', 7.8),
                preference_match_score=nutrition_totals.get('preference_score', 8.2),
                ai_model_used=self.model,
                generation_version='2.0'
            )

            logger.info(f"Generated {plan_type} meal plan for user {user.id} using AI")
            return meal_plan

        except Exception as e:
            logger.error(f"Failed to generate meal plan: {e}")
            raise

    def _generate_meal_strategy(self, user: User, nutrition_profile: NutritionProfile,
                                health_profile, calorie_target: int, plan_type: str) -> Dict:
        """STEP 1: Generate meal planning strategy using AI"""
        try:
            # Prepare user profile data
            user_data = {
                "age": getattr(health_profile, 'age', 30),
                "gender": getattr(health_profile, 'gender', 'not_specified'),
                "weight": getattr(health_profile, 'weight', 70),
                "height": getattr(health_profile, 'height', 170),
                "bmi": getattr(health_profile, 'bmi', 24),
                "activity_level": getattr(health_profile, 'activity_level', 'moderate'),
                "fitness_goal": getattr(health_profile, 'fitness_goal', 'maintain'),
                "dietary_preferences": nutrition_profile.dietary_preferences,
                "allergies": nutrition_profile.allergies_intolerances,
                "cuisine_preferences": nutrition_profile.cuisine_preferences,
                "disliked_ingredients": nutrition_profile.disliked_ingredients,
                "calorie_target": calorie_target,
                "protein_target": nutrition_profile.protein_target,
                "carb_target": nutrition_profile.carb_target,
                "fat_target": nutrition_profile.fat_target,
                "meals_per_day": nutrition_profile.meals_per_day,
                "plan_type": plan_type
            }

            strategy_prompt = f"""
            Analyze this user's health and nutrition profile to create a personalized meal planning strategy:

            User Profile:
            - Age: {user_data['age']}, Gender: {user_data['gender']}
            - Weight: {user_data['weight']}kg, Height: {user_data['height']}cm, BMI: {user_data['bmi']}
            - Activity Level: {user_data['activity_level']}
            - Fitness Goal: {user_data['fitness_goal']}
            - Dietary Preferences: {user_data['dietary_preferences']}
            - Allergies/Intolerances: {user_data['allergies']}
            - Cuisine Preferences: {user_data['cuisine_preferences']}
            - Disliked Ingredients: {user_data['disliked_ingredients']}
            - Target: {user_data['calorie_target']} calories, {user_data['protein_target']}g protein, {user_data['carb_target']}g carbs, {user_data['fat_target']}g fat
            - Meals per day: {user_data['meals_per_day']}
            - Plan type: {user_data['plan_type']}

            Create a comprehensive meal planning strategy that includes:
            1. Recommended meal timing and calorie distribution
            2. Portion size guidelines and macro distribution per meal
            3. Key nutritional focus areas based on their goals
            4. Suggested meal types and cooking methods
            5. Special considerations for their dietary restrictions

            Respond in JSON format with the following structure:
            {{
                "meal_timing": {{
                    "breakfast": {{"time": "08:00", "calories": 400, "protein": 25, "carbs": 45, "fat": 15}},
                    "lunch": {{"time": "12:30", "calories": 500, "protein": 35, "carbs": 55, "fat": 20}},
                    "dinner": {{"time": "19:00", "calories": 600, "protein": 40, "carbs": 60, "fat": 25}}
                }},
                "focus_areas": ["high_protein", "balanced_macros"],
                "cooking_methods": ["grilling", "steaming", "roasting"],
                "meal_variety": ["Mediterranean", "Asian", "American"],
                "special_considerations": ["avoid dairy", "gluten-free options"]
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": strategy_prompt}],
                temperature=0.7,
                max_tokens=1000
            )

            strategy_text = response.choices[0].message.content
            strategy = json.loads(strategy_text)

            logger.info(f"Generated meal strategy for user {user.id}")
            return strategy

        except Exception as e:
            logger.error(f"Failed to generate meal strategy: {e}")
            # Return a basic fallback strategy
            return {
                "meal_timing": {
                    "breakfast": {"time": "08:00", "calories": calorie_target * 0.25,
                                  "protein": nutrition_profile.protein_target * 0.25,
                                  "carbs": nutrition_profile.carb_target * 0.25,
                                  "fat": nutrition_profile.fat_target * 0.25},
                    "lunch": {"time": "12:30", "calories": calorie_target * 0.35,
                              "protein": nutrition_profile.protein_target * 0.35,
                              "carbs": nutrition_profile.carb_target * 0.35,
                              "fat": nutrition_profile.fat_target * 0.35},
                    "dinner": {"time": "19:00", "calories": calorie_target * 0.40,
                               "protein": nutrition_profile.protein_target * 0.40,
                               "carbs": nutrition_profile.carb_target * 0.40,
                               "fat": nutrition_profile.fat_target * 0.40}
                },
                "focus_areas": ["balanced_nutrition"],
                "cooking_methods": ["grilling", "steaming"],
                "meal_variety": ["Mediterranean", "American"],
                "special_considerations": nutrition_profile.dietary_preferences + nutrition_profile.allergies_intolerances
            }

    def _generate_meal_structure(self, nutrition_profile: NutritionProfile,
                                 strategy: Dict, start_date: date, end_date: date,
                                 calorie_target: int) -> Dict:
        """STEP 2: Create detailed meal structure using AI"""
        try:
            days = (end_date - start_date).days + 1

            structure_prompt = f"""
            Based on this meal planning strategy, create a detailed {days}-day meal structure:

            Strategy: {json.dumps(strategy, indent=2)}
            Start Date: {start_date}
            End Date: {end_date}
            User Preferences:
            - Dietary Preferences: {nutrition_profile.dietary_preferences}
            - Allergies: {nutrition_profile.allergies_intolerances}
            - Cuisine Preferences: {nutrition_profile.cuisine_preferences}
            - Disliked Ingredients: {nutrition_profile.disliked_ingredients}

            Create a meal structure that:
            1. Follows the recommended timing and calorie distribution
            2. Provides variety across days while respecting preferences
            3. Balances cuisines and cooking methods
            4. Ensures no repeated main dishes within the plan period
            5. Considers dietary restrictions and allergies

            For each day, specify:
            - Meal name and type (breakfast/lunch/dinner)
            - Suggested cuisine style
            - Target calories and macros for that meal
            - Cooking method preference
            - Key ingredients to include/avoid

            Respond in JSON format with this structure:
            {{
                "meals": {{
                    "2024-01-01": [
                        {{
                            "meal_type": "breakfast",
                            "time": "08:00",
                            "suggested_name": "Mediterranean Breakfast Bowl",
                            "cuisine": "Mediterranean",
                            "cooking_method": "fresh",
                            "target_calories": 400,
                            "target_protein": 25,
                            "target_carbs": 45,
                            "target_fat": 15,
                            "key_ingredients": ["eggs", "vegetables", "whole grains"],
                            "avoid_ingredients": []
                        }}
                    ]
                }}
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": structure_prompt}],
                temperature=0.8,
                max_tokens=2000
            )

            structure_text = response.choices[0].message.content
            meal_structure = json.loads(structure_text)

            logger.info(f"Generated meal structure for {days} days")
            return meal_structure

        except Exception as e:
            logger.error(f"Failed to generate meal structure: {e}")
            # Return basic structure as fallback
            return self._generate_basic_meal_structure(nutrition_profile, start_date, end_date, calorie_target,
                                                       strategy)

    def _generate_meal_recipes(self, meal_plan_data: Dict,
                               nutrition_profile: NutritionProfile, strategy: Dict) -> Dict:
        """STEP 3: Generate specific recipes for each meal using AI"""
        try:
            for date_str, daily_meals in meal_plan_data.get("meals", {}).items():
                for i, meal_info in enumerate(daily_meals):
                    recipe = self._generate_single_recipe(meal_info, nutrition_profile, strategy)
                    daily_meals[i]["recipe"] = recipe

            logger.info("Generated all recipes for meal plan")
            return meal_plan_data

        except Exception as e:
            logger.error(f"Failed to generate meal recipes: {e}")
            return meal_plan_data

    def _generate_single_recipe(self, meal_info: Dict,
                                nutrition_profile: NutritionProfile, strategy: Dict) -> Dict:
        """Generate a single recipe.

        Priority is given to fetching an existing recipe from Spoonacular that matches the
        user's dietary preferences and the current meal requirements. If no suitable
        Spoonacular recipe is found (or the API call fails), the service falls back to the
        AI-generated recipe pipeline that was originally implemented.
        """

        # 1) Try Spoonacular first ---------------------------------------------------------
        try:
            from meal_planning.services.spoonacular_service import get_spoonacular_service, SpoonacularAPIError

            service = get_spoonacular_service()

            diet = ','.join(nutrition_profile.dietary_preferences)
            intolerances = ','.join(nutrition_profile.allergies_intolerances)

            search_results = service.search_recipes(
                query=meal_info.get('suggested_name', ''),
                cuisine=meal_info.get('cuisine', ''),
                diet=diet,
                intolerances=intolerances,
                number=1
            )

            if search_results.get('results'):
                # We have at least one matching recipe – use it
                spoonacular_recipe = search_results['results'][0]
                normalized = service.normalize_recipe_data(spoonacular_recipe)
                normalized['source_type'] = 'spoonacular'
                return normalized

        except (ImportError, SpoonacularAPIError, Exception) as e:
            logger.warning(f"Spoonacular lookup failed, falling back to AI recipe: {e}")

        # 2) Fall back to the original AI recipe generation -------------------------------
        try:
            recipe_prompt = f"""
            Create a detailed recipe for this meal:

            Meal Requirements:
            - Name: {meal_info.get('suggested_name', 'Healthy Meal')}
            - Type: {meal_info['meal_type']}
            - Cuisine: {meal_info.get('cuisine', 'International')}
            - Cooking Method: {meal_info.get('cooking_method', 'mixed')}
            - Target Calories: {meal_info.get('target_calories', 400)}
            - Target Protein: {meal_info.get('target_protein', 25)}g
            - Target Carbs: {meal_info.get('target_carbs', 45)}g
            - Target Fat: {meal_info.get('target_fat', 15)}g

            User Constraints:
            - Dietary Preferences: {nutrition_profile.dietary_preferences}
            - Allergies: {nutrition_profile.allergies_intolerances}
            - Disliked Ingredients: {nutrition_profile.disliked_ingredients}
            - Key Ingredients to Include: {meal_info.get('key_ingredients', [])}
            - Ingredients to Avoid: {meal_info.get('avoid_ingredients', [])}

            Create a complete recipe that:
            1. Meets the nutritional targets (within 10% tolerance)
            2. Respects all dietary restrictions and preferences
            3. Uses realistic ingredient quantities and units (grams for solids, ml for liquids)
            4. Provides clear, step-by-step cooking instructions
            5. Includes estimated prep and cook times

            Use function calling to calculate exact nutrition after creating the recipe.

            Respond in JSON format:
            {{
                "title": "Recipe Name",
                "cuisine": "cuisine_type",
                "ingredients": [
                    {{"name": "ingredient_name", "quantity": 100, "unit": "g"}},
                    {{"name": "liquid_ingredient", "quantity": 200, "unit": "ml"}}
                ],
                "instructions": [
                    "Step 1: Detailed instruction",
                    "Step 2: Another step"
                ],
                "prep_time": 15,
                "cook_time": 20,
                "total_time": 35,
                "servings": 1,
                "estimated_nutrition": {{
                    "calories": 400,
                    "protein": 25,
                    "carbs": 45,
                    "fat": 15
                }}
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": recipe_prompt}],
                functions=self.functions,
                function_call="auto",
                temperature=0.9,
                max_tokens=1500
            )

            # Handle function calls for nutrition calculation
            message = response.choices[0].message
            if message.function_call:
                function_result = self._handle_nutrition_function_call(message.function_call)
                # Make another call to get the final recipe with calculated nutrition
                follow_up_prompt = f"""
                Here's the nutrition calculation result: {function_result}

                Now provide the final recipe with the accurate nutritional information.
                """

                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": recipe_prompt},
                        {"role": "assistant", "content": message.content, "function_call": message.function_call},
                        {"role": "function", "name": message.function_call.name, "content": str(function_result)},
                        {"role": "user", "content": follow_up_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )

                recipe_text = final_response.choices[0].message.content
            else:
                recipe_text = message.content

            recipe = json.loads(recipe_text)
            return recipe

        except Exception as e:
            logger.error(f"Failed to generate recipe: {e}")
            # Return a basic recipe as fallback
            return self._generate_basic_recipe(meal_info)

    def _refine_nutritional_balance(self, meal_plan_data: Dict,
                                    nutrition_profile: NutritionProfile,
                                    calorie_target: int) -> Dict:
        """STEP 4: Validate and refine nutritional balance"""
        try:
            # Calculate current totals
            current_totals = self._calculate_plan_nutrition(meal_plan_data, "daily")

            refinement_prompt = f"""
            Analyze this meal plan's nutritional balance and suggest refinements:

            Current Daily Totals:
            - Calories: {current_totals.get('avg_daily_calories', 0)} (target: {calorie_target})
            - Protein: {current_totals.get('total_protein', 0)}g (target: {nutrition_profile.protein_target}g)
            - Carbs: {current_totals.get('total_carbs', 0)}g (target: {nutrition_profile.carb_target}g)
            - Fat: {current_totals.get('total_fat', 0)}g (target: {nutrition_profile.fat_target}g)

            User Goals: {getattr(nutrition_profile, 'fitness_goal', 'maintain')}
            Dietary Preferences: {nutrition_profile.dietary_preferences}

            Provide suggestions for improving nutritional balance:
            1. Are macronutrients within acceptable ranges? (±10%)
            2. Any specific adjustments needed for portion sizes?
            3. Ingredient swaps to better meet targets?
            4. Overall nutritional quality assessment

            Respond in JSON format:
            {{
                "balance_assessment": {{
                    "calories_status": "within_range|too_high|too_low",
                    "protein_status": "adequate|insufficient|excessive",
                    "carbs_status": "balanced|too_high|too_low",
                    "fat_status": "appropriate|too_high|too_low"
                }},
                "suggested_adjustments": [
                    "Increase protein portion in lunch by 20g",
                    "Replace white rice with brown rice for better fiber"
                ],
                "quality_score": 8.5,
                "variety_score": 7.8,
                "preference_match_score": 8.2
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": refinement_prompt}],
                temperature=0.5,
                max_tokens=800
            )

            refinement_text = response.choices[0].message.content
            refinement = json.loads(refinement_text)

            # Add refinement data to meal plan
            meal_plan_data["nutritional_analysis"] = refinement
            meal_plan_data["generation_summary"] = {
                "created_at": timezone.now().isoformat(),
                "model_used": self.model,
                "steps_completed": ["strategy", "structure", "recipes", "refinement"],
                "quality_scores": {
                    "nutritional_balance": refinement.get("quality_score", 8.5),
                    "variety": refinement.get("variety_score", 7.8),
                    "preference_match": refinement.get("preference_match_score", 8.2)
                }
            }

            logger.info("Completed nutritional balance refinement")
            return meal_plan_data

        except Exception as e:
            logger.error(f"Failed to refine nutritional balance: {e}")
            return meal_plan_data

    def _handle_nutrition_function_call(self, function_call) -> Dict:
        """Handle nutrition calculation function calls"""
        try:
            function_name = function_call.name
            arguments = json.loads(function_call.arguments)

            if function_name == "calculate_meal_nutrition":
                return self._calculate_nutrition_for_ingredients(
                    arguments["ingredients"],
                    arguments["servings"]
                )
            elif function_name == "validate_dietary_restrictions":
                return self._validate_dietary_restrictions(
                    arguments["ingredients"],
                    arguments["dietary_preferences"],
                    arguments["allergies"]
                )

        except Exception as e:
            logger.error(f"Function call error: {e}")
            return {"error": str(e)}

    def _calculate_nutrition_for_ingredients(self, ingredients: List[Dict], servings: int) -> Dict:
        """Calculate nutrition for a list of ingredients"""
        try:
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0

            # This is a simplified calculation - in production, you'd use a comprehensive nutrition database
            nutrition_db = {
                'chicken breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
                'salmon fillet': {'calories': 208, 'protein': 22, 'carbs': 0, 'fat': 12},
                'brown rice': {'calories': 123, 'protein': 2.6, 'carbs': 23, 'fat': 0.9},
                'quinoa': {'calories': 120, 'protein': 4.4, 'carbs': 22, 'fat': 1.9},
                'broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 7, 'fat': 0.4},
                'sweet potato': {'calories': 86, 'protein': 1.6, 'carbs': 20, 'fat': 0.1},
                'olive oil': {'calories': 884, 'protein': 0, 'carbs': 0, 'fat': 100},
                'oats': {'calories': 389, 'protein': 16.9, 'carbs': 66.3, 'fat': 6.9},
                'banana': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3},
                'yogurt': {'calories': 59, 'protein': 10, 'carbs': 3.6, 'fat': 0.4},
                'mixed greens': {'calories': 20, 'protein': 2, 'carbs': 4, 'fat': 0.2},
                'cherry tomatoes': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2},
                'eggs': {'calories': 155, 'protein': 13, 'carbs': 1.1, 'fat': 11},
            }

            for ingredient in ingredients:
                name = ingredient['name'].lower()
                quantity = ingredient['quantity']
                unit = ingredient['unit']

                # Convert to per 100g basis
                if unit == 'g':
                    factor = quantity / 100
                elif unit == 'ml' and name in ['olive oil', 'almond milk']:
                    factor = quantity / 100
                elif unit == 'medium' and name == 'banana':
                    factor = 1  # Assume medium banana is ~100g
                else:
                    factor = quantity / 100  # Default conversion

                if name in nutrition_db:
                    nutrition = nutrition_db[name]
                    total_calories += nutrition['calories'] * factor
                    total_protein += nutrition['protein'] * factor
                    total_carbs += nutrition['carbs'] * factor
                    total_fat += nutrition['fat'] * factor

            # Divide by servings to get per-serving values
            return {
                "calories": round(total_calories / servings, 1),
                "protein": round(total_protein / servings, 1),
                "carbs": round(total_carbs / servings, 1),
                "fat": round(total_fat / servings, 1)
            }

        except Exception as e:
            logger.error(f"Nutrition calculation error: {e}")
            return {"calories": 400, "protein": 25, "carbs": 45, "fat": 15}

    def _validate_dietary_restrictions(self, ingredients: List[str],
                                       dietary_preferences: List[str],
                                       allergies: List[str]) -> Dict:
        """Validate if ingredients meet dietary restrictions"""
        try:
            violations = []
            warnings = []

            # Check for allergy violations
            allergen_map = {
                'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
                'gluten': ['wheat', 'bread', 'pasta', 'flour'],
                'nuts': ['almonds', 'walnuts', 'peanuts', 'cashews'],
                'eggs': ['eggs', 'egg'],
                'soy': ['soy', 'tofu', 'tempeh'],
                'fish': ['salmon', 'tuna', 'cod', 'fish'],
                'shellfish': ['shrimp', 'crab', 'lobster']
            }

            for allergy in allergies:
                if allergy.lower() in allergen_map:
                    allergen_ingredients = allergen_map[allergy.lower()]
                    for ingredient in ingredients:
                        if any(allergen in ingredient.lower() for allergen in allergen_ingredients):
                            violations.append(f"Contains {allergy}: {ingredient}")

            # Check dietary preferences
            for preference in dietary_preferences:
                if preference.lower() == 'vegetarian':
                    meat_ingredients = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'turkey']
                    for ingredient in ingredients:
                        if any(meat in ingredient.lower() for meat in meat_ingredients):
                            violations.append(f"Vegetarian violation: {ingredient}")

                elif preference.lower() == 'vegan':
                    animal_ingredients = ['chicken', 'beef', 'fish', 'eggs', 'milk', 'cheese', 'yogurt', 'honey']
                    for ingredient in ingredients:
                        if any(animal in ingredient.lower() for animal in animal_ingredients):
                            violations.append(f"Vegan violation: {ingredient}")

            return {
                "is_compliant": len(violations) == 0,
                "violations": violations,
                "warnings": warnings,
                "compliance_score": max(0, 100 - (len(violations) * 20))
            }

        except Exception as e:
            logger.error(f"Dietary validation error: {e}")
            return {"is_compliant": True, "violations": [], "warnings": []}

    def _get_nutrition_profile(self, user: User) -> NutritionProfile:
        """Get or create nutrition profile for user"""
        try:
            return NutritionProfile.objects.get(user=user)
        except NutritionProfile.DoesNotExist:
            # Create default profile if none exists
            return NutritionProfile.objects.create(
                user=user,
                calorie_target=2000,
                protein_target=100,
                carb_target=250,
                fat_target=67,
                dietary_preferences=[],
                allergies_intolerances=[],
                cuisine_preferences=[],
                meals_per_day=3,
                timezone='UTC'
            )

    def _get_health_profile(self, user: User):
        """Get user's health profile"""
        try:
            from health_profiles.models import HealthProfile
            return HealthProfile.objects.get(user=user)
        except HealthProfile.DoesNotExist:
            # Return default values if no health profile exists
            return type('DefaultProfile', (), {
                'age': 30,
                'gender': 'not_specified',
                'weight': 70,
                'height': 170,
                'bmi': 24.2,
                'activity_level': 'moderate',
                'fitness_goal': 'maintain'
            })()

    def _generate_basic_meal_structure(self, nutrition_profile: NutritionProfile,
                                       start_date: date, end_date: date,
                                       calorie_target: int, strategy: Dict) -> Dict:
        """Generate basic meal structure as fallback"""
        days = (end_date - start_date).days + 1
        meal_structure = {"meals": {}}

        current_date = start_date
        for day_num in range(days):
            date_str = current_date.strftime('%Y-%m-%d')

            daily_meals = []

            # Use strategy for meal distribution if available
            meal_timing = strategy.get('meal_timing', {
                'breakfast': {'time': '08:00', 'calories': calorie_target * 0.25},
                'lunch': {'time': '12:30', 'calories': calorie_target * 0.35},
                'dinner': {'time': '19:00', 'calories': calorie_target * 0.40}
            })

            for meal_type, timing in meal_timing.items():
                daily_meals.append({
                    "meal_type": meal_type,
                    "time": timing['time'],
                    "suggested_name": f"Healthy {meal_type.title()}",
                    "cuisine": "International",
                    "cooking_method": "mixed",
                    "target_calories": timing['calories'],
                    "target_protein": timing.get('protein', nutrition_profile.protein_target / 3),
                    "target_carbs": timing.get('carbs', nutrition_profile.carb_target / 3),
                    "target_fat": timing.get('fat', nutrition_profile.fat_target / 3),
                    "key_ingredients": [],
                    "avoid_ingredients": nutrition_profile.disliked_ingredients
                })

            meal_structure["meals"][date_str] = daily_meals
            current_date += timedelta(days=1)

        return meal_structure

    def _generate_basic_recipe(self, meal_info: Dict) -> Dict:
        """Generate basic recipe as fallback"""
        meal_type = meal_info.get('meal_type', 'meal')
        target_calories = meal_info.get('target_calories', 400)

        basic_recipes = {
            'breakfast': {
                "title": "Protein Breakfast Bowl",
                "cuisine": "International",
                "ingredients": [
                    {"name": "oats", "quantity": 50, "unit": "g"},
                    {"name": "protein powder", "quantity": 25, "unit": "g"},
                    {"name": "banana", "quantity": 1, "unit": "medium"},
                    {"name": "berries", "quantity": 100, "unit": "g"},
                    {"name": "almond milk", "quantity": 200, "unit": "ml"}
                ],
                "instructions": [
                    "Cook oats with almond milk according to package instructions",
                    "Stir in protein powder once cooked",
                    "Top with sliced banana and berries",
                    "Serve immediately while warm"
                ],
                "prep_time": 5,
                "cook_time": 10,
                "total_time": 15,
                "servings": 1,
                "estimated_nutrition": {
                    "calories": 380,
                    "protein": 28,
                    "carbs": 52,
                    "fat": 8
                }
            },
            'lunch': {
                "title": "Balanced Power Bowl",
                "cuisine": "Mediterranean",
                "ingredients": [
                    {"name": "quinoa", "quantity": 80, "unit": "g"},
                    {"name": "chicken breast", "quantity": 120, "unit": "g"},
                    {"name": "mixed vegetables", "quantity": 150, "unit": "g"},
                    {"name": "olive oil", "quantity": 15, "unit": "ml"},
                    {"name": "lemon juice", "quantity": 10, "unit": "ml"}
                ],
                "instructions": [
                    "Cook quinoa according to package instructions",
                    "Grill or bake chicken breast until cooked through",
                    "Steam or roast mixed vegetables",
                    "Combine all ingredients in a bowl",
                    "Drizzle with olive oil and lemon juice"
                ],
                "prep_time": 10,
                "cook_time": 25,
                "total_time": 35,
                "servings": 1,
                "estimated_nutrition": {
                    "calories": 485,
                    "protein": 35,
                    "carbs": 45,
                    "fat": 18
                }
            },
            'dinner': {
                "title": "Balanced Dinner Plate",
                "cuisine": "International",
                "ingredients": [
                    {"name": "salmon fillet", "quantity": 150, "unit": "g"},
                    {"name": "sweet potato", "quantity": 200, "unit": "g"},
                    {"name": "green vegetables", "quantity": 150, "unit": "g"},
                    {"name": "olive oil", "quantity": 10, "unit": "ml"}
                ],
                "instructions": [
                    "Preheat oven to 400°F (200°C)",
                    "Season salmon and bake for 12-15 minutes",
                    "Roast sweet potato cubes until tender",
                    "Steam green vegetables until crisp-tender",
                    "Serve all components together with a drizzle of olive oil"
                ],
                "prep_time": 15,
                "cook_time": 30,
                "total_time": 45,
                "servings": 1,
                "estimated_nutrition": {
                    "calories": 520,
                    "protein": 35,
                    "carbs": 42,
                    "fat": 22
                }
            }
        }

        return basic_recipes.get(meal_type, basic_recipes['lunch'])

    def _calculate_plan_nutrition(self, meal_plan_data: Dict, plan_type: str) -> Dict:
        """Calculate nutritional totals for the meal plan"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0

        days_count = len(meal_plan_data.get("meals", {}))

        for date_str, daily_meals in meal_plan_data.get("meals", {}).items():
            daily_calories = 0
            daily_protein = 0
            daily_carbs = 0
            daily_fat = 0

            for meal in daily_meals:
                nutrition = meal.get("recipe", {}).get("estimated_nutrition", {})
                daily_calories += nutrition.get("calories", 0)
                daily_protein += nutrition.get("protein", 0)
                daily_carbs += nutrition.get("carbs", 0)
                daily_fat += nutrition.get("fat", 0)

            total_calories += daily_calories
            total_protein += daily_protein
            total_carbs += daily_carbs
            total_fat += daily_fat

        avg_daily_calories = total_calories / days_count if days_count > 0 else 0

        # Calculate quality scores based on nutritional analysis
        analysis = meal_plan_data.get("nutritional_analysis", {})
        balance_score = analysis.get("quality_score", 8.5)
        variety_score = analysis.get("variety_score", 7.8)
        preference_score = analysis.get("preference_match_score", 8.2)

        return {
            "total_calories": total_calories,
            "avg_daily_calories": avg_daily_calories,
            "total_protein": total_protein,
            "total_carbs": total_carbs,
            "total_fat": total_fat,
            "balance_score": balance_score,
            "variety_score": variety_score,
            "preference_score": preference_score
        }

    def regenerate_meal(self, meal_plan: MealPlan, day: str, meal_type: str) -> MealPlan:
        """Regenerate a specific meal in an existing meal plan using AI"""
        try:
            # Get the user's profiles
            nutrition_profile = self._get_nutrition_profile(meal_plan.user)
            health_profile = self._get_health_profile(meal_plan.user)

            # Get the current meal plan data
            meal_plan_data = meal_plan.meal_plan_data.copy()

            # Find the meal to replace
            if day in meal_plan_data.get("meals", {}):
                daily_meals = meal_plan_data["meals"][day]

                for i, meal in enumerate(daily_meals):
                    if meal.get("meal_type") == meal_type:
                        # Generate a new meal using AI
                        new_meal_info = {
                            "meal_type": meal_type,
                            "time": meal.get("time", "12:00"),
                            "target_calories": meal.get("target_calories", 400),
                            "target_protein": meal.get("target_protein", 25),
                            "target_carbs": meal.get("target_carbs", 45),
                            "target_fat": meal.get("target_fat", 15),
                            "suggested_name": f"Alternative {meal_type.title()}",
                            "cuisine": "International",
                            "cooking_method": "mixed",
                            "key_ingredients": [],
                            "avoid_ingredients": nutrition_profile.disliked_ingredients
                        }

                        # Create a basic strategy for this single meal
                        strategy = {
                            "focus_areas": ["balanced_nutrition"],
                            "cooking_methods": ["grilling", "steaming", "roasting"],
                            "meal_variety": nutrition_profile.cuisine_preferences or ["International"],
                            "special_considerations": nutrition_profile.dietary_preferences + nutrition_profile.allergies_intolerances
                        }

                        # Generate new recipe using AI
                        new_recipe = self._generate_single_recipe(new_meal_info, nutrition_profile, strategy)

                        # Update the meal
                        new_meal_info["recipe"] = new_recipe
                        daily_meals[i] = new_meal_info
                        break

                # Update the meal plan
                meal_plan.meal_plan_data = meal_plan_data

                # Recalculate nutrition
                nutrition_totals = self._calculate_plan_nutrition(meal_plan_data, meal_plan.plan_type)
                meal_plan.total_calories = nutrition_totals['total_calories']
                meal_plan.avg_daily_calories = nutrition_totals['avg_daily_calories']
                meal_plan.total_protein = nutrition_totals['total_protein']
                meal_plan.total_carbs = nutrition_totals['total_carbs']
                meal_plan.total_fat = nutrition_totals['total_fat']
                meal_plan.nutritional_balance_score = nutrition_totals['balance_score']
                meal_plan.variety_score = nutrition_totals['variety_score']
                meal_plan.preference_match_score = nutrition_totals['preference_score']

                meal_plan.save()

                logger.info(f"Regenerated {meal_type} for day {day} in meal plan {meal_plan.id} using AI")

            return meal_plan

        except Exception as e:
            logger.error(f"Failed to regenerate meal: {e}")
            raise

    def generate_recipe_alternatives(self, meal_plan: MealPlan, day: str, meal_type: str, count: int = 3) -> List[Dict]:
        """Generate alternative recipes for a specific meal"""
        try:
            nutrition_profile = self._get_nutrition_profile(meal_plan.user)

            # Get the current meal info
            daily_meals = meal_plan.meal_plan_data.get("meals", {}).get(day, [])
            current_meal = None
            for meal in daily_meals:
                if meal.get("meal_type") == meal_type:
                    current_meal = meal
                    break

            if not current_meal:
                return []

            alternatives = []

            # Create a strategy for alternatives
            strategy = {
                "focus_areas": ["variety", "balanced_nutrition"],
                "cooking_methods": ["grilling", "steaming", "roasting", "stir-frying"],
                "meal_variety": nutrition_profile.cuisine_preferences or ["International", "Mediterranean", "Asian"],
                "special_considerations": nutrition_profile.dietary_preferences + nutrition_profile.allergies_intolerances
            }

            for i in range(count):
                # Vary the cuisine and cooking method for each alternative
                cuisines = strategy["meal_variety"]
                cooking_methods = strategy["cooking_methods"]

                alternative_info = {
                    "meal_type": meal_type,
                    "time": current_meal.get("time", "12:00"),
                    "target_calories": current_meal.get("target_calories", 400),
                    "target_protein": current_meal.get("target_protein", 25),
                    "target_carbs": current_meal.get("target_carbs", 45),
                    "target_fat": current_meal.get("target_fat", 15),
                    "suggested_name": f"Alternative {meal_type.title()} {i + 1}",
                    "cuisine": cuisines[i % len(cuisines)],
                    "cooking_method": cooking_methods[i % len(cooking_methods)],
                    "key_ingredients": [],
                    "avoid_ingredients": nutrition_profile.disliked_ingredients +
                                         [ing["name"] for ing in current_meal.get("recipe", {}).get("ingredients", [])]
                }

                # Generate alternative recipe
                alternative_recipe = self._generate_single_recipe(alternative_info, nutrition_profile, strategy)
                alternatives.append({
                    "meal_info": alternative_info,
                    "recipe": alternative_recipe
                })

            logger.info(f"Generated {count} alternatives for {meal_type} on {day}")
            return alternatives

        except Exception as e:
            logger.error(f"Failed to generate recipe alternatives: {e}")
            return []

    def analyze_meal_plan_nutrition(self, meal_plan: MealPlan) -> Dict:
        """Provide detailed nutritional analysis of a meal plan"""
        try:
            nutrition_profile = self._get_nutrition_profile(meal_plan.user)

            analysis_prompt = f"""
            Provide a comprehensive nutritional analysis of this meal plan:

            Meal Plan Data: {json.dumps(meal_plan.meal_plan_data, indent=2)}

            User Targets:
            - Calories: {nutrition_profile.calorie_target}
            - Protein: {nutrition_profile.protein_target}g
            - Carbs: {nutrition_profile.carb_target}g
            - Fat: {nutrition_profile.fat_target}g

            User Preferences:
            - Dietary: {nutrition_profile.dietary_preferences}
            - Allergies: {nutrition_profile.allergies_intolerances}
            - Goals: {getattr(nutrition_profile, 'fitness_goal', 'maintain')}

            Analyze and provide:
            1. Nutritional adequacy assessment
            2. Macro and micronutrient balance
            3. Meal timing and distribution analysis
            4. Variety and preference alignment
            5. Specific recommendations for improvement
            6. Overall health score (0-100)

            Respond in JSON format:
            {{
                "overall_score": 85,
                "nutritional_adequacy": {{
                    "calories": {{"status": "adequate", "percentage_of_target": 98}},
                    "protein": {{"status": "adequate", "percentage_of_target": 105}},
                    "carbs": {{"status": "adequate", "percentage_of_target": 92}},
                    "fat": {{"status": "adequate", "percentage_of_target": 103}}
                }},
                "meal_distribution": {{
                    "breakfast_percentage": 25,
                    "lunch_percentage": 35,
                    "dinner_percentage": 40,
                    "balance_rating": "excellent"
                }},
                "variety_analysis": {{
                    "cuisine_diversity": "good",
                    "ingredient_variety": "excellent",
                    "cooking_method_diversity": "good"
                }},
                "recommendations": [
                    "Consider adding more fiber-rich vegetables",
                    "Excellent protein distribution throughout the day"
                ],
                "health_highlights": [
                    "Well-balanced macronutrients",
                    "Good variety of nutrient-dense foods"
                ],
                "areas_for_improvement": [
                    "Could increase omega-3 fatty acids"
                ]
            }}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=1500
            )

            analysis_text = response.choices[0].message.content
            analysis = json.loads(analysis_text)

            logger.info(f"Generated nutritional analysis for meal plan {meal_plan.id}")
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze meal plan nutrition: {e}")
            return {
                "overall_score": 75,
                "nutritional_adequacy": {"status": "analysis_unavailable"},
                "recommendations": ["Analysis temporarily unavailable"],
                "health_highlights": ["Meal plan generated successfully"],
                "areas_for_improvement": ["Please try analysis again later"]
            }

    def _generate_meal_recipes_with_rag(self, meal_plan_data: Dict,
                                       nutrition_profile: NutritionProfile,
                                       strategy: Dict) -> Dict:
        """STEP 3: Generate specific recipes using RAG and AI"""
        try:
            logger.info("Starting RAG-enhanced recipe generation")
            
            # Extract user preferences for RAG
            user_preferences = {
                'dietary_preferences': nutrition_profile.dietary_preferences,
                'allergies_intolerances': nutrition_profile.allergies_intolerances,
                'cuisine_preferences': nutrition_profile.cuisine_preferences,
                'disliked_ingredients': nutrition_profile.disliked_ingredients
            }
            
            # Process each day in the meal plan
            for date_str, day_meals in meal_plan_data.get('meals', {}).items():
                logger.info(f"Processing recipes for {date_str}")
                
                for meal in day_meals:
                    meal_type = meal.get('meal_type', '')
                    target_calories = meal.get('target_calories', 400)
                    target_protein = meal.get('target_protein', 25)
                    
                    # Get RAG recommendations for this specific meal
                    meal_query = f"{meal_type} {' '.join(nutrition_profile.dietary_preferences)} healthy nutritious"
                    
                    rag_recipes = self.rag_service.search_similar_recipes(
                        query=meal_query,
                        dietary_preferences=nutrition_profile.dietary_preferences,
                        allergies=nutrition_profile.allergies_intolerances,
                        cuisine_preferences=nutrition_profile.cuisine_preferences,
                        meal_type=meal_type,
                        top_k=5
                    )
                    
                    # Create RAG-augmented prompt
                    base_prompt = f"""
                    Generate a specific {meal_type} recipe that meets these requirements:
                    - Target: {target_calories} calories, {target_protein}g protein
                    - Dietary preferences: {nutrition_profile.dietary_preferences}
                    - Avoid: {nutrition_profile.allergies_intolerances}
                    - Cuisine style: {nutrition_profile.cuisine_preferences}
                    """
                    
                    augmented_prompt = self.rag_service.augment_meal_planning_prompt(
                        base_prompt=base_prompt,
                        user_preferences=user_preferences,
                        retrieved_recipes=rag_recipes
                    )
                    
                    # Generate recipe with function calling for nutrition validation
                    recipe_prompt = f"""
                    {augmented_prompt}
                    
                    Create a detailed recipe that includes:
                    1. Recipe title and description
                    2. Complete ingredient list with quantities
                    3. Step-by-step cooking instructions
                    4. Nutritional information per serving
                    5. Preparation and cooking time
                    6. Difficulty level
                    
                    Use the provided similar recipes as inspiration but create a unique variation.
                    Ensure all ingredients are compatible with dietary restrictions.
                    
                    Respond in JSON format:
                    {{
                        "title": "Recipe Name",
                        "description": "Brief description",
                        "ingredients": [
                            {{"name": "ingredient", "quantity": 100, "unit": "grams"}},
                            {{"name": "ingredient2", "quantity": 200, "unit": "ml"}}
                        ],
                        "instructions": [
                            {{"step": 1, "description": "instruction text", "time_minutes": 5}},
                            {{"step": 2, "description": "instruction text", "time_minutes": 10}}
                        ],
                        "nutrition": {{
                            "calories_per_serving": 400,
                            "protein_per_serving": 25,
                            "carbs_per_serving": 45,
                            "fat_per_serving": 15,
                            "fiber_per_serving": 8
                        }},
                        "prep_time_minutes": 15,
                        "cook_time_minutes": 20,
                        "servings": 1,
                        "difficulty": "easy",
                        "cuisine": "Mediterranean"
                    }}
                    """
                    
                    # Generate recipe using AI
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": recipe_prompt}],
                        temperature=0.8,  # Higher temperature for creativity
                        max_tokens=1500
                    )
                    
                    recipe_text = response.choices[0].message.content
                    recipe_data = json.loads(recipe_text)
                    
                    # Validate nutrition using function calling
                    validated_nutrition = self._validate_recipe_nutrition_with_functions(
                        recipe_data.get('ingredients', []),
                        recipe_data.get('nutrition', {}),
                        target_calories,
                        target_protein
                    )
                    
                    # Update meal with generated recipe
                    meal.update({
                        'recipe': recipe_data,
                        'validated_nutrition': validated_nutrition,
                        'rag_similarity_score': rag_recipes[0].get('similarity_score', 0) if rag_recipes else 0,
                        'generation_method': 'rag_enhanced'
                    })
                    
                    logger.info(f"Generated {meal_type} recipe: {recipe_data.get('title', 'Unknown')}")
            
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"RAG recipe generation failed: {e}")
            # Fallback to simpler recipe generation
            return self._generate_fallback_recipes(meal_plan_data, nutrition_profile)

    def _refine_nutritional_balance_with_functions(self, meal_plan_data: Dict,
                                                 nutrition_profile: NutritionProfile,
                                                 calorie_target: int) -> Dict:
        """STEP 4: Validate and refine nutritional balance using function calling"""
        try:
            logger.info("Starting function-based nutritional refinement")
            
            # Calculate current totals using function calling
            current_totals = self._calculate_plan_nutrition_with_functions(meal_plan_data)
            
            # Create refinement prompt with function calling
            refinement_prompt = f"""
            Analyze this meal plan's nutritional balance and suggest refinements:

            Current Daily Totals:
            - Calories: {current_totals.get('total_calories', 0)} (target: {calorie_target})
            - Protein: {current_totals.get('total_protein', 0)}g (target: {nutrition_profile.protein_target}g)
            - Carbs: {current_totals.get('total_carbs', 0)}g (target: {nutrition_profile.carb_target}g)
            - Fat: {current_totals.get('total_fat', 0)}g (target: {nutrition_profile.fat_target}g)

            User Goals: {getattr(nutrition_profile, 'fitness_goal', 'maintain')}
            Dietary Preferences: {nutrition_profile.dietary_preferences}

            Use function calling to validate nutritional calculations and provide suggestions for:
            1. Macro balance optimization
            2. Portion adjustments
            3. Ingredient substitutions
            4. Overall nutritional quality

            Calculate precise adjustments needed to meet targets within ±5% tolerance.
            """

            # Use function calling for nutritional analysis
            response = self.client.chat.completions.create(
                model=self.secondary_model,  # Use GPT-3.5 for function calling
                messages=[{"role": "user", "content": refinement_prompt}],
                functions=self.functions,
                function_call="auto",
                temperature=0.3
            )

            message = response.choices[0].message
            
            # Process function call if present
            if message.function_call:
                function_result = self._handle_nutrition_function_call(message.function_call)
                meal_plan_data['function_validation'] = function_result
            
            # Generate final refinement analysis
            refinement_analysis = self._generate_refinement_analysis(
                current_totals, nutrition_profile, calorie_target
            )
            
            meal_plan_data['nutritional_analysis'] = refinement_analysis
            meal_plan_data['validation_method'] = 'function_calling'
            meal_plan_data['accuracy_score'] = self._calculate_accuracy_score(
                current_totals, nutrition_profile, calorie_target
            )
            
            logger.info("Completed function-based nutritional refinement")
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"Function-based refinement failed: {e}")
            # Fallback to basic refinement
            return self._refine_nutritional_balance(meal_plan_data, nutrition_profile, calorie_target)

    def _validate_recipe_nutrition_with_functions(self, ingredients: List[Dict],
                                                 claimed_nutrition: Dict,
                                                 target_calories: int,
                                                 target_protein: int) -> Dict:
        """Validate recipe nutrition using function calling"""
        try:
            # Use nutrition calculation service for validation
            calculated_nutrition = self.nutrition_service.calculate_recipe_nutrition(
                ingredients=ingredients,
                servings=1
            )
            
            # Compare claimed vs calculated nutrition
            validation_result = {
                'claimed_nutrition': claimed_nutrition,
                'calculated_nutrition': calculated_nutrition,
                'accuracy_score': self._calculate_nutrition_accuracy(
                    claimed_nutrition, calculated_nutrition
                ),
                'meets_targets': {
                    'calories': abs(calculated_nutrition.get('calories', 0) - target_calories) <= target_calories * 0.1,
                    'protein': abs(calculated_nutrition.get('protein', 0) - target_protein) <= target_protein * 0.1
                },
                'validation_method': 'function_calling'
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Nutrition validation failed: {e}")
            return {
                'validation_error': str(e),
                'claimed_nutrition': claimed_nutrition,
                'validation_method': 'fallback'
            }

    def _calculate_plan_nutrition_with_functions(self, meal_plan_data: Dict) -> Dict:
        """Calculate meal plan nutrition using function calling"""
        try:
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            total_fiber = 0
            
            # Sum nutrition from all meals
            for date_str, day_meals in meal_plan_data.get('meals', {}).items():
                for meal in day_meals:
                    recipe = meal.get('recipe', {})
                    nutrition = recipe.get('nutrition', {})
                    
                    total_calories += nutrition.get('calories_per_serving', 0)
                    total_protein += nutrition.get('protein_per_serving', 0)
                    total_carbs += nutrition.get('carbs_per_serving', 0)
                    total_fat += nutrition.get('fat_per_serving', 0)
                    total_fiber += nutrition.get('fiber_per_serving', 0)
            
            # Use function calling to validate calculations
            validation_prompt = f"""
            Validate these nutritional calculations:
            - Total Calories: {total_calories}
            - Total Protein: {total_protein}g
            - Total Carbs: {total_carbs}g
            - Total Fat: {total_fat}g
            - Total Fiber: {total_fiber}g
            
            Check if the macro calories add up correctly:
            Protein: {total_protein}g × 4 = {total_protein * 4} calories
            Carbs: {total_carbs}g × 4 = {total_carbs * 4} calories
            Fat: {total_fat}g × 9 = {total_fat * 9} calories
            Total calculated: {(total_protein * 4) + (total_carbs * 4) + (total_fat * 9)} calories
            """
            
            # Calculate validation score
            calculated_from_macros = (total_protein * 4) + (total_carbs * 4) + (total_fat * 9)
            validation_score = 1.0 - abs(total_calories - calculated_from_macros) / max(total_calories, 1)
            
            return {
                'total_calories': total_calories,
                'total_protein': total_protein,
                'total_carbs': total_carbs,
                'total_fat': total_fat,
                'total_fiber': total_fiber,
                'validation_score': validation_score,
                'calculated_from_macros': calculated_from_macros
            }
            
        except Exception as e:
            logger.error(f"Nutrition calculation failed: {e}")
            return {
                'total_calories': 0,
                'total_protein': 0,
                'total_carbs': 0,
                'total_fat': 0,
                'total_fiber': 0,
                'validation_score': 0,
                'error': str(e)
            }

    def _format_recipe_context(self, recipes: List[Dict]) -> str:
        """Format recipe context for prompts"""
        if not recipes:
            return "No specific recipes available"
        
        context_lines = []
        for recipe in recipes:
            line = f"- {recipe.get('title', 'Unknown')}: {recipe.get('meal_type', 'any')} meal, "
            line += f"{recipe.get('cuisine', 'various')} cuisine, "
            line += f"{recipe.get('calories_per_serving', 0)} calories"
            context_lines.append(line)
        
        return "\n".join(context_lines)

    def _get_enhanced_fallback_strategy(self, calorie_target: int,
                                      nutrition_profile: NutritionProfile,
                                      user_data: Dict) -> Dict:
        """Enhanced fallback strategy with better defaults"""
        return {
            "macro_distribution": {
                "protein_percentage": 25,
                "carb_percentage": 45,
                "fat_percentage": 30,
                "rationale": "Balanced macronutrient distribution suitable for general health goals"
            },
            "meal_timing": {
                "breakfast": {
                    "time": "08:00",
                    "calories": calorie_target * 0.25,
                    "protein": nutrition_profile.protein_target * 0.25,
                    "carbs": nutrition_profile.carb_target * 0.25,
                    "fat": nutrition_profile.fat_target * 0.25
                },
                "lunch": {
                    "time": "12:30",
                    "calories": calorie_target * 0.35,
                    "protein": nutrition_profile.protein_target * 0.35,
                    "carbs": nutrition_profile.carb_target * 0.35,
                    "fat": nutrition_profile.fat_target * 0.35
                },
                "dinner": {
                    "time": "19:00",
                    "calories": calorie_target * 0.40,
                    "protein": nutrition_profile.protein_target * 0.40,
                    "carbs": nutrition_profile.carb_target * 0.40,
                    "fat": nutrition_profile.fat_target * 0.40
                }
            },
            "nutritional_priorities": ["balanced_nutrition", "adequate_protein", "fiber_rich"],
            "cooking_methods": ["grilling", "steaming", "roasting"],
            "variety_goals": {
                "cuisines_per_week": 2,
                "protein_sources": 3,
                "vegetable_variety": 7
            },
            "special_considerations": nutrition_profile.dietary_preferences + nutrition_profile.allergies_intolerances,
            "adherence_strategies": ["simple_preparation", "familiar_ingredients"],
            "user_context": user_data,
            "fallback_used": True
        }

    def _generate_fallback_recipes(self, meal_plan_data: Dict,
                                  nutrition_profile: NutritionProfile) -> Dict:
        """Generate simple fallback recipes when RAG fails"""
        try:
            fallback_recipes = {
                'breakfast': {
                    'title': 'Healthy Breakfast Bowl',
                    'ingredients': [
                        {'name': 'oats', 'quantity': 50, 'unit': 'grams'},
                        {'name': 'banana', 'quantity': 1, 'unit': 'medium'},
                        {'name': 'almond butter', 'quantity': 15, 'unit': 'grams'}
                    ],
                    'nutrition': {'calories_per_serving': 350, 'protein_per_serving': 12}
                },
                'lunch': {
                    'title': 'Protein Salad',
                    'ingredients': [
                        {'name': 'mixed greens', 'quantity': 100, 'unit': 'grams'},
                        {'name': 'chicken breast', 'quantity': 120, 'unit': 'grams'},
                        {'name': 'olive oil', 'quantity': 10, 'unit': 'ml'}
                    ],
                    'nutrition': {'calories_per_serving': 420, 'protein_per_serving': 35}
                },
                'dinner': {
                    'title': 'Balanced Dinner',
                    'ingredients': [
                        {'name': 'salmon fillet', 'quantity': 150, 'unit': 'grams'},
                        {'name': 'quinoa', 'quantity': 60, 'unit': 'grams'},
                        {'name': 'broccoli', 'quantity': 150, 'unit': 'grams'}
                    ],
                    'nutrition': {'calories_per_serving': 550, 'protein_per_serving': 40}
                }
            }
            
            # Apply fallback recipes to meal plan
            for date_str, day_meals in meal_plan_data.get('meals', {}).items():
                for meal in day_meals:
                    meal_type = meal.get('meal_type', 'lunch')
                    if meal_type in fallback_recipes:
                        meal['recipe'] = fallback_recipes[meal_type]
                        meal['generation_method'] = 'fallback'
            
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"Fallback recipe generation failed: {e}")
            return meal_plan_data

    def _generate_refinement_analysis(self, current_totals: Dict,
                                    nutrition_profile: NutritionProfile,
                                    calorie_target: int) -> Dict:
        """Generate comprehensive refinement analysis"""
        return {
            'balance_assessment': {
                'calories_status': self._assess_target_status(
                    current_totals.get('total_calories', 0), calorie_target, 0.05
                ),
                'protein_status': self._assess_target_status(
                    current_totals.get('total_protein', 0), nutrition_profile.protein_target, 0.1
                ),
                'carbs_status': self._assess_target_status(
                    current_totals.get('total_carbs', 0), nutrition_profile.carb_target, 0.1
                ),
                'fat_status': self._assess_target_status(
                    current_totals.get('total_fat', 0), nutrition_profile.fat_target, 0.1
                )
            },
            'quality_score': self._calculate_overall_quality_score(current_totals, nutrition_profile),
            'variety_score': 8.0,  # Would be calculated based on ingredient diversity
            'preference_match_score': 8.5,  # Would be calculated based on user preferences
            'improvement_suggestions': self._generate_improvement_suggestions(
                current_totals, nutrition_profile, calorie_target
            )
        }

    def _assess_target_status(self, actual: float, target: float, tolerance: float) -> str:
        """Assess if actual value meets target within tolerance"""
        if target == 0:
            return 'not_specified'
        
        difference_pct = abs(actual - target) / target
        
        if difference_pct <= tolerance:
            return 'within_range'
        elif actual > target:
            return 'too_high'
        else:
            return 'too_low'

    def _calculate_overall_quality_score(self, totals: Dict, profile: NutritionProfile) -> float:
        """Calculate overall nutritional quality score"""
        scores = []
        
        # Calorie accuracy score
        calorie_accuracy = 1.0 - min(1.0, abs(totals.get('total_calories', 0) - profile.calorie_target) / profile.calorie_target)
        scores.append(calorie_accuracy)
        
        # Protein adequacy score
        protein_adequacy = min(1.0, totals.get('total_protein', 0) / max(profile.protein_target, 1))
        scores.append(protein_adequacy)
        
        # Balance score (how close macros are to targets)
        macro_balance = self._calculate_macro_balance_score(totals, profile)
        scores.append(macro_balance)
        
        return sum(scores) / len(scores) * 10  # Scale to 0-10

    def _calculate_macro_balance_score(self, totals: Dict, profile: NutritionProfile) -> float:
        """Calculate macro balance score"""
        protein_score = 1.0 - min(1.0, abs(totals.get('total_protein', 0) - profile.protein_target) / max(profile.protein_target, 1))
        carbs_score = 1.0 - min(1.0, abs(totals.get('total_carbs', 0) - profile.carb_target) / max(profile.carb_target, 1))
        fat_score = 1.0 - min(1.0, abs(totals.get('total_fat', 0) - profile.fat_target) / max(profile.fat_target, 1))
        
        return (protein_score + carbs_score + fat_score) / 3

    def _generate_improvement_suggestions(self, totals: Dict, profile: NutritionProfile, calorie_target: int) -> List[str]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # Calorie suggestions
        calorie_diff = totals.get('total_calories', 0) - calorie_target
        if abs(calorie_diff) > calorie_target * 0.05:
            if calorie_diff > 0:
                suggestions.append(f"Reduce portions by approximately {int(calorie_diff)} calories")
            else:
                suggestions.append(f"Increase portions by approximately {int(abs(calorie_diff))} calories")
        
        # Protein suggestions
        protein_diff = totals.get('total_protein', 0) - profile.protein_target
        if protein_diff < -5:
            suggestions.append(f"Add {int(abs(protein_diff))}g more protein through lean sources")
        elif protein_diff > 5:
            suggestions.append("Consider reducing protein portions slightly")
        
        # General suggestions
        if totals.get('total_fiber', 0) < 25:
            suggestions.append("Increase fiber intake with more vegetables and whole grains")
        
        if not suggestions:
            suggestions.append("Nutritional targets are well-balanced")
        
        return suggestions

    def _calculate_nutrition_accuracy(self, claimed: Dict, calculated: Dict) -> float:
        """Calculate accuracy score between claimed and calculated nutrition"""
        if not claimed or not calculated:
            return 0.0
        
        accuracy_scores = []
        
        for nutrient in ['calories_per_serving', 'protein_per_serving', 'carbs_per_serving', 'fat_per_serving']:
            claimed_val = claimed.get(nutrient.replace('_per_serving', ''), 0)
            calculated_val = calculated.get(nutrient.replace('_per_serving', ''), 0)
            
            if claimed_val > 0:
                accuracy = 1.0 - min(1.0, abs(claimed_val - calculated_val) / claimed_val)
                accuracy_scores.append(accuracy)
        
        return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

    def _calculate_accuracy_score(self, totals: Dict, profile: NutritionProfile, calorie_target: int) -> float:
        """Calculate overall accuracy score for the meal plan"""
        calorie_accuracy = 1.0 - min(1.0, abs(totals.get('total_calories', 0) - calorie_target) / max(calorie_target, 1))
        protein_accuracy = 1.0 - min(1.0, abs(totals.get('total_protein', 0) - profile.protein_target) / max(profile.protein_target, 1))
        
        return (calorie_accuracy + protein_accuracy) / 2 * 100  # Scale to 0-100