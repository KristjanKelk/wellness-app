import logging
from typing import Dict, List, Optional, Any
from ..models import MealPlan, Recipe
from .enhanced_spoonacular_service import EnhancedSpoonacularService
from .ai_enhanced_meal_service import AIEnhancedMealService
import random

logger = logging.getLogger(__name__)


class AIMealPlanningService:
    """
    AI-powered meal planning service that provides meal regeneration and alternatives.
    """

    def __init__(self):
        self.spoonacular_service = EnhancedSpoonacularService()
        self.ai_service = AIEnhancedMealService()

    def regenerate_meal(self, meal_plan: MealPlan, day: str, meal_type: str) -> MealPlan:
        """
        Regenerate a specific meal in a meal plan.
        
        Args:
            meal_plan: The meal plan to update
            day: The day to regenerate (or meal type name for daily plans)
            meal_type: The type of meal to regenerate
        
        Returns:
            Updated meal plan
        """
        try:
            logger.info(f"Regenerating meal for plan {meal_plan.id}, day: {day}, meal_type: {meal_type}")
            
            # Get user's nutrition profile
            nutrition_profile = meal_plan.user.nutrition_profile
            
            # For daily plans, day might actually be the meal type name
            if meal_plan.plan_type == 'daily' and day in ['breakfast', 'lunch', 'dinner']:
                actual_meal_type = day
                day_key = day
            else:
                actual_meal_type = meal_type
                day_key = day
            
            # Get recipe suggestions based on meal type and user preferences
            recipes = self._get_alternative_recipes(nutrition_profile, actual_meal_type, count=1)
            
            if not recipes:
                logger.warning(f"No alternative recipes found for {actual_meal_type}")
                return meal_plan
            
            # Update the meal plan data
            if hasattr(meal_plan, 'meal_plan_data') and meal_plan.meal_plan_data:
                if 'meals' in meal_plan.meal_plan_data:
                    if day_key in meal_plan.meal_plan_data['meals']:
                        # Find and replace only the specific meal type
                        new_recipe = recipes[0]
                        
                        # Ensure the new recipe has proper meal structure
                        new_recipe.update({
                            'meal_type': actual_meal_type,
                            'time': {
                                'breakfast': '08:00',
                                'lunch': '12:30',
                                'dinner': '19:00'
                            }.get(actual_meal_type, '12:00'),
                            'cuisine': new_recipe.get('cuisines', ['International'])[0] if new_recipe.get('cuisines') else 'International',
                            'target_calories': new_recipe.get('nutrition', {}).get('nutrients', [{}])[0].get('amount', 0) if new_recipe.get('nutrition') else 0
                        })
                        
                        # Get the current meals for the day
                        current_meals = meal_plan.meal_plan_data['meals'][day_key]
                        
                        # Find and replace the specific meal type
                        meal_updated = False
                        for i, meal in enumerate(current_meals):
                            if meal.get('meal_type') == actual_meal_type:
                                current_meals[i] = new_recipe
                                meal_updated = True
                                break
                        
                        # If meal type not found, add it
                        if not meal_updated:
                            current_meals.append(new_recipe)
                        
                        meal_plan.save()
                        logger.info(f"Successfully regenerated {actual_meal_type} meal for {day_key}")
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error regenerating meal: {str(e)}")
            raise e

    def generate_recipe_alternatives(self, meal_plan: MealPlan, day: str, meal_type: str, count: int = 3) -> List[Dict]:
        """
        Generate alternative recipes for a specific meal.
        
        Args:
            meal_plan: The meal plan context
            day: The day to get alternatives for
            meal_type: The type of meal
            count: Number of alternatives to generate
        
        Returns:
            List of alternative recipe options
        """
        try:
            logger.info(f"Generating {count} alternatives for plan {meal_plan.id}, day: {day}, meal_type: {meal_type}")
            
            # Get user's nutrition profile
            nutrition_profile = meal_plan.user.nutrition_profile
            
            # For daily plans, day might actually be the meal type name
            if meal_plan.plan_type == 'daily' and day in ['breakfast', 'lunch', 'dinner']:
                actual_meal_type = day
            else:
                actual_meal_type = meal_type
            
            # Get alternative recipes
            alternatives = self._get_alternative_recipes(nutrition_profile, actual_meal_type, count)
            
            logger.info(f"Generated {len(alternatives)} alternatives")
            return alternatives
            
        except Exception as e:
            logger.error(f"Error generating alternatives: {str(e)}")
            raise e

    def _get_alternative_recipes(self, nutrition_profile, meal_type: str, count: int = 3) -> List[Dict]:
        """
        Get alternative recipes based on nutrition profile and meal type.
        
        Args:
            nutrition_profile: User's nutrition profile
            meal_type: Type of meal (breakfast, lunch, dinner)
            count: Number of recipes to fetch
        
        Returns:
            List of recipe dictionaries
        """
        try:
            # Map meal types to recipe types
            meal_type_mapping = {
                'breakfast': ['breakfast', 'brunch'],
                'lunch': ['lunch', 'main course', 'salad'],
                'dinner': ['dinner', 'main course', 'entree'],
            }
            
            recipe_types = meal_type_mapping.get(meal_type, ['main course'])
            
            # Prepare search parameters
            search_filters = {
                'number': count * 2,  # Get more to have options
                'addRecipeInformation': True,
                'addRecipeNutrition': True,
                'fillIngredients': True
            }
            
            # Add dietary restrictions if any
            if nutrition_profile.dietary_preferences:
                diet_mapping = {
                    'vegetarian': 'vegetarian',
                    'vegan': 'vegan',
                    'pescatarian': 'pescatarian',
                    'keto': 'ketogenic',
                    'paleo': 'paleo',
                    'gluten_free': 'gluten free'
                }
                
                for pref in nutrition_profile.dietary_preferences:
                    if pref in diet_mapping:
                        search_filters['diet'] = diet_mapping[pref]
                        break
            
            # Add intolerances
            if nutrition_profile.allergies_intolerances:
                intolerance_mapping = {
                    'nuts': 'tree nuts',
                    'peanuts': 'peanuts',
                    'dairy': 'dairy',
                    'gluten': 'gluten',
                    'eggs': 'eggs',
                    'fish': 'fish',
                    'shellfish': 'shellfish',
                    'soy': 'soy'
                }
                
                intolerances = []
                for allergy in nutrition_profile.allergies_intolerances:
                    if allergy in intolerance_mapping:
                        intolerances.append(intolerance_mapping[allergy])
                
                if intolerances:
                    search_filters['intolerances'] = ','.join(intolerances)
            
            # Add cuisine preferences
            if nutrition_profile.cuisine_preferences:
                search_filters['cuisine'] = ','.join(nutrition_profile.cuisine_preferences)
            
            # Add calorie constraints
            if nutrition_profile.calorie_target:
                calories_per_meal = nutrition_profile.calorie_target // 3
                search_filters['minCalories'] = max(calories_per_meal - 200, 100)
                search_filters['maxCalories'] = calories_per_meal + 200
            
            # Search for recipes using the correct method signature with meal type as query
            meal_query = random.choice(recipe_types) if recipe_types else ""
            response = self.spoonacular_service.search_recipes(meal_query, **search_filters)
            
            if not response or 'results' not in response:
                logger.warning("No recipe results from Spoonacular search")
                return []
            
            recipes = response['results'][:count]
            
            # Format recipes for consistent structure
            formatted_recipes = []
            for recipe in recipes:
                formatted_recipe = {
                    'id': recipe.get('id'),
                    'title': recipe.get('title'),
                    'image': recipe.get('image'),
                    'servings': recipe.get('servings', 1),
                    'readyInMinutes': recipe.get('readyInMinutes', 30),
                    'summary': recipe.get('summary', ''),
                    'nutrition': recipe.get('nutrition', {}),
                    'ingredients': recipe.get('extendedIngredients', []),
                    'instructions': recipe.get('analyzedInstructions', [])
                }
                formatted_recipes.append(formatted_recipe)
            
            return formatted_recipes
            
        except Exception as e:
            logger.error(f"Error fetching alternative recipes: {str(e)}")
            return []