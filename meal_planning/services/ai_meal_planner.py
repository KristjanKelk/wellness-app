"""
AI-powered meal planning service that works with cached recipes
and user nutrition profiles to create optimal meal plans
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Q
from meal_planning.models import Recipe
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AIMealPlanner:
    """
    AI-powered meal planner that creates personalized meal plans
    based on user preferences, nutrition goals, and available recipes
    """
    
    def __init__(self):
        self.meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        
        # Default nutritional targets (can be overridden by user profile)
        self.default_targets = {
            'calories': 2000,
            'protein': 150,  # grams
            'carbs': 250,    # grams
            'fat': 65,       # grams
            'fiber': 25      # grams
        }
    
    def create_meal_plan(self, 
                        user_profile: Dict = None,
                        days: int = 7,
                        dietary_preferences: List[str] = None,
                        allergies: List[str] = None,
                        cuisine_preferences: List[str] = None,
                        target_calories: int = None) -> Dict:
        """
        Create a personalized meal plan for the specified number of days
        
        Args:
            user_profile: User's nutrition profile
            days: Number of days to plan for
            dietary_preferences: List of dietary preferences (vegetarian, vegan, etc.)
            allergies: List of allergies/intolerances
            cuisine_preferences: Preferred cuisines
            target_calories: Daily calorie target
            
        Returns:
            Dictionary containing the meal plan with nutritional analysis
        """
        
        # Set nutrition targets
        nutrition_targets = self._get_nutrition_targets(user_profile, target_calories)
        
        # Get filtered recipes based on preferences
        available_recipes = self._get_filtered_recipes(
            dietary_preferences=dietary_preferences,
            allergies=allergies,
            cuisine_preferences=cuisine_preferences
        )
        
        if not available_recipes:
            return {
                'error': 'No recipes found matching your preferences',
                'suggestion': 'Try broadening your dietary preferences or run the recipe caching command'
            }
        
        # Generate meal plan
        meal_plan = {}
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for day in range(days):
            date_key = (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
            daily_meals = self._plan_single_day(available_recipes, nutrition_targets)
            
            meal_plan[date_key] = {
                'meals': daily_meals,
                'daily_nutrition': self._calculate_daily_nutrition(daily_meals),
                'nutrition_score': self._calculate_nutrition_score(daily_meals, nutrition_targets)
            }
            
            # Add to total nutrition for weekly summary
            daily_nutrition = meal_plan[date_key]['daily_nutrition']
            for nutrient in total_nutrition:
                total_nutrition[nutrient] += daily_nutrition.get(nutrient, 0)
        
        # Calculate weekly averages
        avg_nutrition = {k: v / days for k, v in total_nutrition.items()}
        
        return {
            'meal_plan': meal_plan,
            'summary': {
                'total_days': days,
                'total_recipes': len(set(
                    recipe['id'] for day_plan in meal_plan.values() 
                    for meal in day_plan['meals'].values() 
                    for recipe in meal['recipes']
                )),
                'avg_daily_nutrition': avg_nutrition,
                'nutrition_targets': nutrition_targets,
                'target_adherence': self._calculate_target_adherence(avg_nutrition, nutrition_targets)
            },
            'recommendations': self._generate_recommendations(meal_plan, nutrition_targets)
        }
    
    def suggest_recipe_substitutions(self, 
                                   current_recipe_id: str,
                                   meal_type: str,
                                   dietary_preferences: List[str] = None,
                                   target_calories: int = None) -> List[Dict]:
        """
        Suggest recipe substitutions for a given recipe
        
        Args:
            current_recipe_id: ID of the current recipe to replace
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            dietary_preferences: User's dietary preferences
            target_calories: Target calories for the substitute
            
        Returns:
            List of substitute recipe suggestions with similarity scores
        """
        try:
            current_recipe = Recipe.objects.get(id=current_recipe_id)
        except Recipe.DoesNotExist:
            return []
        
        # Find similar recipes
        candidates = Recipe.objects.filter(meal_type=meal_type).exclude(id=current_recipe_id)
        
        # Apply dietary filters
        if dietary_preferences:
            for pref in dietary_preferences:
                candidates = candidates.filter(dietary_tags__contains=[pref.lower().replace('-', '_')])
        
        # Filter by calorie range (±20% of current recipe)
        if target_calories:
            calorie_range = target_calories * 0.2
            candidates = candidates.filter(
                calories_per_serving__gte=target_calories - calorie_range,
                calories_per_serving__lte=target_calories + calorie_range
            )
        
        # Calculate similarity scores and rank
        substitutions = []
        for candidate in candidates[:20]:  # Limit to top 20 for performance
            score = self._calculate_recipe_similarity(current_recipe, candidate)
            substitutions.append({
                'recipe': {
                    'id': str(candidate.id),
                    'title': candidate.title,
                    'cuisine': candidate.cuisine,
                    'calories_per_serving': candidate.calories_per_serving,
                    'protein_per_serving': candidate.protein_per_serving,
                    'prep_time_minutes': candidate.prep_time_minutes,
                    'difficulty_level': candidate.difficulty_level,
                    'image_url': candidate.image_url,
                    'dietary_tags': candidate.dietary_tags
                },
                'similarity_score': score,
                'nutrition_difference': {
                    'calories': candidate.calories_per_serving - current_recipe.calories_per_serving,
                    'protein': candidate.protein_per_serving - current_recipe.protein_per_serving,
                    'carbs': candidate.carbs_per_serving - current_recipe.carbs_per_serving,
                    'fat': candidate.fat_per_serving - current_recipe.fat_per_serving
                }
            })
        
        # Sort by similarity score
        substitutions.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return substitutions[:10]  # Return top 10 substitutions
    
    def optimize_meal_plan_nutrition(self, 
                                   current_plan: Dict,
                                   nutrition_targets: Dict) -> Dict:
        """
        Optimize an existing meal plan to better meet nutrition targets
        
        Args:
            current_plan: Current meal plan to optimize
            nutrition_targets: Target nutritional values
            
        Returns:
            Optimized meal plan with better nutritional balance
        """
        optimized_plan = current_plan.copy()
        
        for date, day_plan in optimized_plan['meal_plan'].items():
            daily_nutrition = day_plan['daily_nutrition']
            
            # Identify nutritional gaps
            gaps = {}
            for nutrient, target in nutrition_targets.items():
                current = daily_nutrition.get(nutrient, 0)
                if current < target * 0.9:  # Less than 90% of target
                    gaps[nutrient] = target - current
            
            # Try to address gaps through recipe substitutions
            if gaps:
                for meal_type in self.meal_types:
                    if meal_type in day_plan['meals'] and day_plan['meals'][meal_type]['recipes']:
                        current_recipes = day_plan['meals'][meal_type]['recipes']
                        
                        # Try to substitute recipes to fill gaps
                        for i, recipe_data in enumerate(current_recipes):
                            better_recipes = self._find_nutritionally_better_recipes(
                                recipe_data, gaps, meal_type
                            )
                            
                            if better_recipes:
                                # Replace with the best option
                                optimized_plan['meal_plan'][date]['meals'][meal_type]['recipes'][i] = better_recipes[0]
                                break
                
                # Recalculate nutrition after optimization
                optimized_plan['meal_plan'][date]['daily_nutrition'] = self._calculate_daily_nutrition(
                    optimized_plan['meal_plan'][date]['meals']
                )
        
        return optimized_plan
    
    def _get_nutrition_targets(self, user_profile: Dict = None, target_calories: int = None) -> Dict:
        """Get personalized nutrition targets based on user profile"""
        targets = self.default_targets.copy()
        
        if target_calories:
            targets['calories'] = target_calories
        elif user_profile and user_profile.get('daily_calorie_goal'):
            targets['calories'] = user_profile['daily_calorie_goal']
        
        if user_profile:
            # Adjust based on activity level, goals, etc.
            activity_multipliers = {
                'sedentary': 1.0,
                'lightly_active': 1.2,
                'moderately_active': 1.4,
                'very_active': 1.6,
                'extremely_active': 1.8
            }
            
            activity_level = user_profile.get('activity_level', 'moderately_active')
            multiplier = activity_multipliers.get(activity_level, 1.4)
            
            # Adjust protein based on goals
            if user_profile.get('fitness_goal') == 'muscle_gain':
                targets['protein'] = targets['calories'] * 0.35 / 4  # 35% of calories from protein
            elif user_profile.get('fitness_goal') == 'weight_loss':
                targets['protein'] = targets['calories'] * 0.30 / 4  # 30% of calories from protein
        
        return targets
    
    def _get_filtered_recipes(self, 
                            dietary_preferences: List[str] = None,
                            allergies: List[str] = None,
                            cuisine_preferences: List[str] = None) -> List[Recipe]:
        """Get recipes filtered by user preferences"""
        
        queryset = Recipe.objects.filter(is_verified=True)
        
        # Filter by dietary preferences
        if dietary_preferences:
            for pref in dietary_preferences:
                normalized_pref = pref.lower().replace('-', '_')
                queryset = queryset.filter(dietary_tags__contains=[normalized_pref])
        
        # Exclude allergens
        if allergies:
            for allergen in allergies:
                normalized_allergen = allergen.lower()
                queryset = queryset.exclude(allergens__contains=[normalized_allergen])
        
        # Filter by cuisine preferences (if specified)
        if cuisine_preferences:
            cuisine_q = Q()
            for cuisine in cuisine_preferences:
                cuisine_q |= Q(cuisine__icontains=cuisine)
            queryset = queryset.filter(cuisine_q)
        
        # Ensure we have recipes for all meal types
        recipes_by_meal_type = {}
        for meal_type in self.meal_types:
            recipes_by_meal_type[meal_type] = list(
                queryset.filter(meal_type=meal_type).order_by('?')[:50]  # Random selection
            )
        
        # Flatten the list while maintaining meal type info
        all_recipes = []
        for meal_type, recipes in recipes_by_meal_type.items():
            all_recipes.extend(recipes)
        
        return all_recipes
    
    def _plan_single_day(self, available_recipes: List[Recipe], nutrition_targets: Dict) -> Dict:
        """Plan meals for a single day"""
        
        # Group recipes by meal type
        recipes_by_type = {}
        for recipe in available_recipes:
            meal_type = recipe.meal_type
            if meal_type not in recipes_by_type:
                recipes_by_type[meal_type] = []
            recipes_by_type[meal_type].append(recipe)
        
        daily_meals = {}
        
        # Plan each meal type
        for meal_type in self.meal_types:
            if meal_type not in recipes_by_type or not recipes_by_type[meal_type]:
                continue
            
            # Select recipes for this meal
            target_calories_for_meal = self._get_meal_calorie_target(meal_type, nutrition_targets['calories'])
            selected_recipes = self._select_recipes_for_meal(
                recipes_by_type[meal_type], 
                target_calories_for_meal,
                meal_type
            )
            
            daily_meals[meal_type] = {
                'recipes': [self._recipe_to_dict(recipe) for recipe in selected_recipes],
                'meal_nutrition': self._calculate_meal_nutrition(selected_recipes)
            }
        
        return daily_meals
    
    def _get_meal_calorie_target(self, meal_type: str, daily_calories: int) -> int:
        """Get target calories for a specific meal type"""
        calorie_distribution = {
            'breakfast': 0.25,  # 25% of daily calories
            'lunch': 0.35,      # 35% of daily calories
            'dinner': 0.35,     # 35% of daily calories
            'snack': 0.05       # 5% of daily calories
        }
        
        return int(daily_calories * calorie_distribution.get(meal_type, 0.25))
    
    def _select_recipes_for_meal(self, recipes: List[Recipe], target_calories: int, meal_type: str) -> List[Recipe]:
        """Select the best recipes for a meal based on calorie target"""
        
        if not recipes:
            return []
        
        # For most meals, select 1-2 recipes
        if meal_type == 'snack':
            num_recipes = 1
        else:
            num_recipes = random.choice([1, 1, 2])  # Bias towards 1 recipe
        
        if num_recipes == 1:
            # Find the best single recipe
            best_recipe = min(
                recipes,
                key=lambda r: abs(r.calories_per_serving - target_calories)
            )
            return [best_recipe]
        else:
            # Find the best combination of 2 recipes
            best_combination = None
            best_score = float('inf')
            
            for i, recipe1 in enumerate(recipes[:10]):  # Limit for performance
                for recipe2 in recipes[i+1:10]:
                    total_calories = recipe1.calories_per_serving + recipe2.calories_per_serving
                    score = abs(total_calories - target_calories)
                    
                    if score < best_score:
                        best_score = score
                        best_combination = [recipe1, recipe2]
            
            return best_combination or [random.choice(recipes)]
    
    def _recipe_to_dict(self, recipe: Recipe) -> Dict:
        """Convert recipe model to dictionary"""
        return {
            'id': str(recipe.id),
            'title': recipe.title,
            'cuisine': recipe.cuisine,
            'meal_type': recipe.meal_type,
            'servings': recipe.servings,
            'prep_time_minutes': recipe.prep_time_minutes,
            'cook_time_minutes': recipe.cook_time_minutes,
            'total_time_minutes': recipe.total_time_minutes,
            'difficulty_level': recipe.difficulty_level,
            'calories_per_serving': recipe.calories_per_serving,
            'protein_per_serving': recipe.protein_per_serving,
            'carbs_per_serving': recipe.carbs_per_serving,
            'fat_per_serving': recipe.fat_per_serving,
            'fiber_per_serving': recipe.fiber_per_serving,
            'dietary_tags': recipe.dietary_tags,
            'allergens': recipe.allergens,
            'image_url': recipe.image_url,
            'ingredients_data': recipe.ingredients_data,
            'instructions': recipe.instructions
        }
    
    def _calculate_meal_nutrition(self, recipes: List[Recipe]) -> Dict:
        """Calculate total nutrition for a meal"""
        nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for recipe in recipes:
            nutrition['calories'] += recipe.calories_per_serving
            nutrition['protein'] += recipe.protein_per_serving
            nutrition['carbs'] += recipe.carbs_per_serving
            nutrition['fat'] += recipe.fat_per_serving
            nutrition['fiber'] += recipe.fiber_per_serving
        
        return nutrition
    
    def _calculate_daily_nutrition(self, daily_meals: Dict) -> Dict:
        """Calculate total nutrition for a day"""
        daily_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for meal_data in daily_meals.values():
            meal_nutrition = meal_data.get('meal_nutrition', {})
            for nutrient in daily_nutrition:
                daily_nutrition[nutrient] += meal_nutrition.get(nutrient, 0)
        
        return daily_nutrition
    
    def _calculate_nutrition_score(self, daily_meals: Dict, targets: Dict) -> float:
        """Calculate how well the day meets nutrition targets (0-100)"""
        daily_nutrition = self._calculate_daily_nutrition(daily_meals)
        
        scores = []
        for nutrient, target in targets.items():
            if target > 0:
                actual = daily_nutrition.get(nutrient, 0)
                # Score based on how close to target (penalize both under and over)
                ratio = actual / target
                if ratio <= 1.2 and ratio >= 0.8:  # Within 20% of target
                    score = 100 - abs(1 - ratio) * 50  # Max penalty of 10 points
                else:
                    score = max(0, 100 - abs(1 - ratio) * 100)  # Larger penalty for bigger deviations
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def _calculate_target_adherence(self, avg_nutrition: Dict, targets: Dict) -> Dict:
        """Calculate how well the meal plan meets targets"""
        adherence = {}
        
        for nutrient, target in targets.items():
            if target > 0:
                actual = avg_nutrition.get(nutrient, 0)
                percentage = (actual / target) * 100
                adherence[nutrient] = {
                    'target': target,
                    'actual': round(actual, 1),
                    'percentage': round(percentage, 1),
                    'status': 'good' if 80 <= percentage <= 120 else ('low' if percentage < 80 else 'high')
                }
        
        return adherence
    
    def _calculate_recipe_similarity(self, recipe1: Recipe, recipe2: Recipe) -> float:
        """Calculate similarity between two recipes"""
        score = 0
        
        # Cuisine similarity
        if recipe1.cuisine and recipe2.cuisine and recipe1.cuisine.lower() == recipe2.cuisine.lower():
            score += 20
        
        # Dietary tags similarity
        common_tags = set(recipe1.dietary_tags) & set(recipe2.dietary_tags)
        score += len(common_tags) * 10
        
        # Calorie similarity (closer is better)
        calorie_diff = abs(recipe1.calories_per_serving - recipe2.calories_per_serving)
        calorie_score = max(0, 30 - (calorie_diff / 10))  # Up to 30 points
        score += calorie_score
        
        # Cooking time similarity
        time_diff = abs(recipe1.total_time_minutes - recipe2.total_time_minutes)
        time_score = max(0, 20 - (time_diff / 5))  # Up to 20 points
        score += time_score
        
        # Difficulty similarity
        difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
        diff1 = difficulty_map.get(recipe1.difficulty_level, 2)
        diff2 = difficulty_map.get(recipe2.difficulty_level, 2)
        if diff1 == diff2:
            score += 10
        
        return min(100, score)  # Cap at 100
    
    def _find_nutritionally_better_recipes(self, current_recipe_data: Dict, gaps: Dict, meal_type: str) -> List[Dict]:
        """Find recipes that better fill nutritional gaps"""
        candidates = Recipe.objects.filter(meal_type=meal_type).exclude(id=current_recipe_data['id'])
        
        better_recipes = []
        for candidate in candidates[:20]:  # Limit for performance
            improvement_score = 0
            
            for nutrient, gap in gaps.items():
                if gap > 0:  # We need more of this nutrient
                    current_value = current_recipe_data.get(f'{nutrient}_per_serving', 0)
                    candidate_value = getattr(candidate, f'{nutrient}_per_serving', 0)
                    
                    if candidate_value > current_value:
                        improvement_score += (candidate_value - current_value) / gap * 100
            
            if improvement_score > 10:  # Only consider if there's meaningful improvement
                better_recipes.append({
                    **self._recipe_to_dict(candidate),
                    'improvement_score': improvement_score
                })
        
        # Sort by improvement score
        better_recipes.sort(key=lambda x: x['improvement_score'], reverse=True)
        return better_recipes[:5]
    
    def _generate_recommendations(self, meal_plan: Dict, targets: Dict) -> List[str]:
        """Generate recommendations based on the meal plan analysis"""
        recommendations = []
        
        # Analyze average nutrition across all days
        total_days = len(meal_plan)
        avg_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for day_plan in meal_plan.values():
            daily_nutrition = day_plan['daily_nutrition']
            for nutrient in avg_nutrition:
                avg_nutrition[nutrient] += daily_nutrition.get(nutrient, 0)
        
        for nutrient in avg_nutrition:
            avg_nutrition[nutrient] /= total_days
        
        # Generate specific recommendations
        for nutrient, avg_value in avg_nutrition.items():
            target = targets.get(nutrient, 0)
            if target > 0:
                ratio = avg_value / target
                
                if ratio < 0.8:  # Getting less than 80% of target
                    if nutrient == 'protein':
                        recommendations.append(f"Consider adding more protein-rich foods like lean meats, fish, eggs, or legumes")
                    elif nutrient == 'fiber':
                        recommendations.append(f"Add more fiber with vegetables, fruits, and whole grains")
                    elif nutrient == 'calories':
                        recommendations.append(f"Your calorie intake is below target - consider adding healthy snacks")
                elif ratio > 1.2:  # Getting more than 120% of target
                    if nutrient == 'calories':
                        recommendations.append(f"Consider smaller portions or lower-calorie alternatives")
                    elif nutrient == 'fat':
                        recommendations.append(f"Try reducing added fats and choosing leaner cooking methods")
        
        # Add variety recommendations
        cuisines = set()
        for day_plan in meal_plan.values():
            for meal in day_plan['meals'].values():
                for recipe in meal['recipes']:
                    if recipe.get('cuisine'):
                        cuisines.add(recipe['cuisine'])
        
        if len(cuisines) < 3:
            recommendations.append("Try incorporating more diverse cuisines for variety and different nutrients")
        
        return recommendations


# Utility function to get the service
def get_ai_meal_planner() -> AIMealPlanner:
    """Get configured AI meal planner instance"""
    return AIMealPlanner()