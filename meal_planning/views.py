# meal_planning/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils.decorators import method_decorator
import logging
import json
from datetime import datetime, date

from .models import NutritionProfile, Recipe, MealPlan, NutritionLog
from .serializers import (
    NutritionProfileSerializer, RecipeSerializer, 
    MealPlanSerializer, NutritionLogSerializer
)
from .services.ai_meal_planning_service import AIMealPlanningService
from .services.spoonacular_service import SpoonacularService
from utils.timeouts import with_performance_monitoring, cache_manager, response_optimizer

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 10), name='get')  # Cache for 10 minutes
class NutritionProfileView(generics.RetrieveUpdateAPIView):
    """Optimized nutrition profile view with caching"""
    serializer_class = NutritionProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cache_key = f"nutrition_profile_{self.request.user.id}"
        
        def get_profile():
            profile, created = NutritionProfile.objects.get_or_create(user=self.request.user)
            if created:
                logger.info(f"Created nutrition profile for user {self.request.user.id}")
            return profile
        
        return cache_manager.get_or_set_with_timeout(cache_key, get_profile, timeout=600)

    @with_performance_monitoring('view_response')
    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return response_optimizer.create_optimized_response(
                serializer.data,
                "Nutrition profile retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving nutrition profile: {e}")
            return response_optimizer.create_error_response(
                "Failed to retrieve nutrition profile"
            )

    @with_performance_monitoring('view_response')
    def put(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                
                # Invalidate related caches
                cache_keys = [
                    f"nutrition_profile_{request.user.id}",
                    f"meal_plans_{request.user.id}",
                ]
                cache.delete_many(cache_keys)
                
                return response_optimizer.create_optimized_response(
                    serializer.data,
                    "Nutrition profile updated successfully"
                )
            else:
                return response_optimizer.create_error_response(
                    f"Validation error: {serializer.errors}"
                )
                
        except Exception as e:
            logger.error(f"Error updating nutrition profile: {e}")
            return response_optimizer.create_error_response(
                "Failed to update nutrition profile"
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@with_performance_monitoring('view_response')
def recipe_list_optimized(request):
    """Optimized recipe list with basic filtering and caching"""
    try:
        # Simple caching strategy
        cache_key = "recipes_list_basic"
        
        def get_recipes():
            recipes = Recipe.objects.select_related().filter(
                is_verified=True
            ).values(
                'id', 'title', 'meal_type', 'total_time_minutes',
                'calories_per_serving', 'rating_avg', 'difficulty_level'
            )[:50]  # Limit to 50 recipes for performance
            return list(recipes)
        
        recipes_data = cache_manager.get_or_set_with_timeout(
            cache_key, get_recipes, timeout=300
        )
        
        return response_optimizer.create_optimized_response(
            {'recipes': recipes_data, 'count': len(recipes_data)},
            "Recipes retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving recipes: {e}")
        return response_optimizer.create_error_response(
            "Failed to retrieve recipes"
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@with_performance_monitoring('openai')
def generate_meal_plan_optimized(request):
    """Optimized meal plan generation with timeout protection"""
    try:
        # Check if user has nutrition profile
        try:
            nutrition_profile = NutritionProfile.objects.get(user=request.user)
        except NutritionProfile.DoesNotExist:
            return response_optimizer.create_error_response(
                "Please complete your nutrition profile first"
            )
        
        # Get request parameters
        plan_type = request.data.get('plan_type', 'daily')
        start_date_str = request.data.get('start_date', str(date.today()))
        
        # Check cache first
        cache_key = f"meal_plan_{request.user.id}_{plan_type}_{start_date_str}"
        cached_plan = cache.get(cache_key)
        
        if cached_plan:
            return response_optimizer.create_optimized_response(
                cached_plan,
                "Meal plan retrieved from cache"
            )
        
        # Generate new meal plan with timeout protection
        ai_service = AIMealPlanningService()
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today()
        
        # Use optimized generation method
        meal_plan = ai_service.generate_meal_plan(
            user=request.user,
            plan_type=plan_type,
            start_date=start_date
        )
        
        serializer = MealPlanSerializer(meal_plan)
        response_data = serializer.data
        
        # Cache the result
        cache.set(cache_key, response_data, 1800)  # Cache for 30 minutes
        
        return response_optimizer.create_optimized_response(
            response_data,
            "Meal plan generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating meal plan: {e}")
        return response_optimizer.create_error_response(
            f"Failed to generate meal plan: {str(e)}"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@with_performance_monitoring('view_response')
def user_meal_plans(request):
    """Get user's meal plans with pagination and caching"""
    try:
        cache_key = f"user_meal_plans_{request.user.id}"
        
        def get_meal_plans():
            plans = MealPlan.objects.filter(
                user=request.user,
                is_active=True
            ).order_by('-created_at').values(
                'id', 'plan_type', 'start_date', 'end_date',
                'total_calories', 'created_at'
            )[:10]  # Limit to 10 most recent plans
            return list(plans)
        
        meal_plans_data = cache_manager.get_or_set_with_timeout(
            cache_key, get_meal_plans, timeout=300
        )
        
        return response_optimizer.create_optimized_response(
            {'meal_plans': meal_plans_data, 'count': len(meal_plans_data)},
            "Meal plans retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving meal plans: {e}")
        return response_optimizer.create_error_response(
            "Failed to retrieve meal plans"
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@with_performance_monitoring('spoonacular')
def search_recipes_optimized(request):
    """Optimized recipe search with caching and fallbacks"""
    try:
        query = request.GET.get('query', '')
        meal_type = request.GET.get('meal_type', '')
        
        if not query:
            return response_optimizer.create_error_response(
                "Search query is required"
            )
        
        # Use cache for common searches
        cache_key = f"recipe_search_{query}_{meal_type}"
        
        def search_recipes():
            spoonacular = SpoonacularService()
            try:
                # Use optimized search with shorter timeout
                results = spoonacular.search_recipes(
                    query=query,
                    meal_type=meal_type,
                    max_results=20
                )
                return results
            except Exception as e:
                logger.warning(f"Spoonacular search failed, using fallback: {e}")
                # Fallback to local database search
                local_recipes = Recipe.objects.filter(
                    title__icontains=query,
                    is_verified=True
                ).values(
                    'id', 'title', 'summary', 'total_time_minutes',
                    'calories_per_serving', 'meal_type'
                )[:20]
                return list(local_recipes)
        
        search_results = cache_manager.get_or_set_with_timeout(
            cache_key, search_recipes, timeout=600
        )
        
        return response_optimizer.create_optimized_response(
            {'recipes': search_results, 'count': len(search_results)},
            "Recipe search completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error searching recipes: {e}")
        return response_optimizer.create_error_response(
            "Failed to search recipes"
        )
