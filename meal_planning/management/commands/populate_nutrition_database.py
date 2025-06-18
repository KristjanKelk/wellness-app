from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from meal_planning.models import Recipe, Ingredient
from meal_planning.services.spoonacular_service import get_spoonacular_service, SpoonacularAPIError
import logging
import time
from typing import List, Dict

logger = logging.getLogger('nutrition')


class Command(BaseCommand):
    help = 'Populate the nutrition database with recipes and ingredients from Spoonacular'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recipes',
            type=int,
            default=500,
            help='Number of recipes to import (default: 500)'
        )
        parser.add_argument(
            '--ingredients',
            type=int,
            default=500,
            help='Number of ingredients to import (default: 500)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=20,
            help='Batch size for API requests (default: 20)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip recipes/ingredients that already exist'
        )
        parser.add_argument(
            '--cuisines',
            type=str,
            default='italian,mexican,american,asian,mediterranean,indian,french,thai',
            help='Comma-separated list of cuisines to focus on'
        )
        parser.add_argument(
            '--diet-types',
            type=str,
            default='vegetarian,vegan,gluten free,dairy free,ketogenic',
            help='Comma-separated list of diet types to include'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(
            self.style.SUCCESS('Starting nutrition database population...')
        )

        # Initialize Spoonacular service
        try:
            self.spoonacular = get_spoonacular_service()
        except Exception as e:
            raise CommandError(f'Failed to initialize Spoonacular service: {e}')

        # Parse options
        target_recipes = options['recipes']
        target_ingredients = options['ingredients']
        batch_size = options['batch_size']
        skip_existing = options['skip_existing']
        cuisines = [c.strip() for c in options['cuisines'].split(',')]
        diet_types = [d.strip() for d in options['diet_types'].split(',')]

        # Import recipes
        if target_recipes > 0:
            self.stdout.write(f'Importing {target_recipes} recipes...')
            imported_recipes = self.import_recipes(
                target_recipes, batch_size, skip_existing, cuisines, diet_types
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_recipes} recipes')
            )

        # Import ingredients
        if target_ingredients > 0:
            self.stdout.write(f'Importing {target_ingredients} ingredients...')
            imported_ingredients = self.import_ingredients(
                target_ingredients, batch_size, skip_existing
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_ingredients} ingredients')
            )

        self.stdout.write(
            self.style.SUCCESS('Database population completed!')
        )

    def import_recipes(self, target_count: int, batch_size: int, skip_existing: bool,
                       cuisines: List[str], diet_types: List[str]) -> int:
        """Import recipes from Spoonacular"""
        imported_count = 0
        offset = 0

        # Prepare search queries for variety
        search_queries = self._prepare_recipe_search_queries(cuisines, diet_types)

        for query_data in search_queries:
            if imported_count >= target_count:
                break

            self.stdout.write(f'Searching recipes: {query_data["description"]}')

            try:
                # Search for recipes
                search_results = self.spoonacular.search_recipes(
                    query=query_data.get('query', ''),
                    cuisine=query_data.get('cuisine', ''),
                    diet=query_data.get('diet', ''),
                    number=min(batch_size, target_count - imported_count),
                    offset=offset
                )

                recipes = search_results.get('results', [])

                if not recipes:
                    self.stdout.write(f'No recipes found for: {query_data["description"]}')
                    continue

                # Process each recipe
                for recipe_data in recipes:
                    if imported_count >= target_count:
                        break

                    try:
                        recipe_id = recipe_data.get('id')

                        # Skip if already exists
                        if skip_existing and Recipe.objects.filter(spoonacular_id=recipe_id).exists():
                            continue

                        # Get detailed recipe information
                        detailed_recipe = self.spoonacular.get_recipe_information(recipe_id)

                        # Normalize and save recipe
                        if self._save_recipe(detailed_recipe):
                            imported_count += 1
                            self.stdout.write(
                                f'Imported recipe: {detailed_recipe.get("title", "Unknown")} ({imported_count}/{target_count})')

                        # Respect rate limits
                        time.sleep(1)

                    except Exception as e:
                        logger.error(f'Failed to import recipe {recipe_data.get("id")}: {e}')
                        continue

            except SpoonacularAPIError as e:
                logger.error(f'Spoonacular API error: {e}')
                continue

        return imported_count

    def import_ingredients(self, target_count: int, batch_size: int, skip_existing: bool) -> int:
        """Import ingredients from Spoonacular"""
        imported_count = 0

        # Common ingredients to start with
        ingredient_queries = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'rice', 'pasta', 'potato',
            'onion', 'garlic', 'tomato', 'carrot', 'broccoli', 'spinach', 'lettuce',
            'apple', 'banana', 'orange', 'strawberry', 'milk', 'cheese', 'butter',
            'eggs', 'bread', 'flour', 'sugar', 'salt', 'pepper', 'olive oil',
            'quinoa', 'beans', 'lentils', 'chickpeas', 'avocado', 'bell pepper',
            'mushroom', 'corn', 'peas', 'cabbage', 'cucumber', 'zucchini',
            'sweet potato', 'cauliflower', 'asparagus', 'green beans', 'kale',
            'yogurt', 'coconut', 'almond', 'walnut', 'honey', 'vanilla'
        ]

        for query in ingredient_queries:
            if imported_count >= target_count:
                break

            try:
                # Search for ingredients
                search_results = self.spoonacular.search_ingredients(query, number=10)
                ingredients = search_results.get('results', [])

                for ingredient_data in ingredients:
                    if imported_count >= target_count:
                        break

                    try:
                        ingredient_id = ingredient_data.get('id')

                        # Skip if already exists
                        if skip_existing and Ingredient.objects.filter(spoonacular_id=ingredient_id).exists():
                            continue

                        # Get detailed ingredient information
                        detailed_ingredient = self.spoonacular.get_ingredient_information(ingredient_id)

                        # Normalize and save ingredient
                        if self._save_ingredient(detailed_ingredient):
                            imported_count += 1
                            self.stdout.write(
                                f'Imported ingredient: {detailed_ingredient.get("name", "Unknown")} ({imported_count}/{target_count})')

                        # Respect rate limits
                        time.sleep(1)

                    except Exception as e:
                        logger.error(f'Failed to import ingredient {ingredient_data.get("id")}: {e}')
                        continue

            except SpoonacularAPIError as e:
                logger.error(f'Spoonacular API error for ingredient "{query}": {e}')
                continue

        return imported_count

    def _prepare_recipe_search_queries(self, cuisines: List[str], diet_types: List[str]) -> List[Dict]:
        """Prepare diverse search queries for recipe variety"""
        queries = []

        # General popular recipes
        queries.append({
            'description': 'Popular recipes',
            'query': 'popular',
        })

        # Cuisine-based searches
        for cuisine in cuisines:
            queries.append({
                'description': f'{cuisine.title()} cuisine',
                'cuisine': cuisine,
            })

        # Diet-based searches
        for diet in diet_types:
            queries.append({
                'description': f'{diet.title()} recipes',
                'diet': diet,
            })

        # Meal type searches
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert']
        for meal in meal_types:
            queries.append({
                'description': f'{meal.title()} recipes',
                'query': meal,
            })

        # Healthy and quick recipes
        queries.extend([
            {
                'description': 'Healthy recipes',
                'query': 'healthy',
            },
            {
                'description': 'Quick recipes',
                'query': 'quick easy',
            },
            {
                'description': 'High protein recipes',
                'query': 'high protein',
            }
        ])

        return queries

    @transaction.atomic
    def _save_recipe(self, spoonacular_recipe: Dict) -> bool:
        """Save normalized recipe to database"""
        try:
            # Normalize the recipe data
            normalized_data = self.spoonacular.normalize_recipe_data(spoonacular_recipe)

            # Create or update recipe
            recipe, created = Recipe.objects.update_or_create(
                spoonacular_id=normalized_data['spoonacular_id'],
                defaults=normalized_data
            )

            return created

        except Exception as e:
            logger.error(f'Failed to save recipe: {e}')
            return False

    @transaction.atomic
    def _save_ingredient(self, spoonacular_ingredient: Dict) -> bool:
        """Save normalized ingredient to database"""
        try:
            # Normalize the ingredient data
            normalized_data = self.spoonacular.normalize_ingredient_data(spoonacular_ingredient)

            # Create or update ingredient
            ingredient, created = Ingredient.objects.update_or_create(
                spoonacular_id=normalized_data['spoonacular_id'],
                defaults=normalized_data
            )

            return created

        except Exception as e:
            logger.error(f'Failed to save ingredient: {e}')
            return False


