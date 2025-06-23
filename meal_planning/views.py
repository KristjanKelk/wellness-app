# meal_planning/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models
from .models import NutritionProfile, Recipe, Ingredient, MealPlan, UserRecipeRating, NutritionLog
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

    def _calculate_bmr(self, health_profile):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
        if health_profile.gender == 'male':
            bmr = 10 * health_profile.weight + 6.25 * health_profile.height - 5 * health_profile.age + 5
        else:
            bmr = 10 * health_profile.weight + 6.25 * health_profile.height - 5 * health_profile.age - 161
        return bmr

    def _adjust_for_activity(self, bmr, activity_level):
        """Adjust BMR for activity level"""
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extra_active': 1.9
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


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse and search recipes"""
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Recipe.objects.all()

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

        serializer = self.get_serializer(queryset[:20], many=True)
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
        """Generate a new meal plan using AI (mock implementation for now)"""
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

            # TODO: Implement AI meal plan generation
            # For now, return a mock response based on user's preferences
            mock_meal_plan = self._generate_mock_meal_plan(nutrition_profile)

            # Create meal plan with proper date formatting
            from datetime import datetime

            if isinstance(start_date, str):
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date_obj = start_date

            meal_plan = MealPlan.objects.create(
                user=request.user,
                plan_type=plan_type,
                start_date=start_date_obj,
                end_date=start_date_obj,  # For daily plans
                meal_plan_data=mock_meal_plan,
                total_calories=float(nutrition_profile.calorie_target),
                avg_daily_calories=float(nutrition_profile.calorie_target),
                total_protein=float(nutrition_profile.protein_target),
                total_carbs=float(nutrition_profile.carb_target),
                total_fat=float(nutrition_profile.fat_target),
                ai_model_used='mock_v1.0'
            )

            serializer = self.get_serializer(meal_plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error generating meal plan: {str(e)}")
            return Response(
                {'error': 'Failed to generate meal plan', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_mock_meal_plan(self, profile):
        """Generate a mock meal plan based on user preferences"""
        is_vegetarian = 'vegetarian' in profile.dietary_preferences
        is_vegan = 'vegan' in profile.dietary_preferences
        is_keto = 'keto' in profile.dietary_preferences

        if is_vegan:
            return {
                'breakfast': {
                    'name': 'Vegan Protein Smoothie Bowl',
                    'calories': int(profile.calorie_target * 0.25),
                    'protein': int(profile.protein_target * 0.25),
                    'carbs': int(profile.carb_target * 0.25),
                    'fat': int(profile.fat_target * 0.25)
                },
                'lunch': {
                    'name': 'Quinoa Buddha Bowl with Tahini',
                    'calories': int(profile.calorie_target * 0.35),
                    'protein': int(profile.protein_target * 0.35),
                    'carbs': int(profile.carb_target * 0.35),
                    'fat': int(profile.fat_target * 0.35)
                },
                'dinner': {
                    'name': 'Lentil Curry with Brown Rice',
                    'calories': int(profile.calorie_target * 0.40),
                    'protein': int(profile.protein_target * 0.40),
                    'carbs': int(profile.carb_target * 0.40),
                    'fat': int(profile.fat_target * 0.40)
                }
            }
        elif is_keto:
            return {
                'breakfast': {
                    'name': 'Keto Avocado and Eggs',
                    'calories': int(profile.calorie_target * 0.25),
                    'protein': int(profile.protein_target * 0.25),
                    'carbs': int(profile.carb_target * 0.25),
                    'fat': int(profile.fat_target * 0.25)
                },
                'lunch': {
                    'name': 'Keto Chicken Caesar Salad',
                    'calories': int(profile.calorie_target * 0.35),
                    'protein': int(profile.protein_target * 0.35),
                    'carbs': int(profile.carb_target * 0.35),
                    'fat': int(profile.fat_target * 0.35)
                },
                'dinner': {
                    'name': 'Keto Salmon with Asparagus',
                    'calories': int(profile.calorie_target * 0.40),
                    'protein': int(profile.protein_target * 0.40),
                    'carbs': int(profile.carb_target * 0.40),
                    'fat': int(profile.fat_target * 0.40)
                }
            }
        else:
            # Standard balanced meal plan
            return {
                'breakfast': {
                    'name': 'Protein Oatmeal with Berries',
                    'calories': int(profile.calorie_target * 0.25),
                    'protein': int(profile.protein_target * 0.25),
                    'carbs': int(profile.carb_target * 0.25),
                    'fat': int(profile.fat_target * 0.25)
                },
                'lunch': {
                    'name': 'Grilled Chicken Quinoa Bowl',
                    'calories': int(profile.calorie_target * 0.35),
                    'protein': int(profile.protein_target * 0.35),
                    'carbs': int(profile.carb_target * 0.35),
                    'fat': int(profile.fat_target * 0.35)
                },
                'dinner': {
                    'name': 'Salmon with Sweet Potato and Vegetables',
                    'calories': int(profile.calorie_target * 0.40),
                    'protein': int(profile.protein_target * 0.40),
                    'carbs': int(profile.carb_target * 0.40),
                    'fat': int(profile.fat_target * 0.40)
                }
            }

    @action(detail=True, methods=['post'])
    def regenerate_meal(self, request, pk=None):
        """Regenerate a specific meal in the plan"""
        meal_plan = self.get_object()
        day = request.data.get('day')
        meal_type = request.data.get('meal_type')

        if not day or not meal_type:
            return Response(
                {'error': 'day and meal_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Implement AI meal regeneration
        return Response({'message': 'Meal regenerated successfully'})

    @action(detail=True, methods=['post'])
    def generate_shopping_list(self, request, pk=None):
        """Generate shopping list from meal plan"""
        meal_plan = self.get_object()
        exclude_items = request.data.get('exclude_items', [])
        group_by_category = request.data.get('group_by_category', True)

        # TODO: Implement shopping list generation
        mock_shopping_list = {
            'produce': ['Spinach (200g)', 'Cherry tomatoes (300g)', 'Avocado (2 pieces)'],
            'proteins': ['Chicken breast (500g)', 'Salmon fillet (400g)', 'Eggs (12 pieces)'],
            'grains': ['Quinoa (1 cup)', 'Brown rice (500g)', 'Oats (500g)'],
            'pantry': ['Olive oil', 'Coconut oil', 'Almond butter'],
            'dairy': ['Greek yogurt (500g)', 'Almond milk (1L)']
        }

        # Update meal plan
        meal_plan.shopping_list_data = mock_shopping_list
        meal_plan.shopping_list_generated = True
        meal_plan.save()

        return Response({'shopping_list': mock_shopping_list})


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
        # TODO: Implement dashboard data aggregation
        return Response({'message': 'Dashboard data feature coming soon'})