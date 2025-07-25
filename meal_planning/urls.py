# meal_planning/urls.py
from django.urls import path, include
from . import views

app_name = 'meal_planning'

urlpatterns = [
    # Optimized API endpoints
    path('api/nutrition-profile/', views.NutritionProfileView.as_view(), name='nutrition-profile'),
    path('api/recipes/', views.recipe_list_optimized, name='recipes-list'),
    path('api/recipes/search/', views.search_recipes_optimized, name='recipes-search'),
    path('api/meal-plans/', views.user_meal_plans, name='meal-plans-list'),
    path('api/meal-plans/generate/', views.generate_meal_plan_optimized, name='meal-plans-generate'),
]