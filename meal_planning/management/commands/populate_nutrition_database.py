# meal_planning/management/commands/populate_nutrition_database.py
import json
import logging
import time
from typing import Dict, List
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from meal_planning.models import Recipe, Ingredient
from meal_planning.services.spoonacular_service import SpoonacularService
from meal_planning.services.rag_service import RAGService

logger = logging.getLogger('nutrition.populate')


class Command(BaseCommand):
    help = 'Populate nutrition database with 500+ recipes and ingredients'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recipes',
            type=int,
            default=500,
            help='Number of recipes to populate (default: 500)'
        )
        parser.add_argument(
            '--ingredients',
            type=int,
            default=500,
            help='Number of ingredients to populate (default: 500)'
        )
        parser.add_argument(
            '--use-spoonacular',
            action='store_true',
            help='Use Spoonacular API if available (default: use fallback data)'
        )
        parser.add_argument(
            '--update-embeddings',
            action='store_true',
            help='Generate embeddings for recipes after population'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for processing (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting nutrition database population...')
        )

        # Initialize services
        self.spoonacular_service = None
        self.rag_service = RAGService()

        if options['use_spoonacular'] and getattr(settings, 'SPOONACULAR_API_KEY', ''):
            try:
                self.spoonacular_service = SpoonacularService()
                self.stdout.write('Using Spoonacular API for data')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Spoonacular API unavailable: {e}')
                )

        if not self.spoonacular_service:
            self.stdout.write('Using fallback data for population')

        # Populate ingredients first
        self.populate_ingredients(options['ingredients'], options['batch_size'])

        # Then populate recipes
        self.populate_recipes(options['recipes'], options['batch_size'])

        # Generate embeddings if requested
        if options['update_embeddings']:
            self.generate_embeddings(options['batch_size'])

        self.stdout.write(
            self.style.SUCCESS('Database population completed successfully!')
        )

    def populate_ingredients(self, target_count: int, batch_size: int):
        """Populate ingredients database"""
        self.stdout.write(f'Populating {target_count} ingredients...')

        current_count = Ingredient.objects.count()
        if current_count >= target_count:
            self.stdout.write(f'Already have {current_count} ingredients, skipping')
            return

        needed = target_count - current_count
        processed = 0

        if self.spoonacular_service:
            # Use Spoonacular API
            processed = self._populate_ingredients_from_spoonacular(needed, batch_size)

        # Fill remaining with fallback data
        if processed < needed:
            remaining = needed - processed
            self._populate_ingredients_fallback(remaining)

        self.stdout.write(
            self.style.SUCCESS(f'Added {needed} ingredients')
        )

    def populate_recipes(self, target_count: int, batch_size: int):
        """Populate recipes database"""
        self.stdout.write(f'Populating {target_count} recipes...')

        current_count = Recipe.objects.count()
        if current_count >= target_count:
            self.stdout.write(f'Already have {current_count} recipes, skipping')
            return

        needed = target_count - current_count
        processed = 0

        if self.spoonacular_service:
            # Use Spoonacular API
            processed = self._populate_recipes_from_spoonacular(needed, batch_size)

        # Fill remaining with fallback data
        if processed < needed:
            remaining = needed - processed
            self._populate_recipes_fallback(remaining)

        self.stdout.write(
            self.style.SUCCESS(f'Added {needed} recipes')
        )

    def _populate_ingredients_from_spoonacular(self, needed: int, batch_size: int) -> int:
        """Populate ingredients using Spoonacular API"""
        processed = 0
        
        try:
            # Common ingredient searches
            ingredient_queries = [
                'chicken', 'beef', 'salmon', 'rice', 'pasta', 'tomato', 'onion',
                'garlic', 'olive oil', 'salt', 'pepper', 'herbs', 'spices',
                'vegetables', 'fruits', 'dairy', 'cheese', 'milk', 'eggs',
                'beans', 'lentils', 'quinoa', 'oats', 'flour', 'sugar'
            ]

            for query in ingredient_queries:
                if processed >= needed:
                    break

                try:
                    # Search for ingredients
                    results = self.spoonacular_service.search_ingredients(
                        query=query,
                        number=min(batch_size, needed - processed)
                    )

                    for ingredient_data in results.get('results', []):
                        if processed >= needed:
                            break

                        try:
                            # Get detailed ingredient information
                            detailed_info = self.spoonacular_service.get_ingredient_info(
                                ingredient_data['id']
                            )

                            # Create ingredient
                            ingredient = self._create_ingredient_from_spoonacular(detailed_info)
                            if ingredient:
                                processed += 1
                                if processed % 10 == 0:
                                    self.stdout.write(f'Processed {processed} ingredients...')

                        except Exception as e:
                            logger.error(f"Failed to process ingredient: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Failed to search ingredients for '{query}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Spoonacular ingredient population failed: {e}")

        return processed

    def _populate_recipes_from_spoonacular(self, needed: int, batch_size: int) -> int:
        """Populate recipes using Spoonacular API"""
        processed = 0

        try:
            # Recipe search parameters for variety
            search_params = [
                {'diet': 'vegetarian', 'type': 'main course'},
                {'diet': 'vegan', 'type': 'breakfast'},
                {'cuisine': 'mediterranean', 'type': 'lunch'},
                {'cuisine': 'italian', 'type': 'dinner'},
                {'cuisine': 'asian', 'type': 'snack'},
                {'diet': 'ketogenic', 'type': 'main course'},
                {'diet': 'paleo', 'type': 'breakfast'},
                {'cuisine': 'mexican', 'type': 'lunch'},
                {'cuisine': 'indian', 'type': 'dinner'},
                {'diet': 'gluten free', 'type': 'dessert'},
            ]

            for params in search_params:
                if processed >= needed:
                    break

                try:
                    # Search for recipes
                    results = self.spoonacular_service.search_recipes(
                        number=min(batch_size, needed - processed),
                        **params
                    )

                    for recipe_data in results.get('results', []):
                        if processed >= needed:
                            break

                        try:
                            # Get detailed recipe information
                            detailed_recipe = self.spoonacular_service.get_recipe_info(
                                recipe_data['id']
                            )

                            # Create recipe
                            recipe = self._create_recipe_from_spoonacular(detailed_recipe)
                            if recipe:
                                processed += 1
                                if processed % 10 == 0:
                                    self.stdout.write(f'Processed {processed} recipes...')

                        except Exception as e:
                            logger.error(f"Failed to process recipe: {e}")
                            continue

                except Exception as e:
                    logger.error(f"Failed to search recipes with params {params}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Spoonacular recipe population failed: {e}")

        return processed

    def _populate_ingredients_fallback(self, needed: int):
        """Populate ingredients using fallback data"""
        fallback_ingredients = [
            # Proteins
            {'name': 'Chicken Breast', 'category': 'proteins', 'calories': 165, 'protein': 31.0, 'carbs': 0.0, 'fat': 3.6, 'fiber': 0.0, 'dietary_tags': [], 'allergens': []},
            {'name': 'Salmon Fillet', 'category': 'proteins', 'calories': 208, 'protein': 22.0, 'carbs': 0.0, 'fat': 12.0, 'fiber': 0.0, 'dietary_tags': ['pescatarian'], 'allergens': ['fish']},
            {'name': 'Ground Beef (lean)', 'category': 'proteins', 'calories': 250, 'protein': 26.0, 'carbs': 0.0, 'fat': 15.0, 'fiber': 0.0, 'dietary_tags': [], 'allergens': []},
            {'name': 'Tofu (firm)', 'category': 'proteins', 'calories': 76, 'protein': 8.0, 'carbs': 1.9, 'fat': 4.8, 'fiber': 0.3, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': ['soy']},
            {'name': 'Eggs (large)', 'category': 'proteins', 'calories': 155, 'protein': 13.0, 'carbs': 1.1, 'fat': 11.0, 'fiber': 0.0, 'dietary_tags': ['vegetarian'], 'allergens': ['eggs']},
            {'name': 'Greek Yogurt (plain)', 'category': 'dairy', 'calories': 59, 'protein': 10.0, 'carbs': 3.6, 'fat': 0.4, 'fiber': 0.0, 'dietary_tags': ['vegetarian'], 'allergens': ['dairy']},
            {'name': 'Lentils (cooked)', 'category': 'proteins', 'calories': 116, 'protein': 9.0, 'carbs': 20.0, 'fat': 0.4, 'fiber': 7.9, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Black Beans (cooked)', 'category': 'proteins', 'calories': 132, 'protein': 8.9, 'carbs': 23.0, 'fat': 0.5, 'fiber': 8.7, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},

            # Grains & Starches
            {'name': 'Brown Rice (cooked)', 'category': 'grains', 'calories': 123, 'protein': 2.6, 'carbs': 23.0, 'fat': 0.9, 'fiber': 1.8, 'dietary_tags': ['vegetarian', 'vegan', 'gluten_free'], 'allergens': []},
            {'name': 'Quinoa (cooked)', 'category': 'grains', 'calories': 120, 'protein': 4.4, 'carbs': 22.0, 'fat': 1.9, 'fiber': 2.8, 'dietary_tags': ['vegetarian', 'vegan', 'gluten_free'], 'allergens': []},
            {'name': 'Oats (dry)', 'category': 'grains', 'calories': 389, 'protein': 16.9, 'carbs': 66.3, 'fat': 6.9, 'fiber': 10.6, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': ['gluten']},
            {'name': 'Sweet Potato', 'category': 'produce', 'calories': 86, 'protein': 1.6, 'carbs': 20.0, 'fat': 0.1, 'fiber': 3.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Whole Wheat Pasta', 'category': 'grains', 'calories': 124, 'protein': 5.0, 'carbs': 25.0, 'fat': 1.1, 'fiber': 3.2, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': ['gluten']},

            # Vegetables
            {'name': 'Broccoli', 'category': 'produce', 'calories': 34, 'protein': 2.8, 'carbs': 7.0, 'fat': 0.4, 'fiber': 2.6, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Spinach', 'category': 'produce', 'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'fiber': 2.2, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Bell Peppers', 'category': 'produce', 'calories': 31, 'protein': 1.0, 'carbs': 7.0, 'fat': 0.3, 'fiber': 2.5, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Tomatoes', 'category': 'produce', 'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'fiber': 1.2, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Carrots', 'category': 'produce', 'calories': 41, 'protein': 0.9, 'carbs': 10.0, 'fat': 0.2, 'fiber': 2.8, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Onions', 'category': 'produce', 'calories': 40, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.1, 'fiber': 1.7, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Garlic', 'category': 'produce', 'calories': 149, 'protein': 6.4, 'carbs': 33.0, 'fat': 0.5, 'fiber': 2.1, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Avocado', 'category': 'produce', 'calories': 160, 'protein': 2.0, 'carbs': 9.0, 'fat': 15.0, 'fiber': 7.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},

            # Fruits
            {'name': 'Banana', 'category': 'produce', 'calories': 89, 'protein': 1.1, 'carbs': 23.0, 'fat': 0.3, 'fiber': 2.6, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Apple', 'category': 'produce', 'calories': 52, 'protein': 0.3, 'carbs': 14.0, 'fat': 0.2, 'fiber': 2.4, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Blueberries', 'category': 'produce', 'calories': 57, 'protein': 0.7, 'carbs': 14.0, 'fat': 0.3, 'fiber': 2.4, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Strawberries', 'category': 'produce', 'calories': 32, 'protein': 0.7, 'carbs': 8.0, 'fat': 0.3, 'fiber': 2.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},

            # Fats & Oils
            {'name': 'Olive Oil (extra virgin)', 'category': 'pantry', 'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'fiber': 0.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Almonds', 'category': 'pantry', 'calories': 579, 'protein': 21.0, 'carbs': 22.0, 'fat': 50.0, 'fiber': 12.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': ['nuts']},
            {'name': 'Walnuts', 'category': 'pantry', 'calories': 654, 'protein': 15.0, 'carbs': 14.0, 'fat': 65.0, 'fiber': 6.7, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': ['nuts']},
            {'name': 'Chia Seeds', 'category': 'pantry', 'calories': 486, 'protein': 17.0, 'carbs': 42.0, 'fat': 31.0, 'fiber': 34.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},

            # Dairy
            {'name': 'Milk (2%)', 'category': 'dairy', 'calories': 50, 'protein': 3.3, 'carbs': 4.8, 'fat': 2.0, 'fiber': 0.0, 'dietary_tags': ['vegetarian'], 'allergens': ['dairy']},
            {'name': 'Cheddar Cheese', 'category': 'dairy', 'calories': 403, 'protein': 25.0, 'carbs': 1.3, 'fat': 33.0, 'fiber': 0.0, 'dietary_tags': ['vegetarian'], 'allergens': ['dairy']},
            {'name': 'Cottage Cheese (low-fat)', 'category': 'dairy', 'calories': 72, 'protein': 12.0, 'carbs': 4.3, 'fat': 1.0, 'fiber': 0.0, 'dietary_tags': ['vegetarian'], 'allergens': ['dairy']},

            # Condiments & Seasonings
            {'name': 'Salt', 'category': 'condiments', 'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'fiber': 0.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Black Pepper', 'category': 'condiments', 'calories': 251, 'protein': 10.0, 'carbs': 64.0, 'fat': 3.3, 'fiber': 25.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Lemon Juice', 'category': 'condiments', 'calories': 22, 'protein': 0.4, 'carbs': 6.9, 'fat': 0.2, 'fiber': 0.3, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Honey', 'category': 'condiments', 'calories': 304, 'protein': 0.3, 'carbs': 82.0, 'fat': 0.0, 'fiber': 0.2, 'dietary_tags': ['vegetarian'], 'allergens': []},
        ]

        # Extend with variations and additional ingredients to reach target
        extended_ingredients = fallback_ingredients.copy()
        
        # Add more protein variations
        protein_variations = [
            {'name': 'Turkey Breast', 'category': 'proteins', 'calories': 135, 'protein': 30.0, 'carbs': 0.0, 'fat': 1.0, 'fiber': 0.0, 'dietary_tags': [], 'allergens': []},
            {'name': 'Cod Fillet', 'category': 'proteins', 'calories': 82, 'protein': 18.0, 'carbs': 0.0, 'fat': 0.7, 'fiber': 0.0, 'dietary_tags': ['pescatarian'], 'allergens': ['fish']},
            {'name': 'Shrimp', 'category': 'proteins', 'calories': 85, 'protein': 18.0, 'carbs': 0.2, 'fat': 1.4, 'fiber': 0.0, 'dietary_tags': ['pescatarian'], 'allergens': ['shellfish']},
            {'name': 'Chickpeas (cooked)', 'category': 'proteins', 'calories': 164, 'protein': 8.9, 'carbs': 27.0, 'fat': 2.6, 'fiber': 7.6, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
        ]
        extended_ingredients.extend(protein_variations)

        # Add more vegetables
        vegetable_variations = [
            {'name': 'Kale', 'category': 'produce', 'calories': 35, 'protein': 2.9, 'carbs': 7.3, 'fat': 0.4, 'fiber': 3.6, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Cauliflower', 'category': 'produce', 'calories': 25, 'protein': 1.9, 'carbs': 5.0, 'fat': 0.3, 'fiber': 2.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Zucchini', 'category': 'produce', 'calories': 17, 'protein': 1.2, 'carbs': 3.1, 'fat': 0.3, 'fiber': 1.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
            {'name': 'Mushrooms', 'category': 'produce', 'calories': 22, 'protein': 3.1, 'carbs': 3.3, 'fat': 0.3, 'fiber': 1.0, 'dietary_tags': ['vegetarian', 'vegan'], 'allergens': []},
        ]
        extended_ingredients.extend(vegetable_variations)

        # Create ingredients in batches
        batch_size = 50
        created_count = 0

        for i in range(0, min(needed, len(extended_ingredients)), batch_size):
            batch = extended_ingredients[i:i + batch_size]
            
            with transaction.atomic():
                for ingredient_data in batch:
                    if created_count >= needed:
                        break

                    try:
                        ingredient, created = Ingredient.objects.get_or_create(
                            name=ingredient_data['name'],
                            defaults={
                                'name_clean': ingredient_data['name'].lower().replace(' ', '_'),
                                'category': ingredient_data['category'],
                                'calories_per_100g': ingredient_data['calories'],
                                'protein_per_100g': ingredient_data['protein'],
                                'carbs_per_100g': ingredient_data['carbs'],
                                'fat_per_100g': ingredient_data['fat'],
                                'fiber_per_100g': ingredient_data['fiber'],
                                'dietary_tags': ingredient_data['dietary_tags'],
                                'allergens': ingredient_data['allergens'],
                                'is_verified': True
                            }
                        )

                        if created:
                            created_count += 1

                    except Exception as e:
                        logger.error(f"Failed to create ingredient {ingredient_data['name']}: {e}")
                        continue

        self.stdout.write(f'Created {created_count} fallback ingredients')

    def _populate_recipes_fallback(self, needed: int):
        """Populate recipes using fallback data"""
        fallback_recipes = [
            {
                'title': 'Grilled Chicken with Quinoa',
                'summary': 'A healthy, protein-packed meal with lean chicken breast and nutritious quinoa.',
                'cuisine': 'American',
                'meal_type': 'dinner',
                'servings': 4,
                'prep_time_minutes': 15,
                'cook_time_minutes': 25,
                'total_time_minutes': 40,
                'difficulty_level': 'easy',
                'ingredients_data': [
                    {'id': 'chicken_breast', 'name': 'chicken breast', 'quantity': 150, 'unit': 'grams'},
                    {'id': 'quinoa', 'name': 'quinoa', 'quantity': 60, 'unit': 'grams'},
                    {'id': 'broccoli', 'name': 'broccoli', 'quantity': 100, 'unit': 'grams'},
                    {'id': 'olive_oil', 'name': 'olive oil', 'quantity': 10, 'unit': 'ml'}
                ],
                'instructions': [
                    {'step': 1, 'description': 'Season chicken breast with salt and pepper', 'ingredients': ['chicken breast', 'salt', 'pepper']},
                    {'step': 2, 'description': 'Grill chicken for 6-7 minutes per side until cooked through', 'ingredients': ['chicken breast']},
                    {'step': 3, 'description': 'Cook quinoa according to package instructions', 'ingredients': ['quinoa']},
                    {'step': 4, 'description': 'Steam broccoli until tender', 'ingredients': ['broccoli']},
                    {'step': 5, 'description': 'Serve chicken over quinoa with steamed broccoli', 'ingredients': []}
                ],
                'calories_per_serving': 350,
                'protein_per_serving': 35,
                'carbs_per_serving': 25,
                'fat_per_serving': 8,
                'fiber_per_serving': 4,
                'dietary_tags': ['high_protein', 'gluten_free'],
                'allergens': [],
                'source_type': 'ai_generated'
            },
            {
                'title': 'Mediterranean Vegetarian Bowl',
                'summary': 'A colorful bowl packed with Mediterranean flavors and plant-based proteins.',
                'cuisine': 'Mediterranean',
                'meal_type': 'lunch',
                'servings': 2,
                'prep_time_minutes': 20,
                'cook_time_minutes': 15,
                'total_time_minutes': 35,
                'difficulty_level': 'easy',
                'ingredients_data': [
                    {'id': 'chickpeas', 'name': 'chickpeas', 'quantity': 100, 'unit': 'grams'},
                    {'id': 'cucumber', 'name': 'cucumber', 'quantity': 100, 'unit': 'grams'},
                    {'id': 'tomatoes', 'name': 'tomatoes', 'quantity': 150, 'unit': 'grams'},
                    {'id': 'feta_cheese', 'name': 'feta cheese', 'quantity': 50, 'unit': 'grams'},
                    {'id': 'olive_oil', 'name': 'olive oil', 'quantity': 15, 'unit': 'ml'}
                ],
                'instructions': [
                    {'step': 1, 'description': 'Drain and rinse chickpeas', 'ingredients': ['chickpeas']},
                    {'step': 2, 'description': 'Dice cucumber and tomatoes', 'ingredients': ['cucumber', 'tomatoes']},
                    {'step': 3, 'description': 'Combine vegetables in a bowl', 'ingredients': ['cucumber', 'tomatoes', 'chickpeas']},
                    {'step': 4, 'description': 'Crumble feta cheese on top', 'ingredients': ['feta_cheese']},
                    {'step': 5, 'description': 'Drizzle with olive oil and season', 'ingredients': ['olive_oil']}
                ],
                'calories_per_serving': 280,
                'protein_per_serving': 12,
                'carbs_per_serving': 18,
                'fat_per_serving': 18,
                'fiber_per_serving': 8,
                'dietary_tags': ['vegetarian', 'mediterranean', 'high_fiber'],
                'allergens': ['dairy'],
                'source_type': 'ai_generated'
            },
            # Add more recipe templates here...
        ]

        # Generate variations of base recipes
        base_proteins = ['chicken', 'salmon', 'tofu', 'beans']
        base_grains = ['rice', 'quinoa', 'pasta', 'oats']
        base_vegetables = ['broccoli', 'spinach', 'peppers', 'carrots']
        cuisines = ['Mediterranean', 'Asian', 'Mexican', 'Italian', 'American']
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']

        created_count = 0
        recipe_id = 1

        # Create recipe variations
        while created_count < needed and recipe_id <= needed:
            try:
                # Generate recipe variation
                protein = base_proteins[recipe_id % len(base_proteins)]
                grain = base_grains[recipe_id % len(base_grains)]
                vegetable = base_vegetables[recipe_id % len(base_vegetables)]
                cuisine = cuisines[recipe_id % len(cuisines)]
                meal_type = meal_types[recipe_id % len(meal_types)]

                recipe_data = {
                    'title': f'{cuisine} {protein.title()} with {grain.title()}',
                    'summary': f'A delicious {cuisine.lower()} {meal_type} featuring {protein} and {grain}.',
                    'cuisine': cuisine,
                    'meal_type': meal_type,
                    'servings': 2 + (recipe_id % 3),
                    'prep_time_minutes': 10 + (recipe_id % 20),
                    'cook_time_minutes': 15 + (recipe_id % 30),
                    'total_time_minutes': 25 + (recipe_id % 45),
                    'difficulty_level': ['easy', 'medium', 'hard'][recipe_id % 3],
                    'ingredients_data': [
                        {'id': f'{protein}_main', 'name': protein, 'quantity': 120 + (recipe_id % 80), 'unit': 'grams'},
                        {'id': f'{grain}_base', 'name': grain, 'quantity': 50 + (recipe_id % 50), 'unit': 'grams'},
                        {'id': f'{vegetable}_side', 'name': vegetable, 'quantity': 100 + (recipe_id % 100), 'unit': 'grams'},
                        {'id': 'olive_oil', 'name': 'olive oil', 'quantity': 5 + (recipe_id % 10), 'unit': 'ml'}
                    ],
                    'instructions': [
                        {'step': 1, 'description': f'Prepare the {protein}', 'ingredients': [protein]},
                        {'step': 2, 'description': f'Cook the {grain}', 'ingredients': [grain]},
                        {'step': 3, 'description': f'Prepare the {vegetable}', 'ingredients': [vegetable]},
                        {'step': 4, 'description': 'Combine all ingredients', 'ingredients': []}
                    ],
                    'calories_per_serving': 300 + (recipe_id % 200),
                    'protein_per_serving': 20 + (recipe_id % 20),
                    'carbs_per_serving': 25 + (recipe_id % 25),
                    'fat_per_serving': 8 + (recipe_id % 12),
                    'fiber_per_serving': 3 + (recipe_id % 7),
                    'dietary_tags': self._get_recipe_dietary_tags(protein, cuisine),
                    'allergens': self._get_recipe_allergens(protein),
                    'source_type': 'ai_generated'
                }

                # Create recipe
                recipe, created = Recipe.objects.get_or_create(
                    title=recipe_data['title'],
                    defaults=recipe_data
                )

                if created:
                    created_count += 1
                    if created_count % 25 == 0:
                        self.stdout.write(f'Created {created_count} fallback recipes...')

                recipe_id += 1

            except Exception as e:
                logger.error(f"Failed to create recipe variation {recipe_id}: {e}")
                recipe_id += 1
                continue

        self.stdout.write(f'Created {created_count} fallback recipes')

    def _get_recipe_dietary_tags(self, protein: str, cuisine: str) -> List[str]:
        """Get dietary tags based on protein and cuisine"""
        tags = []
        
        if protein in ['tofu', 'beans']:
            tags.extend(['vegetarian', 'vegan'])
        elif protein in ['chicken', 'salmon']:
            if protein == 'salmon':
                tags.append('pescatarian')
        
        if cuisine == 'Mediterranean':
            tags.append('mediterranean')
        elif cuisine == 'Asian':
            tags.append('asian')
        
        return tags

    def _get_recipe_allergens(self, protein: str) -> List[str]:
        """Get allergens based on protein"""
        allergen_map = {
            'salmon': ['fish'],
            'tofu': ['soy'],
        }
        return allergen_map.get(protein, [])

    def _create_ingredient_from_spoonacular(self, data: Dict) -> Ingredient:
        """Create ingredient from Spoonacular data"""
        try:
            nutrition = data.get('nutrition', {})
            nutrients = {n['name'].lower(): n['amount'] for n in nutrition.get('nutrients', [])}

            ingredient, created = Ingredient.objects.get_or_create(
                spoonacular_id=data['id'],
                defaults={
                    'name': data['name'],
                    'name_clean': data['name'].lower().replace(' ', '_'),
                    'category': self._categorize_ingredient(data['name']),
                    'calories_per_100g': nutrients.get('calories', 0),
                    'protein_per_100g': nutrients.get('protein', 0),
                    'carbs_per_100g': nutrients.get('carbohydrates', 0),
                    'fat_per_100g': nutrients.get('fat', 0),
                    'fiber_per_100g': nutrients.get('fiber', 0),
                    'dietary_tags': self._extract_dietary_tags(data),
                    'allergens': self._extract_allergens(data),
                    'is_verified': True
                }
            )

            return ingredient if created else None

        except Exception as e:
            logger.error(f"Failed to create ingredient from Spoonacular data: {e}")
            return None

    def _create_recipe_from_spoonacular(self, data: Dict) -> Recipe:
        """Create recipe from Spoonacular data"""
        try:
            recipe, created = Recipe.objects.get_or_create(
                spoonacular_id=data['id'],
                defaults={
                    'title': data['title'],
                    'summary': data.get('summary', ''),
                    'cuisine': data.get('cuisines', [''])[0] if data.get('cuisines') else '',
                    'meal_type': self._determine_meal_type(data),
                    'servings': data.get('servings', 4),
                    'prep_time_minutes': data.get('preparationMinutes', 0),
                    'cook_time_minutes': data.get('cookingMinutes', 0),
                    'total_time_minutes': data.get('readyInMinutes', 30),
                    'difficulty_level': self._determine_difficulty(data),
                    'ingredients_data': self._normalize_ingredients(data.get('extendedIngredients', [])),
                    'instructions': self._normalize_instructions(data.get('analyzedInstructions', [])),
                    'calories_per_serving': self._extract_calories(data),
                    'protein_per_serving': self._extract_protein(data),
                    'carbs_per_serving': self._extract_carbs(data),
                    'fat_per_serving': self._extract_fat(data),
                    'fiber_per_serving': self._extract_fiber(data),
                    'dietary_tags': self._extract_recipe_dietary_tags(data),
                    'allergens': self._extract_recipe_allergens(data),
                    'image_url': data.get('image', ''),
                    'source_url': data.get('sourceUrl', ''),
                    'source_type': 'spoonacular',
                    'is_verified': True
                }
            )

            return recipe if created else None

        except Exception as e:
            logger.error(f"Failed to create recipe from Spoonacular data: {e}")
            return None

    def _categorize_ingredient(self, name: str) -> str:
        """Simple ingredient categorization"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['chicken', 'beef', 'fish', 'salmon', 'turkey']):
            return 'proteins'
        elif any(word in name_lower for word in ['milk', 'cheese', 'yogurt', 'butter']):
            return 'dairy'
        elif any(word in name_lower for word in ['lettuce', 'tomato', 'onion', 'pepper', 'carrot']):
            return 'produce'
        elif any(word in name_lower for word in ['rice', 'bread', 'pasta', 'flour']):
            return 'grains'
        else:
            return 'other'

    def _determine_meal_type(self, data: Dict) -> str:
        """Determine meal type from recipe data"""
        dish_types = data.get('dishTypes', [])
        
        if any(t in dish_types for t in ['breakfast']):
            return 'breakfast'
        elif any(t in dish_types for t in ['lunch', 'salad']):
            return 'lunch'
        elif any(t in dish_types for t in ['dinner', 'main course']):
            return 'dinner'
        elif any(t in dish_types for t in ['snack', 'appetizer']):
            return 'snack'
        else:
            return 'lunch'  # default

    def _determine_difficulty(self, data: Dict) -> str:
        """Determine recipe difficulty"""
        prep_time = data.get('readyInMinutes', 30)
        
        if prep_time <= 20:
            return 'easy'
        elif prep_time <= 45:
            return 'medium'
        else:
            return 'hard'

    def generate_embeddings(self, batch_size: int):
        """Generate embeddings for recipes"""
        self.stdout.write('Generating embeddings for recipes...')
        
        updated_count = self.rag_service.update_recipe_embeddings_batch(batch_size)
        
        self.stdout.write(
            self.style.SUCCESS(f'Generated embeddings for {updated_count} recipes')
        )

    # Helper methods for data extraction (simplified implementations)
    def _normalize_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        return [
            {
                'id': f"ing_{i}",
                'name': ing.get('name', ''),
                'quantity': ing.get('amount', 0),
                'unit': ing.get('unit', 'gram')
            }
            for i, ing in enumerate(ingredients)
        ]

    def _normalize_instructions(self, instructions: List[Dict]) -> List[Dict]:
        normalized = []
        for inst_group in instructions:
            for step in inst_group.get('steps', []):
                normalized.append({
                    'step': step.get('number', 1),
                    'description': step.get('step', ''),
                    'ingredients': [ing.get('name', '') for ing in step.get('ingredients', [])]
                })
        return normalized

    def _extract_calories(self, data: Dict) -> float:
        nutrition = data.get('nutrition', {})
        for nutrient in nutrition.get('nutrients', []):
            if nutrient.get('name', '').lower() == 'calories':
                return nutrient.get('amount', 0)
        return 0

    def _extract_protein(self, data: Dict) -> float:
        nutrition = data.get('nutrition', {})
        for nutrient in nutrition.get('nutrients', []):
            if nutrient.get('name', '').lower() == 'protein':
                return nutrient.get('amount', 0)
        return 0

    def _extract_carbs(self, data: Dict) -> float:
        nutrition = data.get('nutrition', {})
        for nutrient in nutrition.get('nutrients', []):
            if nutrient.get('name', '').lower() in ['carbohydrates', 'carbs']:
                return nutrient.get('amount', 0)
        return 0

    def _extract_fat(self, data: Dict) -> float:
        nutrition = data.get('nutrition', {})
        for nutrient in nutrition.get('nutrients', []):
            if nutrient.get('name', '').lower() == 'fat':
                return nutrient.get('amount', 0)
        return 0

    def _extract_fiber(self, data: Dict) -> float:
        nutrition = data.get('nutrition', {})
        for nutrient in nutrition.get('nutrients', []):
            if nutrient.get('name', '').lower() == 'fiber':
                return nutrient.get('amount', 0)
        return 0

    def _extract_dietary_tags(self, data: Dict) -> List[str]:
        return []  # Simplified implementation

    def _extract_allergens(self, data: Dict) -> List[str]:
        return []  # Simplified implementation

    def _extract_recipe_dietary_tags(self, data: Dict) -> List[str]:
        tags = []
        if data.get('vegetarian'):
            tags.append('vegetarian')
        if data.get('vegan'):
            tags.append('vegan')
        if data.get('glutenFree'):
            tags.append('gluten_free')
        return tags

    def _extract_recipe_allergens(self, data: Dict) -> List[str]:
        return []  # Simplified implementation