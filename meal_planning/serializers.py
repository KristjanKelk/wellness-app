# meal_planning/serializers.py
from rest_framework import serializers
from .models import NutritionProfile, Recipe, Ingredient, MealPlan, UserRecipeRating, NutritionLog


class NutritionProfileSerializer(serializers.ModelSerializer):
    """Serializer for nutrition profiles that matches your Django model"""

    # Add calculated fields
    macro_percentages = serializers.SerializerMethodField()
    ai_generated = serializers.SerializerMethodField()
    ai_insights = serializers.SerializerMethodField()
    goal_based_preferences = serializers.SerializerMethodField()
    fitness_goal = serializers.SerializerMethodField()
    nutrition_strategy = serializers.SerializerMethodField()

    class Meta:
        model = NutritionProfile
        fields = [
            'id', 'calorie_target', 'protein_target', 'carb_target', 'fat_target',
            'dietary_preferences', 'allergies_intolerances', 'cuisine_preferences',
            'disliked_ingredients', 'meals_per_day', 'snacks_per_day',
            'breakfast_time', 'lunch_time', 'dinner_time', 'timezone',
            'advanced_preferences', 'macro_percentages', 'ai_generated', 'ai_insights',
            'goal_based_preferences', 'fitness_goal', 'nutrition_strategy',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'macro_percentages', 'ai_generated',
            'ai_insights', 'goal_based_preferences', 'fitness_goal', 'nutrition_strategy'
        ]

    def get_macro_percentages(self, obj):
        """Calculate macronutrient percentages"""
        total_calories = (obj.protein_target * 4) + (obj.carb_target * 4) + (obj.fat_target * 9)
        if total_calories == 0:
            return {'protein': 0, 'carbs': 0, 'fat': 0}

        return {
            'protein': round((obj.protein_target * 4 / total_calories) * 100),
            'carbs': round((obj.carb_target * 4 / total_calories) * 100),
            'fat': round((obj.fat_target * 9 / total_calories) * 100)
        }

    def get_ai_generated(self, obj):
        """Check if profile was AI-generated"""
        return obj.advanced_preferences.get('ai_generated', False)

    def get_ai_insights(self, obj):
        """Get AI insights and recommendations"""
        ai_recommendations = obj.advanced_preferences.get('ai_recommendations', {})
        if not ai_recommendations:
            return None
        
        return {
            'foods_to_emphasize': obj.advanced_preferences.get('foods_to_emphasize', []),
            'foods_to_limit': obj.advanced_preferences.get('foods_to_limit', []),
            'hydration_target': obj.advanced_preferences.get('hydration_target'),
            'supplement_recommendations': obj.advanced_preferences.get('supplement_recommendations', []),
            'pre_workout_nutrition': obj.advanced_preferences.get('pre_workout_nutrition'),
            'post_workout_nutrition': obj.advanced_preferences.get('post_workout_nutrition'),
            'progress_monitoring': obj.advanced_preferences.get('progress_monitoring', {}),
            'ai_confidence': ai_recommendations.get('ai_confidence', 0),
            'generated_at': ai_recommendations.get('generated_at')
        }

    def get_goal_based_preferences(self, obj):
        """Get goal-based dietary preferences"""
        try:
            return obj.get_goal_based_preferences()
        except Exception:
            return {}

    def get_fitness_goal(self, obj):
        """Get user's fitness goal from health profile"""
        try:
            health_profile = getattr(obj.user, 'health_profile', None)
            if health_profile:
                return {
                    'goal': health_profile.fitness_goal,
                    'goal_display': health_profile.get_fitness_goal_display(),
                    'target_weight_kg': float(health_profile.target_weight_kg) if health_profile.target_weight_kg else None
                }
            return None
        except Exception:
            return None

    def get_nutrition_strategy(self, obj):
        """Get AI-generated nutrition strategy"""
        return obj.advanced_preferences.get('nutrition_strategy', '')

    def validate(self, data):
        """Validate nutrition profile data"""
        # Check if macro calories roughly match calorie target
        if all(key in data for key in ['calorie_target', 'protein_target', 'carb_target', 'fat_target']):
            macro_calories = (data['protein_target'] * 4) + (data['carb_target'] * 4) + (data['fat_target'] * 9)
            calorie_difference = abs(macro_calories - data['calorie_target'])

            if calorie_difference > 200:  # Allow 200 calorie difference
                print(f"Macro calorie validation failed: {macro_calories} vs {data['calorie_target']}")
                # Make this a warning instead of an error for now
                pass

        # Validate dietary preference conflicts (make this a warning too)
        dietary_prefs = data.get('dietary_preferences', [])
        conflicts = self._check_dietary_conflicts(dietary_prefs)
        if conflicts:
            print(f"Dietary conflicts detected: {conflicts}")
            # Just log conflicts for now, don't block saving
            pass

        return data

    def _check_dietary_conflicts(self, preferences):
        """Check for conflicting dietary preferences"""
        conflicts = []
        conflict_map = {
            'vegan': ['paleo', 'pescatarian', 'keto'],
            'vegetarian': ['paleo'],
            'pescatarian': ['vegan', 'vegetarian', 'paleo'],
            'keto': ['vegan', 'mediterranean'],
            'paleo': ['vegetarian', 'vegan', 'pescatarian', 'mediterranean'],
            'mediterranean': ['keto', 'paleo', 'low_carb'],
            'low_carb': ['mediterranean'],
            'low_fat': ['keto'],
            'flexitarian': ['vegan', 'vegetarian'],
            'whole30': ['vegetarian', 'vegan'],
        }

        for pref in preferences:
            conflicting_prefs = conflict_map.get(pref, [])
            for conflict in conflicting_prefs:
                if conflict in preferences:
                    conflicts.append(f"{pref} conflicts with {conflict}")

        return conflicts


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients that matches your Django model"""

    class Meta:
        model = Ingredient
        fields = [
            'id', 'name', 'name_clean', 'spoonacular_id', 'category',
            'calories_per_100g', 'protein_per_100g', 'carbs_per_100g',
            'fat_per_100g', 'fiber_per_100g', 'sugar_per_100g', 'sodium_per_100g',
            'micronutrients', 'dietary_tags', 'allergens', 'enhanced_data',
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'name_clean', 'created_at', 'updated_at']


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes that matches your Django model"""

    # Add calculated fields
    nutrition_per_serving = serializers.SerializerMethodField()
    dietary_tags_display = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    is_saved_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'summary', 'cuisine', 'meal_type', 'servings',
            'prep_time_minutes', 'cook_time_minutes', 'total_time_minutes',
            'difficulty_level', 'spoonacular_id', 'ingredients_data', 'instructions',
            'calories_per_serving', 'protein_per_serving', 'carbs_per_serving',
            'fat_per_serving', 'fiber_per_serving', 'nutrition_per_serving',
            'dietary_tags', 'dietary_tags_display', 'allergens', 'image_url',
            'source_url', 'source_type', 'view_count', 'rating_avg', 'rating_count',
            'user_rating', 'is_saved_by_user', 'is_verified', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_time_minutes', 'nutrition_per_serving', 'dietary_tags_display',
            'rating_avg', 'rating_count', 'user_rating', 'is_saved_by_user', 'view_count', 'created_at'
        ]

    def get_nutrition_per_serving(self, obj):
        """Get formatted nutrition information"""
        return {
            'calories': obj.calories_per_serving,
            'protein': obj.protein_per_serving,
            'carbs': obj.carbs_per_serving,
            'fat': obj.fat_per_serving,
            'fiber': obj.fiber_per_serving,
            'protein_percentage': round(
                (obj.protein_per_serving * 4 / obj.calories_per_serving) * 100) if obj.calories_per_serving else 0,
            'carbs_percentage': round(
                (obj.carbs_per_serving * 4 / obj.calories_per_serving) * 100) if obj.calories_per_serving else 0,
            'fat_percentage': round(
                (obj.fat_per_serving * 9 / obj.calories_per_serving) * 100) if obj.calories_per_serving else 0,
        }

    def get_dietary_tags_display(self, obj):
        """Get formatted dietary tags"""
        tag_map = {
            'vegetarian': 'Vegetarian',
            'vegan': 'Vegan',
            'gluten_free': 'Gluten Free',
            'dairy_free': 'Dairy Free',
            'keto': 'Keto',
            'paleo': 'Paleo',
            'low_carb': 'Low Carb',
            'high_protein': 'High Protein'
        }
        return [tag_map.get(tag, tag.title()) for tag in obj.dietary_tags]

    def get_user_rating(self, obj):
        """Get current user's rating for this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = obj.ratings.get(user=request.user)
                return {
                    'rating': rating.rating,
                    'review': rating.review,
                    'created_at': rating.created_at
                }
            except UserRecipeRating.DoesNotExist:
                return None
        return None

    def get_is_saved_by_user(self, obj):
        """Check if current user has saved this recipe"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if user has saved this recipe by spoonacular_id or by the recipe itself
            if obj.spoonacular_id:
                return Recipe.objects.filter(
                    created_by=request.user,
                    spoonacular_id=obj.spoonacular_id
                ).exists()
            else:
                # If no spoonacular_id, check if this exact recipe belongs to the user
                return obj.created_by == request.user
        return False


