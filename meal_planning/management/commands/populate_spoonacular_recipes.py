"""
Management command to populate database with Spoonacular recipes and remove fallback recipes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from meal_planning.models import Recipe
from meal_planning.services.spoonacular_service import get_spoonacular_service, SpoonacularAPIError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate database with Spoonacular recipes and remove fallback recipes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove-fallbacks',
            action='store_true',
            help='Remove existing fallback recipes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of recipes to fetch per meal type',
        )
        parser.add_argument(
            '--meal-types',
            nargs='+',
            default=['breakfast', 'lunch', 'dinner', 'snack'],
            help='Meal types to fetch recipes for',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Spoonacular recipe population...'))
        
        # Remove fallback recipes if requested
        if options['remove_fallbacks']:
            self.remove_fallback_recipes()
        
        # Populate with Spoonacular recipes
        self.populate_spoonacular_recipes(
            meal_types=options['meal_types'],
            limit=options['limit']
        )
        
        self.stdout.write(self.style.SUCCESS('Spoonacular recipe population completed!'))

    def remove_fallback_recipes(self):
        """Remove fallback and placeholder recipes"""
        self.stdout.write('Removing fallback recipes...')
        
        # Identify fallback recipes by common patterns
        fallback_patterns = [
            'fallback',
            'placeholder',
            'mock',
            'default',
            'basic',
            'simple',
            'Protein Breakfast Bowl',
            'Balanced Power Bowl',
            'Balanced Dinner Plate',
            'Healthy Breakfast Bowl',
            'Protein Salad',
            'Balanced Dinner'
        ]
        
        fallback_count = 0
        for pattern in fallback_patterns:
            deleted = Recipe.objects.filter(title__icontains=pattern).delete()
            fallback_count += deleted[0]
        
        # Also remove recipes without spoonacular_id that are not user-submitted
        deleted = Recipe.objects.filter(
            spoonacular_id__isnull=True,
            source_type__in=['ai_generated', 'rag_database']
        ).delete()
        fallback_count += deleted[0]
        
        self.stdout.write(
            self.style.WARNING(f'Removed {fallback_count} fallback recipes')
        )

    def populate_spoonacular_recipes(self, meal_types, limit):
        """Populate database with real Spoonacular recipes"""
        service = get_spoonacular_service()
        
        # Common dietary preferences to ensure variety
        dietary_preferences = [
            '',  # No specific diet
            'vegetarian',
            'vegan',
            'gluten-free',
            'dairy-free',
            'keto',
            'paleo',
            'mediterranean'
        ]
        
        # Popular cuisines
        cuisines = [
            '',  # No specific cuisine
            'italian',
            'mexican',
            'asian',
            'mediterranean',
            'american',
            'indian',
            'thai'
        ]
        
        total_added = 0
        
        for meal_type in meal_types:
            self.stdout.write(f'Fetching {meal_type} recipes...')
            meal_added = 0
            
            # Search for recipes with different combinations
            for diet in dietary_preferences:
                for cuisine in cuisines:
                    if meal_added >= limit:
                        break
                    
                    try:
                        # Build search query
                        query = f"healthy {meal_type}"
                        if cuisine:
                            query += f" {cuisine}"
                        
                        search_results = service.search_recipes(
                            query=query,
                            cuisine=cuisine,
                            diet=diet,
                            number=min(10, limit - meal_added)
                        )
                        
                        for spoon_recipe in search_results.get('results', []):
                            if meal_added >= limit:
                                break
                            
                            try:
                                # Check if recipe already exists
                                if Recipe.objects.filter(
                                    spoonacular_id=spoon_recipe.get('id')
                                ).exists():
                                    continue
                                
                                # Normalize and save recipe
                                normalized_data = service.normalize_recipe_data(spoon_recipe)
                                
                                with transaction.atomic():
                                    recipe = Recipe.objects.create(
                                        title=normalized_data['title'],
                                        summary=normalized_data.get('summary', ''),
                                        cuisine=normalized_data.get('cuisine', ''),
                                        meal_type=normalized_data.get('meal_type', meal_type),
                                        servings=normalized_data.get('servings', 4),
                                        prep_time_minutes=normalized_data.get('prep_time_minutes', 0),
                                        cook_time_minutes=normalized_data.get('cook_time_minutes', 0),
                                        total_time_minutes=normalized_data.get('total_time_minutes', 30),
                                        difficulty_level=normalized_data.get('difficulty_level', 'medium'),
                                        spoonacular_id=normalized_data.get('spoonacular_id'),
                                        ingredients_data=normalized_data.get('ingredients_data', []),
                                        instructions=normalized_data.get('instructions', []),
                                        calories_per_serving=normalized_data.get('calories_per_serving', 0),
                                        protein_per_serving=normalized_data.get('protein_per_serving', 0),
                                        carbs_per_serving=normalized_data.get('carbs_per_serving', 0),
                                        fat_per_serving=normalized_data.get('fat_per_serving', 0),
                                        fiber_per_serving=normalized_data.get('fiber_per_serving', 0),
                                        dietary_tags=normalized_data.get('dietary_tags', []),
                                        allergens=normalized_data.get('allergens', []),
                                        image_url=normalized_data.get('image_url', ''),
                                        source_url=normalized_data.get('source_url', ''),
                                        source_type='spoonacular',
                                        is_verified=True
                                    )
                                    
                                    meal_added += 1
                                    total_added += 1
                                    
                                    self.stdout.write(f'  ✓ Added: {recipe.title}')
                                    
                            except Exception as e:
                                logger.warning(f"Failed to save recipe {spoon_recipe.get('id')}: {e}")
                                continue
                                
                    except SpoonacularAPIError as e:
                        logger.warning(f"Spoonacular API error for {meal_type}/{diet}/{cuisine}: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error for {meal_type}/{diet}/{cuisine}: {e}")
                        continue
                
                if meal_added >= limit:
                    break
            
            self.stdout.write(
                self.style.SUCCESS(f'Added {meal_added} {meal_type} recipes')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total recipes added: {total_added}')
        )
        
        # Update recipe counts
        total_recipes = Recipe.objects.count()
        spoonacular_recipes = Recipe.objects.filter(source_type='spoonacular').count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Database now contains {total_recipes} total recipes '
                f'({spoonacular_recipes} from Spoonacular)'
            )
        )