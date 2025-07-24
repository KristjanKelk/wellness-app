"""
Advanced AI Meal Planning Service
Implements modern OpenAI integration with function calling, RAG, and sequential prompting
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

import openai
import numpy as np
from openai import OpenAI

# Conditional chromadb import for RAG capabilities
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMADB_AVAILABLE = False

from ..models import (
    NutritionProfile, Recipe, Ingredient, MealPlan, 
    IngredientSubstitution, UserRecipeRating
)


logger = logging.getLogger(__name__)


@dataclass
class MealPlanRequest:
    """Structured request for meal plan generation"""
    user_id: int
    plan_type: str  # 'daily' or 'weekly'
    start_date: datetime
    dietary_restrictions: List[str]
    cuisine_preferences: List[str]
    disliked_ingredients: List[str]
    calorie_target: int
    macronutrient_targets: Dict[str, float]
    meals_per_day: int
    preferred_meal_times: Dict[str, str]
    timezone: str
    additional_requirements: Optional[str] = None


@dataclass
class GeneratedMeal:
    """Structure for a generated meal"""
    name: str
    meal_type: str  # breakfast, lunch, dinner, snack
    time: str  # ISO 8601 format
    recipe_id: Optional[str]
    calories: float
    protein: float
    carbs: float
    fats: float
    ingredients: List[Dict[str, Any]]
    cooking_time: int
    difficulty: str
    alternatives: List[Dict[str, Any]]


class AdvancedAIMealPlanningService:
    """
    Advanced AI Meal Planning Service with:
    - Modern OpenAI integration with function calling
    - RAG (Retrieval-Augmented Generation) capabilities
    - Sequential prompting (3+ step process)
    - Comprehensive nutrition analysis
    - Smart ingredient substitutions
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.setup_vector_database()
        self.setup_function_definitions()
    
    def setup_vector_database(self):
        """Initialize ChromaDB for RAG capabilities"""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available - RAG capabilities disabled. Install 'chromadb' for enhanced functionality.")
            self.chroma_client = None
            return
            
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=getattr(settings, 'CHROMA_PERSIST_DIRECTORY', './chroma_db')
            )
            
            # Recipe collection for RAG
            self.recipe_collection = self.chroma_client.get_or_create_collection(
                name="recipes",
                metadata={"description": "Recipe database for meal planning"}
            )
            
            # Nutrition collection for intelligent recommendations
            self.nutrition_collection = self.chroma_client.get_or_create_collection(
                name="nutrition_knowledge",
                metadata={"description": "Nutrition knowledge base"}
            )
            
        except Exception as e:
            logger.error(f"Failed to setup vector database: {e}")
            self.chroma_client = None
    
    def setup_function_definitions(self):
        """Define function schemas for OpenAI function calling"""
        self.functions = [
            {
                "name": "analyze_nutrition_requirements",
                "description": "Analyze user's nutritional needs based on profile and goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_profile": {
                            "type": "object",
                            "properties": {
                                "dietary_restrictions": {"type": "array", "items": {"type": "string"}},
                                "allergies": {"type": "array", "items": {"type": "string"}},
                                "calorie_target": {"type": "number"},
                                "protein_target": {"type": "number"},
                                "carb_target": {"type": "number"},
                                "fat_target": {"type": "number"}
                            }
                        },
                        "health_goals": {"type": "array", "items": {"type": "string"}},
                        "activity_level": {"type": "string"}
                    },
                    "required": ["user_profile"]
                }
            },
            {
                "name": "generate_meal_structure",
                "description": "Generate optimal meal structure and timing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meals_per_day": {"type": "number"},
                        "preferred_times": {"type": "object"},
                        "calorie_distribution": {"type": "object"},
                        "special_requirements": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["meals_per_day"]
                }
            },
            {
                "name": "create_meal_suggestions",
                "description": "Create specific meal suggestions with recipes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meal_type": {"type": "string"},
                        "target_calories": {"type": "number"},
                        "target_macros": {"type": "object"},
                        "dietary_restrictions": {"type": "array", "items": {"type": "string"}},
                        "cuisine_preference": {"type": "string"},
                        "cooking_time_limit": {"type": "number"},
                        "difficulty_preference": {"type": "string"}
                    },
                    "required": ["meal_type", "target_calories"]
                }
            },
            {
                "name": "generate_shopping_list",
                "description": "Generate categorized shopping list from meal plan",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "meals": {"type": "array", "items": {"type": "object"}},
                        "serving_adjustments": {"type": "object"},
                        "pantry_items_to_exclude": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["meals"]
                }
            }
        ]
    
    async def generate_comprehensive_meal_plan(
        self, 
        request: MealPlanRequest,
        regenerate_specific_meal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for comprehensive meal plan generation
        Uses 3+ step sequential prompting with function calling
        """
        try:
            # Step 1: Nutrition Analysis and Requirements
            nutrition_analysis = await self._step1_analyze_nutrition_requirements(request)
            
            # Step 2: Meal Structure and Timing Optimization
            meal_structure = await self._step2_optimize_meal_structure(
                request, nutrition_analysis
            )
            
            # Step 3: RAG-Enhanced Recipe Retrieval and Selection
            recipes_context = await self._step3_retrieve_relevant_recipes(request)
            
            # Step 4: Intelligent Meal Generation with Function Calling
            meal_plan = await self._step4_generate_meals_with_ai(
                request, nutrition_analysis, meal_structure, recipes_context,
                regenerate_specific_meal
            )
            
            # Step 5: Post-processing and Optimization
            optimized_plan = await self._step5_optimize_and_validate(
                meal_plan, request, nutrition_analysis
            )
            
            # Step 6: Generate Shopping List
            shopping_list = await self._generate_shopping_list(optimized_plan)
            
            return {
                "success": True,
                "meal_plan": optimized_plan,
                "shopping_list": shopping_list,
                "nutrition_summary": nutrition_analysis,
                "metadata": {
                    "generated_at": timezone.now().isoformat(),
                    "plan_type": request.plan_type,
                    "total_days": 7 if request.plan_type == 'weekly' else 1,
                    "regenerated_meal": regenerate_specific_meal
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating meal plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_suggestions": await self._generate_fallback_plan(request)
            }
    
    async def _step1_analyze_nutrition_requirements(
        self, 
        request: MealPlanRequest
    ) -> Dict[str, Any]:
        """
        Step 1: Deep nutrition analysis using AI function calling
        """
        try:
            # Get user's nutrition profile
            nutrition_profile = await self._get_nutrition_profile(request.user_id)
            
            # Prepare context for AI analysis
            user_context = {
                "dietary_restrictions": request.dietary_restrictions,
                "allergies": nutrition_profile.get('allergies_intolerances', []),
                "calorie_target": request.calorie_target,
                "protein_target": request.macronutrient_targets.get('protein', 0),
                "carb_target": request.macronutrient_targets.get('carbs', 0),
                "fat_target": request.macronutrient_targets.get('fats', 0),
                "age": nutrition_profile.get('age'),
                "activity_level": nutrition_profile.get('activity_level', 'moderate'),
                "health_goals": nutrition_profile.get('health_goals', [])
            }
            
            # AI function call for nutrition analysis
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a certified nutritionist AI specializing in personalized nutrition analysis. 
                        Analyze the user's nutritional requirements and provide detailed recommendations for optimal health.
                        Consider dietary restrictions, health goals, and metabolic needs."""
                    },
                    {
                        "role": "user",
                        "content": f"""Please analyze the nutritional requirements for this user profile:
                        {json.dumps(user_context, indent=2)}
                        
                        Provide:
                        1. Optimal macro distribution for their goals
                        2. Key micronutrients to focus on
                        3. Meal timing recommendations
                        4. Special considerations for their dietary restrictions
                        5. Hydration and supplementation suggestions"""
                    }
                ],
                functions=self.functions,
                function_call={"name": "analyze_nutrition_requirements"}
            )
            
            # Parse AI response
            function_call = response.choices[0].message.function_call
            analysis_result = json.loads(function_call.arguments)
            
            return {
                "optimal_macros": analysis_result.get("optimal_macros", {}),
                "micronutrient_focus": analysis_result.get("micronutrient_focus", []),
                "meal_timing": analysis_result.get("meal_timing", {}),
                "special_considerations": analysis_result.get("special_considerations", []),
                "daily_targets": {
                    "calories": request.calorie_target,
                    "protein": request.macronutrient_targets.get('protein', 0),
                    "carbs": request.macronutrient_targets.get('carbs', 0),
                    "fats": request.macronutrient_targets.get('fats', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Step 1 nutrition analysis failed: {e}")
            return await self._fallback_nutrition_analysis(request)
    
    async def _step2_optimize_meal_structure(
        self, 
        request: MealPlanRequest, 
        nutrition_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 2: Optimize meal structure and timing using AI
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a meal planning expert specializing in optimizing meal structure and timing.
                        Design meal schedules that maximize nutritional absorption, energy levels, and user satisfaction."""
                    },
                    {
                        "role": "user",
                        "content": f"""Design an optimal meal structure for:
                        - {request.meals_per_day} meals per day
                        - Target calories: {request.calorie_target}
                        - Preferred times: {request.preferred_meal_times}
                        - Timezone: {request.timezone}
                        - Plan type: {request.plan_type}
                        
                        Nutrition analysis results: {json.dumps(nutrition_analysis, indent=2)}
                        
                        Optimize for energy levels, digestion, and metabolic efficiency."""
                    }
                ],
                functions=self.functions,
                function_call={"name": "generate_meal_structure"}
            )
            
            function_call = response.choices[0].message.function_call
            structure_result = json.loads(function_call.arguments)
            
            return {
                "meal_schedule": structure_result.get("meal_schedule", {}),
                "calorie_distribution": structure_result.get("calorie_distribution", {}),
                "optimal_timing": structure_result.get("optimal_timing", {}),
                "pre_post_workout": structure_result.get("pre_post_workout", {})
            }
            
        except Exception as e:
            logger.error(f"Step 2 meal structure optimization failed: {e}")
            return await self._fallback_meal_structure(request)
    
    async def _step3_retrieve_relevant_recipes(
        self, 
        request: MealPlanRequest
    ) -> Dict[str, Any]:
        """
        Step 3: RAG-enhanced recipe retrieval
        """
        try:
            if not self.chroma_client:
                return await self._fallback_recipe_retrieval(request)
            
            # Create search query embedding
            search_query = f"""
            Dietary restrictions: {', '.join(request.dietary_restrictions)}
            Cuisine preferences: {', '.join(request.cuisine_preferences)}
            Disliked ingredients: {', '.join(request.disliked_ingredients)}
            Calorie target: {request.calorie_target}
            """
            
            # Get embedding for search query
            embedding_response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=search_query
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Search in vector database
            relevant_recipes = self.recipe_collection.query(
                query_embeddings=[query_embedding],
                n_results=20,
                include=['documents', 'metadatas']
            )
            
            # Also get highly rated recipes from database
            high_rated_recipes = Recipe.objects.filter(
                dietary_tags__overlap=request.dietary_restrictions,
                allergens__overlap=[]  # No allergens that user has
            ).order_by('-average_rating')[:10]
            
            return {
                "rag_recipes": relevant_recipes,
                "high_rated_recipes": [self._serialize_recipe(r) for r in high_rated_recipes],
                "recipe_count": len(relevant_recipes['documents'][0]) if relevant_recipes['documents'] else 0
            }
            
        except Exception as e:
            logger.error(f"Step 3 RAG recipe retrieval failed: {e}")
            return await self._fallback_recipe_retrieval(request)
    
    async def _step4_generate_meals_with_ai(
        self, 
        request: MealPlanRequest,
        nutrition_analysis: Dict[str, Any],
        meal_structure: Dict[str, Any],
        recipes_context: Dict[str, Any],
        regenerate_specific_meal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 4: Generate actual meals using AI with comprehensive context
        """
        try:
            # Determine which meals to generate
            if regenerate_specific_meal:
                meals_to_generate = [regenerate_specific_meal]
            else:
                meal_types = self._get_meal_types_for_plan(request.meals_per_day)
                meals_to_generate = meal_types
            
            generated_meals = {}
            
            for meal_type in meals_to_generate:
                # Calculate target nutrition for this meal
                meal_calories = self._calculate_meal_calories(
                    meal_type, request.calorie_target, meal_structure
                )
                meal_macros = self._calculate_meal_macros(
                    meal_type, request.macronutrient_targets, meal_structure
                )
                
                # Generate meal with AI
                meal_response = await self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a creative chef and nutritionist creating personalized meal suggestions.
                            Generate detailed, nutritionally balanced meals that satisfy user preferences and restrictions."""
                        },
                        {
                            "role": "user",
                            "content": f"""Create a {meal_type} meal with:
                            
                            REQUIREMENTS:
                            - Target calories: {meal_calories}
                            - Target macros: {meal_macros}
                            - Dietary restrictions: {request.dietary_restrictions}
                            - Cuisine preferences: {request.cuisine_preferences}
                            - Avoid ingredients: {request.disliked_ingredients}
                            
                            AVAILABLE RECIPES CONTEXT:
                            {json.dumps(recipes_context, indent=2)[:2000]}...
                            
                            NUTRITION ANALYSIS:
                            {json.dumps(nutrition_analysis, indent=2)}
                            
                            Provide complete recipe with:
                            1. Detailed ingredients with quantities
                            2. Step-by-step instructions
                            3. Accurate nutritional information
                            4. Cooking time and difficulty
                            5. 2-3 alternative meal options
                            6. Ingredient substitution suggestions"""
                        }
                    ],
                    functions=self.functions,
                    function_call={"name": "create_meal_suggestions"}
                )
                
                function_call = meal_response.choices[0].message.function_call
                meal_data = json.loads(function_call.arguments)
                
                # Process and structure the meal data
                generated_meals[meal_type] = self._process_generated_meal(
                    meal_data, meal_type, request
                )
            
            return {
                "meals": generated_meals,
                "total_calories": sum(m.get('calories', 0) for m in generated_meals.values()),
                "total_macros": self._calculate_total_macros(generated_meals)
            }
            
        except Exception as e:
            logger.error(f"Step 4 meal generation failed: {e}")
            return await self._fallback_meal_generation(request)
    
    async def _step5_optimize_and_validate(
        self, 
        meal_plan: Dict[str, Any],
        request: MealPlanRequest,
        nutrition_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 5: Final optimization and validation
        """
        try:
            # Validate nutritional targets
            validation_results = self._validate_nutrition_targets(
                meal_plan, request, nutrition_analysis
            )
            
            # Optimize if needed
            if not validation_results['meets_targets']:
                meal_plan = await self._optimize_meal_plan(
                    meal_plan, request, validation_results
                )
            
            # Add meal timing in user's timezone
            meal_plan = self._add_meal_timing(meal_plan, request)
            
            # Generate alternatives for each meal
            meal_plan = await self._generate_meal_alternatives(meal_plan, request)
            
            return {
                **meal_plan,
                "validation_results": validation_results,
                "optimization_applied": not validation_results['meets_targets']
            }
            
        except Exception as e:
            logger.error(f"Step 5 optimization failed: {e}")
            return meal_plan  # Return unoptimized plan if optimization fails
    
    async def _generate_shopping_list(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate intelligent, categorized shopping list
        """
        try:
            # Extract all ingredients from meal plan
            all_ingredients = []
            for meal_type, meal_data in meal_plan.get('meals', {}).items():
                ingredients = meal_data.get('ingredients', [])
                all_ingredients.extend(ingredients)
            
            # Use AI to generate categorized shopping list
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a shopping list optimization expert. Create well-organized, 
                        categorized shopping lists that make grocery shopping efficient and comprehensive."""
                    },
                    {
                        "role": "user",
                        "content": f"""Create a categorized shopping list from these ingredients:
                        {json.dumps(all_ingredients, indent=2)}
                        
                        Categories should include:
                        - Produce (Fruits & Vegetables)
                        - Meat & Seafood  
                        - Dairy & Eggs
                        - Grains & Bread
                        - Pantry Staples
                        - Condiments & Sauces
                        - Beverages
                        - Frozen Foods
                        - Other
                        
                        Consolidate duplicate items and optimize quantities."""
                    }
                ],
                functions=self.functions,
                function_call={"name": "generate_shopping_list"}
            )
            
            function_call = response.choices[0].message.function_call
            shopping_data = json.loads(function_call.arguments)
            
            return {
                "categorized_items": shopping_data.get("categorized_items", {}),
                "total_items": shopping_data.get("total_items", 0),
                "estimated_cost": shopping_data.get("estimated_cost"),
                "shopping_tips": shopping_data.get("shopping_tips", [])
            }
            
        except Exception as e:
            logger.error(f"Shopping list generation failed: {e}")
            return await self._fallback_shopping_list(meal_plan)
    
    # Helper methods
    async def _get_nutrition_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user's nutrition profile"""
        try:
            profile = NutritionProfile.objects.get(user_id=user_id)
            return {
                'dietary_preferences': profile.dietary_preferences,
                'allergies_intolerances': profile.allergies_intolerances,
                'cuisine_preferences': profile.cuisine_preferences,
                'disliked_ingredients': profile.disliked_ingredients,
                'calorie_target': profile.calorie_target,
                'protein_target': profile.protein_target,
                'carb_target': profile.carb_target,
                'fat_target': profile.fat_target,
                'meals_per_day': profile.meals_per_day,
                'activity_level': getattr(profile, 'activity_level', 'moderate')
            }
        except NutritionProfile.DoesNotExist:
            return {}
    
    def _serialize_recipe(self, recipe: Recipe) -> Dict[str, Any]:
        """Serialize recipe object for AI processing"""
        return {
            'id': str(recipe.id),
            'title': recipe.title,
            'description': recipe.description,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions,
            'prep_time': recipe.prep_time_minutes,
            'cook_time': recipe.cook_time_minutes,
            'servings': recipe.servings,
            'calories_per_serving': recipe.calories_per_serving,
            'protein_per_serving': recipe.protein_per_serving,
            'carbs_per_serving': recipe.carbs_per_serving,
            'fat_per_serving': recipe.fat_per_serving,
            'dietary_tags': recipe.dietary_tags,
            'allergens': recipe.allergens,
            'difficulty': recipe.difficulty,
            'average_rating': float(recipe.average_rating) if recipe.average_rating else 0
        }
    
    def _get_meal_types_for_plan(self, meals_per_day: int) -> List[str]:
        """Get meal types based on meals per day"""
        if meals_per_day == 3:
            return ['breakfast', 'lunch', 'dinner']
        elif meals_per_day == 4:
            return ['breakfast', 'lunch', 'snack', 'dinner']
        elif meals_per_day == 5:
            return ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner']
        elif meals_per_day == 6:
            return ['breakfast', 'morning_snack', 'lunch', 'afternoon_snack', 'dinner', 'evening_snack']
        else:
            return ['breakfast', 'lunch', 'dinner']  # Default
    
    def _calculate_meal_calories(
        self, 
        meal_type: str, 
        total_calories: int, 
        meal_structure: Dict[str, Any]
    ) -> int:
        """Calculate target calories for specific meal"""
        distribution = meal_structure.get('calorie_distribution', {})
        
        if meal_type in distribution:
            return int(total_calories * distribution[meal_type])
        
        # Default distributions
        defaults = {
            'breakfast': 0.25,
            'lunch': 0.35,
            'dinner': 0.35,
            'snack': 0.05,
            'morning_snack': 0.10,
            'afternoon_snack': 0.10,
            'evening_snack': 0.05
        }
        
        return int(total_calories * defaults.get(meal_type, 0.25))
    
    def _calculate_meal_macros(
        self, 
        meal_type: str, 
        total_macros: Dict[str, float], 
        meal_structure: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate target macros for specific meal"""
        meal_ratio = meal_structure.get('calorie_distribution', {}).get(meal_type, 0.25)
        
        return {
            'protein': total_macros.get('protein', 0) * meal_ratio,
            'carbs': total_macros.get('carbs', 0) * meal_ratio,
            'fats': total_macros.get('fats', 0) * meal_ratio
        }
    
    def _process_generated_meal(
        self, 
        meal_data: Dict[str, Any], 
        meal_type: str, 
        request: MealPlanRequest
    ) -> Dict[str, Any]:
        """Process and structure generated meal data"""
        return {
            'meal_type': meal_type,
            'name': meal_data.get('name', f'Generated {meal_type.title()}'),
            'description': meal_data.get('description', ''),
            'ingredients': meal_data.get('ingredients', []),
            'instructions': meal_data.get('instructions', []),
            'prep_time': meal_data.get('prep_time', 15),
            'cook_time': meal_data.get('cook_time', 30),
            'calories': meal_data.get('calories', 0),
            'protein': meal_data.get('protein', 0),
            'carbs': meal_data.get('carbs', 0),
            'fats': meal_data.get('fats', 0),
            'fiber': meal_data.get('fiber', 0),
            'difficulty': meal_data.get('difficulty', 'Medium'),
            'alternatives': meal_data.get('alternatives', []),
            'substitutions': meal_data.get('substitutions', [])
        }
    
    def _calculate_total_macros(self, meals: Dict[str, Any]) -> Dict[str, float]:
        """Calculate total macros for all meals"""
        totals = {'protein': 0, 'carbs': 0, 'fats': 0, 'fiber': 0}
        
        for meal in meals.values():
            totals['protein'] += meal.get('protein', 0)
            totals['carbs'] += meal.get('carbs', 0)
            totals['fats'] += meal.get('fats', 0)
            totals['fiber'] += meal.get('fiber', 0)
        
        return totals
    
    def _validate_nutrition_targets(
        self, 
        meal_plan: Dict[str, Any],
        request: MealPlanRequest,
        nutrition_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate if meal plan meets nutrition targets"""
        total_calories = meal_plan.get('total_calories', 0)
        total_macros = meal_plan.get('total_macros', {})
        targets = nutrition_analysis.get('daily_targets', {})
        
        calorie_diff = abs(total_calories - targets.get('calories', 0))
        calorie_tolerance = targets.get('calories', 0) * 0.1  # 10% tolerance
        
        protein_diff = abs(total_macros.get('protein', 0) - targets.get('protein', 0))
        protein_tolerance = targets.get('protein', 0) * 0.15  # 15% tolerance
        
        return {
            'meets_targets': (
                calorie_diff <= calorie_tolerance and 
                protein_diff <= protein_tolerance
            ),
            'calorie_difference': calorie_diff,
            'protein_difference': protein_diff,
            'recommendations': []
        }
    
    def _add_meal_timing(
        self, 
        meal_plan: Dict[str, Any], 
        request: MealPlanRequest
    ) -> Dict[str, Any]:
        """Add meal timing in user's timezone"""
        from datetime import datetime
        import pytz
        
        try:
            user_tz = pytz.timezone(request.timezone)
            base_date = request.start_date.replace(tzinfo=pytz.UTC).astimezone(user_tz)
            
            default_times = {
                'breakfast': '08:00',
                'morning_snack': '10:30',
                'lunch': '12:30',
                'afternoon_snack': '15:30',
                'dinner': '18:30',
                'evening_snack': '20:30'
            }
            
            for meal_type, meal_data in meal_plan.get('meals', {}).items():
                preferred_time = request.preferred_meal_times.get(
                    meal_type, 
                    default_times.get(meal_type, '12:00')
                )
                
                meal_datetime = datetime.combine(
                    base_date.date(),
                    datetime.strptime(preferred_time, '%H:%M').time()
                ).replace(tzinfo=user_tz)
                
                meal_data['scheduled_time'] = meal_datetime.isoformat()
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Failed to add meal timing: {e}")
            return meal_plan
    
    # Fallback methods for error handling
    async def _fallback_nutrition_analysis(self, request: MealPlanRequest) -> Dict[str, Any]:
        """Fallback nutrition analysis if AI fails"""
        return {
            "daily_targets": {
                "calories": request.calorie_target,
                "protein": request.macronutrient_targets.get('protein', request.calorie_target * 0.15 / 4),
                "carbs": request.macronutrient_targets.get('carbs', request.calorie_target * 0.5 / 4),
                "fats": request.macronutrient_targets.get('fats', request.calorie_target * 0.35 / 9)
            },
            "special_considerations": ["Basic nutritional requirements"]
        }
    
    async def _fallback_meal_structure(self, request: MealPlanRequest) -> Dict[str, Any]:
        """Fallback meal structure if AI fails"""
        if request.meals_per_day == 3:
            distribution = {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.40}
        elif request.meals_per_day == 4:
            distribution = {'breakfast': 0.25, 'lunch': 0.30, 'snack': 0.10, 'dinner': 0.35}
        else:
            distribution = {'breakfast': 0.20, 'morning_snack': 0.10, 'lunch': 0.30, 
                          'afternoon_snack': 0.10, 'dinner': 0.30}
        
        return {"calorie_distribution": distribution}
    
    async def _fallback_recipe_retrieval(self, request: MealPlanRequest) -> Dict[str, Any]:
        """Fallback recipe retrieval if RAG fails"""
        recipes = Recipe.objects.filter(
            dietary_tags__overlap=request.dietary_restrictions
        )[:10]
        
        return {
            "high_rated_recipes": [self._serialize_recipe(r) for r in recipes],
            "recipe_count": len(recipes)
        }
    
    async def _fallback_meal_generation(self, request: MealPlanRequest) -> Dict[str, Any]:
        """Fallback meal generation if AI fails"""
        return {
            "meals": {
                "breakfast": {
                    "name": "Simple Breakfast",
                    "calories": request.calorie_target * 0.25,
                    "protein": request.macronutrient_targets.get('protein', 0) * 0.25,
                    "carbs": request.macronutrient_targets.get('carbs', 0) * 0.25,
                    "fats": request.macronutrient_targets.get('fats', 0) * 0.25
                }
            }
        }
    
    async def _fallback_shopping_list(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback shopping list if AI fails"""
        return {
            "categorized_items": {
                "produce": ["Basic fruits and vegetables"],
                "pantry": ["Basic pantry items"]
            },
            "total_items": 2
        }
    
    async def _generate_fallback_plan(self, request: MealPlanRequest) -> Dict[str, Any]:
        """Generate basic fallback plan"""
        return {
            "meals": {
                "breakfast": {"name": "Basic Breakfast", "calories": 400},
                "lunch": {"name": "Basic Lunch", "calories": 500},
                "dinner": {"name": "Basic Dinner", "calories": 600}
            },
            "note": "Simplified meal plan due to system limitations"
        }


# Convenience function for external use
async def generate_ai_meal_plan(
    user_id: int,
    plan_type: str = 'weekly',
    start_date: Optional[datetime] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to generate AI meal plan
    """
    if start_date is None:
        start_date = timezone.now()
    
    # Get user's nutrition profile
    try:
        nutrition_profile = NutritionProfile.objects.get(user_id=user_id)
        
        request = MealPlanRequest(
            user_id=user_id,
            plan_type=plan_type,
            start_date=start_date,
            dietary_restrictions=nutrition_profile.dietary_preferences,
            cuisine_preferences=nutrition_profile.cuisine_preferences,
            disliked_ingredients=nutrition_profile.disliked_ingredients,
            calorie_target=nutrition_profile.calorie_target,
            macronutrient_targets={
                'protein': nutrition_profile.protein_target,
                'carbs': nutrition_profile.carb_target,
                'fats': nutrition_profile.fat_target
            },
            meals_per_day=nutrition_profile.meals_per_day,
            preferred_meal_times=getattr(nutrition_profile, 'preferred_meal_times', {}),
            timezone=kwargs.get('timezone', 'UTC'),
            **kwargs
        )
        
    except NutritionProfile.DoesNotExist:
        # Create default request
        request = MealPlanRequest(
            user_id=user_id,
            plan_type=plan_type,
            start_date=start_date,
            dietary_restrictions=[],
            cuisine_preferences=[],
            disliked_ingredients=[],
            calorie_target=2000,
            macronutrient_targets={'protein': 150, 'carbs': 250, 'fats': 67},
            meals_per_day=3,
            preferred_meal_times={},
            timezone=kwargs.get('timezone', 'UTC')
        )
    
    service = AdvancedAIMealPlanningService()
    return await service.generate_comprehensive_meal_plan(request)