class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer for meal plans that matches your Django model"""

    # Add calculated fields
    days_count = serializers.SerializerMethodField()
    daily_averages = serializers.SerializerMethodField()

    class Meta:
        model = MealPlan
        fields = [
            'id', 'plan_type', 'start_date', 'end_date', 'generation_version',
            'ai_model_used', 'prompt_strategy', 'meal_plan_data',
            'total_calories', 'avg_daily_calories', 'total_protein', 'total_carbs', 'total_fat',
            'nutritional_balance_score', 'variety_score', 'preference_match_score',
            'days_count', 'daily_averages', 'is_active', 'user_rating', 'user_feedback',
            'shopping_list_generated', 'shopping_list_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'days_count', 'daily_averages', 'avg_daily_calories',
            'created_at', 'updated_at'
        ]

    def get_days_count(self, obj):
        """Calculate number of days in the meal plan"""
        return (obj.end_date - obj.start_date).days + 1

    def get_daily_averages(self, obj):
        """Calculate daily nutrition averages"""
        days = self.get_days_count(obj)
        if days == 0:
            return None

        return {
            'calories': round(obj.total_calories / days),
            'protein': round(obj.total_protein / days, 1),
            'carbs': round(obj.total_carbs / days, 1),
            'fat': round(obj.total_fat / days, 1)
        }


class UserRecipeRatingSerializer(serializers.ModelSerializer):
    """Serializer for user recipe ratings"""

    recipe_title = serializers.CharField(source='recipe.title', read_only=True)

    class Meta:
        model = UserRecipeRating
        fields = [
            'id', 'recipe', 'recipe_title', 'rating', 'review',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'recipe_title', 'created_at', 'updated_at']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class NutritionLogSerializer(serializers.ModelSerializer):
    """Serializer for nutrition logs that matches your Django model"""

    # Add calculated fields
    progress_percentage = serializers.SerializerMethodField()
    calorie_deficit_surplus = serializers.SerializerMethodField()
    macro_distribution = serializers.SerializerMethodField()

    class Meta:
        model = NutritionLog
        fields = [
            'id', 'date', 'total_calories', 'total_protein', 'total_carbs',
            'total_fat', 'total_fiber', 'meals_data', 'calorie_deficit_surplus',
            'macro_balance_score', 'meal_plan', 'ai_analysis',
            'progress_percentage', 'macro_distribution',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'progress_percentage', 'macro_distribution',
            'created_at', 'updated_at'
        ]

    def get_progress_percentage(self, obj):
        """Get progress towards daily targets"""
        try:
            profile = obj.user.nutrition_profile
            return {
                'calories': min(100,
                                (obj.total_calories / profile.calorie_target) * 100) if profile.calorie_target else 0,
                'protein': min(100,
                               (obj.total_protein / profile.protein_target) * 100) if profile.protein_target else 0,
                'carbs': min(100, (obj.total_carbs / profile.carb_target) * 100) if profile.carb_target else 0,
                'fat': min(100, (obj.total_fat / profile.fat_target) * 100) if profile.fat_target else 0,
            }
        except NutritionProfile.DoesNotExist:
            return {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}

    def get_calorie_deficit_surplus(self, obj):
        """Calculate calorie deficit or surplus"""
        try:
            profile = obj.user.nutrition_profile
            difference = obj.total_calories - profile.calorie_target
            return {
                'difference': difference,
                'status': 'surplus' if difference > 0 else 'deficit' if difference < 0 else 'balanced',
                'percentage': round(abs(difference) / profile.calorie_target * 100, 1) if profile.calorie_target else 0
            }
        except NutritionProfile.DoesNotExist:
            return None

    def get_macro_distribution(self, obj):
        """Calculate actual macro distribution"""
        total_calories = obj.total_calories
        if total_calories == 0:
            return {'protein': 0, 'carbs': 0, 'fat': 0}

        return {
            'protein': round((obj.total_protein * 4 / total_calories) * 100),
            'carbs': round((obj.total_carbs * 4 / total_calories) * 100),
            'fat': round((obj.total_fat * 9 / total_calories) * 100)
        }