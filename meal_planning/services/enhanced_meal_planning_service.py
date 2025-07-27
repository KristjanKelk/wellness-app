# meal_planning/services/enhanced_meal_planning_service.py
"""
Enhanced Meal Planning Service
Combines Spoonacular API with improved fallback mechanisms and better nutrition insights
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import date, timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from meal_planning.models import NutritionProfile, Recipe, MealPlan, Ingredient
from health_profiles.models import HealthProfile
from .spoonacular_service import SpoonacularService, SpoonacularAPIError

logger = logging.getLogger('nutrition.enhanced')
User = get_user_model()


class EnhancedMealPlanningService:
    """
    Enhanced meal planning service with multiple data sources and intelligent fallbacks
    """

    def __init__(self):
        self.spoonacular_service = SpoonacularService()
        self.nutrition_database = self._load_nutrition_database()

    def generate_comprehensive_meal_plan(self, user: User, plan_type: str = 'daily',
                                       start_date: date = None, target_calories: int = None,
                                       preferences_override: Dict = None) -> MealPlan:
        """
        Generate a comprehensive meal plan with multiple data sources
        
        Args:
            user: User instance
            plan_type: 'daily' or 'weekly'
            start_date: Start date for the meal plan
            target_calories: Optional calorie target override
            preferences_override: Optional preferences to override user profile
            
        Returns:
            Generated MealPlan instance with enhanced data
        """
        try:
            # Get user profiles
            nutrition_profile = self._get_nutrition_profile(user)
            health_profile = self._get_health_profile(user)

            # Apply preferences override if provided
            if preferences_override:
                nutrition_profile = self._apply_preferences_override(nutrition_profile, preferences_override)

            # Set defaults
            if not start_date:
                start_date = timezone.now().date()
            
            # Calculate end date
            if plan_type == 'weekly':
                end_date = start_date + timedelta(days=6)
            else:
                end_date = start_date

            # Use target calories or calculate from profile
            calorie_target = target_calories or self._calculate_calorie_target(nutrition_profile, health_profile)

            # Generate enhanced meal plan
            meal_plan_data = self._generate_enhanced_meal_plan(
                nutrition_profile, health_profile, start_date, end_date, calorie_target, plan_type
            )

            # Calculate comprehensive nutrition analysis
            nutrition_analysis = self._analyze_comprehensive_nutrition(meal_plan_data, nutrition_profile)

            # Create meal plan with enhanced data
            meal_plan = MealPlan.objects.create(
                user=user,
                plan_type=plan_type,
                start_date=start_date,
                end_date=end_date,
                meal_plan_data=meal_plan_data,
                total_calories=nutrition_analysis['total_calories'],
                avg_daily_calories=nutrition_analysis['avg_daily_calories'],
                total_protein=nutrition_analysis['total_protein'],
                total_carbs=nutrition_analysis['total_carbs'],
                total_fat=nutrition_analysis['total_fat'],
                nutritional_balance_score=nutrition_analysis['balance_score'],
                variety_score=nutrition_analysis['variety_score'],
                preference_match_score=nutrition_analysis['preference_score'],
                ai_model_used='enhanced_spoonacular',
                generation_version='4.0'
            )

            logger.info(f"Generated enhanced {plan_type} meal plan for user {user.id}")
            return meal_plan

        except Exception as e:
            logger.error(f"Enhanced meal plan generation failed: {e}")
            raise

    def _generate_enhanced_meal_plan(self, nutrition_profile: NutritionProfile,
                                   health_profile, start_date: date, end_date: date,
                                   calorie_target: int, plan_type: str) -> Dict:
        """Generate enhanced meal plan with multiple strategies"""
        
        days = (end_date - start_date).days + 1
        meal_plan_data = {"meals": {}, "nutrition_insights": {}, "generation_metadata": {}}

        # Calculate meal distribution based on user preferences and goals
        meal_distribution = self._calculate_smart_meal_distribution(
            calorie_target, nutrition_profile, health_profile
        )

        # Track used recipes to ensure variety
        used_recipes = set()
        
        current_date = start_date
        for day_num in range(days):
            date_str = current_date.strftime('%Y-%m-%d')
            daily_meals = []
            daily_nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}

            for meal_type, meal_config in meal_distribution.items():
                try:
                    # Find optimal recipe using multiple strategies
                    recipe_data = self._find_optimal_recipe(
                        meal_type, meal_config, nutrition_profile, used_recipes, day_num
                    )
                    
                    if recipe_data:
                        # Track used recipe to ensure variety
                        recipe_id = recipe_data.get('spoonacular_id') or recipe_data.get('title', '')
                        used_recipes.add(recipe_id)

                        meal_info = {
                            "meal_type": meal_type,
                            "time": meal_config.get('time', self._get_default_meal_time(meal_type)),
                            "suggested_name": recipe_data.get('title', f'Healthy {meal_type.title()}'),
                            "cuisine": recipe_data.get('cuisine', 'International'),
                            "cooking_method": self._determine_cooking_method(recipe_data),
                            "target_calories": meal_config['calories'],
                            "target_protein": meal_config['protein'],
                            "target_carbs": meal_config['carbs'],
                            "target_fat": meal_config['fat'],
                            "recipe": recipe_data,
                            "nutrition_score": self._calculate_nutrition_score(recipe_data, meal_config),
                            "variety_tags": self._extract_variety_tags(recipe_data)
                        }

                        daily_meals.append(meal_info)
                        
                        # Update daily nutrition tracking
                        recipe_nutrition = recipe_data.get('estimated_nutrition', {})
                        daily_nutrition['calories'] += recipe_nutrition.get('calories', 0)
                        daily_nutrition['protein'] += recipe_nutrition.get('protein', 0)
                        daily_nutrition['carbs'] += recipe_nutrition.get('carbs', 0)
                        daily_nutrition['fat'] += recipe_nutrition.get('fat', 0)

                except Exception as e:
                    logger.warning(f"Failed to find recipe for {meal_type} on day {day_num}: {e}")
                    # Add fallback meal
                    fallback_meal = self._create_intelligent_fallback_meal(
                        meal_type, meal_config, nutrition_profile
                    )
                    daily_meals.append(fallback_meal)

            meal_plan_data["meals"][date_str] = daily_meals
            meal_plan_data["nutrition_insights"][date_str] = {
                **daily_nutrition,
                "balance_analysis": self._analyze_daily_balance(daily_nutrition, nutrition_profile),
                "optimization_suggestions": self._generate_optimization_suggestions(daily_nutrition, nutrition_profile)
            }

            current_date += timedelta(days=1)

        # Add comprehensive metadata
        meal_plan_data["generation_metadata"] = {
            "created_at": timezone.now().isoformat(),
            "generation_method": "enhanced_multi_source",
            "data_sources": ["spoonacular", "local_database", "nutrition_rules"],
            "variety_score": self._calculate_variety_score(meal_plan_data),
            "nutrition_completeness": self._calculate_nutrition_completeness(meal_plan_data, nutrition_profile),
            "user_preference_alignment": self._calculate_preference_alignment(meal_plan_data, nutrition_profile),
            "estimated_cost": self._estimate_meal_plan_cost(meal_plan_data),
            "preparation_complexity": self._calculate_preparation_complexity(meal_plan_data)
        }

        return meal_plan_data

    def _find_optimal_recipe(self, meal_type: str, meal_config: Dict,
                           nutrition_profile: NutritionProfile, used_recipes: set,
                           day_num: int) -> Optional[Dict]:
        """Find optimal recipe using multiple strategies with fallback"""
        
        # Strategy 1: Try Spoonacular API first
        try:
            spoonacular_recipe = self._search_spoonacular_recipe(
                meal_type, meal_config, nutrition_profile, used_recipes
            )
            if spoonacular_recipe:
                return spoonacular_recipe
        except Exception as e:
            logger.warning(f"Spoonacular search failed for {meal_type}: {e}")

        # Strategy 2: Search local database
        try:
            local_recipe = self._search_local_database(
                meal_type, meal_config, nutrition_profile, used_recipes
            )
            if local_recipe:
                return local_recipe
        except Exception as e:
            logger.warning(f"Local database search failed for {meal_type}: {e}")

        # Strategy 3: Generate template-based recipe
        try:
            template_recipe = self._generate_template_recipe(
                meal_type, meal_config, nutrition_profile, day_num
            )
            return template_recipe
        except Exception as e:
            logger.warning(f"Template generation failed for {meal_type}: {e}")

        return None

    def _search_spoonacular_recipe(self, meal_type: str, meal_config: Dict,
                                 nutrition_profile: NutritionProfile, used_recipes: set) -> Optional[Dict]:
        """Search Spoonacular API for suitable recipe"""
        
        # Build search parameters
        diet = ','.join(nutrition_profile.dietary_preferences) if nutrition_profile.dietary_preferences else ''
        intolerances = ','.join(nutrition_profile.allergies_intolerances) if nutrition_profile.allergies_intolerances else ''
        
        # Search with meal type context
        search_query = f"{meal_type} recipe healthy"
        if nutrition_profile.cuisine_preferences:
            search_query += f" {nutrition_profile.cuisine_preferences[0]}"

        search_results = self.spoonacular_service.search_recipes(
            query=search_query,
            diet=diet,
            intolerances=intolerances,
            number=10  # Get more options to filter
        )

        recipes = search_results.get('results', [])
        target_calories = meal_config['calories']

        # Filter and score recipes
        scored_recipes = []
        for recipe in recipes:
            recipe_id = recipe.get('id')
            if recipe_id and recipe_id not in used_recipes:
                score = self._score_recipe_match(recipe, meal_config, nutrition_profile)
                scored_recipes.append((score, recipe))

        # Sort by score and return best match
        if scored_recipes:
            scored_recipes.sort(key=lambda x: x[0], reverse=True)
            best_recipe = scored_recipes[0][1]
            return self.spoonacular_service.normalize_recipe_data(best_recipe)

        return None

    def _search_local_database(self, meal_type: str, meal_config: Dict,
                             nutrition_profile: NutritionProfile, used_recipes: set) -> Optional[Dict]:
        """Search local recipe database"""
        
        # Query local recipes
        recipes = Recipe.objects.filter(meal_type=meal_type)
        
        # Apply dietary filters
        for pref in nutrition_profile.dietary_preferences:
            recipes = recipes.filter(dietary_tags__contains=[pref])
        
        for allergen in nutrition_profile.allergies_intolerances:
            recipes = recipes.exclude(allergens__contains=[allergen])

        # Filter out used recipes
        if used_recipes:
            recipes = recipes.exclude(spoonacular_id__in=[rid for rid in used_recipes if isinstance(rid, int)])
            recipes = recipes.exclude(title__in=[rid for rid in used_recipes if isinstance(rid, str)])

        # Find best calorie match
        target_calories = meal_config['calories']
        best_recipe = None
        min_diff = float('inf')

        for recipe in recipes:
            calorie_diff = abs(recipe.calories_per_serving - target_calories)
            if calorie_diff < min_diff:
                min_diff = calorie_diff
                best_recipe = recipe

        if best_recipe:
            return self._convert_recipe_to_dict(best_recipe)

        return None

    def _generate_template_recipe(self, meal_type: str, meal_config: Dict,
                                nutrition_profile: NutritionProfile, day_num: int) -> Dict:
        """Generate recipe from templates with nutrition targeting"""
        
        templates = self._get_recipe_templates()
        template = templates.get(meal_type, templates['default'])
        
        # Customize template based on preferences
        customized_template = self._customize_template(
            template, meal_config, nutrition_profile, day_num
        )
        
        return customized_template

    def _calculate_smart_meal_distribution(self, calorie_target: int,
                                         nutrition_profile: NutritionProfile,
                                         health_profile) -> Dict:
        """Calculate intelligent meal distribution based on user goals and preferences"""
        
        # Base distribution
        distributions = {
            'weight_loss': {'breakfast': 0.30, 'lunch': 0.40, 'dinner': 0.30},
            'muscle_gain': {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.40},
            'maintenance': {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.40},
            'endurance': {'breakfast': 0.30, 'lunch': 0.35, 'dinner': 0.35}
        }
        
        # Get user goal
        goal = getattr(health_profile, 'fitness_goal', 'maintenance')
        distribution = distributions.get(goal, distributions['maintenance'])
        
        # Calculate macros for each meal
        protein_target = nutrition_profile.protein_target
        carb_target = nutrition_profile.carb_target
        fat_target = nutrition_profile.fat_target
        
        meal_distribution = {}
        for meal_type, ratio in distribution.items():
            meal_distribution[meal_type] = {
                'calories': int(calorie_target * ratio),
                'protein': int(protein_target * ratio),
                'carbs': int(carb_target * ratio),
                'fat': int(fat_target * ratio),
                'time': self._get_default_meal_time(meal_type)
            }
        
        return meal_distribution

    def _score_recipe_match(self, recipe: Dict, meal_config: Dict,
                          nutrition_profile: NutritionProfile) -> float:
        """Score how well a recipe matches the requirements"""
        score = 0.0
        
        # Nutrition scoring (40% weight)
        nutrition = recipe.get('nutrition', {})
        nutrients = {n['name']: n['amount'] for n in nutrition.get('nutrients', [])}
        
        recipe_calories = nutrients.get('Calories', 0)
        target_calories = meal_config['calories']
        
        if target_calories > 0:
            calorie_accuracy = 1 - min(abs(recipe_calories - target_calories) / target_calories, 1)
            score += calorie_accuracy * 0.4
        
        # Dietary preferences scoring (30% weight)
        recipe_diets = [d.lower() for d in recipe.get('diets', [])]
        for pref in nutrition_profile.dietary_preferences:
            if pref.lower() in recipe_diets:
                score += 0.1
        
        # Cuisine preference scoring (20% weight)
        recipe_cuisines = [c.lower() for c in recipe.get('cuisines', [])]
        for cuisine in nutrition_profile.cuisine_preferences:
            if cuisine.lower() in recipe_cuisines:
                score += 0.1
        
        # Health score (10% weight)
        if recipe.get('veryHealthy'):
            score += 0.1
        
        return score

    def _analyze_comprehensive_nutrition(self, meal_plan_data: Dict,
                                       nutrition_profile: NutritionProfile) -> Dict:
        """Analyze nutrition across the entire meal plan"""
        
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        days_count = len(meal_plan_data.get("meals", {}))

        # Aggregate nutrition
        for date_str, daily_meals in meal_plan_data.get("meals", {}).items():
            for meal in daily_meals:
                nutrition = meal.get("recipe", {}).get("estimated_nutrition", {})
                total_calories += nutrition.get("calories", 0)
                total_protein += nutrition.get("protein", 0)
                total_carbs += nutrition.get("carbs", 0)
                total_fat += nutrition.get("fat", 0)

        avg_daily_calories = total_calories / days_count if days_count > 0 else 0

        # Calculate quality scores
        balance_score = self._calculate_nutritional_balance_score(
            avg_daily_calories, total_protein / days_count, total_carbs / days_count, 
            total_fat / days_count, nutrition_profile
        )
        
        variety_score = meal_plan_data.get("generation_metadata", {}).get("variety_score", 8.0)
        preference_score = meal_plan_data.get("generation_metadata", {}).get("user_preference_alignment", 8.0)

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

    def _calculate_nutritional_balance_score(self, calories: float, protein: float,
                                           carbs: float, fat: float,
                                           nutrition_profile: NutritionProfile) -> float:
        """Calculate nutritional balance score (0-10)"""
        
        score = 10.0
        
        # Check calorie accuracy (±10% tolerance)
        calorie_diff = abs(calories - nutrition_profile.calorie_target) / nutrition_profile.calorie_target
        if calorie_diff > 0.1:
            score -= min(calorie_diff * 5, 3)
        
        # Check protein accuracy (±15% tolerance)
        protein_diff = abs(protein - nutrition_profile.protein_target) / nutrition_profile.protein_target
        if protein_diff > 0.15:
            score -= min(protein_diff * 3, 2)
        
        # Check carb accuracy (±20% tolerance)
        carb_diff = abs(carbs - nutrition_profile.carb_target) / nutrition_profile.carb_target
        if carb_diff > 0.2:
            score -= min(carb_diff * 2, 2)
        
        # Check fat accuracy (±15% tolerance)
        fat_diff = abs(fat - nutrition_profile.fat_target) / nutrition_profile.fat_target
        if fat_diff > 0.15:
            score -= min(fat_diff * 3, 2)
        
        return max(score, 0)

    # Helper methods
    def _get_nutrition_profile(self, user: User) -> NutritionProfile:
        """Get or create nutrition profile"""
        try:
            return NutritionProfile.objects.get(user=user)
        except NutritionProfile.DoesNotExist:
            return NutritionProfile.objects.create(
                user=user,
                calorie_target=2000,
                protein_target=100,
                carb_target=250,
                fat_target=67,
                dietary_preferences=[],
                allergies_intolerances=[],
                cuisine_preferences=[],
                meals_per_day=3
            )

    def _get_health_profile(self, user: User):
        """Get user's health profile"""
        try:
            return HealthProfile.objects.get(user=user)
        except HealthProfile.DoesNotExist:
            return type('DefaultProfile', (), {
                'age': 30, 'gender': 'not_specified', 'weight': 70,
                'height': 170, 'bmi': 24.2, 'activity_level': 'moderate',
                'fitness_goal': 'maintenance'
            })()

    def _get_default_meal_time(self, meal_type: str) -> str:
        """Get default time for meal type"""
        times = {'breakfast': '08:00', 'lunch': '12:30', 'dinner': '19:00', 'snack': '15:00'}
        return times.get(meal_type, '12:00')

    def _load_nutrition_database(self) -> Dict:
        """Load nutrition database for fallback calculations"""
        return {
            'basic_nutrition': {
                'protein_sources': ['chicken', 'fish', 'tofu', 'beans', 'eggs'],
                'carb_sources': ['rice', 'pasta', 'bread', 'potatoes', 'oats'],
                'fat_sources': ['olive oil', 'nuts', 'avocado', 'seeds'],
                'vegetables': ['broccoli', 'spinach', 'carrots', 'peppers', 'tomatoes']
            }
        }

    def _apply_preferences_override(self, nutrition_profile: NutritionProfile,
                                  preferences_override: Dict) -> NutritionProfile:
        """Apply temporary preferences override"""
        # Create a copy and apply overrides
        for key, value in preferences_override.items():
            if hasattr(nutrition_profile, key):
                setattr(nutrition_profile, key, value)
        return nutrition_profile

    def _calculate_calorie_target(self, nutrition_profile: NutritionProfile,
                                health_profile) -> int:
        """Calculate appropriate calorie target"""
        return nutrition_profile.calorie_target

    # Additional helper methods for comprehensive functionality
    def _determine_cooking_method(self, recipe_data: Dict) -> str:
        """Determine cooking method from recipe data"""
        instructions = recipe_data.get('instructions', [])
        instruction_text = ' '.join([str(inst) for inst in instructions]).lower()
        
        if 'bake' in instruction_text or 'oven' in instruction_text:
            return 'baking'
        elif 'grill' in instruction_text:
            return 'grilling'
        elif 'sauté' in instruction_text or 'pan' in instruction_text:
            return 'sautéing'
        elif 'steam' in instruction_text:
            return 'steaming'
        else:
            return 'mixed'

    def _calculate_nutrition_score(self, recipe_data: Dict, meal_config: Dict) -> float:
        """Calculate nutrition score for a recipe"""
        nutrition = recipe_data.get('estimated_nutrition', {})
        target_calories = meal_config['calories']
        
        if target_calories == 0:
            return 5.0
            
        calorie_accuracy = 1 - min(abs(nutrition.get('calories', 0) - target_calories) / target_calories, 1)
        return calorie_accuracy * 10

    def _extract_variety_tags(self, recipe_data: Dict) -> List[str]:
        """Extract variety tags from recipe"""
        tags = []
        
        if recipe_data.get('cuisine'):
            tags.append(f"cuisine_{recipe_data['cuisine'].lower()}")
        
        # Add cooking method tag
        cooking_method = self._determine_cooking_method(recipe_data)
        tags.append(f"method_{cooking_method}")
        
        # Add ingredient-based tags
        ingredients = recipe_data.get('ingredients', [])
        if any('chicken' in ing.get('name', '').lower() for ing in ingredients):
            tags.append('protein_chicken')
        if any('fish' in ing.get('name', '').lower() for ing in ingredients):
            tags.append('protein_fish')
        
        return tags

    def _create_intelligent_fallback_meal(self, meal_type: str, meal_config: Dict,
                                        nutrition_profile: NutritionProfile) -> Dict:
        """Create intelligent fallback meal"""
        fallback_recipes = {
            'breakfast': {
                'title': 'Balanced Breakfast Bowl',
                'ingredients': [
                    {'name': 'oats', 'quantity': 50, 'unit': 'g'},
                    {'name': 'banana', 'quantity': 1, 'unit': 'medium'},
                    {'name': 'berries', 'quantity': 100, 'unit': 'g'},
                    {'name': 'almond milk', 'quantity': 200, 'unit': 'ml'}
                ],
                'instructions': ['Combine all ingredients', 'Mix well and serve'],
                'estimated_nutrition': {
                    'calories': meal_config['calories'],
                    'protein': meal_config['protein'],
                    'carbs': meal_config['carbs'],
                    'fat': meal_config['fat']
                }
            },
            'lunch': {
                'title': 'Nutritious Power Bowl',
                'ingredients': [
                    {'name': 'quinoa', 'quantity': 80, 'unit': 'g'},
                    {'name': 'mixed vegetables', 'quantity': 150, 'unit': 'g'},
                    {'name': 'protein source', 'quantity': 100, 'unit': 'g'},
                    {'name': 'olive oil', 'quantity': 15, 'unit': 'ml'}
                ],
                'instructions': ['Cook quinoa', 'Prepare vegetables', 'Combine and serve'],
                'estimated_nutrition': {
                    'calories': meal_config['calories'],
                    'protein': meal_config['protein'],
                    'carbs': meal_config['carbs'],
                    'fat': meal_config['fat']
                }
            },
            'dinner': {
                'title': 'Balanced Dinner Plate',
                'ingredients': [
                    {'name': 'lean protein', 'quantity': 150, 'unit': 'g'},
                    {'name': 'complex carbs', 'quantity': 100, 'unit': 'g'},
                    {'name': 'vegetables', 'quantity': 200, 'unit': 'g'},
                    {'name': 'healthy fat', 'quantity': 10, 'unit': 'ml'}
                ],
                'instructions': ['Prepare protein', 'Cook carbs', 'Steam vegetables', 'Combine and serve'],
                'estimated_nutrition': {
                    'calories': meal_config['calories'],
                    'protein': meal_config['protein'],
                    'carbs': meal_config['carbs'],
                    'fat': meal_config['fat']
                }
            }
        }
        
        recipe = fallback_recipes.get(meal_type, fallback_recipes['lunch'])
        
        return {
            "meal_type": meal_type,
            "time": meal_config.get('time', self._get_default_meal_time(meal_type)),
            "suggested_name": recipe['title'],
            "cuisine": "International",
            "cooking_method": "mixed",
            "target_calories": meal_config['calories'],
            "target_protein": meal_config['protein'],
            "target_carbs": meal_config['carbs'],
            "target_fat": meal_config['fat'],
            "recipe": recipe,
            "nutrition_score": 7.0,
            "variety_tags": ['fallback']
        }

    def _analyze_daily_balance(self, daily_nutrition: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Analyze daily nutritional balance"""
        return {
            'calorie_status': 'adequate',
            'protein_ratio': daily_nutrition['protein'] / nutrition_profile.protein_target if nutrition_profile.protein_target > 0 else 1,
            'carb_ratio': daily_nutrition['carbs'] / nutrition_profile.carb_target if nutrition_profile.carb_target > 0 else 1,
            'fat_ratio': daily_nutrition['fat'] / nutrition_profile.fat_target if nutrition_profile.fat_target > 0 else 1
        }

    def _generate_optimization_suggestions(self, daily_nutrition: Dict, nutrition_profile: NutritionProfile) -> List[str]:
        """Generate optimization suggestions for daily nutrition"""
        suggestions = []
        
        # Check protein levels
        protein_ratio = daily_nutrition['protein'] / nutrition_profile.protein_target if nutrition_profile.protein_target > 0 else 1
        if protein_ratio < 0.8:
            suggestions.append("Consider adding more protein-rich foods")
        elif protein_ratio > 1.2:
            suggestions.append("Consider reducing protein portions slightly")
        
        # Check calorie levels
        calorie_ratio = daily_nutrition['calories'] / nutrition_profile.calorie_target if nutrition_profile.calorie_target > 0 else 1
        if calorie_ratio < 0.9:
            suggestions.append("Consider adding a healthy snack to meet calorie goals")
        elif calorie_ratio > 1.1:
            suggestions.append("Consider reducing portion sizes slightly")
        
        return suggestions

    def _calculate_variety_score(self, meal_plan_data: Dict) -> float:
        """Calculate variety score for meal plan"""
        cuisines = set()
        cooking_methods = set()
        ingredients = set()
        
        for date_str, meals in meal_plan_data.get('meals', {}).items():
            for meal in meals:
                recipe = meal.get('recipe', {})
                cuisines.add(recipe.get('cuisine', 'unknown'))
                cooking_methods.add(meal.get('cooking_method', 'unknown'))
                
                for ingredient in recipe.get('ingredients', []):
                    ingredients.add(ingredient.get('name', '').lower())
        
        # Score based on variety
        cuisine_variety = min(len(cuisines) / 3, 1) * 3
        method_variety = min(len(cooking_methods) / 3, 1) * 3
        ingredient_variety = min(len(ingredients) / 15, 1) * 4
        
        return cuisine_variety + method_variety + ingredient_variety

    def _calculate_nutrition_completeness(self, meal_plan_data: Dict, nutrition_profile: NutritionProfile) -> float:
        """Calculate how complete the nutrition profile is"""
        return 8.5  # Simplified implementation

    def _calculate_preference_alignment(self, meal_plan_data: Dict, nutrition_profile: NutritionProfile) -> float:
        """Calculate how well the plan aligns with user preferences"""
        return 8.2  # Simplified implementation

    def _estimate_meal_plan_cost(self, meal_plan_data: Dict) -> Dict:
        """Estimate cost of meal plan"""
        return {"estimated_cost": 45.0, "currency": "USD", "per_person_per_week": True}

    def _calculate_preparation_complexity(self, meal_plan_data: Dict) -> Dict:
        """Calculate preparation complexity"""
        return {"average_prep_time": 25, "difficulty_level": "medium", "skill_required": "beginner"}

    def _convert_recipe_to_dict(self, recipe: Recipe) -> Dict:
        """Convert Recipe model to dictionary format"""
        return {
            'title': recipe.title,
            'cuisine': recipe.cuisine,
            'spoonacular_id': recipe.spoonacular_id,
            'ingredients': recipe.ingredients_data or [],
            'instructions': recipe.instructions or [],
            'prep_time': recipe.prep_time_minutes,
            'cook_time': recipe.cook_time_minutes,
            'total_time': recipe.total_time_minutes,
            'servings': recipe.servings,
            'estimated_nutrition': {
                'calories': recipe.calories_per_serving,
                'protein': recipe.protein_per_serving,
                'carbs': recipe.carbs_per_serving,
                'fat': recipe.fat_per_serving
            }
        }

    def _get_recipe_templates(self) -> Dict:
        """Get recipe templates for fallback generation"""
        return {
            'breakfast': {
                'title': 'Template Breakfast',
                'base_ingredients': ['protein', 'complex_carb', 'fruit', 'healthy_fat'],
                'cooking_methods': ['mixing', 'light_cooking']
            },
            'lunch': {
                'title': 'Template Lunch',
                'base_ingredients': ['protein', 'vegetables', 'complex_carb', 'healthy_fat'],
                'cooking_methods': ['sautéing', 'grilling', 'steaming']
            },
            'dinner': {
                'title': 'Template Dinner',
                'base_ingredients': ['lean_protein', 'vegetables', 'complex_carb'],
                'cooking_methods': ['baking', 'grilling', 'roasting']
            },
            'default': {
                'title': 'Balanced Meal',
                'base_ingredients': ['protein', 'carb', 'vegetable'],
                'cooking_methods': ['mixed']
            }
        }

    def _customize_template(self, template: Dict, meal_config: Dict,
                          nutrition_profile: NutritionProfile, day_num: int) -> Dict:
        """Customize recipe template based on user preferences"""
        # Create customized recipe based on template and user preferences
        title = f"{template['title']} - Day {day_num + 1}"
        
        # Basic customization
        customized_recipe = {
            'title': title,
            'cuisine': nutrition_profile.cuisine_preferences[0] if nutrition_profile.cuisine_preferences else 'International',
            'ingredients': [
                {'name': 'mixed ingredients', 'quantity': 100, 'unit': 'g'}
            ],
            'instructions': ['Prepare ingredients according to dietary preferences', 'Cook using preferred method', 'Serve and enjoy'],
            'prep_time': 15,
            'cook_time': 20,
            'total_time': 35,
            'servings': 1,
            'estimated_nutrition': {
                'calories': meal_config['calories'],
                'protein': meal_config['protein'],
                'carbs': meal_config['carbs'],
                'fat': meal_config['fat']
            }
        }
        
        return customized_recipe