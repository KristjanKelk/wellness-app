# meal_planning/services/rag_service.py
import openai
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.db import models
from django.core.cache import cache
from sklearn.metrics.pairwise import cosine_similarity
import json

from meal_planning.models import Recipe, Ingredient

logger = logging.getLogger('nutrition.rag')


class RAGService:
    """
    Retrieval-Augmented Generation service for intelligent recipe and ingredient retrieval
    
    This service implements the complete RAG pipeline:
    1. Database → 2. Embedding → 3. Retrieval → 4. Augmentation → 5. Generation
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=getattr(settings, 'OPENAI_API_KEY', ''))
        self.embedding_model = 'text-embedding-ada-002'
        self.embedding_dimension = 1536
        
    def generate_recipe_embedding(self, recipe: Recipe) -> List[float]:
        """
        Generate embeddings for a recipe based on its content
        
        Args:
            recipe: Recipe model instance
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Create comprehensive text representation of the recipe
            recipe_text = self._create_recipe_text(recipe)
            
            # Check cache first
            cache_key = f"recipe_embedding_{recipe.id}"
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                return cached_embedding
            
            # Generate embedding using OpenAI
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=recipe_text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the embedding for 24 hours
            cache.set(cache_key, embedding, 86400)
            
            logger.info(f"Generated embedding for recipe: {recipe.title}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate recipe embedding: {e}")
            return [0.0] * self.embedding_dimension
    
    def generate_ingredient_embedding(self, ingredient: Ingredient) -> List[float]:
        """
        Generate embeddings for an ingredient based on its properties
        
        Args:
            ingredient: Ingredient model instance
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Create comprehensive text representation of the ingredient
            ingredient_text = self._create_ingredient_text(ingredient)
            
            # Check cache first
            cache_key = f"ingredient_embedding_{ingredient.id}"
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                return cached_embedding
            
            # Generate embedding using OpenAI
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=ingredient_text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the embedding for 24 hours
            cache.set(cache_key, embedding, 86400)
            
            logger.info(f"Generated embedding for ingredient: {ingredient.name}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate ingredient embedding: {e}")
            return [0.0] * self.embedding_dimension
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query string
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Check cache first
            cache_key = f"query_embedding_{hash(query)}"
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                return cached_embedding
            
            # Generate embedding using OpenAI
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            
            embedding = response.data[0].embedding
            
            # Cache the embedding for 1 hour
            cache.set(cache_key, embedding, 3600)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return [0.0] * self.embedding_dimension
    
    def search_similar_recipes(self, 
                              query: str,
                              dietary_preferences: List[str] = None,
                              allergies: List[str] = None,
                              cuisine_preferences: List[str] = None,
                              meal_type: str = None,
                              max_prep_time: int = None,
                              top_k: int = 10) -> List[Dict]:
        """
        Search for similar recipes using vector similarity and filters
        
        Args:
            query: Search query (e.g., "healthy chicken dinner")
            dietary_preferences: List of dietary preferences to filter by
            allergies: List of allergies to avoid
            cuisine_preferences: List of preferred cuisines
            meal_type: Specific meal type (breakfast, lunch, dinner, snack)
            max_prep_time: Maximum preparation time in minutes
            top_k: Number of top results to return
            
        Returns:
            List of recipe dictionaries with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_query_embedding(query)
            
            # Start with base recipe queryset
            recipes_qs = Recipe.objects.all()
            
            # Apply filters
            if dietary_preferences:
                for pref in dietary_preferences:
                    recipes_qs = recipes_qs.filter(dietary_tags__contains=[pref])
            
            if allergies:
                for allergy in allergies:
                    recipes_qs = recipes_qs.exclude(allergens__contains=[allergy])
            
            if cuisine_preferences:
                recipes_qs = recipes_qs.filter(cuisine__in=cuisine_preferences)
            
            if meal_type:
                recipes_qs = recipes_qs.filter(meal_type=meal_type)
            
            if max_prep_time:
                recipes_qs = recipes_qs.filter(total_time_minutes__lte=max_prep_time)
            
            # Get recipes with embeddings
            recipes_with_embeddings = recipes_qs.exclude(
                embedding_vector__isnull=True
            ).exclude(
                embedding_vector=[]
            )
            
            if not recipes_with_embeddings.exists():
                logger.warning("No recipes found with embeddings")
                return []
            
            # Calculate similarities
            similarities = []
            for recipe in recipes_with_embeddings:
                if recipe.embedding_vector:
                    similarity = cosine_similarity(
                        [query_embedding],
                        [recipe.embedding_vector]
                    )[0][0]
                    
                    similarities.append({
                        'recipe': recipe,
                        'similarity': float(similarity),
                        'score': self._calculate_recipe_score(recipe, similarity)
                    })
            
            # Sort by combined score and return top_k
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            results = []
            for item in similarities[:top_k]:
                recipe = item['recipe']
                results.append({
                    'id': str(recipe.id),
                    'title': recipe.title,
                    'cuisine': recipe.cuisine,
                    'meal_type': recipe.meal_type,
                    'prep_time': recipe.total_time_minutes,
                    'difficulty': recipe.difficulty_level,
                    'calories_per_serving': recipe.calories_per_serving,
                    'protein_per_serving': recipe.protein_per_serving,
                    'carbs_per_serving': recipe.carbs_per_serving,
                    'fat_per_serving': recipe.fat_per_serving,
                    'dietary_tags': recipe.dietary_tags,
                    'image_url': recipe.image_url,
                    'similarity_score': item['similarity'],
                    'relevance_score': item['score'],
                    'summary': recipe.summary
                })
            
            logger.info(f"Found {len(results)} similar recipes for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Recipe similarity search failed: {e}")
            return []
    
    def search_similar_ingredients(self,
                                  query: str,
                                  dietary_restrictions: List[str] = None,
                                  allergies: List[str] = None,
                                  category: str = None,
                                  top_k: int = 10) -> List[Dict]:
        """
        Search for similar ingredients using vector similarity
        
        Args:
            query: Search query (e.g., "protein source")
            dietary_restrictions: List of dietary restrictions to filter by
            allergies: List of allergies to avoid
            category: Specific ingredient category
            top_k: Number of top results to return
            
        Returns:
            List of ingredient dictionaries with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_query_embedding(query)
            
            # Start with base ingredient queryset
            ingredients_qs = Ingredient.objects.all()
            
            # Apply filters
            if dietary_restrictions:
                for restriction in dietary_restrictions:
                    ingredients_qs = ingredients_qs.filter(dietary_tags__contains=[restriction])
            
            if allergies:
                for allergy in allergies:
                    ingredients_qs = ingredients_qs.exclude(allergens__contains=[allergy])
            
            if category:
                ingredients_qs = ingredients_qs.filter(category=category)
            
            # Calculate similarities (note: ingredients may not have embeddings yet)
            similarities = []
            for ingredient in ingredients_qs:
                # Generate embedding if not exists
                if not ingredient.embedding_vector:
                    embedding = self.generate_ingredient_embedding(ingredient)
                    # Note: In production, save this back to the database
                else:
                    embedding = ingredient.embedding_vector
                
                if embedding and any(embedding):  # Check if embedding is valid
                    similarity = cosine_similarity(
                        [query_embedding],
                        [embedding]
                    )[0][0]
                    
                    similarities.append({
                        'ingredient': ingredient,
                        'similarity': float(similarity)
                    })
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            results = []
            for item in similarities[:top_k]:
                ingredient = item['ingredient']
                results.append({
                    'id': str(ingredient.id),
                    'name': ingredient.name,
                    'category': ingredient.category,
                    'calories_per_100g': ingredient.calories_per_100g,
                    'protein_per_100g': ingredient.protein_per_100g,
                    'carbs_per_100g': ingredient.carbs_per_100g,
                    'fat_per_100g': ingredient.fat_per_100g,
                    'dietary_tags': ingredient.dietary_tags,
                    'allergens': ingredient.allergens,
                    'similarity_score': item['similarity']
                })
            
            logger.info(f"Found {len(results)} similar ingredients for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Ingredient similarity search failed: {e}")
            return []
    
    def get_recipe_recommendations(self,
                                  user_preferences: Dict,
                                  previous_meals: List[str] = None,
                                  diversity_factor: float = 0.3) -> List[Dict]:
        """
        Get personalized recipe recommendations using RAG
        
        Args:
            user_preferences: Dictionary containing user dietary preferences
            previous_meals: List of recently consumed meals to avoid repetition
            diversity_factor: Factor to promote diversity (0-1)
            
        Returns:
            List of recommended recipes with explanations
        """
        try:
            # Create query based on user preferences
            query_parts = []
            
            if user_preferences.get('dietary_preferences'):
                query_parts.extend(user_preferences['dietary_preferences'])
            
            if user_preferences.get('cuisine_preferences'):
                query_parts.extend(user_preferences['cuisine_preferences'])
            
            if user_preferences.get('health_goal'):
                query_parts.append(user_preferences['health_goal'])
            
            query = ' '.join(query_parts) + ' nutritious healthy meal'
            
            # Search for similar recipes
            recommendations = self.search_similar_recipes(
                query=query,
                dietary_preferences=user_preferences.get('dietary_preferences', []),
                allergies=user_preferences.get('allergies_intolerances', []),
                cuisine_preferences=user_preferences.get('cuisine_preferences', []),
                top_k=20  # Get more results for diversity filtering
            )
            
            # Apply diversity filtering
            if previous_meals:
                recommendations = self._apply_diversity_filter(
                    recommendations, previous_meals, diversity_factor
                )
            
            # Add recommendation explanations
            for rec in recommendations:
                rec['recommendation_reason'] = self._generate_recommendation_reason(
                    rec, user_preferences
                )
            
            return recommendations[:10]  # Return top 10 after diversity filtering
            
        except Exception as e:
            logger.error(f"Recipe recommendation failed: {e}")
            return []
    
    def augment_meal_planning_prompt(self,
                                   base_prompt: str,
                                   user_preferences: Dict,
                                   retrieved_recipes: List[Dict]) -> str:
        """
        Augment meal planning prompt with retrieved recipe context
        
        Args:
            base_prompt: Base prompt for meal planning
            user_preferences: User dietary preferences and restrictions
            retrieved_recipes: List of retrieved recipes from RAG
            
        Returns:
            Augmented prompt with recipe context
        """
        try:
            # Create recipe context
            recipe_context = "Available recipes that match your preferences:\n\n"
            
            for i, recipe in enumerate(retrieved_recipes[:5], 1):
                recipe_context += f"{i}. {recipe['title']}\n"
                recipe_context += f"   - Cuisine: {recipe['cuisine']}\n"
                recipe_context += f"   - Prep time: {recipe['prep_time']} minutes\n"
                recipe_context += f"   - Calories: {recipe['calories_per_serving']} per serving\n"
                recipe_context += f"   - Protein: {recipe['protein_per_serving']}g\n"
                recipe_context += f"   - Dietary tags: {', '.join(recipe['dietary_tags'])}\n"
                if recipe.get('summary'):
                    recipe_context += f"   - Description: {recipe['summary'][:100]}...\n"
                recipe_context += "\n"
            
            # Create dietary context
            dietary_context = "User preferences and restrictions:\n"
            if user_preferences.get('dietary_preferences'):
                dietary_context += f"- Dietary preferences: {', '.join(user_preferences['dietary_preferences'])}\n"
            if user_preferences.get('allergies_intolerances'):
                dietary_context += f"- Allergies/intolerances: {', '.join(user_preferences['allergies_intolerances'])}\n"
            if user_preferences.get('cuisine_preferences'):
                dietary_context += f"- Preferred cuisines: {', '.join(user_preferences['cuisine_preferences'])}\n"
            
            # Combine everything
            augmented_prompt = f"""
{base_prompt}

