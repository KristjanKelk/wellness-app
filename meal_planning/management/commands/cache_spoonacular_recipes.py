"""
Management command to cache a large variety of Spoonacular recipes for offline use
This helps avoid timeout issues when users search for recipes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from meal_planning.models import Recipe
from meal_planning.services.spoonacular_service import get_spoonacular_service, SpoonacularAPIError
import logging
import time
import random

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cache a diverse set of Spoonacular recipes for offline search functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--total-recipes',
            type=int,
            default=500,
            help='Total number of recipes to cache (default: 500)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=20,
            help='Number of recipes to fetch per API call (default: 20)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.5,
            help='Delay between API calls in seconds (default: 1.5)',
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Re-fetch recipes even if they already exist in database',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting recipe caching process...'))
        
        service = get_spoonacular_service()
        total_target = options['total_recipes']
        batch_size = options['batch_size']
        delay = options['delay']
        force_refresh = options['force_refresh']
        
        # Define diverse search parameters to get variety
        search_configs = self.get_search_configurations()
        
        total_cached = 0
        errors = 0
        skipped = 0
        
        self.stdout.write(f'Target: {total_target} recipes across {len(search_configs)} categories')
        
        for i, config in enumerate(search_configs):
            if total_cached >= total_target:
                break
                
            remaining = total_target - total_cached
            recipes_for_this_config = min(batch_size, remaining)
            
            self.stdout.write(f'\n[{i+1}/{len(search_configs)}] Fetching {recipes_for_this_config} recipes: {config["name"]}')
            
            try:
                # Make API request
                search_results = service.search_recipes(
                    query=config.get('query', ''),
                    cuisine=config.get('cuisine', ''),
                    diet=config.get('diet', ''),
                    intolerances=config.get('intolerances', ''),
                    number=recipes_for_this_config,
                    offset=0
                )
                
                # Process results
                for spoon_recipe in search_results.get('results', []):
                    if total_cached >= total_target:
                        break
                        
                    try:
                        spoonacular_id = spoon_recipe.get('id')
                        
                        # Check if recipe already exists
                        if not force_refresh and Recipe.objects.filter(spoonacular_id=spoonacular_id).exists():
                            skipped += 1
                            self.stdout.write(f'  ⏭️  Skipped existing: {spoon_recipe.get("title", "Unknown")}')
                            continue
                        
                        # Normalize recipe data
                        normalized_data = service.normalize_recipe_data(spoon_recipe)
                        
                        # Create or update recipe
                        with transaction.atomic():
                            recipe, created = Recipe.objects.update_or_create(
                                spoonacular_id=spoonacular_id,
                                defaults={
                                    'title': normalized_data['title'],
                                    'summary': normalized_data.get('summary', ''),
                                    'cuisine': normalized_data.get('cuisine', ''),
                                    'meal_type': normalized_data.get('meal_type', 'lunch'),
                                    'servings': normalized_data.get('servings', 4),
                                    'prep_time_minutes': normalized_data.get('prep_time_minutes', 0),
                                    'cook_time_minutes': normalized_data.get('cook_time_minutes', 0),
                                    'total_time_minutes': normalized_data.get('total_time_minutes', 30),
                                    'difficulty_level': normalized_data.get('difficulty_level', 'medium'),
                                    'ingredients_data': normalized_data.get('ingredients_data', []),
                                    'instructions': normalized_data.get('instructions', []),
                                    'calories_per_serving': normalized_data.get('calories_per_serving', 0),
                                    'protein_per_serving': normalized_data.get('protein_per_serving', 0),
                                    'carbs_per_serving': normalized_data.get('carbs_per_serving', 0),
                                    'fat_per_serving': normalized_data.get('fat_per_serving', 0),
                                    'fiber_per_serving': normalized_data.get('fiber_per_serving', 0),
                                    'dietary_tags': normalized_data.get('dietary_tags', []),
                                    'allergens': normalized_data.get('allergens', []),
                                    'image_url': normalized_data.get('image_url', ''),
                                    'source_url': normalized_data.get('source_url', ''),
                                    'source_type': 'spoonacular',
                                    'is_verified': True
                                }
                            )
                            
                            total_cached += 1
                            action = "✅ Created" if created else "🔄 Updated"
                            self.stdout.write(f'  {action}: {recipe.title}')
                            
                    except Exception as e:
                        errors += 1
                        logger.warning(f"Failed to save recipe {spoon_recipe.get('id', 'unknown')}: {e}")
                        self.stdout.write(f'  ❌ Error: {str(e)[:50]}...')
                        continue
                
                # Rate limiting delay
                if delay > 0:
                    time.sleep(delay)
                    
            except SpoonacularAPIError as e:
                errors += 1
                logger.error(f"Spoonacular API error for config {config['name']}: {e}")
                self.stdout.write(f'  ❌ API Error: {str(e)[:50]}...')
                # Wait longer on API errors
                time.sleep(delay * 2)
                continue
            except Exception as e:
                errors += 1
                logger.error(f"Unexpected error for config {config['name']}: {e}")
                self.stdout.write(f'  ❌ Unexpected Error: {str(e)[:50]}...')
                continue
        
        # Summary
        self.stdout.write(f'\n{self.style.SUCCESS("Recipe caching completed!")}')
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'  • Total cached: {total_cached}')
        self.stdout.write(f'  • Skipped existing: {skipped}')
        self.stdout.write(f'  • Errors: {errors}')
        
        # Database stats
        total_recipes = Recipe.objects.count()
        spoonacular_recipes = Recipe.objects.filter(source_type='spoonacular').count()
        
        self.stdout.write(f'\n🗄️  Database Summary:')
        self.stdout.write(f'  • Total recipes: {total_recipes}')
        self.stdout.write(f'  • Spoonacular recipes: {spoonacular_recipes}')
        self.stdout.write(f'  • Other sources: {total_recipes - spoonacular_recipes}')

    def get_search_configurations(self):
        """
        Get diverse search configurations to cache a wide variety of recipes
        """
        # Popular recipe queries
        popular_queries = [
            'chicken breast', 'salmon', 'pasta', 'salad', 'soup', 'stir fry',
            'breakfast bowl', 'smoothie', 'tacos', 'curry', 'rice', 'quinoa',
            'vegetable', 'protein', 'healthy', 'quick', 'easy', 'one pot'
        ]
        
        # Cuisines
        cuisines = [
            'italian', 'mexican', 'asian', 'mediterranean', 'american',
            'indian', 'thai', 'chinese', 'japanese', 'greek', 'french',
            'middle eastern', 'korean', 'vietnamese'
        ]
        
        # Diets
        diets = [
            'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto',
            'paleo', 'mediterranean', 'whole30', 'low-carb', 'high-protein'
        ]
        
        # Meal types
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert']
        
        configs = []
        
        # Popular query combinations
        for query in popular_queries[:10]:  # Limit to avoid too many requests
            configs.append({
                'name': f'Popular: {query}',
                'query': query
            })
        
        # Cuisine-based searches
        for cuisine in cuisines[:8]:  # Limit cuisines
            configs.append({
                'name': f'Cuisine: {cuisine}',
                'cuisine': cuisine,
                'query': 'healthy'
            })
        
        # Diet-based searches
        for diet in diets[:8]:  # Limit diets
            configs.append({
                'name': f'Diet: {diet}',
                'diet': diet,
                'query': 'delicious'
            })
        
        # Meal type combinations
        for meal_type in meal_types:
            configs.append({
                'name': f'Meal: {meal_type}',
                'query': f'healthy {meal_type}'
            })
        
        # Cuisine + Diet combinations (popular ones)
        popular_combinations = [
            ('italian', 'vegetarian'),
            ('mediterranean', 'healthy'),
            ('asian', 'gluten-free'),
            ('mexican', 'dairy-free'),
            ('american', 'high-protein'),
        ]
        
        for cuisine, diet in popular_combinations:
            configs.append({
                'name': f'Combo: {cuisine} + {diet}',
                'cuisine': cuisine,
                'diet': diet
            })
        
        # Shuffle to avoid patterns and return
        random.shuffle(configs)
        return configs