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

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='current')
    def current_profile(self, request):
        """Get or update current user's nutrition profile - This is the endpoint your frontend calls"""
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
        """Generate a new meal plan using the AI meal planning service"""
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

            # Apply filters from request data
            target_calories = plan_data.get('target_calories')
            cuisine_preferences = plan_data.get('cuisine_preferences', [])
            max_cook_time = plan_data.get('max_cook_time')
            
            # Update nutrition profile temporarily with form overrides
            if target_calories:
                # Create a copy of the profile with updated calories
                from copy import deepcopy
                temp_profile = deepcopy(nutrition_profile)
                temp_profile.calorie_target = target_calories
                nutrition_profile = temp_profile
            
            if cuisine_preferences:
                # Create a copy of the profile with updated cuisine preferences
                from copy import deepcopy
                if not hasattr(nutrition_profile, '__dict__'):
                    temp_profile = deepcopy(nutrition_profile)
                else:
                    temp_profile = nutrition_profile
                temp_profile.cuisine_preferences = cuisine_preferences
                nutrition_profile = temp_profile

            # Use the enhanced AI meal planning service
            ai_meal_service = AIEnhancedMealService()
            
            # Determine number of days based on plan type
            days = 1 if plan_type == 'daily' else 7
            
            # Generate the meal plan with custom filters
            generation_options = {}
            if max_cook_time:
                generation_options['max_cook_time'] = max_cook_time
                
            meal_plan_data = ai_meal_service.generate_smart_meal_plan(
                nutrition_profile, 
                days, 
                generation_options=generation_options
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
        serializer.save(user=self.request.user)

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
