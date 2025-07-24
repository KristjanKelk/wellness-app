"""
Meal Planning URLs
Complete API endpoints for advanced meal planning features
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'meal_planning'

# Main views
urlpatterns = [
    # Dashboard and template views
    path('', views.MealPlanningDashboardView.as_view(), name='dashboard'),
    path('meal-plan/<int:plan_id>/', views.meal_plan_view, name='meal_plan_detail'),
    path('recipe/<int:recipe_id>/', views.recipe_detail_view, name='recipe_detail'),
    
    # API endpoints for nutrition profile
    path('api/nutrition-profile/', views.nutrition_profile_view, name='nutrition_profile_api'),
    
    # API endpoints for meal planning
    path('api/meal-plans/generate/', views.generate_meal_plan_view, name='generate_meal_plan'),
    path('api/meal-plans/', views.get_meal_plans_view, name='get_meal_plans'),
    path('api/meal-plans/<int:plan_id>/', views.meal_plan_detail_view, name='meal_plan_detail_api'),
    path('api/meal-plans/<int:plan_id>/regenerate-meal/', views.regenerate_meal_view, name='regenerate_meal'),
    path('api/meal-plans/<int:plan_id>/swap-meals/', views.swap_meals_view, name='swap_meals'),
    path('api/meal-plans/<int:plan_id>/add-manual-meal/', views.add_manual_meal_view, name='add_manual_meal'),
    
    # API endpoints for shopping lists
    path('api/meal-plans/<int:plan_id>/shopping-list/', views.generate_shopping_list_view, name='generate_shopping_list'),
    path('api/meal-plans/<int:plan_id>/shopping-list/update/', views.update_shopping_list_view, name='update_shopping_list'),
    
    # API endpoints for recipes
    path('api/recipes/', views.get_recipes_view, name='get_recipes'),
    path('api/recipes/<int:recipe_id>/', views.get_recipe_detail_view, name='get_recipe_detail'),
    path('api/recipes/<int:recipe_id>/rate/', views.rate_recipe_view, name='rate_recipe'),
    
    # API endpoints for nutrition logging
    path('api/nutrition-log/', views.get_nutrition_log_view, name='get_nutrition_log'),
    
    # Utility endpoints
    path('api/supported-options/', views.get_supported_options_view, name='supported_options'),
]