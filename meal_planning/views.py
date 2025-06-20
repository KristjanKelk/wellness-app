# meal_planning/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    NutritionProfile, Recipe, Ingredient, MealPlan,
    NutritionLog, UserRecipeRating
)

# Simple serializers first (we'll move these to serializers.py later)
from rest_framework import serializers


class SimpleRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'summary', 'cuisine', 'meal_type', 'servings',
                  'total_time_minutes', 'calories_per_serving', 'protein_per_serving',
                  'carbs_per_serving', 'fat_per_serving', 'dietary_tags', 'source_type']


class SimpleIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'calories_per_100g', 'protein_per_100g',
                  'carbs_per_100g', 'fat_per_100g', 'category', 'dietary_tags']


class SimpleNutritionProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionProfile
        fields = ['dietary_preferences', 'allergies_intolerances', 'cuisine_preferences',
                  'calorie_target', 'protein_target', 'carb_target', 'fat_target',
                  'meals_per_day', 'timezone', 'created_at']


# Simple ViewSets
class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """Simple recipe API"""
    serializer_class = SimpleRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recipe.objects.all().order_by('-created_at')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Simple ingredient API"""
    serializer_class = SimpleIngredientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ingredient.objects.filter(is_verified=True).order_by('name')


class NutritionProfileViewSet(viewsets.ModelViewSet):
    """Simple nutrition profile API"""
    serializer_class = SimpleNutritionProfileSerializer
    permission_classes = [IsAuthenticated]  # Remove authentication for now

    def get_queryset(self):
        # Handle anonymous users
        if not self.request.user.is_authenticated:
            return NutritionProfile.objects.none()
        return NutritionProfile.objects.filter(user=self.request.user)

    def list(self, request):
        if not request.user.is_authenticated:
            return Response({"message": "Please log in to view nutrition profile"})

        # Try to get or create profile
        try:
            nutrition_profile, created = NutritionProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'calorie_target': 2000,
                    'protein_target': 100,
                    'carb_target': 250,
                    'fat_target': 67
                }
            )
            serializer = self.get_serializer(nutrition_profile)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


# Placeholder ViewSets (we'll implement these later)
class MealPlanViewSet(viewsets.ModelViewSet):
    """Placeholder for meal plans"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealPlan.objects.filter(user=self.request.user)

    def list(self, request):
        return Response({"message": "Meal plans coming soon!"})


class NutritionLogViewSet(viewsets.ModelViewSet):
    """Placeholder for nutrition logs"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NutritionLog.objects.filter(user=self.request.user)

    def list(self, request):
        return Response({"message": "Nutrition logs coming soon!"})
