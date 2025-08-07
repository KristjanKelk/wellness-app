# meal_planning/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models
from .models import NutritionProfile, Recipe, Ingredient, MealPlan, UserRecipeRating, NutritionLog
from .services.ai_enhanced_meal_service import AIEnhancedMealService
from .services.enhanced_spoonacular_service import EnhancedSpoonacularService, SpoonacularAPIError
from .services.ai_meal_planning_service import AIMealPlanningService
from .services.ai_nutrition_profile_service import AINutritionProfileService
from .services.shopping_list_service import ShoppingListService
from .serializers import (
    NutritionProfileSerializer, RecipeSerializer, IngredientSerializer,
    MealPlanSerializer, UserRecipeRatingSerializer, NutritionLogSerializer
)
import logging
from datetime import datetime, date, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class NutritionProfileViewSet(viewsets.ModelViewSet):
    """Manage user nutrition profiles"""
    serializer_class = NutritionProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NutritionProfile.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create nutrition profile for current user"""
        profile, created = NutritionProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'calorie_target': 2000,
                'protein_target': 100.0,
                'carb_target': 250.0,
                'fat_target': 67.0,
                'dietary_preferences': [],
                'allergies_intolerances': [],
                'cuisine_preferences': [],
                'disliked_ingredients': [],
                'meals_per_day': 3,
                'snacks_per_day': 1,
                'timezone': 'UTC'
            }
        )
        return profile

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='my_profile')
    def my_profile(self, request):
        """Get or update current user's nutrition profile - Updated endpoint name for frontend"""
        if request.method == 'GET':
            profile = self.get_object()
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            profile = self.get_object()

            # Debug: Log the incoming data
            print(f"Received data: {request.data}")
            print(f"Profile before update: {profile.__dict__}")

            # Try to update fields manually first to identify the issue
            try:
                # Update simple fields first
                simple_fields = ['calorie_target', 'protein_target', 'carb_target', 'fat_target',
                                 'meals_per_day', 'snacks_per_day', 'timezone']

                for field in simple_fields:
                    if field in request.data:
                        setattr(profile, field, request.data[field])
                        print(f"Updated {field}: {request.data[field]}")

                # Update array fields
                array_fields = ['dietary_preferences', 'allergies_intolerances', 'cuisine_preferences',
                                'disliked_ingredients']
                for field in array_fields:
                    if field in request.data:
                        # Ensure it's a list
                        value = request.data[field]
                        if not isinstance(value, list):
                            print(f"Converting {field} from {type(value)} to list: {value}")
                            value = list(value) if value else []
                        setattr(profile, field, value)
                        print(f"Updated {field}: {value}")

                # Update time fields
                time_fields = ['breakfast_time', 'lunch_time', 'dinner_time']
                for field in time_fields:
                    if field in request.data:
                        setattr(profile, field, request.data[field])
                        print(f"Updated {field}: {request.data[field]}")

                # Save the profile
                profile.save()
                print("✅ Profile saved successfully!")

                # Return the updated profile
                serializer = self.get_serializer(profile)
                return Response(serializer.data, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"❌ Manual update failed: {str(e)}")
                import traceback
                traceback.print_exc()

                # Fall back to serializer approach
                serializer = self.get_serializer(
                    profile,
                    data=request.data,
                    partial=(request.method == 'PATCH')
                )

                if serializer.is_valid():
                    try:
                        with transaction.atomic():
                            serializer.save()
                            logger.info(f"Nutrition profile updated for user {request.user.username}")
                            return Response(serializer.data, status=status.HTTP_200_OK)
                    except Exception as e:
                        logger.error(f"Error updating nutrition profile: {str(e)}")
                        return Response(
                            {'error': 'Failed to update profile', 'details': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                else:
                    # Debug: Log validation errors
                    print(f"Validation errors: {serializer.errors}")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='current')
    def current_profile(self, request):
        """Get or update current user's nutrition profile - This is the endpoint your frontend calls"""
        return self.my_profile(request)

    @action(detail=False, methods=['post'])
    def calculate_targets(self, request):
        """Auto-calculate nutrition targets based on user's health profile"""
        try:
            profile = self.get_object()

            # Get user's health profile if available
            health_profile = getattr(request.user, 'health_profile', None)

            if health_profile:
                # Calculate BMR and adjust for activity level
                bmr = self._calculate_bmr(health_profile)
                calorie_target = self._adjust_for_activity(bmr, health_profile.activity_level)

                # Get dietary preferences to adjust macros
                dietary_prefs = profile.dietary_preferences

                # Calculate macro distribution
                macros = self._calculate_macro_distribution(calorie_target, dietary_prefs)

                # Update profile
                profile.calorie_target = calorie_target
                profile.protein_target = macros['protein']
                profile.carb_target = macros['carbs']
                profile.fat_target = macros['fat']
                profile.save()

                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            else:
                # Fallback calculation without health profile
                dietary_prefs = profile.dietary_preferences
                base_calories = 2000
                macros = self._calculate_macro_distribution(base_calories, dietary_prefs)

                profile.calorie_target = base_calories
                profile.protein_target = macros['protein']
                profile.carb_target = macros['carbs']
                profile.fat_target = macros['fat']
                profile.save()

                serializer = self.get_serializer(profile)
                return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error calculating targets: {str(e)}")
            return Response(
                {'error': 'Failed to calculate targets', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def generate_ai_profile(self, request):
        """Generate AI-powered nutrition profile based on health profile and goals"""
        try:
            ai_service = AINutritionProfileService()
            force_regenerate = request.data.get('force_regenerate', False)
            
            result = ai_service.generate_ai_nutrition_profile(
                user=request.user,
                force_regenerate=force_regenerate
            )
            
            if result['status'] == 'success':
                return Response({
                    'message': result['message'],
                    'profile': result['profile'],
                    'ai_insights': result['ai_insights'],
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            elif result['status'] == 'existing':
                return Response({
                    'message': result['message'],
                    'profile': result['profile'],
                    'status': 'existing'
                }, status=status.HTTP_200_OK)
            elif result['status'] == 'fallback':
                return Response({
                    'message': result['message'],
                    'profile': result['profile'],
                    'status': 'fallback'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result['message'],
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error generating AI nutrition profile: {str(e)}")
            return Response(
                {'error': 'Failed to generate AI nutrition profile', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def ai_generate(self, request):
        """Generate AI-powered nutrition profile based on custom input data"""
        try:
            from .services.ai_nutrition_profile_service import AINutritionProfileService
            
            # Extract user data from request
            user_data = request.data.get('user_data', {})
            goals = request.data.get('goals', {})
            preferences = request.data.get('preferences', {})
            
            # Validate required fields
            required_fields = ['age', 'gender', 'height', 'weight']
            for field in required_fields:
                if field not in user_data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            ai_service = AINutritionProfileService()
            
            # Generate profile using custom data
            result = ai_service.generate_custom_nutrition_profile(
                user=request.user,
                user_data=user_data,
                goals=goals,
                preferences=preferences
            )
            
            if result['status'] == 'success':
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error generating custom AI nutrition profile: {str(e)}")
            return Response(
                {'error': 'Failed to generate AI nutrition profile', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def update_with_progress(self, request):
        """Update nutrition profile based on user progress and feedback"""
        try:
            profile = self.get_object()
            ai_service = AINutritionProfileService()
            
            progress_data = {
                'user_feedback': request.data.get('feedback', ''),
                'goal_achievement': request.data.get('goal_achievement', {}),
                'challenges': request.data.get('challenges', []),
                'weight_change': request.data.get('weight_change'),
                'energy_levels': request.data.get('energy_levels'),
                'satisfaction': request.data.get('satisfaction')
            }
            
            result = ai_service.update_profile_based_on_progress(profile, progress_data)
            
            if result['status'] == 'success':
                # Refresh profile data
                profile.refresh_from_db()
                serializer = self.get_serializer(profile)
                return Response({
                    'message': result['message'],
                    'profile': serializer.data,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result['message'],
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating profile with progress: {str(e)}")
            return Response(
                {'error': 'Failed to update profile with progress', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def get_daily_insights(self, request):
        """Get AI insights about daily nutrition intake"""
        try:
            profile = self.get_object()
            ai_service = AINutritionProfileService()
            
            daily_intake = {
                'calories': request.data.get('calories', 0),
                'protein': request.data.get('protein', 0),
                'carbs': request.data.get('carbs', 0),
                'fat': request.data.get('fat', 0),
                'meals': request.data.get('meals', []),
                'date': request.data.get('date')
            }
            
            insights = ai_service.get_nutrition_insights(profile, daily_intake)
            
            return Response({
                'insights': insights['insights'],
                'recommendations': insights.get('recommendations', []),
                'status': 'success'
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting daily insights: {str(e)}")
            return Response(
                {'error': 'Failed to get daily insights', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def ai_recommendations(self, request):
        """Get AI recommendations from stored profile data"""
        try:
            profile = self.get_object()
            
            ai_recommendations = profile.advanced_preferences.get('ai_recommendations', {})
            
            if not ai_recommendations:
                return Response({
                    'message': 'No AI recommendations found. Generate an AI profile first.',
                    'has_recommendations': False
                }, status=status.HTTP_200_OK)
            
            return Response({
                'recommendations': ai_recommendations,
                'foods_to_emphasize': profile.advanced_preferences.get('foods_to_emphasize', []),
                'foods_to_limit': profile.advanced_preferences.get('foods_to_limit', []),
                'nutrition_strategy': profile.advanced_preferences.get('nutrition_strategy', ''),
                'hydration_target': profile.advanced_preferences.get('hydration_target'),
                'supplement_recommendations': profile.advanced_preferences.get('supplement_recommendations', []),
                'progress_monitoring': profile.advanced_preferences.get('progress_monitoring', {}),
                'has_recommendations': True,
                'generated_at': ai_recommendations.get('generated_at'),
                'ai_confidence': ai_recommendations.get('ai_confidence', 0)
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {str(e)}")
            return Response(
                {'error': 'Failed to get AI recommendations', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def goal_based_preferences(self, request):
        """Get goal-based dietary preferences and recommendations"""
        try:
            profile = self.get_object()
            goal_preferences = profile.get_goal_based_preferences()
            
            # Get user's fitness goal from health profile
            health_profile = getattr(request.user, 'health_profile', None)
            fitness_goal = health_profile.fitness_goal if health_profile else 'general_fitness'
            
            return Response({
                'fitness_goal': fitness_goal,
                'goal_preferences': goal_preferences,
                'emphasized_foods': goal_preferences.get('emphasized_foods', []),
                'limited_foods': goal_preferences.get('limited_foods', []),
                'meal_timing': goal_preferences.get('meal_timing', 'flexible'),
                'portion_control': goal_preferences.get('portion_control', 'moderate')
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting goal-based preferences: {str(e)}")
            return Response(
                {'error': 'Failed to get goal-based preferences', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_bmr(self, health_profile):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
        weight = float(health_profile.weight_kg or 0)
        height = float(health_profile.height_cm or 0)
        age = health_profile.age or 0

        if health_profile.gender == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        return bmr

    def _adjust_for_activity(self, bmr, activity_level):
        """Adjust BMR for activity level"""
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        multiplier = activity_multipliers.get(activity_level, 1.375)
        return int(bmr * multiplier)

    def _calculate_macro_distribution(self, calories, dietary_prefs):
        """Calculate macro distribution based on dietary preferences"""
        # Default balanced diet
        protein_ratio = 0.25
        carb_ratio = 0.45
        fat_ratio = 0.30

        # Adjust based on dietary preferences
        if 'keto' in dietary_prefs:
            protein_ratio = 0.25
            carb_ratio = 0.05
            fat_ratio = 0.70
        elif 'low_carb' in dietary_prefs:
            protein_ratio = 0.30
            carb_ratio = 0.20
            fat_ratio = 0.50
        elif 'high_protein' in dietary_prefs:
            protein_ratio = 0.35
            carb_ratio = 0.35
            fat_ratio = 0.30
        elif 'low_fat' in dietary_prefs:
            protein_ratio = 0.25
            carb_ratio = 0.60
            fat_ratio = 0.15
        elif 'mediterranean' in dietary_prefs:
            protein_ratio = 0.20
            carb_ratio = 0.50
            fat_ratio = 0.30

        return {
            'protein': round((calories * protein_ratio) / 4, 1),
            'carbs': round((calories * carb_ratio) / 4, 1),
            'fat': round((calories * fat_ratio) / 9, 1)
        }

    @action(detail=False, methods=['post'])
    def connect_spoonacular(self, request):
        """Connect user to Spoonacular for personalized meal planning"""
        try:
            profile = self.get_object()
            user = request.user
            
            # Check if user is already connected
            if profile.spoonacular_username and profile.spoonacular_user_hash:
                return Response({
                    'message': 'User already connected to Spoonacular',
                    'spoonacular_username': profile.spoonacular_username,
                    'connected': True
                })

            # Connect to Spoonacular
            spoonacular_service = SpoonacularService()
            
            connection_data = spoonacular_service.connect_user(
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email
            )
            
            # Save Spoonacular credentials to profile
            profile.spoonacular_username = connection_data.get('username')
            profile.spoonacular_user_hash = connection_data.get('hash')
            profile.save()
            
            logger.info(f"Successfully connected user {user.username} to Spoonacular")
            
            return Response({
                'message': 'Successfully connected to Spoonacular',
                'spoonacular_username': profile.spoonacular_username,
                'connected': True,
                'spoonacular_password': connection_data.get('spoonacularPassword')  # For user reference
            })
            
        except SpoonacularAPIError as e:
            logger.error(f"Spoonacular connection failed for user {request.user.username}: {str(e)}")
            return Response(
                {'error': 'Failed to connect to Spoonacular', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error connecting to Spoonacular: {str(e)}")
            
            # Check if it's a Redis connection issue
            if "connection_pool_kwargs" in str(e) or "AbstractConnection" in str(e):
                return Response(
                    {'error': 'Service temporarily unavailable', 'details': 'Cache service unavailable, please try again'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            return Response(
                {'error': 'Unexpected error occurred', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def spoonacular_status(self, request):
        """Check if user is connected to Spoonacular"""
        try:
            profile = self.get_object()
            connected = bool(profile.spoonacular_username and profile.spoonacular_user_hash)
            
            return Response({
                'connected': connected,
                'spoonacular_username': profile.spoonacular_username if connected else None
            })
            
        except Exception as e:
            logger.error(f"Error checking Spoonacular status: {str(e)}")
            return Response(
                {'error': 'Failed to check connection status'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def spoonacular_meal_plan(self, request):
        """Get user's Spoonacular meal plan with AI analysis"""
        try:
            profile = self.get_object()
            
            # Get start date from query params
            start_date = request.query_params.get('start_date')
            
            # Use enhanced service that combines Spoonacular + AI
            ai_meal_service = AIEnhancedMealService()
            meal_plan = ai_meal_service.get_spoonacular_meal_plan(
                nutrition_profile=profile,
                start_date=start_date
            )
            
            return Response(meal_plan)
            
        except SpoonacularAPIError as e:
            logger.error(f"Failed to get Spoonacular meal plan: {str(e)}")
            return Response(
                {'error': 'Failed to get meal plan', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error getting meal plan: {str(e)}")
            return Response(
                {'error': 'Unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def add_to_spoonacular_meal_plan(self, request):
        """Add item to user's Spoonacular meal plan"""
        try:
            profile = self.get_object()
            
            if not profile.spoonacular_username or not profile.spoonacular_user_hash:
                return Response(
                    {'error': 'User not connected to Spoonacular'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = request.data
            required_fields = ['date', 'slot', 'position', 'type', 'value']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            spoonacular_service = SpoonacularService()
            result = spoonacular_service.add_to_meal_plan(
                spoonacular_username=profile.spoonacular_username,
                user_hash=profile.spoonacular_user_hash,
                date=data['date'],
                slot=data['slot'],
                position=data['position'],
                item_type=data['type'],
                value=data['value']
            )
            
            return Response(result)
            
        except SpoonacularAPIError as e:
            logger.error(f"Failed to add to Spoonacular meal plan: {str(e)}")
            return Response(
                {'error': 'Failed to add to meal plan', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error adding to meal plan: {str(e)}")
            return Response(
                {'error': 'Unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def spoonacular_shopping_list(self, request):
        """Get user's Spoonacular shopping list"""
        try:
            profile = self.get_object()
            
            # Use enhanced service
            ai_meal_service = AIEnhancedMealService()
            shopping_list = ai_meal_service.get_spoonacular_shopping_list(profile)
            
            return Response(shopping_list)
            
        except SpoonacularAPIError as e:
            logger.error(f"Failed to get Spoonacular shopping list: {str(e)}")
            return Response(
                {'error': 'Failed to get shopping list', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error getting shopping list: {str(e)}")
            return Response(
                {'error': 'Unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def generate_smart_meal_plan(self, request):
        """Generate an AI-enhanced meal plan using Spoonacular"""
        try:
            profile = self.get_object()
            days = request.data.get('days', 7)
            
            # Validate days parameter
            if not isinstance(days, int) or days < 1 or days > 14:
                return Response(
                    {'error': 'Days must be an integer between 1 and 14'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate meal plan with AI enhancements
            ai_meal_service = AIEnhancedMealService()
            meal_plan = ai_meal_service.generate_smart_meal_plan(profile, days)
            
            return Response(meal_plan)
            
        except SpoonacularAPIError as e:
            logger.error(f"Failed to generate smart meal plan: {str(e)}")
            return Response(
                {'error': 'Failed to generate meal plan', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error generating smart meal plan: {str(e)}")
            return Response(
                {'error': 'Unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def analyze_meal_plan(self, request):
        """Analyze any meal plan with AI"""
        try:
            profile = self.get_object()
            meal_plan_data = request.data.get('meal_plan_data')
            
            if not meal_plan_data:
                return Response(
                    {'error': 'meal_plan_data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Analyze with AI
            ai_meal_service = AIEnhancedMealService()
            analysis = ai_meal_service.analyze_meal_plan_with_ai(meal_plan_data, profile)
            
            return Response(analysis)
            
        except Exception as e:
            logger.error(f"Failed to analyze meal plan: {str(e)}")
            return Response(
                {'error': 'Analysis failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def connect_spoonacular(self, request):
        """Connect user to Spoonacular for personalized meal planning"""
        try:
            profile = self.get_object()
            
            # Use enhanced service to connect
            ai_meal_service = AIEnhancedMealService()
            connection = ai_meal_service.spoonacular_service.connect_user(
                username=f"user_{profile.user.id}",
                first_name=profile.user.first_name,
                last_name=profile.user.last_name,
                email=profile.user.email
            )
            
            # Save connection details
            profile.spoonacular_username = connection.get('username')
            profile.spoonacular_user_hash = connection.get('hash')
            profile.save()
            
            return Response({
                'message': 'Successfully connected to Spoonacular',
                'connected': True,
                'spoonacular_username': profile.spoonacular_username
            })
            
        except SpoonacularAPIError as e:
            logger.error(f"Failed to connect to Spoonacular: {str(e)}")
            return Response(
                {'error': 'Failed to connect to Spoonacular', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error connecting to Spoonacular: {str(e)}")
            return Response(
                {'error': 'Unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecipeViewSet(viewsets.ModelViewSet):
    """Browse and search recipes with save/remove functionality"""
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Check if we should filter by user's saved recipes
        my_recipes_only = self.request.query_params.get('my_recipes', 'false').lower() == 'true'
        
        if my_recipes_only:
            # Show only recipes saved/created by the current user
            queryset = Recipe.objects.filter(created_by=self.request.user)
        else:
            # Show all public recipes
            queryset = Recipe.objects.filter(is_public=True)

        # Filter by dietary preferences
        dietary_prefs = self.request.query_params.getlist('dietary_preferences')
        if dietary_prefs:
            for pref in dietary_prefs:
                queryset = queryset.filter(dietary_tags__contains=[pref])

        # Filter by cuisine
        cuisine = self.request.query_params.get('cuisine')
        if cuisine:
            queryset = queryset.filter(cuisine=cuisine)

        # Filter by meal type
        meal_type = self.request.query_params.get('meal_type')
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)

        # Filter by max calories
        max_calories = self.request.query_params.get('max_calories')
        if max_calories:
            queryset = queryset.filter(calories_per_serving__lte=max_calories)

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset.order_by('-rating_avg', '-created_at')

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced recipe search with nutritional filters"""
        data = request.data
        queryset = Recipe.objects.all()

        # Apply filters from search data
        if data.get('dietary_preferences'):
            for pref in data['dietary_preferences']:
                queryset = queryset.filter(dietary_tags__contains=[pref])

        if data.get('allergies_to_avoid'):
            # Filter out recipes containing allergens
            for allergen in data['allergies_to_avoid']:
                queryset = queryset.exclude(allergens__contains=[allergen])

        if data.get('max_prep_time'):
            queryset = queryset.filter(prep_time_minutes__lte=data['max_prep_time'])

        if data.get('cuisine_preferences'):
            queryset = queryset.filter(cuisine__in=data['cuisine_preferences'])

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a recipe"""
        recipe = self.get_object()
        rating_value = request.data.get('rating')
        review_text = request.data.get('review', '')

        if not rating_value or not (1 <= rating_value <= 5):
            return Response(
                {'error': 'Rating must be between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update rating
        rating, created = UserRecipeRating.objects.update_or_create(
            user=request.user,
            recipe=recipe,
            defaults={'rating': rating_value, 'review': review_text}
        )

        # Update recipe's average rating
        recipe.view_count += 1
        ratings = recipe.ratings.all()
        if ratings.exists():
            recipe.rating_avg = ratings.aggregate(models.Avg('rating'))['rating__avg']
            recipe.rating_count = ratings.count()
        recipe.save()

        serializer = UserRecipeRatingSerializer(rating)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def save_to_my_recipes(self, request, pk=None):
        """Save a recipe to user's collection"""
        try:
            source_recipe = self.get_object()
            
            # Check if user already has this recipe saved
            existing_recipe = Recipe.objects.filter(
                created_by=request.user,
                spoonacular_id=source_recipe.spoonacular_id
            ).first()
            
            if existing_recipe:
                return Response(
                    {'message': 'Recipe already in your collection', 'recipe_id': str(existing_recipe.id)},
                    status=status.HTTP_200_OK
                )
            
            # Create a copy of the recipe for the user
            saved_recipe = Recipe.objects.create(
                title=source_recipe.title,
                summary=source_recipe.summary,
                cuisine=source_recipe.cuisine,
                meal_type=source_recipe.meal_type,
                servings=source_recipe.servings,
                prep_time_minutes=source_recipe.prep_time_minutes,
                cook_time_minutes=source_recipe.cook_time_minutes,
                total_time_minutes=source_recipe.total_time_minutes,
                difficulty_level=source_recipe.difficulty_level,
                spoonacular_id=source_recipe.spoonacular_id,
                ingredients_data=source_recipe.ingredients_data,
                instructions=source_recipe.instructions,
                calories_per_serving=source_recipe.calories_per_serving,
                protein_per_serving=source_recipe.protein_per_serving,
                carbs_per_serving=source_recipe.carbs_per_serving,
                fat_per_serving=source_recipe.fat_per_serving,
                fiber_per_serving=source_recipe.fiber_per_serving,
                dietary_tags=source_recipe.dietary_tags,
                allergens=source_recipe.allergens,
                image_url=source_recipe.image_url,
                source_url=source_recipe.source_url,
                source_type=source_recipe.source_type,
                enhanced_data=source_recipe.enhanced_data,
                is_public=False,  # User's saved recipes are private by default
                created_by=request.user
            )
            
            serializer = self.get_serializer(saved_recipe)
            return Response({
                'message': 'Recipe saved to your collection!',
                'recipe': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error saving recipe: {str(e)}")
            return Response(
                {'error': 'Failed to save recipe'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def save_from_meal_plan(self, request):
        """Save a recipe from meal plan data to user's collection"""
        try:
            recipe_data = request.data
            logger.info(f"Attempting to save recipe from meal plan: {recipe_data.get('title', 'Unknown')}")
            
            # Check if this is a fallback recipe that cannot be saved
            recipe_id = recipe_data.get('spoonacular_id') or recipe_data.get('id')
            if recipe_id and str(recipe_id).startswith('fallback_'):
                logger.warning(f"Cannot save fallback recipe: {recipe_id}")
                return Response(
                    {'error': 'Cannot save fallback recipe', 'message': 'This is a temporary recipe that cannot be saved to your collection.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already has this recipe saved by spoonacular_id
            spoonacular_id = recipe_data.get('spoonacular_id') or recipe_data.get('id')
            
            # Only check for existing recipes if we have a valid spoonacular_id (not fallback)
            if spoonacular_id and not str(spoonacular_id).startswith('fallback_'):
                try:
                    # Convert to int if it's a valid spoonacular ID
                    spoonacular_id_int = int(spoonacular_id)
                    existing_recipe = Recipe.objects.filter(
                        created_by=request.user,
                        spoonacular_id=spoonacular_id_int
                    ).first()
                    
                    if existing_recipe:
                        return Response(
                            {'message': 'Recipe already in your collection', 'recipe_id': str(existing_recipe.id)},
                            status=status.HTTP_200_OK
                        )
                except (ValueError, TypeError):
                    # If spoonacular_id is not a valid integer, treat as None
                    spoonacular_id_int = None
            else:
                spoonacular_id_int = None
            
            # Validate and normalize required fields with proper defaults
            def safe_int(value, default=0):
                try:
                    return int(value) if value is not None else default
                except (ValueError, TypeError):
                    return default
                    
            def safe_float(value, default=0.0):
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default
            
            # Extract and normalize the data with proper validation
            saved_recipe = Recipe.objects.create(
                title=recipe_data.get('title', 'Untitled Recipe'),
                summary=recipe_data.get('summary', ''),
                cuisine=recipe_data.get('cuisine', ''),
                meal_type=recipe_data.get('meal_type', 'dinner'),
                servings=safe_int(recipe_data.get('servings'), 4),
                prep_time_minutes=safe_int(recipe_data.get('prep_time_minutes'), 30),  # Default 30 min prep
                cook_time_minutes=safe_int(recipe_data.get('cook_time_minutes'), 0),
                total_time_minutes=safe_int(recipe_data.get('total_time_minutes'), 30),  # Default 30 min total
                difficulty_level=recipe_data.get('difficulty_level', 'medium'),
                spoonacular_id=spoonacular_id_int,  # Use the validated integer ID or None
                ingredients_data=recipe_data.get('ingredients_data', []),
                instructions=recipe_data.get('instructions', []),
                calories_per_serving=safe_float(recipe_data.get('calories_per_serving'), 300),  # Default 300 calories
                protein_per_serving=safe_float(recipe_data.get('protein_per_serving'), 15),    # Default 15g protein
                carbs_per_serving=safe_float(recipe_data.get('carbs_per_serving'), 30),       # Default 30g carbs
                fat_per_serving=safe_float(recipe_data.get('fat_per_serving'), 10),          # Default 10g fat
                fiber_per_serving=safe_float(recipe_data.get('fiber_per_serving'), 0),
                dietary_tags=recipe_data.get('dietary_tags', []),
                allergens=recipe_data.get('allergens', []),
                image_url=recipe_data.get('image_url', ''),
                source_url=recipe_data.get('source_url', ''),
                source_type='spoonacular',
                is_public=False,  # User's saved recipes are private by default
                created_by=request.user
            )
            
            logger.info(f"Successfully saved recipe: {saved_recipe.title} (ID: {saved_recipe.id})")
            
            serializer = self.get_serializer(saved_recipe)
            return Response({
                'message': 'Recipe saved to your collection!',
                'recipe': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error saving recipe from meal plan: {str(e)}")
            logger.error(f"Recipe data: {recipe_data}")
            return Response(
                {'error': 'Failed to save recipe', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Remove a recipe from user's collection - only allow deletion of user's own recipes"""
        recipe = self.get_object()
        
        if recipe.created_by != request.user:
            return Response(
                {'error': 'You can only delete your own saved recipes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        recipe.delete()
        return Response(
            {'message': 'Recipe removed from your collection'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'])
    def adjust_portions(self, request, pk=None):
        """Get recipe with adjusted portions for ingredients and nutrition"""
        try:
            recipe = self.get_object()
            servings = request.data.get('servings', recipe.servings)
            
            if servings <= 0:
                return Response(
                    {'error': 'Servings must be a positive number'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate multiplier
            multiplier = servings / recipe.servings
            
            # Adjust nutrition values
            adjusted_nutrition = {
                'calories_per_serving': recipe.calories_per_serving,
                'protein_per_serving': recipe.protein_per_serving,
                'carbs_per_serving': recipe.carbs_per_serving,
                'fat_per_serving': recipe.fat_per_serving,
                'fiber_per_serving': recipe.fiber_per_serving,
                'total_calories': recipe.calories_per_serving * servings,
                'total_protein': recipe.protein_per_serving * servings,
                'total_carbs': recipe.carbs_per_serving * servings,
                'total_fat': recipe.fat_per_serving * servings,
                'total_fiber': recipe.fiber_per_serving * servings,
            }
            
            # Adjust ingredients
            adjusted_ingredients = []
            for ingredient in recipe.ingredients_data:
                adjusted_ingredient = self._adjust_ingredient_quantity(ingredient, multiplier)
                adjusted_ingredients.append(adjusted_ingredient)
            
            return Response({
                'recipe_id': recipe.id,
                'original_servings': recipe.servings,
                'adjusted_servings': servings,
                'multiplier': multiplier,
                'nutrition': adjusted_nutrition,
                'ingredients': adjusted_ingredients
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error adjusting recipe portions: {str(e)}")
            return Response(
                {'error': 'Failed to adjust recipe portions', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _adjust_ingredient_quantity(self, ingredient, multiplier):
        """Helper method to adjust ingredient quantities"""
        import re
        
        if isinstance(ingredient, str):
            return self._adjust_string_ingredient(ingredient, multiplier)
        
        # Handle dictionary ingredient format
        adjusted = ingredient.copy()
        
        # Adjust the 'original' field if it exists
        if 'original' in adjusted:
            adjusted['original'] = self._adjust_string_ingredient(adjusted['original'], multiplier)
        
        # Adjust numeric quantity fields
        for field in ['amount', 'quantity']:
            if field in adjusted and adjusted[field]:
                try:
                    value = float(adjusted[field])
                    adjusted[field] = self._round_quantity(value * multiplier)
                except (ValueError, TypeError):
                    pass
        
        return adjusted
    
    def _adjust_string_ingredient(self, ingredient_str, multiplier):
        """Adjust quantities in string ingredient descriptions"""
        import re
        
        if not ingredient_str or multiplier == 1:
            return ingredient_str
        
        # Patterns to match quantities
        patterns = [
            r'^(\d+(?:\.\d+)?(?:/\d+)?(?:\s+\d+/\d+)?)',  # Numbers and fractions
            r'^(\d+-\d+)',  # Ranges like 2-3
        ]
        
        for pattern in patterns:
            match = re.match(pattern, ingredient_str.strip())
            if match:
                original_quantity = match.group(1)
                try:
                    if '/' in original_quantity:
                        # Handle fractions
                        adjusted_quantity = self._adjust_fraction(original_quantity, multiplier)
                    elif '-' in original_quantity:
                        # Handle ranges
                        parts = original_quantity.split('-')
                        min_val = float(parts[0]) * multiplier
                        max_val = float(parts[1]) * multiplier
                        adjusted_quantity = f"{self._round_quantity(min_val)}-{self._round_quantity(max_val)}"
                    else:
                        # Handle regular numbers
                        value = float(original_quantity) * multiplier
                        adjusted_quantity = str(self._round_quantity(value))
                    
                    return ingredient_str.replace(original_quantity, adjusted_quantity, 1)
                except (ValueError, TypeError):
                    pass
        
        return ingredient_str
    
    def _adjust_fraction(self, fraction_str, multiplier):
        """Convert fraction to decimal, multiply, and convert back to readable format"""
        parts = fraction_str.strip().split()
        decimal_value = 0
        
        for part in parts:
            if '/' in part:
                numerator, denominator = part.split('/')
                decimal_value += int(numerator) / int(denominator)
            else:
                decimal_value += int(part)
        
        adjusted_value = decimal_value * multiplier
        return self._decimal_to_readable(adjusted_value)
    
    def _decimal_to_readable(self, decimal_value):
        """Convert decimal to readable fraction or mixed number"""
        # If close to a whole number, return whole number
        if abs(decimal_value - round(decimal_value)) < 0.1:
            return str(round(decimal_value))
        
        # Common fractions
        fractions = [
            (0.125, '1/8'), (0.25, '1/4'), (0.333, '1/3'), (0.375, '3/8'),
            (0.5, '1/2'), (0.625, '5/8'), (0.667, '2/3'), (0.75, '3/4'), (0.875, '7/8')
        ]
        
        whole_part = int(decimal_value)
        fractional_part = decimal_value - whole_part
        
        # Find closest fraction
        for frac_decimal, frac_str in fractions:
            if abs(fractional_part - frac_decimal) < 0.1:
                if whole_part > 0:
                    return f"{whole_part} {frac_str}"
                else:
                    return frac_str
        
        # If no close fraction found, use decimal
        if whole_part > 0:
            return f"{decimal_value:.1f}"
        else:
            return f"{decimal_value:.2f}"
    
    def _round_quantity(self, quantity):
        """Round quantity to appropriate precision"""
        if quantity < 0.1:
            return round(quantity, 2)
        elif quantity < 1:
            return round(quantity, 1)
        elif quantity < 10:
            return round(quantity * 4) / 4  # Round to nearest quarter
        else:
            return round(quantity)

    @action(detail=True, methods=['post'])
    def generate_shopping_list(self, request, pk=None):
        """Generate shopping list for a single recipe"""
        try:
            recipe = self.get_object()
            servings_multiplier = request.data.get('servings_multiplier', 1.0)
            
            shopping_service = ShoppingListService()
            shopping_list = shopping_service.generate_shopping_list_from_recipes(
                recipe_ids=[str(recipe.id)],
                servings_multiplier={str(recipe.id): servings_multiplier}
            )
            
            return Response({
                'shopping_list': shopping_list,
                'recipe_name': recipe.title,
                'servings_multiplier': servings_multiplier
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating shopping list for recipe: {str(e)}")
            return Response(
                {'error': 'Failed to generate shopping list', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def generate_shopping_list_multiple(self, request):
        """Generate shopping list for multiple recipes"""
        try:
            recipe_ids = request.data.get('recipe_ids', [])
            servings_multipliers = request.data.get('servings_multipliers', {})
            
            if not recipe_ids:
                return Response(
                    {'error': 'recipe_ids is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            shopping_service = ShoppingListService()
            shopping_list = shopping_service.generate_shopping_list_from_recipes(
                recipe_ids=recipe_ids,
                servings_multiplier=servings_multipliers
            )
            
            return Response({
                'shopping_list': shopping_list,
                'recipe_count': len(recipe_ids)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating shopping list for multiple recipes: {str(e)}")
            return Response(
                {'error': 'Failed to generate shopping list', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse ingredients and their nutritional information"""
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Ingredient.objects.all()

        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by('name')


class MealPlanViewSet(viewsets.ModelViewSet):
    """Manage meal plans"""
    serializer_class = MealPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealPlan.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new meal plan using the enhanced dynamic AI meal planning service"""
        try:
            # Get user's nutrition profile
            nutrition_profile = get_object_or_404(NutritionProfile, user=request.user)

            # Get generation parameters
            plan_data = request.data
            plan_type = plan_data.get('plan_type', 'daily')
            start_date = plan_data.get('start_date')

            if not start_date:
                return Response(
                    {'error': 'start_date is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            from datetime import datetime

            if isinstance(start_date, str):
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date_obj = start_date

            # Get custom options from request
            custom_options = {}
            
            # Apply filters from request data
            target_calories = plan_data.get('target_calories')
            cuisine_preferences = plan_data.get('cuisine_preferences', [])
            max_cook_time = plan_data.get('max_cook_time')
            dietary_preferences_override = plan_data.get('dietary_preferences', [])
            
            if target_calories:
                custom_options['target_calories'] = target_calories
            if cuisine_preferences:
                custom_options['cuisine_preferences'] = cuisine_preferences
            if max_cook_time:
                custom_options['max_cook_time'] = max_cook_time
            if dietary_preferences_override:
                custom_options['dietary_preferences_override'] = dietary_preferences_override
            
            # Use enhanced dynamic meal planning service
            from .services.dynamic_meal_planning_service import DynamicMealPlanningService
            from .services.enhanced_nutrition_profile_service import EnhancedNutritionProfileService
            
            dynamic_service = DynamicMealPlanningService()
            profile_service = EnhancedNutritionProfileService()
            
            # Determine number of days based on plan type
            days = 1 if plan_type == 'daily' else 7
            
            # Create enhanced nutrition profile with overrides if provided
            enhanced_profile = nutrition_profile
            if custom_options:
                # Create temporary profile with custom options
                from copy import deepcopy
                enhanced_profile = deepcopy(nutrition_profile)
                
                if target_calories:
                    enhanced_profile.calorie_target = int(target_calories)
                if cuisine_preferences:
                    enhanced_profile.cuisine_preferences = cuisine_preferences
                if dietary_preferences_override:
                    enhanced_profile.dietary_preferences = dietary_preferences_override
            
            # Generate comprehensive meal plan using dynamic planning
            meal_plan_data = dynamic_service.generate_personalized_meal_plan(
                enhanced_profile, 
                days, 
                custom_options
            )
            
            # Create a MealPlan object
            end_date = start_date_obj
            if plan_type == 'weekly':
                from datetime import timedelta
                end_date = start_date_obj + timedelta(days=6)
            
            meal_plan = MealPlan.objects.create(
                user=request.user,
                plan_type=plan_type,
                start_date=start_date_obj,
                end_date=end_date,
                meal_plan_data=meal_plan_data,
                total_calories=meal_plan_data.get('nutrition', {}).get('calories', 0),
                avg_daily_calories=meal_plan_data.get('nutrition', {}).get('calories', 0),
                total_protein=meal_plan_data.get('nutrition', {}).get('protein', 0),
                total_carbs=meal_plan_data.get('nutrition', {}).get('carbs', 0),
                total_fat=meal_plan_data.get('nutrition', {}).get('fat', 0),
                nutritional_balance_score=meal_plan_data.get('scores', {}).get('balance_score', 5.0),
                variety_score=meal_plan_data.get('scores', {}).get('variety_score', 5.0),
                preference_match_score=meal_plan_data.get('scores', {}).get('preference_match_score', 5.0)
            )

            serializer = self.get_serializer(meal_plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error generating meal plan: {str(e)}")
            return Response(
                {'error': 'Failed to generate meal plan', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def nutrition_analysis(self, request):
        """Get enhanced nutrition analysis for the user's profile"""
        try:
            # Get user's nutrition profile
            nutrition_profile = get_object_or_404(NutritionProfile, user=request.user)
            
            # Use enhanced nutrition profile service
            from .services.enhanced_nutrition_profile_service import EnhancedNutritionProfileService
            
            profile_service = EnhancedNutritionProfileService()
            
            # Get comprehensive analysis
            analysis = profile_service.analyze_and_optimize_profile(nutrition_profile)
            
            return Response(analysis, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting nutrition analysis: {str(e)}")
            return Response(
                {'error': 'Failed to get nutrition analysis', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def optimize_nutrition(self, request):
        """Get optimized nutrition targets based on custom parameters"""
        try:
            # Get user's nutrition profile
            nutrition_profile = get_object_or_404(NutritionProfile, user=request.user)
            
            # Get parameters from request
            fitness_goal = request.data.get('fitness_goal')
            activity_level = request.data.get('activity_level')
            custom_factors = request.data.get('custom_factors', {})
            
            # Use enhanced nutrition profile service
            from .services.enhanced_nutrition_profile_service import EnhancedNutritionProfileService
            
            profile_service = EnhancedNutritionProfileService()
            
            # Get dynamic macro distribution
            macro_analysis = profile_service.get_dynamic_macro_distribution(
                nutrition_profile, fitness_goal, activity_level
            )
            
            # Get adjusted calorie needs
            calorie_analysis = profile_service.calculate_adjusted_calorie_needs(
                nutrition_profile, custom_factors
            )
            
            # Generate nutrition strategy
            strategy = profile_service.generate_nutrition_strategy(nutrition_profile)
            
            response_data = {
                'macro_analysis': macro_analysis,
                'calorie_analysis': calorie_analysis,
                'nutrition_strategy': strategy,
                'generated_at': datetime.now().isoformat()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error optimizing nutrition: {str(e)}")
            return Response(
                {'error': 'Failed to optimize nutrition', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_mock_meal_plan(self, profile, start_date=None, plan_type='daily'):
        """Generate a simple meal plan using available recipes.

        This selects recipes from the local database that match the user's
        preferences. If no suitable recipe exists for a meal type, the function
        fetches one from Spoonacular and stores it for future use.
        """
        from datetime import date as date_cls
        from django.utils import timezone
        from .services.spoonacular_service import search_recipes_by_dietary_preferences

        if start_date is None:
            start_date = timezone.now().date()
        if isinstance(start_date, str):
            start_date = date_cls.fromisoformat(start_date)

        date_str = start_date.isoformat()

        meal_recipes = {}
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            recipes = Recipe.objects.filter(meal_type=meal_type)

            for pref in profile.dietary_preferences:
                recipes = recipes.filter(dietary_tags__contains=[pref])
            for allergen in profile.allergies_intolerances:
                recipes = recipes.exclude(allergens__contains=[allergen])
            if profile.cuisine_preferences:
                recipes = recipes.filter(cuisine__in=profile.cuisine_preferences)

            recipe = recipes.order_by('?').first()

            if not recipe:
                prefs = {
                    'dietary_preferences': profile.dietary_preferences,
                    'allergies_intolerances': profile.allergies_intolerances,
                    'cuisine_preferences': profile.cuisine_preferences,
                }
                results = search_recipes_by_dietary_preferences(prefs)
                if results:
                    data = results[0]
                    if data.get('spoonacular_id'):
                        recipe = (Recipe.objects
                                  .filter(spoonacular_id=data['spoonacular_id'])
                                  .first())
                    else:
                        recipe = None

                    if not recipe:
                        recipe = Recipe.objects.create(
                            title=data['title'],
                            summary=data.get('summary', ''),
                            cuisine=data.get('cuisine', ''),
                            meal_type=data.get('meal_type', meal_type),
                            servings=data.get('servings', 1),
                            prep_time_minutes=data.get('prep_time_minutes', 0),
                            cook_time_minutes=data.get('cook_time_minutes', 0),
                            total_time_minutes=data.get('total_time_minutes', 0),
                            difficulty_level=data.get('difficulty_level', 'medium'),
                            spoonacular_id=data.get('spoonacular_id'),
                            ingredients_data=data.get('ingredients_data', []),
                            instructions=data.get('instructions', []),
                            calories_per_serving=data.get('calories_per_serving', 0),
                            protein_per_serving=data.get('protein_per_serving', 0),
                            carbs_per_serving=data.get('carbs_per_serving', 0),
                            fat_per_serving=data.get('fat_per_serving', 0),
                            fiber_per_serving=data.get('fiber_per_serving', 0),
                            dietary_tags=data.get('dietary_tags', []),
                            allergens=data.get('allergens', []),
                            image_url=data.get('image_url', ''),
                            source_url=data.get('source_url', ''),
                            source_type=data.get('source_type', 'spoonacular'),
                        )

            if recipe:
                meal_recipes[meal_type] = {
                    'name': recipe.title,
                    'calories': int(recipe.calories_per_serving),
                    'protein': int(recipe.protein_per_serving),
                    'carbs': int(recipe.carbs_per_serving),
                    'fat': int(recipe.fat_per_serving),
                }

        daily_meals = [
            {
                'meal_type': 'breakfast',
                'time': '08:00',
                'recipe': meal_recipes.get('breakfast', {}),
            },
            {
                'meal_type': 'lunch',
                'time': '12:30',
                'recipe': meal_recipes.get('lunch', {}),
            },
            {
                'meal_type': 'dinner',
                'time': '19:00',
                'recipe': meal_recipes.get('dinner', {}),
            },
        ]

        return {
            'plan_type': plan_type,
            'meals': {
                date_str: daily_meals,
            },
        }

    @action(detail=True, methods=['post'])
    def regenerate_meal(self, request, pk=None):
        """Regenerate a specific meal in the plan"""
        try:
            meal_plan = self.get_object()
            day = request.data.get('day')
            meal_type = request.data.get('meal_type')

            if not day or not meal_type:
                return Response(
                    {'error': 'day and meal_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Use AI service to regenerate the meal
            ai_service = AIMealPlanningService()
            updated_meal_plan = ai_service.regenerate_meal(meal_plan, day, meal_type)

            serializer = self.get_serializer(updated_meal_plan)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error regenerating meal: {str(e)}")
            return Response(
                {'error': 'Failed to regenerate meal', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def analyze(self, request, pk=None):
        """Analyze meal plan nutrition (mock implementation)"""
        meal_plan = self.get_object()

        # Return mock analysis data for now
        mock_analysis = {
            'overall_score': 85,
            'nutritional_adequacy': {
                'calories': {'status': 'adequate', 'percentage_of_target': 98},
                'protein': {'status': 'adequate', 'percentage_of_target': 105},
                'carbs': {'status': 'adequate', 'percentage_of_target': 92},
                'fat': {'status': 'adequate', 'percentage_of_target': 103}
            },
            'meal_distribution': {
                'breakfast_percentage': 25,
                'lunch_percentage': 35,
                'dinner_percentage': 40,
                'balance_rating': 'excellent'
            },
            'variety_analysis': {
                'cuisine_diversity': 'good',
                'ingredient_variety': 'excellent',
                'cooking_method_diversity': 'good'
            },
            'recommendations': [
                'Consider adding more fiber-rich vegetables',
                'Excellent protein distribution throughout the day'
            ],
            'health_highlights': [
                'Well-balanced macronutrients',
                'Good variety of nutrient-dense foods'
            ],
            'areas_for_improvement': [
                'Could increase omega-3 fatty acids'
            ]
        }

        return Response(mock_analysis)

    @action(detail=True, methods=['post'])
    def get_alternatives(self, request, pk=None):
        """Get meal alternatives for a specific meal including user's saved recipes"""
        try:
            meal_plan = self.get_object()
            day = request.data.get('day')
            meal_type = request.data.get('meal_type')
            count = request.data.get('count', 3)
            include_user_recipes = request.data.get('include_user_recipes', True)

            if not day or not meal_type:
                return Response(
                    {'error': 'day and meal_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Use AI service to get alternatives
            ai_service = AIMealPlanningService()
            alternatives = ai_service.generate_recipe_alternatives(
                meal_plan, day, meal_type, count, include_user_recipes=include_user_recipes
            )

            return Response({
                'alternatives': alternatives,
                'total_count': len(alternatives),
                'user_recipes_included': include_user_recipes
            })

        except Exception as e:
            logger.error(f"Error getting meal alternatives: {str(e)}")
            return Response(
                {'error': 'Failed to get alternatives', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def swap_meal(self, request, pk=None):
        """Swap a meal with a selected alternative recipe"""
        try:
            meal_plan = self.get_object()
            day = request.data.get('day')
            meal_type = request.data.get('meal_type')
            new_recipe = request.data.get('new_recipe')

            if not day or not meal_type or not new_recipe:
                return Response(
                    {'error': 'day, meal_type, and new_recipe are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Swapping meal for plan {meal_plan.id}, day: {day}, meal_type: {meal_type}")

            # Get the meal plan data
            meal_plan_data = meal_plan.meal_plan_data or {}
            
            # For daily plans, the day might be the meal type
            if meal_plan.plan_type == 'daily' and day in ['breakfast', 'lunch', 'dinner']:
                target_day = 'day_1'
                target_meal_type = day
            else:
                target_day = day
                target_meal_type = meal_type

            # Initialize day data if it doesn't exist
            if target_day not in meal_plan_data:
                meal_plan_data[target_day] = {}

            # Update the meal with the new recipe
            meal_plan_data[target_day][target_meal_type] = {
                'recipe': {
                    'id': new_recipe.get('id'),
                    'title': new_recipe.get('title'),
                    'image': new_recipe.get('image'),
                    'servings': new_recipe.get('servings', 1),
                    'readyInMinutes': new_recipe.get('readyInMinutes', 30),
                    'summary': new_recipe.get('summary', ''),
                    'nutrition': new_recipe.get('nutrition', {}),
                    'ingredients': new_recipe.get('ingredients', []),
                    'instructions': new_recipe.get('instructions', ''),
                    'spoonacular_id': new_recipe.get('id'),
                    'database_id': new_recipe.get('database_id'),
                    'is_user_recipe': new_recipe.get('is_user_recipe', False),
                    'source': new_recipe.get('source', 'external')
                },
                'meal_type': target_meal_type
            }

            # Save the updated meal plan
            meal_plan.meal_plan_data = meal_plan_data
            meal_plan.save()

            logger.info(f"Successfully swapped meal for {target_meal_type} on {target_day}")

            # Return the updated meal plan
            serializer = self.get_serializer(meal_plan)
            return Response({
                'message': 'Meal swapped successfully',
                'meal_plan': serializer.data
            })

        except Exception as e:
            logger.error(f"Error swapping meal: {str(e)}")
            return Response(
                {'error': 'Failed to swap meal', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def generate_shopping_list(self, request, pk=None):
        """Generate shopping list from meal plan"""
        try:
            meal_plan = self.get_object()
            exclude_items = request.data.get('exclude_items', [])
            group_by_category = request.data.get('group_by_category', True)
            
            shopping_service = ShoppingListService()
            shopping_list = shopping_service.generate_shopping_list_from_meal_plan(str(meal_plan.id))
            
            # Filter out excluded items if provided
            if exclude_items:
                for category_key, category_data in shopping_list['categories'].items():
                    category_data['items'] = [
                        item for item in category_data['items'] 
                        if item['name'].lower() not in [excluded.lower() for excluded in exclude_items]
                    ]
                    category_data['item_count'] = len(category_data['items'])
            
            # Save shopping list to meal plan
            shopping_service.save_shopping_list_to_meal_plan(str(meal_plan.id), shopping_list)
            
            return Response({
                'shopping_list': shopping_list,
                'meal_plan_id': str(meal_plan.id),
                'excluded_items': exclude_items
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating shopping list for meal plan: {str(e)}")
            return Response(
                {'error': 'Failed to generate shopping list', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def get_shopping_list(self, request, pk=None):
        """Get existing shopping list for meal plan"""
        try:
            meal_plan = self.get_object()
            
            if not meal_plan.shopping_list_generated or not meal_plan.shopping_list_data:
                return Response(
                    {'message': 'No shopping list generated for this meal plan', 'has_shopping_list': False},
                    status=status.HTTP_200_OK
                )
            
            return Response({
                'shopping_list': meal_plan.shopping_list_data,
                'has_shopping_list': True,
                'generated_at': meal_plan.updated_at.isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting shopping list: {str(e)}")
            return Response(
                {'error': 'Failed to get shopping list', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        """Get today's active meal plan in a simple structured format"""
        from assistant.services import AssistantDAL, DataNotFound
        try:
            data = AssistantDAL.get_meal_plan_for_date(request.user)
            return Response(data)
        except DataNotFound as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class UserRecipeRatingViewSet(viewsets.ModelViewSet):
    """Manage user recipe ratings"""
    serializer_class = UserRecipeRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserRecipeRating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NutritionLogViewSet(viewsets.ModelViewSet):
    """Manage daily nutrition logs"""
    serializer_class = NutritionLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NutritionLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        log_data = serializer.validated_data.copy()
        
        # Calculate deficit/surplus if we have nutrition profile
        try:
            nutrition_profile = NutritionProfile.objects.get(user=user)
            if nutrition_profile.calorie_target:
                total_calories = log_data.get('total_calories', 0)
                deficit_surplus = total_calories - nutrition_profile.calorie_target
                log_data['calorie_deficit_surplus'] = deficit_surplus
        except NutritionProfile.DoesNotExist:
            pass
        
        serializer.save(user=user, **log_data)

    @action(detail=False, methods=['get'], url_path='(?P<date>[^/.]+)')
    def get_by_date(self, request, date=None):
        """Get nutrition log for a specific date"""
        try:
            # Parse date string
            if isinstance(date, str):
                log_date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                log_date = date
            
            try:
                log = self.get_queryset().get(date=log_date)
                serializer = self.get_serializer(log)
                return Response(serializer.data)
            except NutritionLog.DoesNotExist:
                # Return empty log structure if no data exists for this date
                return Response({
                    'date': log_date.strftime('%Y-%m-%d'),
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fat': 0,
                    'total_fiber': 0,
                    'calorie_deficit_surplus': 0,
                    'macro_balance_score': 0,
                    'meals_data': {},
                    'ai_analysis': {}
                }, status=status.HTTP_200_OK)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting nutrition log by date: {str(e)}")
            return Response(
                {'error': 'Failed to get nutrition log', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post', 'put'], url_path='(?P<date>[^/.]+)')
    def save_by_date(self, request, date=None):
        """Create or update nutrition log for a specific date"""
        try:
            # Parse date string
            if isinstance(date, str):
                log_date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                log_date = date
            
            # Get or create nutrition log for this date
            log, created = NutritionLog.objects.get_or_create(
                user=request.user,
                date=log_date,
                defaults=request.data
            )
            
            if not created:
                # Update existing log
                for field, value in request.data.items():
                    if hasattr(log, field):
                        setattr(log, field, value)
                
                # Calculate deficit/surplus
                try:
                    nutrition_profile = NutritionProfile.objects.get(user=request.user)
                    if nutrition_profile.calorie_target:
                        total_calories = request.data.get('total_calories', log.total_calories)
                        log.calorie_deficit_surplus = total_calories - nutrition_profile.calorie_target
                except NutritionProfile.DoesNotExist:
                    pass
                
                log.save()
            
            serializer = self.get_serializer(log)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error saving nutrition log by date: {str(e)}")
            return Response(
                {'error': 'Failed to save nutrition log', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'], url_path='(?P<date>[^/.]+)')
    def delete_by_date(self, request, date=None):
        """Delete nutrition log for a specific date"""
        try:
            # Parse date string
            if isinstance(date, str):
                log_date = datetime.strptime(date, '%Y-%m-%d').date()
            else:
                log_date = date
            
            try:
                log = self.get_queryset().get(date=log_date)
                log.delete()
                return Response({'message': 'Nutrition log deleted successfully'}, status=status.HTTP_200_OK)
            except NutritionLog.DoesNotExist:
                return Response(
                    {'error': 'No nutrition log found for this date'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error deleting nutrition log by date: {str(e)}")
            return Response(
                {'error': 'Failed to delete nutrition log', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """Get nutrition logs for a date range"""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                return Response(
                    {'error': 'start_date and end_date are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            logs = self.get_queryset().filter(
                date__gte=start_date_obj,
                date__lte=end_date_obj
            ).order_by('date')
            
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting nutrition logs by date range: {str(e)}")
            return Response(
                {'error': 'Failed to get nutrition logs', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def progress_summary(self, request):
        """Get nutrition progress summary for a date range"""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                return Response(
                    {'error': 'start_date and end_date are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            logs = self.get_queryset().filter(
                date__gte=start_date_obj,
                date__lte=end_date_obj
            )
            
            # Get user's nutrition profile for targets
            try:
                nutrition_profile = NutritionProfile.objects.get(user=request.user)
            except NutritionProfile.DoesNotExist:
                return Response(
                    {'error': 'No nutrition profile found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate summary statistics
            if logs.exists():
                totals = logs.aggregate(
                    avg_calories=models.Avg('total_calories'),
                    avg_protein=models.Avg('total_protein'),
                    avg_carbs=models.Avg('total_carbs'),
                    avg_fat=models.Avg('total_fat'),
                    total_deficit=models.Sum('calorie_deficit_surplus')
                )
                
                # Calculate goal achievement stats
                calorie_target = nutrition_profile.calorie_target
                days_on_target = logs.filter(
                    total_calories__gte=calorie_target * 0.9,
                    total_calories__lte=calorie_target * 1.1
                ).count()
                
                total_days = logs.count()
                consistency_score = (days_on_target / total_days * 100) if total_days > 0 else 0
                
                summary = {
                    'averages': {
                        'calories': round(totals['avg_calories'] or 0, 1),
                        'protein': round(totals['avg_protein'] or 0, 1),
                        'carbs': round(totals['avg_carbs'] or 0, 1),
                        'fat': round(totals['avg_fat'] or 0, 1),
                        'total_deficit': round(totals['total_deficit'] or 0, 1)
                    },
                    'targets': {
                        'calories': nutrition_profile.calorie_target,
                        'protein': nutrition_profile.protein_target,
                        'carbs': nutrition_profile.carb_target,
                        'fat': nutrition_profile.fat_target
                    },
                    'stats': {
                        'total_days': total_days,
                        'days_on_target': days_on_target,
                        'consistency_score': round(consistency_score, 1)
                    },
                    'date_range': {
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            else:
                summary = {
                    'averages': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'total_deficit': 0},
                    'targets': {
                        'calories': nutrition_profile.calorie_target,
                        'protein': nutrition_profile.protein_target,
                        'carbs': nutrition_profile.carb_target,
                        'fat': nutrition_profile.fat_target
                    },
                    'stats': {'total_days': 0, 'days_on_target': 0, 'consistency_score': 0},
                    'date_range': {'start_date': start_date, 'end_date': end_date}
                }
            
            return Response(summary)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting progress summary: {str(e)}")
            return Response(
                {'error': 'Failed to get progress summary', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def weekly_averages(self, request):
        """Get weekly nutrition averages"""
        try:
            week_start = request.query_params.get('week_start')
            
            if not week_start:
                return Response(
                    {'error': 'week_start is required (YYYY-MM-DD format)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse week start date
            week_start_obj = datetime.strptime(week_start, '%Y-%m-%d').date()
            week_end_obj = week_start_obj + timedelta(days=6)
            
            logs = self.get_queryset().filter(
                date__gte=week_start_obj,
                date__lte=week_end_obj
            )
            
            if logs.exists():
                averages = logs.aggregate(
                    avg_calories=models.Avg('total_calories'),
                    avg_protein=models.Avg('total_protein'),
                    avg_carbs=models.Avg('total_carbs'),
                    avg_fat=models.Avg('total_fat'),
                    total_deficit=models.Sum('calorie_deficit_surplus')
                )
                
                result = {
                    'week_start': week_start,
                    'week_end': week_end_obj.strftime('%Y-%m-%d'),
                    'averages': {
                        'calories': round(averages['avg_calories'] or 0, 1),
                        'protein': round(averages['avg_protein'] or 0, 1),
                        'carbs': round(averages['avg_carbs'] or 0, 1),
                        'fat': round(averages['avg_fat'] or 0, 1),
                        'total_deficit': round(averages['total_deficit'] or 0, 1)
                    },
                    'days_logged': logs.count()
                }
            else:
                result = {
                    'week_start': week_start,
                    'week_end': week_end_obj.strftime('%Y-%m-%d'),
                    'averages': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'total_deficit': 0},
                    'days_logged': 0
                }
            
            return Response(result)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting weekly averages: {str(e)}")
            return Response(
                {'error': 'Failed to get weekly averages', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def goal_stats(self, request):
        """Get nutrition goal achievement statistics"""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not start_date or not end_date:
                return Response(
                    {'error': 'start_date and end_date are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            logs = self.get_queryset().filter(
                date__gte=start_date_obj,
                date__lte=end_date_obj
            )
            
            # Get user's nutrition profile for targets
            try:
                nutrition_profile = NutritionProfile.objects.get(user=request.user)
            except NutritionProfile.DoesNotExist:
                return Response(
                    {'error': 'No nutrition profile found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if logs.exists():
                total_days = logs.count()
                calorie_target = nutrition_profile.calorie_target
                protein_target = nutrition_profile.protein_target
                carb_target = nutrition_profile.carb_target
                fat_target = nutrition_profile.fat_target
                
                # Calculate achievement rates for each macro
                calorie_achievements = logs.filter(
                    total_calories__gte=calorie_target * 0.9,
                    total_calories__lte=calorie_target * 1.1
                ).count()
                
                protein_achievements = logs.filter(
                    total_protein__gte=protein_target * 0.8
                ).count()
                
                carb_achievements = logs.filter(
                    total_carbs__gte=carb_target * 0.8,
                    total_carbs__lte=carb_target * 1.2
                ).count()
                
                fat_achievements = logs.filter(
                    total_fat__gte=fat_target * 0.8,
                    total_fat__lte=fat_target * 1.2
                ).count()
                
                stats = {
                    'total_days': total_days,
                    'achievements': {
                        'calories': {
                            'days_achieved': calorie_achievements,
                            'percentage': round(calorie_achievements / total_days * 100, 1)
                        },
                        'protein': {
                            'days_achieved': protein_achievements,
                            'percentage': round(protein_achievements / total_days * 100, 1)
                        },
                        'carbs': {
                            'days_achieved': carb_achievements,
                            'percentage': round(carb_achievements / total_days * 100, 1)
                        },
                        'fat': {
                            'days_achieved': fat_achievements,
                            'percentage': round(fat_achievements / total_days * 100, 1)
                        }
                    },
                    'overall_consistency': round((calorie_achievements + protein_achievements + carb_achievements + fat_achievements) / (4 * total_days) * 100, 1),
                    'date_range': {
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            else:
                stats = {
                    'total_days': 0,
                    'achievements': {
                        'calories': {'days_achieved': 0, 'percentage': 0},
                        'protein': {'days_achieved': 0, 'percentage': 0},
                        'carbs': {'days_achieved': 0, 'percentage': 0},
                        'fat': {'days_achieved': 0, 'percentage': 0}
                    },
                    'overall_consistency': 0,
                    'date_range': {'start_date': start_date, 'end_date': end_date}
                }
            
            return Response(stats)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting goal stats: {str(e)}")
            return Response(
                {'error': 'Failed to get goal stats', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get nutrition trends analysis"""
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            metric = request.query_params.get('metric', 'calories')
            
            if not start_date or not end_date:
                return Response(
                    {'error': 'start_date and end_date are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if metric not in ['calories', 'protein', 'carbs', 'fat']:
                return Response(
                    {'error': 'metric must be one of: calories, protein, carbs, fat'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            logs = self.get_queryset().filter(
                date__gte=start_date_obj,
                date__lte=end_date_obj
            ).order_by('date')
            
            if logs.exists():
                # Get field name for the metric
                field_map = {
                    'calories': 'total_calories',
                    'protein': 'total_protein', 
                    'carbs': 'total_carbs',
                    'fat': 'total_fat'
                }
                field_name = field_map[metric]
                
                # Extract daily values
                daily_values = []
                dates = []
                for log in logs:
                    daily_values.append(getattr(log, field_name, 0))
                    dates.append(log.date.strftime('%Y-%m-%d'))
                
                # Calculate trend statistics
                if len(daily_values) > 1:
                    # Simple linear trend calculation
                    x_values = list(range(len(daily_values)))
                    n = len(daily_values)
                    sum_x = sum(x_values)
                    sum_y = sum(daily_values)
                    sum_xy = sum(x * y for x, y in zip(x_values, daily_values))
                    sum_x2 = sum(x * x for x in x_values)
                    
                    # Linear regression slope
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
                    
                    # Calculate average and determine trend
                    average = sum_y / n
                    trend_direction = 'increasing' if slope > 0.1 else ('decreasing' if slope < -0.1 else 'stable')
                    
                    # Calculate recent vs previous period averages
                    mid_point = len(daily_values) // 2
                    recent_avg = sum(daily_values[mid_point:]) / len(daily_values[mid_point:]) if len(daily_values[mid_point:]) > 0 else 0
                    previous_avg = sum(daily_values[:mid_point]) / len(daily_values[:mid_point]) if len(daily_values[:mid_point]) > 0 else 0
                    
                    trend_data = {
                        'metric': metric,
                        'date_range': {'start_date': start_date, 'end_date': end_date},
                        'daily_data': {
                            'dates': dates,
                            'values': daily_values
                        },
                        'statistics': {
                            'average': round(average, 1),
                            'minimum': round(min(daily_values), 1),
                            'maximum': round(max(daily_values), 1),
                            'slope': round(slope, 3),
                            'trend_direction': trend_direction
                        },
                        'period_comparison': {
                            'recent_average': round(recent_avg, 1),
                            'previous_average': round(previous_avg, 1),
                            'change': round(recent_avg - previous_avg, 1),
                            'change_percentage': round((recent_avg - previous_avg) / previous_avg * 100, 1) if previous_avg > 0 else 0
                        },
                        'data_points': len(daily_values)
                    }
                else:
                    trend_data = {
                        'metric': metric,
                        'date_range': {'start_date': start_date, 'end_date': end_date},
                        'daily_data': {'dates': dates, 'values': daily_values},
                        'statistics': {
                            'average': daily_values[0] if daily_values else 0,
                            'minimum': daily_values[0] if daily_values else 0,
                            'maximum': daily_values[0] if daily_values else 0,
                            'slope': 0,
                            'trend_direction': 'insufficient_data'
                        },
                        'period_comparison': {
                            'recent_average': 0,
                            'previous_average': 0,
                            'change': 0,
                            'change_percentage': 0
                        },
                        'data_points': len(daily_values)
                    }
            else:
                trend_data = {
                    'metric': metric,
                    'date_range': {'start_date': start_date, 'end_date': end_date},
                    'daily_data': {'dates': [], 'values': []},
                    'statistics': {
                        'average': 0, 'minimum': 0, 'maximum': 0, 'slope': 0,
                        'trend_direction': 'no_data'
                    },
                    'period_comparison': {
                        'recent_average': 0, 'previous_average': 0, 'change': 0, 'change_percentage': 0
                    },
                    'data_points': 0
                }
            
            return Response(trend_data)
                
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error getting nutrition trends: {str(e)}")
            return Response(
                {'error': 'Failed to get nutrition trends', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Analyze nutrition data and provide insights"""
        # TODO: Implement nutrition analysis
        return Response({'message': 'Nutrition analysis feature coming soon'})

    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """Get nutrition dashboard data"""
        from django.utils import timezone
        from datetime import timedelta

        days = int(request.query_params.get('days', 7))
        today = timezone.now().date()
        start_date = today - timedelta(days=days - 1)

        logs = (self.get_queryset()
                .filter(date__gte=start_date, date__lte=today)
                .order_by('date'))

        data = {
            'labels': [],
            'calories': [],
            'protein': [],
            'carbs': [],
            'fat': [],
        }

        logs_by_date = {log.date: log for log in logs}
        for i in range(days):
            current = start_date + timedelta(days=i)
            log = logs_by_date.get(current)
            data['labels'].append(current.isoformat())
            if log:
                data['calories'].append(log.total_calories)
                data['protein'].append(log.total_protein)
                data['carbs'].append(log.total_carbs)
                data['fat'].append(log.total_fat)
            else:
                data['calories'].append(0)
                data['protein'].append(0)
                data['carbs'].append(0)
                data['fat'].append(0)

        data['totals'] = {
            'calories': sum(data['calories']),
            'protein': sum(data['protein']),
            'carbs': sum(data['carbs']),
            'fat': sum(data['fat']),
        }

        return Response(data)
