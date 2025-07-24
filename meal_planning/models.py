# meal_planning/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
try:
    from django.contrib.postgres.fields import ArrayField
except ImportError:
    ArrayField = None
import uuid
from django.conf import settings
import json

User = get_user_model()


class CompatibleArrayField(models.JSONField):
    """
    A field that stores arrays and is compatible with both SQLite and PostgreSQL
    """
    def __init__(self, base_field=None, size=None, **kwargs):
        # Accept base_field for PostgreSQL compatibility but ignore it for JSONField
        kwargs.setdefault('default', list)
        super().__init__(**kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return value or []
    
    def to_python(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(value, list):
            return value
        return []


class NutritionProfile(models.Model):
    """Extended nutrition profile linked to existing health profile"""
    # Link to existing user/health system
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='nutrition_profile')

    # Dietary Preferences (15+ supported)
    DIETARY_PREFERENCES = [
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('pescatarian', 'Pescatarian'),
        ('keto', 'Ketogenic'),
        ('paleo', 'Paleo'),
        ('mediterranean', 'Mediterranean'),
        ('dash', 'DASH'),
        ('low_carb', 'Low Carb'),
        ('low_fat', 'Low Fat'),
        ('high_protein', 'High Protein'),
        ('intermittent_fasting', 'Intermittent Fasting'),
        ('whole30', 'Whole30'),
        ('raw_food', 'Raw Food'),
        ('gluten_free', 'Gluten Free'),
        ('dairy_free', 'Dairy Free'),
        ('flexitarian', 'Flexitarian'),
    ]

    # Allergies and Intolerances (10+ supported)
    ALLERGIES_INTOLERANCES = [
        ('nuts', 'Tree Nuts'),
        ('peanuts', 'Peanuts'),
        ('dairy', 'Dairy/Lactose'),
        ('gluten', 'Gluten'),
        ('eggs', 'Eggs'),
        ('fish', 'Fish'),
        ('shellfish', 'Shellfish'),
        ('soy', 'Soy'),
        ('sesame', 'Sesame'),
        ('sulfites', 'Sulfites'),
        ('nightshades', 'Nightshades'),
        ('histamine', 'Histamine Intolerance'),
    ]

    CUISINE_PREFERENCES = [
        ('italian', 'Italian'),
        ('mexican', 'Mexican'),
        ('asian', 'Asian'),
        ('indian', 'Indian'),
        ('mediterranean', 'Mediterranean'),
        ('american', 'American'),
        ('french', 'French'),
        ('thai', 'Thai'),
        ('japanese', 'Japanese'),
        ('chinese', 'Chinese'),
        ('greek', 'Greek'),
        ('middle_eastern', 'Middle Eastern'),
    ]

    # Nutrition preferences
    dietary_preferences = CompatibleArrayField(
        base_field=models.CharField(max_length=50, choices=DIETARY_PREFERENCES),
        default=list, blank=True
    )
    allergies_intolerances = CompatibleArrayField(
        base_field=models.CharField(max_length=50, choices=ALLERGIES_INTOLERANCES),
        default=list, blank=True
    )
    cuisine_preferences = CompatibleArrayField(
        base_field=models.CharField(max_length=50, choices=CUISINE_PREFERENCES),
        default=list, blank=True
    )
    disliked_ingredients = CompatibleArrayField(
        base_field=models.CharField(max_length=100),
        default=list, blank=True
    )

    # Nutritional targets (auto-calculated from health profile, but user can override)
    calorie_target = models.PositiveIntegerField(
        validators=[MinValueValidator(1000), MaxValueValidator(5000)],
        help_text="Daily calorie target in kcal"
    )
    protein_target = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(500)],
        help_text="Daily protein target in grams"
    )
    carb_target = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Daily carbohydrate target in grams"
    )
    fat_target = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Daily fat target in grams"
    )

    # Meal preferences
    meals_per_day = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    snacks_per_day = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(4)]
    )

    # Meal timing preferences (stored as time objects)
    breakfast_time = models.TimeField(default='08:00:00')
    lunch_time = models.TimeField(default='12:30:00')
    dinner_time = models.TimeField(default='19:00:00')

    # User timezone (ISO 8601 requirement)
    timezone = models.CharField(max_length=50, default='UTC')

    # Future-ready: Advanced preferences stored as JSON
    advanced_preferences = models.JSONField(default=dict, blank=True,
                                            help_text="Advanced user preferences in JSON format")

    # Spoonacular integration fields
    spoonacular_user_hash = models.CharField(max_length=100, blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_targets_from_health_profile(self):
        """Auto-calculate nutrition targets based on existing health profile"""
        # This will integrate with your existing health profile BMI/activity calculations
        health_profile = getattr(self.user, 'health_profile', None)
        if health_profile:
            # Base calorie calculation from BMI + activity level
            bmr = self._calculate_bmr(health_profile)
            activity_multiplier = self._get_activity_multiplier(health_profile.activity_level)
            maintenance_calories = bmr * activity_multiplier

            # Adjust for goals
            if health_profile.fitness_goal == 'weight_loss':
                self.calorie_target = int(maintenance_calories * 0.85)  # 15% deficit
            elif health_profile.fitness_goal == 'weight_gain':
                self.calorie_target = int(maintenance_calories * 1.15)  # 15% surplus
            else:
                self.calorie_target = int(maintenance_calories)

            # Calculate macros (example ratios, can be customized)
            self.protein_target = self.calorie_target * 0.25 / 4  # 25% protein
            self.carb_target = self.calorie_target * 0.45 / 4  # 45% carbs
            self.fat_target = self.calorie_target * 0.30 / 9  # 30% fats

    def _calculate_bmr(self, health_profile):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        weight = float(health_profile.weight_kg or 0)
        height = float(health_profile.height_cm or 0)
        age = health_profile.age or 0

        if health_profile.gender == 'M':
            return (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            return (10 * weight) + (6.25 * height) - (5 * age) - 161

    def _get_activity_multiplier(self, activity_level):
        """Convert activity level to calorie multiplier"""
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        return multipliers.get(activity_level, 1.375)

    class Meta:
        db_table = 'nutrition_profiles'


class Ingredient(models.Model):
    """Master ingredient database - populated from Spoonacular and user additions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core ingredient data
    name = models.CharField(max_length=200, unique=True)
    name_clean = models.CharField(max_length=200, db_index=True)  # Lowercase, no spaces for search

    # Spoonacular integration
    spoonacular_id = models.PositiveIntegerField(unique=True, null=True, blank=True)

    # Nutritional information per 100g (standardized)
    calories_per_100g = models.FloatField()
    protein_per_100g = models.FloatField(default=0)
    carbs_per_100g = models.FloatField(default=0)
    fat_per_100g = models.FloatField(default=0)
    fiber_per_100g = models.FloatField(default=0)
    sugar_per_100g = models.FloatField(default=0)
    sodium_per_100g = models.FloatField(default=0)  # in mg

    # Future-ready: Micronutrients (bonus feature ready)
    micronutrients = models.JSONField(default=dict, blank=True, help_text="Micronutrient data in JSON format")

    # Categorization for shopping lists
    FOOD_CATEGORIES = [
        ('produce', 'Fruits & Vegetables'),
        ('proteins', 'Meat & Seafood'),
        ('dairy', 'Dairy & Eggs'),
        ('grains', 'Grains & Bread'),
        ('pantry', 'Pantry Staples'),
        ('condiments', 'Condiments & Sauces'),
        ('beverages', 'Beverages'),
        ('snacks', 'Snacks'),
        ('frozen', 'Frozen Foods'),
        ('other', 'Other'),
    ]

    category = models.CharField(max_length=50, choices=FOOD_CATEGORIES, default='other')

    # Dietary tags for filtering
    dietary_tags = CompatibleArrayField(
        base_field=models.CharField(max_length=50),
        default=list, blank=True,
        help_text="vegetarian, vegan, gluten-free, etc."
    )

    # Common allergens
    allergens = CompatibleArrayField(
        base_field=models.CharField(max_length=50),
        default=list, blank=True
    )

    # Future-ready: Enhanced nutritional data (bonus feature)
    enhanced_data = models.JSONField(default=dict, blank=True, help_text="Enhanced nutritional data in JSON format")

    # Metadata
    is_verified = models.BooleanField(default=False)  # Spoonacular vs user-added
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ingredients'
        indexes = [
            models.Index(fields=['name_clean']),
            models.Index(fields=['category']),
            models.Index(fields=['spoonacular_id']),
        ]


class Recipe(models.Model):
    """Recipe database - populated from Spoonacular + RAG + user additions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core recipe data
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    cuisine = models.CharField(max_length=100, blank=True)

    # Meal categorization
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('dessert', 'Dessert'),
        ('appetizer', 'Appetizer'),
    ]
    meal_type = models.CharField(max_length=50, choices=MEAL_TYPES)

    # Recipe metadata
    servings = models.PositiveSmallIntegerField(default=4)
    prep_time_minutes = models.PositiveIntegerField()
    cook_time_minutes = models.PositiveIntegerField(default=0)
    total_time_minutes = models.PositiveIntegerField()

    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='medium')

    # Spoonacular integration
    spoonacular_id = models.PositiveIntegerField(unique=True, null=True, blank=True)

    # Recipe content
    ingredients_data = models.JSONField(help_text="List of ingredients with quantities in grams/ml")
    instructions = models.JSONField(help_text="Step-by-step cooking instructions")

    # Nutritional information (calculated from ingredients)
    calories_per_serving = models.FloatField()
    protein_per_serving = models.FloatField()
    carbs_per_serving = models.FloatField()
    fat_per_serving = models.FloatField()
    fiber_per_serving = models.FloatField(default=0)

    # Dietary and allergen information
    dietary_tags = CompatibleArrayField(
        base_field=models.CharField(max_length=50),
        default=list, blank=True
    )
    allergens = CompatibleArrayField(
        base_field=models.CharField(max_length=50),
        default=list, blank=True
    )

    # Image and source
    image_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True)

    # RAG and AI features
    SOURCE_TYPES = [
        ('spoonacular', 'Spoonacular API'),
        ('ai_generated', 'AI Generated'),
        ('user_submitted', 'User Submitted'),
        ('rag_database', 'RAG Database'),
    ]
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES)

    # Vector embeddings for RAG (future implementation)
    embedding_vector = models.JSONField(
        null=True, blank=True,
        help_text="OpenAI embedding vector (1536 dimensions)"
    )

    # User engagement (for community-driven RAG bonus)
    view_count = models.PositiveIntegerField(default=0)
    rating_avg = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    rating_count = models.PositiveIntegerField(default=0)

    # Future-ready: Enhanced recipe data
    enhanced_data = models.JSONField(default=dict, blank=True, help_text="Enhanced recipe data in JSON format")

    # Metadata
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes'
        indexes = [
            models.Index(fields=['meal_type']),
            models.Index(fields=['cuisine']),
            models.Index(fields=['total_time_minutes']),
            models.Index(fields=['rating_avg']),
            models.Index(fields=['spoonacular_id']),
        ]


