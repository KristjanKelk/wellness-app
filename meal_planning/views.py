"""
Comprehensive Meal Planning Views
Implements all required features: AI meal plans, shopping lists, meal swapping, etc.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.db import transaction
from django.db import models

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    NutritionProfile, MealPlan, Recipe, Ingredient, 
    IngredientSubstitution, UserRecipeRating, NutritionLog
)
from .services.ai_meal_planning_service import (
    AdvancedAIMealPlanningService, MealPlanRequest, generate_ai_meal_plan
)
from .services.nutrition_calculation_service import NutritionCalculationService


class MealPlanningDashboardView(View):
    """Main dashboard view for meal planning"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Render the meal planning dashboard"""
        try:
            # Get user's nutrition profile
            nutrition_profile, created = NutritionProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'calorie_target': 2000,
                    'protein_target': 150,
                    'carb_target': 250,
                    'fat_target': 67,
                    'meals_per_day': 3,
                    'dietary_preferences': [],
                    'allergies_intolerances': [],
                    'cuisine_preferences': [],
                    'disliked_ingredients': []
                }
            )
            
            # Get recent meal plans
            recent_plans = MealPlan.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
            
            # Get nutrition log for the last 7 days
            week_ago = timezone.now().date() - timedelta(days=7)
            recent_logs = NutritionLog.objects.filter(
                user=request.user,
                date__gte=week_ago
            ).order_by('-date')
            
            context = {
                'nutrition_profile': nutrition_profile,
                'recent_plans': recent_plans,
                'recent_logs': recent_logs,
                'total_meal_plans': MealPlan.objects.filter(user=request.user).count(),
                'has_active_plan': MealPlan.objects.filter(
                    user=request.user, 
                    is_active=True
                ).exists()
            }
            
            return render(request, 'meal_planning/dashboard.html', context)
            
        except Exception as e:
            return render(request, 'meal_planning/dashboard.html', {
                'error': f'Error loading dashboard: {str(e)}'
            })


