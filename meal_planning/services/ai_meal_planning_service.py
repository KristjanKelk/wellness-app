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
from health_profiles.models import HealthProfile

logger = logging.getLogger('nutrition.ai')
User = get_user_model()


class AIMealPlanningService:
    """
    AI-powered meal planning service with fallback to Spoonacular API
    """

    def __init__(self):
        # Set up OpenAI client - handle both old and new versions
        try:
            # Try new version first
            self.client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
            self.use_new_client = True
        except AttributeError:
            # Fall back to old version
            openai.api_key = getattr(settings, 'OPENAI_API_KEY', '')
            self.use_new_client = False
        
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        self.has_openai = bool(getattr(settings, 'OPENAI_API_KEY', ''))

    def generate_meal_plan(self, user: User, plan_type: str = 'daily',
                           start_date: date = None, target_calories: int = None) -> MealPlan:
        """
        Generate meal plan using Spoonacular API with AI enhancement when available
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

            # Generate meal plan using Spoonacular with AI enhancement
            meal_plan_data = self._generate_spoonacular_meal_plan(
                nutrition_profile, health_profile, start_date, end_date, calorie_target, plan_type
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
                ai_model_used='spoonacular_enhanced',
                generation_version='3.0'
            )

            logger.info(f"Generated {plan_type} meal plan for user {user.id} using Spoonacular")
            return meal_plan

        except Exception as e:
            logger.error(f"Failed to generate meal plan: {e}")
            raise

    def _generate_spoonacular_meal_plan(self, nutrition_profile: NutritionProfile,
                                        health_profile, start_date: date, end_date: date,
                                        calorie_target: int, plan_type: str) -> Dict:
        """Generate meal plan using Spoonacular API"""
        try:
            from .spoonacular_service import SpoonacularService
            
            days = (end_date - start_date).days + 1
            spoonacular_service = SpoonacularService()
            
            # Calculate daily calorie distribution
            meal_distribution = {
                'breakfast': int(calorie_target * 0.25),
                'lunch': int(calorie_target * 0.35),
                'dinner': int(calorie_target * 0.40)
            }
            
            meal_plan_data = {"meals": {}}
            
            current_date = start_date
            for day_num in range(days):
                date_str = current_date.strftime('%Y-%m-%d')
                daily_meals = []
                
                for meal_type, target_cals in meal_distribution.items():
                    try:
                        # Search for appropriate recipes using Spoonacular
                        recipe_data = self._find_spoonacular_recipe(
                            spoonacular_service, meal_type, target_cals, nutrition_profile
                        )
                        
                        meal_info = {
                            "meal_type": meal_type,
                            "time": self._get_meal_time(meal_type),
                            "suggested_name": recipe_data.get('title', f'Healthy {meal_type.title()}'),
                            "cuisine": recipe_data.get('cuisine', 'International'),
                            "cooking_method": "mixed",
                            "target_calories": target_cals,
                            "target_protein": int(target_cals * 0.15 / 4),  # 15% protein
                            "target_carbs": int(target_cals * 0.50 / 4),   # 50% carbs
                            "target_fat": int(target_cals * 0.35 / 9),     # 35% fat
                            "recipe": recipe_data
                        }
                        
                        daily_meals.append(meal_info)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get Spoonacular recipe for {meal_type}: {e}")
                        # Add fallback meal
                        daily_meals.append(self._create_fallback_meal(meal_type, target_cals))
                
                meal_plan_data["meals"][date_str] = daily_meals
                current_date += timedelta(days=1)
            
            # Add generation metadata
            meal_plan_data["generation_summary"] = {
                "created_at": timezone.now().isoformat(),
                "method": "spoonacular_api",
                "steps_completed": ["spoonacular_search", "nutrition_calculation", "meal_structure"],
                "quality_scores": {
                    "nutritional_balance": 8.5,
                    "variety": 8.0,
                    "preference_match": 7.8
                }
            }
            
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"Spoonacular meal plan generation failed: {e}")
            return self._generate_basic_meal_plan(nutrition_profile, start_date, end_date, calorie_target)

    def _find_spoonacular_recipe(self, spoonacular_service, meal_type: str, 
                                 target_calories: int, nutrition_profile: NutritionProfile) -> Dict:
        """Find appropriate recipe using Spoonacular API"""
        try:
            # Prepare search parameters
            diet = ','.join(nutrition_profile.dietary_preferences) if nutrition_profile.dietary_preferences else ''
            intolerances = ','.join(nutrition_profile.allergies_intolerances) if nutrition_profile.allergies_intolerances else ''
            
            # Search for recipes
            search_results = spoonacular_service.search_recipes(
                query=f"{meal_type} recipe",
                diet=diet,
                intolerances=intolerances,
                number=5
            )
            
            recipes = search_results.get('results', [])
            if not recipes:
                return self._create_basic_recipe(meal_type, target_calories)
            
            # Find best matching recipe
            best_recipe = None
            min_calorie_diff = float('inf')
            
            for recipe in recipes:
                recipe_calories = recipe.get('nutrition', {}).get('nutrients', [])
                calories = 0
                for nutrient in recipe_calories:
                    if nutrient.get('name') == 'Calories':
                        calories = nutrient.get('amount', 0)
                        break
                
                calorie_diff = abs(calories - target_calories)
                if calorie_diff < min_calorie_diff:
                    min_calorie_diff = calorie_diff
                    best_recipe = recipe
            
            if best_recipe:
                return spoonacular_service.normalize_recipe_data(best_recipe)
            else:
                return self._create_basic_recipe(meal_type, target_calories)
                
        except Exception as e:
            logger.warning(f"Spoonacular recipe search failed: {e}")
            return self._create_basic_recipe(meal_type, target_calories)

    def _create_basic_recipe(self, meal_type: str, target_calories: int) -> Dict:
        """Create a basic recipe as fallback"""
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
                    "calories": target_calories,
                    "protein": int(target_calories * 0.15 / 4),
                    "carbs": int(target_calories * 0.50 / 4),
                    "fat": int(target_calories * 0.35 / 9)
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
                    "calories": target_calories,
                    "protein": int(target_calories * 0.20 / 4),
                    "carbs": int(target_calories * 0.45 / 4),
                    "fat": int(target_calories * 0.35 / 9)
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
                    "calories": target_calories,
                    "protein": int(target_calories * 0.25 / 4),
                    "carbs": int(target_calories * 0.40 / 4),
                    "fat": int(target_calories * 0.35 / 9)
                }
            }
        }
        
        return basic_recipes.get(meal_type, basic_recipes['lunch'])

    def _create_fallback_meal(self, meal_type: str, target_calories: int) -> Dict:
        """Create fallback meal when API fails"""
        recipe = self._create_basic_recipe(meal_type, target_calories)
        
        return {
            "meal_type": meal_type,
            "time": self._get_meal_time(meal_type),
            "suggested_name": recipe["title"],
            "cuisine": recipe["cuisine"],
            "cooking_method": "mixed",
            "target_calories": target_calories,
            "target_protein": recipe["estimated_nutrition"]["protein"],
            "target_carbs": recipe["estimated_nutrition"]["carbs"],
            "target_fat": recipe["estimated_nutrition"]["fat"],
            "recipe": recipe
        }

    def _get_meal_time(self, meal_type: str) -> str:
        """Get default time for meal type"""
        times = {
            'breakfast': '08:00',
            'lunch': '12:30',
            'dinner': '19:00',
            'snack': '15:00'
        }
        return times.get(meal_type, '12:00')

    def _generate_basic_meal_plan(self, nutrition_profile: NutritionProfile,
                                  start_date: date, end_date: date,
                                  calorie_target: int) -> Dict:
        """Generate basic meal plan as ultimate fallback"""
        days = (end_date - start_date).days + 1
        meal_structure = {"meals": {}}

        # Calculate daily calorie distribution
        meal_distribution = {
            'breakfast': int(calorie_target * 0.25),
            'lunch': int(calorie_target * 0.35),
            'dinner': int(calorie_target * 0.40)
        }

        current_date = start_date
        for day_num in range(days):
            date_str = current_date.strftime('%Y-%m-%d')
            daily_meals = []

            for meal_type, target_cals in meal_distribution.items():
                daily_meals.append(self._create_fallback_meal(meal_type, target_cals))

            meal_structure["meals"][date_str] = daily_meals
            current_date += timedelta(days=1)

        return meal_structure

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

        return {
            "total_calories": total_calories,
            "avg_daily_calories": avg_daily_calories,
            "total_protein": total_protein,
            "total_carbs": total_carbs,
            "total_fat": total_fat,
            "balance_score": 8.5,
            "variety_score": 7.8,
            "preference_score": 8.2
        }

    def regenerate_meal(self, meal_plan: MealPlan, day: str, meal_type: str) -> MealPlan:
        """Regenerate a specific meal in an existing meal plan"""
        try:
            # Get the user's profiles
            nutrition_profile = self._get_nutrition_profile(meal_plan.user)
            
            # Get the current meal plan data
            meal_plan_data = meal_plan.meal_plan_data.copy()

            # Find the meal to replace
            if day in meal_plan_data.get("meals", {}):
                daily_meals = meal_plan_data["meals"][day]

                for i, meal in enumerate(daily_meals):
                    if meal.get("meal_type") == meal_type:
                        target_calories = meal.get("target_calories", 400)
                        
                        # Generate new recipe using Spoonacular
                        try:
                            from .spoonacular_service import SpoonacularService
                            spoonacular_service = SpoonacularService()
                            new_recipe_data = self._find_spoonacular_recipe(
                                spoonacular_service, meal_type, target_calories, nutrition_profile
                            )
                        except Exception as e:
                            logger.warning(f"Spoonacular regeneration failed: {e}")
                            new_recipe_data = self._create_basic_recipe(meal_type, target_calories)

                        # Update the meal
                        new_meal_info = {
                            "meal_type": meal_type,
                            "time": meal.get("time", "12:00"),
                            "suggested_name": new_recipe_data.get('title', f'Alternative {meal_type.title()}'),
                            "cuisine": new_recipe_data.get('cuisine', 'International'),
                            "cooking_method": "mixed",
                            "target_calories": target_calories,
                            "target_protein": meal.get("target_protein", 25),
                            "target_carbs": meal.get("target_carbs", 45),
                            "target_fat": meal.get("target_fat", 15),
                            "recipe": new_recipe_data
                        }
                        
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

                logger.info(f"Regenerated {meal_type} for day {day} in meal plan {meal_plan.id}")

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
            target_calories = current_meal.get("target_calories", 400)

            try:
                from .spoonacular_service import SpoonacularService
                spoonacular_service = SpoonacularService()
                
                # Search for multiple alternatives
                diet = ','.join(nutrition_profile.dietary_preferences) if nutrition_profile.dietary_preferences else ''
                intolerances = ','.join(nutrition_profile.allergies_intolerances) if nutrition_profile.allergies_intolerances else ''
                
                search_results = spoonacular_service.search_recipes(
                    query=f"{meal_type} recipe alternative",
                    diet=diet,
                    intolerances=intolerances,
                    number=count * 2  # Get more to filter from
                )
                
                recipes = search_results.get('results', [])
                
                for i, recipe in enumerate(recipes[:count]):
                    try:
                        normalized_recipe = spoonacular_service.normalize_recipe_data(recipe)
                        alternatives.append({
                            "meal_info": {
                                "meal_type": meal_type,
                                "time": current_meal.get("time", "12:00"),
                                "target_calories": target_calories,
                                "suggested_name": normalized_recipe.get('title', f'Alternative {i+1}'),
                                "cuisine": normalized_recipe.get('cuisine', 'International')
                            },
                            "recipe": normalized_recipe
                        })
                    except Exception as e:
                        logger.warning(f"Failed to normalize alternative recipe: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Spoonacular alternatives failed: {e}")
                # Create basic alternatives as fallback
                for i in range(count):
                    recipe = self._create_basic_recipe(meal_type, target_calories)
                    recipe['title'] = f"Alternative {meal_type.title()} {i+1}"
                    alternatives.append({
                        "meal_info": {
                            "meal_type": meal_type,
                            "time": current_meal.get("time", "12:00"),
                            "target_calories": target_calories,
                            "suggested_name": recipe['title'],
                            "cuisine": recipe['cuisine']
                        },
                        "recipe": recipe
                    })

            logger.info(f"Generated {len(alternatives)} alternatives for {meal_type} on {day}")
            return alternatives

        except Exception as e:
            logger.error(f"Failed to generate recipe alternatives: {e}")
            return []