class MealPlan(models.Model):
    """AI-generated meal plans"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')

    # Plan metadata
    PLAN_TYPES = [
        ('daily', 'Daily Plan'),
        ('weekly', 'Weekly Plan'),
    ]
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='daily')
    start_date = models.DateField()
    end_date = models.DateField()

    # AI generation metadata
    generation_version = models.CharField(max_length=10, default='1.0')
    ai_model_used = models.CharField(max_length=100, blank=True)
    prompt_strategy = models.TextField(blank=True)  # Store for debugging/improvement

    # Meal plan content (JSON structure for flexibility)
    meal_plan_data = models.JSONField(help_text="Complete meal plan with recipes and timing")

    # Nutritional summary for the plan
    total_calories = models.FloatField()
    avg_daily_calories = models.FloatField()
    total_protein = models.FloatField()
    total_carbs = models.FloatField()
    total_fat = models.FloatField()

    # Plan quality metrics
    nutritional_balance_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    variety_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    preference_match_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])

    # User interaction
    is_active = models.BooleanField(default=True)
    user_rating = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user_feedback = models.TextField(blank=True)

    # Shopping list generation
    shopping_list_generated = models.BooleanField(default=False)
    shopping_list_data = models.JSONField(default=dict, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meal_plans'
        indexes = [
            models.Index(fields=['user', 'start_date']),
            models.Index(fields=['plan_type', 'is_active']),
        ]


class NutritionLog(models.Model):
    """Daily nutrition tracking - linked to meal plans or manual entries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrition_logs')
    date = models.DateField()

    # Daily totals
    total_calories = models.FloatField(default=0)
    total_protein = models.FloatField(default=0)
    total_carbs = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    total_fiber = models.FloatField(default=0)

    # Meal breakdown
    meals_data = models.JSONField(default=dict, help_text="Breakdown by meal with recipes and portions")

    # Progress indicators
    calorie_deficit_surplus = models.FloatField(default=0)  # Negative = deficit, Positive = surplus
    macro_balance_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])

    # Links to meal plan if applicable
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.SET_NULL, null=True, blank=True)

    # AI analysis results
    ai_analysis = models.JSONField(default=dict, blank=True, help_text="AI-generated nutrition insights")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nutrition_logs'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]


# Future-ready models for bonus features

class UserRecipeRating(models.Model):
    """User ratings for community-driven RAG"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'recipe']
        db_table = 'user_recipe_ratings'


class IngredientSubstitution(models.Model):
    """AI-powered ingredient substitution suggestions"""
    original_ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='substitutions')
    substitute_ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='substitute_for')
    conversion_ratio = models.FloatField(default=1.0)  # How much substitute per original
    context = models.CharField(max_length=200, blank=True)  # "baking", "cooking", "raw", etc.
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])

    class Meta:
        unique_together = ['original_ingredient', 'substitute_ingredient', 'context']
        db_table = 'ingredient_substitutions'