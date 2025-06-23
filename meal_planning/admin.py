# meal_planning/admin.py
from django.contrib import admin
from .models import NutritionProfile, Recipe, Ingredient, MealPlan, UserRecipeRating, NutritionLog

# Simple admin registration without custom configurations
# We'll keep it basic to avoid field name conflicts

@admin.register(NutritionProfile)
class NutritionProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'calorie_target', 'created_at']
    search_fields = ['user__username']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'calories_per_100g']
    search_fields = ['name']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'cuisine', 'meal_type', 'servings']
    search_fields = ['title']

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_type', 'start_date', 'is_active']
    search_fields = ['user__username']

@admin.register(UserRecipeRating)
class UserRecipeRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'rating']
    search_fields = ['user__username']

@admin.register(NutritionLog)
class NutritionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_calories']
    search_fields = ['user__username']