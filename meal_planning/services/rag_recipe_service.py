# meal_planning/services/rag_recipe_service.py
import logging
import json
from typing import Dict, List, Optional, Any
from django.db.models import Q
from django.db import transaction
from ..models import Recipe, Ingredient, NutritionProfile
import openai
from decouple import config

logger = logging.getLogger('nutrition.rag_recipe')


class RAGRecipeService:
    """
    Retrieval-Augmented Generation (RAG) Service for Recipe Recommendations
    
    This service:
    1. Retrieves relevant recipes from the database based on user preferences
    2. Uses AI to generate customized recipes based on retrieved examples
    3. Combines database knowledge with AI creativity for better recommendations
    """

    def __init__(self):
        openai.api_key = config('OPENAI_API_KEY', default='')
        self.min_recipe_database_size = 100  # Minimum recipes needed for good RAG

    @transaction.atomic
    def get_rag_recipe_recommendations(self, nutrition_profile: NutritionProfile, 
                                     meal_type: str, cuisine_preference: str = None) -> Dict:
        """
        Generate recipe recommendations using RAG approach
        
        Args:
            nutrition_profile: User's nutrition profile
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            cuisine_preference: Preferred cuisine type
            
        Returns:
            Dictionary with retrieved recipes and AI-generated alternatives
        """
        try:
            # Step 1: Retrieve relevant recipes from database
            retrieved_recipes = self._retrieve_relevant_recipes(
                nutrition_profile, meal_type, cuisine_preference
            )
            
            # Step 2: Check if we have enough data for good RAG
            if len(retrieved_recipes) < 3:
                logger.warning(f"Limited recipe data for RAG. Found {len(retrieved_recipes)} recipes.")
                return self._generate_basic_recommendations(nutrition_profile, meal_type)
            
            # Step 3: Generate AI-augmented recipes
            ai_generated_recipes = self._generate_rag_recipes(
                retrieved_recipes, nutrition_profile, meal_type, cuisine_preference
            )
            
            # Step 4: Combine and rank recommendations
            combined_recommendations = self._combine_and_rank_recipes(
                retrieved_recipes, ai_generated_recipes, nutrition_profile
            )
            
            return {
                'status': 'success',
                'method': 'rag_enhanced',
                'retrieved_count': len(retrieved_recipes),
                'generated_count': len(ai_generated_recipes),
                'recommendations': combined_recommendations,
                'rag_insights': {
                    'database_coverage': len(retrieved_recipes),
                    'ai_creativity_boost': len(ai_generated_recipes),
                    'personalization_score': self._calculate_personalization_score(
                        combined_recommendations, nutrition_profile
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"RAG recipe recommendation failed: {str(e)}")
            return self._generate_basic_recommendations(nutrition_profile, meal_type)

    def _retrieve_relevant_recipes(self, nutrition_profile: NutritionProfile, 
                                 meal_type: str, cuisine_preference: str = None) -> List[Recipe]:
        """
        Retrieve recipes from database that match user preferences
        
        This is the "Retrieval" part of RAG
        """
        try:
            # Start with base query
            recipes = Recipe.objects.filter(meal_type=meal_type)
            
            # Filter by dietary preferences
            for dietary_pref in nutrition_profile.dietary_preferences or []:
                recipes = recipes.filter(dietary_tags__contains=[dietary_pref])
            
            # Exclude allergens
            for allergen in nutrition_profile.allergies_intolerances or []:
                recipes = recipes.exclude(allergens__contains=[allergen])
            
            # Filter by cuisine if specified
            if cuisine_preference:
                recipes = recipes.filter(cuisine__icontains=cuisine_preference)
            elif nutrition_profile.cuisine_preferences:
                recipes = recipes.filter(cuisine__in=nutrition_profile.cuisine_preferences)
            
            # Exclude disliked ingredients
            for disliked in nutrition_profile.disliked_ingredients or []:
                recipes = recipes.exclude(ingredients__icontains=disliked)
            
            # Filter by calorie range (within 20% of target per meal)
            meal_calorie_target = nutrition_profile.calorie_target // nutrition_profile.meals_per_day
            calorie_min = meal_calorie_target * 0.8
            calorie_max = meal_calorie_target * 1.2
            
            recipes = recipes.filter(
                nutrition_per_serving__calories__gte=calorie_min,
                nutrition_per_serving__calories__lte=calorie_max
            )
            
            # Order by rating and relevance
            recipes = recipes.order_by('-rating', '-created_at')
            
            # Return top 10 most relevant recipes
            return list(recipes[:10])
            
        except Exception as e:
            logger.error(f"Error retrieving relevant recipes: {str(e)}")
            return []

    def _generate_rag_recipes(self, retrieved_recipes: List[Recipe], 
                            nutrition_profile: NutritionProfile, 
                            meal_type: str, cuisine_preference: str = None) -> List[Dict]:
        """
        Generate new recipes using retrieved recipes as context
        
        This is the "Augmented Generation" part of RAG
        """
        try:
            if not retrieved_recipes:
                return []
            
            # Prepare context from retrieved recipes
            recipe_context = self._prepare_recipe_context(retrieved_recipes)
            
            # Prepare user profile context
            user_context = self._prepare_user_context(nutrition_profile, meal_type, cuisine_preference)
            
            # Generate AI prompt with retrieved context
            prompt = f"""
            As a professional chef and nutritionist, create 3 new {meal_type} recipes inspired by these existing recipes:

            EXISTING RECIPE EXAMPLES:
            {recipe_context}

            USER REQUIREMENTS:
            {user_context}

            Please create 3 unique recipes that:
            1. Draw inspiration from the existing recipes but are original
            2. Meet the user's nutritional requirements
            3. Accommodate their dietary preferences and restrictions
            4. Are practical and delicious
            5. Include detailed ingredients and instructions

            Format each recipe as JSON with: title, ingredients, instructions, nutrition_estimate, cooking_time, difficulty
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content
            
            # Parse AI response into structured recipes
            generated_recipes = self._parse_ai_recipes(ai_response)
            
            return generated_recipes
            
        except Exception as e:
            logger.error(f"Error generating RAG recipes: {str(e)}")
            return []

    def _prepare_recipe_context(self, recipes: List[Recipe]) -> str:
        """Prepare retrieved recipes as context for AI"""
        context = ""
        for i, recipe in enumerate(recipes[:5], 1):  # Limit to top 5 to avoid token limits
            context += f"""
            Recipe {i}: {recipe.title}
            Cuisine: {recipe.cuisine}
            Ingredients: {', '.join(recipe.ingredients[:10])}  # First 10 ingredients
            Calories: {recipe.nutrition_per_serving.get('calories', 'N/A')}
            Protein: {recipe.nutrition_per_serving.get('protein', 'N/A')}g
            Rating: {recipe.rating}/5
            Tags: {', '.join(recipe.dietary_tags or [])}
            """
        return context

    def _prepare_user_context(self, nutrition_profile: NutritionProfile, 
                            meal_type: str, cuisine_preference: str = None) -> str:
        """Prepare user requirements as context for AI"""
        meal_calorie_target = nutrition_profile.calorie_target // nutrition_profile.meals_per_day
        
        context = f"""
        Meal Type: {meal_type}
        Target Calories per meal: {meal_calorie_target}
        Daily Protein Target: {nutrition_profile.protein_target}g
        Daily Carb Target: {nutrition_profile.carb_target}g
        Daily Fat Target: {nutrition_profile.fat_target}g
        
        Dietary Preferences: {', '.join(nutrition_profile.dietary_preferences or ['None'])}
        Allergies/Intolerances: {', '.join(nutrition_profile.allergies_intolerances or ['None'])}
        Cuisine Preferences: {', '.join(nutrition_profile.cuisine_preferences or ['Any'])}
        Disliked Ingredients: {', '.join(nutrition_profile.disliked_ingredients or ['None'])}
        
        Preferred Cuisine for this meal: {cuisine_preference or 'Any'}
        """
        return context

    def _parse_ai_recipes(self, ai_response: str) -> List[Dict]:
        """Parse AI response into structured recipe data"""
        try:
            # Try to extract JSON from response
            recipes = []
            lines = ai_response.split('\n')
            current_recipe = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Title:') or line.startswith('Recipe'):
                    if current_recipe:
                        recipes.append(current_recipe)
                        current_recipe = {}
                    current_recipe['title'] = line.split(':', 1)[1].strip() if ':' in line else line
                elif line.startswith('Ingredients:'):
                    current_recipe['ingredients'] = line.split(':', 1)[1].strip()
                elif line.startswith('Instructions:'):
                    current_recipe['instructions'] = line.split(':', 1)[1].strip()
                elif line.startswith('Calories:'):
                    try:
                        current_recipe['estimated_calories'] = int(line.split(':')[1].strip().split()[0])
                    except:
                        current_recipe['estimated_calories'] = 400
            
            if current_recipe:
                recipes.append(current_recipe)
            
            # Ensure we have at least basic structure
            for recipe in recipes:
                if 'title' not in recipe:
                    recipe['title'] = 'AI-Generated Recipe'
                if 'ingredients' not in recipe:
                    recipe['ingredients'] = 'Ingredients not specified'
                if 'instructions' not in recipe:
                    recipe['instructions'] = 'Instructions not specified'
                if 'estimated_calories' not in recipe:
                    recipe['estimated_calories'] = 400
                
                recipe['source'] = 'rag_generated'
                recipe['ai_generated'] = True
            
            return recipes[:3]  # Return max 3 recipes
            
        except Exception as e:
            logger.error(f"Error parsing AI recipes: {str(e)}")
            return []

    def _combine_and_rank_recipes(self, retrieved_recipes: List[Recipe], 
                                ai_generated_recipes: List[Dict], 
                                nutrition_profile: NutritionProfile) -> List[Dict]:
        """Combine retrieved and generated recipes, then rank by relevance"""
        try:
            combined_recipes = []
            
            # Add retrieved recipes
            for recipe in retrieved_recipes[:5]:  # Top 5 retrieved
                combined_recipes.append({
                    'id': recipe.id,
                    'title': recipe.title,
                    'cuisine': recipe.cuisine,
                    'ingredients': recipe.ingredients,
                    'instructions': recipe.preparation_steps,
                    'nutrition': recipe.nutrition_per_serving,
                    'rating': recipe.rating,
                    'source': 'database',
                    'dietary_tags': recipe.dietary_tags or [],
                    'cooking_time': recipe.cook_time,
                    'difficulty': recipe.difficulty_level,
                    'relevance_score': self._calculate_relevance_score(recipe, nutrition_profile)
                })
            
            # Add AI-generated recipes
            for recipe in ai_generated_recipes:
                combined_recipes.append({
                    'title': recipe.get('title', 'AI Recipe'),
                    'cuisine': 'Various',
                    'ingredients': recipe.get('ingredients', ''),
                    'instructions': recipe.get('instructions', ''),
                    'estimated_calories': recipe.get('estimated_calories', 400),
                    'source': 'rag_generated',
                    'ai_generated': True,
                    'relevance_score': 0.8  # AI recipes get a base relevance score
                })
            
            # Sort by relevance score
            combined_recipes.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return combined_recipes[:8]  # Return top 8 recommendations
            
        except Exception as e:
            logger.error(f"Error combining and ranking recipes: {str(e)}")
            return []

    def _calculate_relevance_score(self, recipe: Recipe, nutrition_profile: NutritionProfile) -> float:
        """Calculate how relevant a recipe is to the user's profile"""
        try:
            score = 0.0
            
            # Base score from rating
            score += (recipe.rating or 0) / 5 * 0.3
            
            # Dietary preference matching
            user_prefs = set(nutrition_profile.dietary_preferences or [])
            recipe_tags = set(recipe.dietary_tags or [])
            if user_prefs:
                pref_match = len(user_prefs.intersection(recipe_tags)) / len(user_prefs)
                score += pref_match * 0.3
            
            # Cuisine preference matching
            if nutrition_profile.cuisine_preferences:
                if recipe.cuisine in nutrition_profile.cuisine_preferences:
                    score += 0.2
            
            # Calorie target matching
            meal_target = nutrition_profile.calorie_target // nutrition_profile.meals_per_day
            recipe_calories = recipe.nutrition_per_serving.get('calories', meal_target)
            calorie_diff = abs(recipe_calories - meal_target) / meal_target
            score += max(0, (1 - calorie_diff)) * 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {str(e)}")
            return 0.5

    def _calculate_personalization_score(self, recommendations: List[Dict], 
                                       nutrition_profile: NutritionProfile) -> float:
        """Calculate how well personalized the recommendations are"""
        try:
            if not recommendations:
                return 0.0
            
            scores = []
            for rec in recommendations:
                score = rec.get('relevance_score', 0.5)
                scores.append(score)
            
            return sum(scores) / len(scores)
            
        except Exception as e:
            logger.error(f"Error calculating personalization score: {str(e)}")
            return 0.5

    def _generate_basic_recommendations(self, nutrition_profile: NutritionProfile, 
                                      meal_type: str) -> Dict:
        """Fallback method when RAG isn't possible"""
        try:
            # Get any available recipes for the meal type
            basic_recipes = Recipe.objects.filter(meal_type=meal_type)[:5]
            
            recommendations = []
            for recipe in basic_recipes:
                recommendations.append({
                    'id': recipe.id,
                    'title': recipe.title,
                    'cuisine': recipe.cuisine,
                    'rating': recipe.rating,
                    'source': 'database_basic',
                    'relevance_score': 0.6
                })
            
            return {
                'status': 'success',
                'method': 'basic_fallback',
                'recommendations': recommendations,
                'message': 'Using basic recommendations due to limited recipe database'
            }
            
        except Exception as e:
            logger.error(f"Error generating basic recommendations: {str(e)}")
            return {
                'status': 'error',
                'method': 'fallback_failed',
                'recommendations': [],
                'message': 'Unable to generate recipe recommendations'
            }

    def populate_recipe_database(self, recipe_data: List[Dict]) -> Dict:
        """
        Populate the recipe database for better RAG performance
        
        Args:
            recipe_data: List of recipe dictionaries to add to database
            
        Returns:
            Dictionary with population results
        """
        try:
            created_count = 0
            updated_count = 0
            
            for recipe_dict in recipe_data:
                recipe, created = Recipe.objects.get_or_create(
                    title=recipe_dict.get('title', ''),
                    defaults={
                        'cuisine': recipe_dict.get('cuisine', 'International'),
                        'ingredients': recipe_dict.get('ingredients', []),
                        'preparation_steps': recipe_dict.get('instructions', ''),
                        'nutrition_per_serving': recipe_dict.get('nutrition', {}),
                        'meal_type': recipe_dict.get('meal_type', 'dinner'),
                        'cook_time': recipe_dict.get('cook_time', 30),
                        'difficulty_level': recipe_dict.get('difficulty', 'medium'),
                        'dietary_tags': recipe_dict.get('dietary_tags', []),
                        'source_type': 'rag_database'
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            total_recipes = Recipe.objects.count()
            
            return {
                'status': 'success',
                'created_count': created_count,
                'updated_count': updated_count,
                'total_recipes': total_recipes,
                'rag_ready': total_recipes >= self.min_recipe_database_size
            }
            
        except Exception as e:
            logger.error(f"Error populating recipe database: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to populate recipe database: {str(e)}'
            }