{dietary_context}

{recipe_context}

Please prioritize using the recipes listed above when creating the meal plan, as they have been specifically selected to match the user's preferences and dietary requirements. You may adapt portions and combinations as needed to meet nutritional targets.
"""
            
            return augmented_prompt.strip()
            
        except Exception as e:
            logger.error(f"Prompt augmentation failed: {e}")
            return base_prompt
    
    def _create_recipe_text(self, recipe: Recipe) -> str:
        """Create comprehensive text representation of a recipe for embedding"""
        text_parts = [
            recipe.title,
            recipe.summary or '',
            recipe.cuisine or '',
            recipe.meal_type,
            recipe.difficulty_level,
            ' '.join(recipe.dietary_tags),
            f"preparation time {recipe.total_time_minutes} minutes",
            f"serves {recipe.servings}"
        ]
        
        # Add ingredient information
        if recipe.ingredients_data:
            if isinstance(recipe.ingredients_data, list):
                for ing in recipe.ingredients_data:
                    if isinstance(ing, dict) and 'name' in ing:
                        text_parts.append(ing['name'])
            elif isinstance(recipe.ingredients_data, dict):
                text_parts.append(str(recipe.ingredients_data))
        
        # Add nutritional information
        text_parts.extend([
            f"{recipe.calories_per_serving} calories",
            f"{recipe.protein_per_serving}g protein",
            f"{recipe.carbs_per_serving}g carbs",
            f"{recipe.fat_per_serving}g fat"
        ])
        
        return ' '.join(filter(None, text_parts))
    
    def _create_ingredient_text(self, ingredient: Ingredient) -> str:
        """Create comprehensive text representation of an ingredient for embedding"""
        text_parts = [
            ingredient.name,
            ingredient.category,
            ' '.join(ingredient.dietary_tags),
            f"{ingredient.calories_per_100g} calories per 100g",
            f"{ingredient.protein_per_100g}g protein per 100g",
            f"{ingredient.carbs_per_100g}g carbs per 100g",
            f"{ingredient.fat_per_100g}g fat per 100g"
        ]
        
        return ' '.join(filter(None, text_parts))
    
    def _calculate_recipe_score(self, recipe: Recipe, similarity: float) -> float:
        """Calculate combined score for recipe ranking"""
        # Base similarity score
        score = similarity
        
        # Boost for higher ratings
        if recipe.rating_avg > 0:
            score += (recipe.rating_avg / 5.0) * 0.1
        
        # Boost for verified recipes
        if recipe.is_verified:
            score += 0.05
        
        # Boost for popular recipes
        if recipe.view_count > 100:
            score += 0.02
        
        return score
    
    def _apply_diversity_filter(self,
                               recommendations: List[Dict],
                               previous_meals: List[str],
                               diversity_factor: float) -> List[Dict]:
        """Apply diversity filtering to avoid repetitive recommendations"""
        # Simple diversity: penalize recipes with similar cuisines or titles
        filtered_recommendations = []
        used_cuisines = set()
        
        for rec in recommendations:
            cuisine = rec.get('cuisine', '').lower()
            title_words = set(rec.get('title', '').lower().split())
            
            # Check for cuisine diversity
            cuisine_penalty = 0
            if cuisine in used_cuisines:
                cuisine_penalty = diversity_factor
            
            # Check for title similarity with previous meals
            title_penalty = 0
            for prev_meal in previous_meals:
                prev_words = set(prev_meal.lower().split())
                overlap = len(title_words.intersection(prev_words))
                if overlap > 1:  # Significant overlap
                    title_penalty = diversity_factor
                    break
            
            # Apply penalties
            rec['diversity_score'] = rec['relevance_score'] - cuisine_penalty - title_penalty
            filtered_recommendations.append(rec)
            used_cuisines.add(cuisine)
        
        # Sort by diversity score
        filtered_recommendations.sort(key=lambda x: x['diversity_score'], reverse=True)
        return filtered_recommendations
    
    def _generate_recommendation_reason(self,
                                       recipe: Dict,
                                       user_preferences: Dict) -> str:
        """Generate explanation for why this recipe was recommended"""
        reasons = []
        
        # Check dietary preferences match
        recipe_tags = recipe.get('dietary_tags', [])
        user_dietary = user_preferences.get('dietary_preferences', [])
        matching_dietary = set(recipe_tags).intersection(set(user_dietary))
        if matching_dietary:
            reasons.append(f"Matches your {', '.join(matching_dietary)} preferences")
        
        # Check cuisine preferences
        cuisine = recipe.get('cuisine', '')
        user_cuisines = user_preferences.get('cuisine_preferences', [])
        if cuisine.lower() in [c.lower() for c in user_cuisines]:
            reasons.append(f"Features your preferred {cuisine} cuisine")
        
        # Check nutritional alignment
        if recipe.get('protein_per_serving', 0) > 20:
            reasons.append("High protein content")
        
        if recipe.get('calories_per_serving', 0) < 400:
            reasons.append("Lower calorie option")
        
        # Default reason
        if not reasons:
            reasons.append("High similarity to your preferences")
        
        return "; ".join(reasons)

    def update_recipe_embeddings_batch(self, batch_size: int = 50) -> int:
        """
        Update embeddings for recipes that don't have them
        
        Args:
            batch_size: Number of recipes to process in each batch
            
        Returns:
            Number of recipes updated
        """
        try:
            # Get recipes without embeddings
            recipes_without_embeddings = Recipe.objects.filter(
                models.Q(embedding_vector__isnull=True) | 
                models.Q(embedding_vector=[])
            )[:batch_size]
            
            updated_count = 0
            for recipe in recipes_without_embeddings:
                try:
                    embedding = self.generate_recipe_embedding(recipe)
                    recipe.embedding_vector = embedding
                    recipe.save(update_fields=['embedding_vector'])
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to update embedding for recipe {recipe.id}: {e}")
                    continue
            
            logger.info(f"Updated embeddings for {updated_count} recipes")
            return updated_count
            
        except Exception as e:
            logger.error(f"Batch embedding update failed: {e}")
            return 0