# API Views for Meal Planning

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def nutrition_profile_view(request):
    """Get or update user's nutrition profile"""
    
    if request.method == 'GET':
        try:
            profile = NutritionProfile.objects.get(user=request.user)
            return Response({
                'success': True,
                'data': {
                    'dietary_preferences': profile.dietary_preferences,
                    'allergies_intolerances': profile.allergies_intolerances,
                    'cuisine_preferences': profile.cuisine_preferences,
                    'disliked_ingredients': profile.disliked_ingredients,
                    'calorie_target': profile.calorie_target,
                    'protein_target': profile.protein_target,
                    'carb_target': profile.carb_target,
                    'fat_target': profile.fat_target,
                    'meals_per_day': profile.meals_per_day,
                    'preferred_meal_times': getattr(profile, 'preferred_meal_times', {}),
                    'timezone': getattr(profile, 'timezone', 'UTC')
                }
            })
        except NutritionProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Nutrition profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['calorie_target', 'protein_target', 'carb_target', 'fat_target']
            for field in required_fields:
                if field not in data:
                    return Response({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate dietary preferences (must be from supported list)
            supported_diets = [choice[0] for choice in NutritionProfile.DIETARY_PREFERENCES]
            dietary_preferences = data.get('dietary_preferences', [])
            for diet in dietary_preferences:
                if diet not in supported_diets:
                    return Response({
                        'success': False,
                        'error': f'Unsupported dietary preference: {diet}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate allergies (must be from supported list)
            supported_allergies = [choice[0] for choice in NutritionProfile.ALLERGIES_INTOLERANCES]
            allergies = data.get('allergies_intolerances', [])
            for allergy in allergies:
                if allergy not in supported_allergies:
                    return Response({
                        'success': False,
                        'error': f'Unsupported allergy/intolerance: {allergy}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update or create profile
            profile, created = NutritionProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    'dietary_preferences': dietary_preferences,
                    'allergies_intolerances': allergies,
                    'cuisine_preferences': data.get('cuisine_preferences', []),
                    'disliked_ingredients': data.get('disliked_ingredients', []),
                    'calorie_target': int(data['calorie_target']),
                    'protein_target': float(data['protein_target']),
                    'carb_target': float(data['carb_target']),
                    'fat_target': float(data['fat_target']),
                    'meals_per_day': int(data.get('meals_per_day', 3)),
                    'preferred_meal_times': data.get('preferred_meal_times', {}),
                    'timezone': data.get('timezone', 'UTC')
                }
            )
            
            return Response({
                'success': True,
                'message': 'Nutrition profile updated successfully',
                'created': created
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error updating profile: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_meal_plan_view(request):
    """Generate AI-powered meal plan"""
    
    try:
        data = request.data
        
        # Validate input data
        plan_type = data.get('plan_type', 'weekly')
        if plan_type not in ['daily', 'weekly']:
            return Response({
                'success': False,
                'error': 'plan_type must be "daily" or "weekly"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse start date
        start_date_str = data.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid start_date format. Use ISO 8601 format.'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            start_date = timezone.now()
        
        # Get user timezone
        user_timezone = data.get('timezone', 'UTC')
        
        # Generate meal plan using AI service
        try:
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                generate_ai_meal_plan(
                    user_id=request.user.id,
                    plan_type=plan_type,
                    start_date=start_date,
                    timezone=user_timezone,
                    **data.get('additional_requirements', {})
                )
            )
            loop.close()
            
            if not result.get('success'):
                return Response({
                    'success': False,
                    'error': result.get('error', 'Failed to generate meal plan'),
                    'fallback_suggestions': result.get('fallback_suggestions')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Save meal plan to database
            end_date = start_date + timedelta(days=6 if plan_type == 'weekly' else 0)
            
            meal_plan = MealPlan.objects.create(
                user=request.user,
                plan_type=plan_type,
                start_date=start_date.date(),
                end_date=end_date.date(),
                meal_plan_data=result['meal_plan'],
                shopping_list_data=result['shopping_list'],
                total_calories=result['meal_plan'].get('total_calories', 0),
                avg_daily_calories=result['meal_plan'].get('total_calories', 0) / (7 if plan_type == 'weekly' else 1),
                total_protein=result['meal_plan'].get('total_macros', {}).get('protein', 0),
                total_carbs=result['meal_plan'].get('total_macros', {}).get('carbs', 0),
                total_fat=result['meal_plan'].get('total_macros', {}).get('fats', 0),
                nutritional_balance_score=8.5,  # Default score, can be calculated
                variety_score=8.0,
                preference_match_score=8.5,
                ai_model_used='gpt-4',
                generation_version='3.0'
            )
            
            return Response({
                'success': True,
                'data': {
                    'meal_plan_id': meal_plan.id,
                    'meal_plan': result['meal_plan'],
                    'shopping_list': result['shopping_list'],
                    'nutrition_summary': result['nutrition_summary'],
                    'metadata': result['metadata']
                }
            })
            
        except Exception as ai_error:
            return Response({
                'success': False,
                'error': f'AI service error: {str(ai_error)}',
                'details': 'The meal planning AI service encountered an error. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meal_plans_view(request):
    """Get user's meal plans with pagination"""
    
    try:
        # Query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 10)), 50)  # Max 50 per page
        plan_type = request.GET.get('plan_type')  # Filter by type
        is_active = request.GET.get('is_active')  # Filter by active status
        
        # Build queryset
        queryset = MealPlan.objects.filter(user=request.user).order_by('-created_at')
        
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        meal_plans = []
        for plan in page_obj:
            meal_plans.append({
                'id': plan.id,
                'plan_type': plan.plan_type,
                'start_date': plan.start_date.isoformat(),
                'end_date': plan.end_date.isoformat(),
                'is_active': plan.is_active,
                'total_calories': plan.total_calories,
                'avg_daily_calories': plan.avg_daily_calories,
                'nutritional_balance_score': plan.nutritional_balance_score,
                'variety_score': plan.variety_score,
                'preference_match_score': plan.preference_match_score,
                'created_at': plan.created_at.isoformat(),
                'meal_count': len(plan.meal_plan_data.get('meals', {})) if plan.meal_plan_data else 0
            })
        
        return Response({
            'success': True,
            'data': {
                'meal_plans': meal_plans,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error retrieving meal plans: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def meal_plan_detail_view(request, plan_id):
    """Get, update, or delete a specific meal plan"""
    
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        
        if request.method == 'GET':
            return Response({
                'success': True,
                'data': {
                    'id': meal_plan.id,
                    'plan_type': meal_plan.plan_type,
                    'start_date': meal_plan.start_date.isoformat(),
                    'end_date': meal_plan.end_date.isoformat(),
                    'is_active': meal_plan.is_active,
                    'meal_plan_data': meal_plan.meal_plan_data,
                    'shopping_list_data': meal_plan.shopping_list_data,
                    'nutrition_summary': {
                        'total_calories': meal_plan.total_calories,
                        'avg_daily_calories': meal_plan.avg_daily_calories,
                        'total_protein': meal_plan.total_protein,
                        'total_carbs': meal_plan.total_carbs,
                        'total_fat': meal_plan.total_fat
                    },
                    'scores': {
                        'nutritional_balance': meal_plan.nutritional_balance_score,
                        'variety': meal_plan.variety_score,
                        'preference_match': meal_plan.preference_match_score
                    },
                    'metadata': {
                        'ai_model_used': meal_plan.ai_model_used,
                        'generation_version': meal_plan.generation_version,
                        'created_at': meal_plan.created_at.isoformat(),
                        'updated_at': meal_plan.updated_at.isoformat()
                    }
                }
            })
        
        elif request.method == 'PUT':
            # Update meal plan (e.g., activate/deactivate, update meal data)
            data = request.data
            
            if 'is_active' in data:
                if data['is_active']:
                    # Deactivate other meal plans first
                    MealPlan.objects.filter(user=request.user, is_active=True).update(is_active=False)
                meal_plan.is_active = data['is_active']
            
            if 'meal_plan_data' in data:
                meal_plan.meal_plan_data = data['meal_plan_data']
                # Recalculate nutrition if needed
                # This could be enhanced with proper nutrition calculation
            
            meal_plan.save()
            
            return Response({
                'success': True,
                'message': 'Meal plan updated successfully'
            })
        
        elif request.method == 'DELETE':
            meal_plan.delete()
            return Response({
                'success': True,
                'message': 'Meal plan deleted successfully'
            })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error handling meal plan: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_meal_view(request, plan_id):
    """Regenerate a specific meal in a meal plan"""
    
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        data = request.data
        
        # Validate required fields
        meal_type = data.get('meal_type')
        day_date = data.get('day_date')  # ISO date string
        
        if not meal_type or not day_date:
            return Response({
                'success': False,
                'error': 'meal_type and day_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use AI service to regenerate the specific meal
        try:
            # Get user's nutrition profile for regeneration
            nutrition_profile = NutritionProfile.objects.get(user=request.user)
            
            # Create meal plan request for regeneration
            request_obj = MealPlanRequest(
                user_id=request.user.id,
                plan_type=meal_plan.plan_type,
                start_date=datetime.combine(meal_plan.start_date, datetime.min.time()),
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
                timezone=getattr(nutrition_profile, 'timezone', 'UTC')
            )
            
            # Run AI regeneration
            ai_service = AdvancedAIMealPlanningService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                ai_service.generate_comprehensive_meal_plan(
                    request_obj, 
                    regenerate_specific_meal=meal_type
                )
            )
            loop.close()
            
            if result.get('success'):
                # Update the meal plan data with the new meal
                updated_meal_data = meal_plan.meal_plan_data.copy()
                new_meal = result['meal_plan']['meals'].get(meal_type)
                
                if new_meal:
                    # Update the specific meal in the plan data
                    # This is a simplified approach - in production you might want more sophisticated merging
                    if 'meals' not in updated_meal_data:
                        updated_meal_data['meals'] = {}
                    
                    updated_meal_data['meals'][meal_type] = new_meal
                    
                    # Update the meal plan
                    meal_plan.meal_plan_data = updated_meal_data
                    meal_plan.save()
                    
                    return Response({
                        'success': True,
                        'data': {
                            'regenerated_meal': new_meal,
                            'meal_type': meal_type,
                            'day_date': day_date
                        },
                        'message': f'{meal_type.title()} regenerated successfully'
                    })
                else:
                    return Response({
                        'success': False,
                        'error': 'Failed to generate new meal'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'AI regeneration failed')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except NutritionProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Nutrition profile required for meal regeneration'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error regenerating meal: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def swap_meals_view(request, plan_id):
    """Swap two meals in a meal plan"""
    
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        data = request.data
        
        # Validate required fields
        meal1 = data.get('meal1')  # {meal_type: str, day_date: str}
        meal2 = data.get('meal2')  # {meal_type: str, day_date: str}
        
        if not meal1 or not meal2:
            return Response({
                'success': False,
                'error': 'meal1 and meal2 objects are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        required_fields = ['meal_type', 'day_date']
        for meal_obj in [meal1, meal2]:
            for field in required_fields:
                if field not in meal_obj:
                    return Response({
                        'success': False,
                        'error': f'Missing {field} in meal object'
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Perform the swap in meal plan data
        meal_plan_data = meal_plan.meal_plan_data.copy()
        
        # This is a simplified swap - in production you'd handle more complex meal plan structures
        meals = meal_plan_data.get('meals', {})
        
        # Get meals to swap
        meal1_data = meals.get(meal1['meal_type'])
        meal2_data = meals.get(meal2['meal_type'])
        
        if not meal1_data or not meal2_data:
            return Response({
                'success': False,
                'error': 'One or both meals not found in meal plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Swap the meals
        meals[meal1['meal_type']] = meal2_data
        meals[meal2['meal_type']] = meal1_data
        
        # Update the meal plan
        meal_plan.meal_plan_data = meal_plan_data
        meal_plan.save()
        
        return Response({
            'success': True,
            'message': 'Meals swapped successfully',
            'data': {
                'swapped_meals': [meal1, meal2],
                'updated_meal_plan': meal_plan_data
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error swapping meals: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_manual_meal_view(request, plan_id):
    """Add a manual meal to a meal plan"""
    
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        data = request.data
        
        # Validate required fields
        required_fields = ['meal_type', 'day_date', 'meal_data']
        for field in required_fields:
            if field not in data:
                return Response({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        meal_data = data['meal_data']
        
        # Validate meal data structure
        meal_required_fields = ['name', 'calories', 'ingredients']
        for field in meal_required_fields:
            if field not in meal_data:
                return Response({
                    'success': False,
                    'error': f'Missing required meal field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add the manual meal to the plan
        meal_plan_data = meal_plan.meal_plan_data.copy()
        
        if 'meals' not in meal_plan_data:
            meal_plan_data['meals'] = {}
        
        # Add manual meal indicator
        meal_data['manual_meal'] = True
        meal_data['added_at'] = timezone.now().isoformat()
        
        meal_plan_data['meals'][data['meal_type']] = meal_data
        
        # Update totals if nutrition info provided
        if all(key in meal_data for key in ['protein', 'carbs', 'fats']):
            # Recalculate plan totals
            total_calories = sum(
                meal.get('calories', 0) 
                for meal in meal_plan_data['meals'].values()
            )
            total_protein = sum(
                meal.get('protein', 0) 
                for meal in meal_plan_data['meals'].values()
            )
            total_carbs = sum(
                meal.get('carbs', 0) 
                for meal in meal_plan_data['meals'].values()
            )
            total_fat = sum(
                meal.get('fats', 0) 
                for meal in meal_plan_data['meals'].values()
            )
            
            meal_plan.total_calories = total_calories
            meal_plan.total_protein = total_protein
            meal_plan.total_carbs = total_carbs
            meal_plan.total_fat = total_fat
        
        meal_plan.meal_plan_data = meal_plan_data
        meal_plan.save()
        
        return Response({
            'success': True,
            'message': 'Manual meal added successfully',
            'data': {
                'added_meal': meal_data,
                'meal_type': data['meal_type'],
                'day_date': data['day_date']
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error adding manual meal: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_shopping_list_view(request, plan_id):
    """Generate or get shopping list for a meal plan"""
    
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        
        # Check if shopping list already exists
        if meal_plan.shopping_list_data:
            shopping_list = meal_plan.shopping_list_data
        else:
            # Generate new shopping list using AI service
            ai_service = AdvancedAIMealPlanningService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            shopping_list = loop.run_until_complete(
                ai_service._generate_shopping_list(meal_plan.meal_plan_data)
            )
            loop.close()
            
            # Save to meal plan
            meal_plan.shopping_list_data = shopping_list
            meal_plan.save()
        
        return Response({
            'success': True,
            'data': {
                'shopping_list': shopping_list,
                'meal_plan_id': plan_id,
                'generated_at': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error generating shopping list: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_shopping_list_view(request, plan_id):
    """Update shopping list (remove items, adjust quantities)"""
    
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        data = request.data
        
        # Get current shopping list
        shopping_list = meal_plan.shopping_list_data or {}
        
        # Handle different update operations
        operation = data.get('operation')
        
        if operation == 'remove_item':
            category = data.get('category')
            item_name = data.get('item_name')
            
            if category and item_name:
                categorized_items = shopping_list.get('categorized_items', {})
                if category in categorized_items:
                    items = categorized_items[category]
                    if isinstance(items, list) and item_name in items:
                        items.remove(item_name)
                    elif isinstance(items, dict) and item_name in items:
                        del items[item_name]
        
        elif operation == 'adjust_quantity':
            category = data.get('category')
            item_name = data.get('item_name')
            new_quantity = data.get('quantity')
            
            if category and item_name and new_quantity:
                categorized_items = shopping_list.get('categorized_items', {})
                if category in categorized_items:
                    items = categorized_items[category]
                    if isinstance(items, dict) and item_name in items:
                        items[item_name]['quantity'] = new_quantity
        
        elif operation == 'add_item':
            category = data.get('category')
            item_name = data.get('item_name')
            quantity = data.get('quantity', '1')
            
            if category and item_name:
                categorized_items = shopping_list.get('categorized_items', {})
                if category not in categorized_items:
                    categorized_items[category] = {}
                
                if isinstance(categorized_items[category], list):
                    categorized_items[category].append(item_name)
                else:
                    categorized_items[category][item_name] = {'quantity': quantity}
        
        # Update the shopping list
        shopping_list['last_updated'] = timezone.now().isoformat()
        meal_plan.shopping_list_data = shopping_list
        meal_plan.save()
        
        return Response({
            'success': True,
            'message': 'Shopping list updated successfully',
            'data': {
                'updated_shopping_list': shopping_list
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error updating shopping list: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recipes_view(request):
    """Get recipes with filtering and search"""
    
    try:
        # Query parameters
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 20)), 100)
        search = request.GET.get('search', '').strip()
        dietary_tags = request.GET.getlist('dietary_tags')
        cuisine = request.GET.get('cuisine')
        difficulty = request.GET.get('difficulty')
        max_prep_time = request.GET.get('max_prep_time')
        min_rating = request.GET.get('min_rating')
        
        # Build queryset
        queryset = Recipe.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(ingredients__icontains=search)
            )
        
        if dietary_tags:
            for tag in dietary_tags:
                queryset = queryset.filter(dietary_tags__contains=[tag])
        
        if cuisine:
            queryset = queryset.filter(cuisine__iexact=cuisine)
        
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)
        
        if max_prep_time:
            total_time = int(max_prep_time)
            queryset = queryset.filter(
                prep_time_minutes + models.F('cook_time_minutes') <= total_time
            )
        
        if min_rating:
            min_rating_val = float(min_rating)
            queryset = queryset.filter(average_rating__gte=min_rating_val)
        
        # Order by rating and creation date
        queryset = queryset.order_by('-average_rating', '-created_at')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize recipes
        recipes = []
        for recipe in page_obj:
            recipes.append({
                'id': recipe.id,
                'title': recipe.title,
                'description': recipe.description,
                'cuisine': recipe.cuisine,
                'difficulty': recipe.difficulty,
                'prep_time': recipe.prep_time_minutes,
                'cook_time': recipe.cook_time_minutes,
                'total_time': recipe.prep_time_minutes + recipe.cook_time_minutes,
                'servings': recipe.servings,
                'calories_per_serving': recipe.calories_per_serving,
                'protein_per_serving': recipe.protein_per_serving,
                'carbs_per_serving': recipe.carbs_per_serving,
                'fat_per_serving': recipe.fat_per_serving,
                'dietary_tags': recipe.dietary_tags,
                'allergens': recipe.allergens,
                'average_rating': float(recipe.average_rating) if recipe.average_rating else 0,
                'rating_count': recipe.rating_count,
                'image_url': recipe.image_url,
                'created_at': recipe.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'data': {
                'recipes': recipes,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error retrieving recipes: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recipe_detail_view(request, recipe_id):
    """Get detailed recipe information"""
    
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        
        # Get user's rating if it exists
        user_rating = None
        try:
            rating = UserRecipeRating.objects.get(user=request.user, recipe=recipe)
            user_rating = {
                'rating': rating.rating,
                'comment': rating.comment,
                'created_at': rating.created_at.isoformat()
            }
        except UserRecipeRating.DoesNotExist:
            pass
        
        # Get ingredient substitutions
        substitutions = IngredientSubstitution.objects.filter(
            original_ingredient__in=[ing.get('name', '') for ing in recipe.ingredients]
        )
        
        substitution_map = {}
        for sub in substitutions:
            if sub.original_ingredient not in substitution_map:
                substitution_map[sub.original_ingredient] = []
            substitution_map[sub.original_ingredient].append({
                'substitute': sub.substitute_ingredient,
                'ratio': float(sub.substitution_ratio),
                'notes': sub.notes
            })
        
        return Response({
            'success': True,
            'data': {
                'id': recipe.id,
                'title': recipe.title,
                'description': recipe.description,
                'cuisine': recipe.cuisine,
                'difficulty': recipe.difficulty,
                'prep_time': recipe.prep_time_minutes,
                'cook_time': recipe.cook_time_minutes,
                'total_time': recipe.prep_time_minutes + recipe.cook_time_minutes,
                'servings': recipe.servings,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions,
                'nutrition': {
                    'calories_per_serving': recipe.calories_per_serving,
                    'protein_per_serving': recipe.protein_per_serving,
                    'carbs_per_serving': recipe.carbs_per_serving,
                    'fat_per_serving': recipe.fat_per_serving,
                    'fiber_per_serving': recipe.fiber_per_serving
                },
                'dietary_tags': recipe.dietary_tags,
                'allergens': recipe.allergens,
                'average_rating': float(recipe.average_rating) if recipe.average_rating else 0,
                'rating_count': recipe.rating_count,
                'user_rating': user_rating,
                'substitutions': substitution_map,
                'image_url': recipe.image_url,
                'source_url': recipe.source_url,
                'source_type': recipe.source_type,
                'created_at': recipe.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error retrieving recipe: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_recipe_view(request, recipe_id):
    """Rate a recipe"""
    
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = request.data
        
        rating_value = data.get('rating')
        comment = data.get('comment', '')
        
        if not rating_value or not (1 <= rating_value <= 5):
            return Response({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create rating
        rating, created = UserRecipeRating.objects.update_or_create(
            user=request.user,
            recipe=recipe,
            defaults={
                'rating': rating_value,
                'comment': comment
            }
        )
        
        # Update recipe's average rating
        avg_rating = UserRecipeRating.objects.filter(recipe=recipe).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating']
        
        recipe.average_rating = avg_rating or 0
        recipe.rating_count = UserRecipeRating.objects.filter(recipe=recipe).count()
        recipe.save()
        
        return Response({
            'success': True,
            'message': 'Recipe rated successfully',
            'data': {
                'user_rating': rating_value,
                'user_comment': comment,
                'recipe_average_rating': float(recipe.average_rating),
                'recipe_rating_count': recipe.rating_count,
                'created': created
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error rating recipe: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutrition_log_view(request):
    """Get user's nutrition log with date filtering"""
    
    try:
        # Query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', 30)), 100)
        
        # Build queryset
        queryset = NutritionLog.objects.filter(user=request.user).order_by('-date')
        
        if start_date:
            try:
                start_date_obj = datetime.fromisoformat(start_date).date()
                queryset = queryset.filter(date__gte=start_date_obj)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid start_date format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date).date()
                queryset = queryset.filter(date__lte=end_date_obj)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid end_date format'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        nutrition_logs = []
        for log in page_obj:
            nutrition_logs.append({
                'id': log.id,
                'date': log.date.isoformat(),
                'total_calories': log.total_calories,
                'total_protein': log.total_protein,
                'total_carbs': log.total_carbs,
                'total_fat': log.total_fat,
                'total_fiber': log.total_fiber,
                'meals_data': log.meals_data,
                'notes': log.notes,
                'created_at': log.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'data': {
                'nutrition_logs': nutrition_logs,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error retrieving nutrition log: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Frontend Template Views (if needed)

@login_required
def meal_plan_view(request, plan_id):
    """View a specific meal plan (template view)"""
    try:
        meal_plan = get_object_or_404(MealPlan, id=plan_id, user=request.user)
        
        context = {
            'meal_plan': meal_plan,
            'meal_plan_json': json.dumps(meal_plan.meal_plan_data),
            'shopping_list_json': json.dumps(meal_plan.shopping_list_data) if meal_plan.shopping_list_data else 'null'
        }
        
        return render(request, 'meal_planning/meal_plan_detail.html', context)
        
    except Exception as e:
        return render(request, 'meal_planning/error.html', {
            'error': f'Error loading meal plan: {str(e)}'
        })


@login_required
def recipe_detail_view(request, recipe_id):
    """View a specific recipe (template view)"""
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        
        # Get user rating if exists
        user_rating = None
        try:
            rating = UserRecipeRating.objects.get(user=request.user, recipe=recipe)
            user_rating = rating
        except UserRecipeRating.DoesNotExist:
            pass
        
        context = {
            'recipe': recipe,
            'user_rating': user_rating,
            'ingredients_json': json.dumps(recipe.ingredients),
            'instructions_json': json.dumps(recipe.instructions)
        }
        
        return render(request, 'meal_planning/recipe_detail.html', context)
        
    except Exception as e:
        return render(request, 'meal_planning/error.html', {
            'error': f'Error loading recipe: {str(e)}'
        })


# Utility endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_supported_options_view(request):
    """Get supported dietary preferences, allergies, cuisines, etc."""
    
    return Response({
        'success': True,
        'data': {
            'dietary_preferences': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in NutritionProfile.DIETARY_PREFERENCES
            ],
            'allergies_intolerances': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in NutritionProfile.ALLERGIES_INTOLERANCES
            ],
            'cuisine_preferences': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in NutritionProfile.CUISINE_PREFERENCES
            ],
            'food_categories': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Ingredient.FOOD_CATEGORIES
            ],
            'recipe_difficulties': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in Recipe.DIFFICULTY_CHOICES
            ],
            'plan_types': [
                {'value': 'daily', 'label': 'Daily Plan'},
                {'value': 'weekly', 'label': 'Weekly Plan'}
            ]
        }
    })
