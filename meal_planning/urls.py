from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'nutrition-profile', views.NutritionProfileViewSet, basename='nutrition-profile')
router.register(r'recipes', views.RecipeViewSet, basename='recipes')
router.register(r'ingredients', views.IngredientViewSet, basename='ingredients')
router.register(r'meal-plans', views.MealPlanViewSet, basename='meal-plans')
router.register(r'nutrition-logs', views.NutritionLogViewSet, basename='nutrition-logs')

app_name = 'meal_planning'

urlpatterns = [
    path('api/', include(router.urls)),
]