# Additional management command for updating existing data
class UpdateNutritionDataCommand(BaseCommand):
    """Update existing nutrition data from Spoonacular"""
    help = 'Update existing recipes and ingredients with latest data from Spoonacular'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than',
            type=int,
            default=30,
            help='Update records older than X days (default: 30)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Batch size for updates (default: 10)'
        )

    def handle(self, *args, **options):
        """Update existing nutrition data"""
        from datetime import datetime, timedelta

        older_than_days = options['older_than']
        batch_size = options['batch_size']
        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        self.stdout.write(f'Updating data older than {older_than_days} days...')

        try:
            spoonacular = get_spoonacular_service()

            # Update recipes
            old_recipes = Recipe.objects.filter(
                updated_at__lt=cutoff_date,
                spoonacular_id__isnull=False
            )[:batch_size]

            for recipe in old_recipes:
                try:
                    updated_data = spoonacular.get_recipe_information(recipe.spoonacular_id)
                    normalized_data = spoonacular.normalize_recipe_data(updated_data)

                    for field, value in normalized_data.items():
                        setattr(recipe, field, value)
                    recipe.save()

                    self.stdout.write(f'Updated recipe: {recipe.title}')
                    time.sleep(1)  # Rate limiting

                except Exception as e:
                    logger.error(f'Failed to update recipe {recipe.id}: {e}')

            # Update ingredients
            old_ingredients = Ingredient.objects.filter(
                updated_at__lt=cutoff_date,
                spoonacular_id__isnull=False
            )[:batch_size]

            for ingredient in old_ingredients:
                try:
                    updated_data = spoonacular.get_ingredient_information(ingredient.spoonacular_id)
                    normalized_data = spoonacular.normalize_ingredient_data(updated_data)

                    for field, value in normalized_data.items():
                        setattr(ingredient, field, value)
                    ingredient.save()

                    self.stdout.write(f'Updated ingredient: {ingredient.name}')
                    time.sleep(1)  # Rate limiting

                except Exception as e:
                    logger.error(f'Failed to update ingredient {ingredient.id}: {e}')

            self.stdout.write(self.style.SUCCESS('Update completed!'))

        except Exception as e:
            raise CommandError(f'Update failed: {e}')