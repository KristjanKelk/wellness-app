from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from meal_planning.models import Recipe
from meal_planning.services.enhanced_spoonacular_service import EnhancedSpoonacularService
import logging
import time
from typing import List, Dict

logger = logging.getLogger('nutrition_fix')


class Command(BaseCommand):
    help = 'Fix nutrition data for existing recipes that have 0 calories or 0 fiber'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for processing recipes (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Update all recipes, not just those with nutrition issues'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        force_all = options['force_all']

        try:
            self.spoonacular = EnhancedSpoonacularService()
        except Exception as e:
            raise CommandError(f'Failed to initialize Spoonacular service: {e}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Find recipes that need nutrition updates
        if force_all:
            recipes_to_fix = Recipe.objects.all()
            self.stdout.write(f'Found {recipes_to_fix.count()} total recipes to process')
        else:
            recipes_to_fix = Recipe.objects.filter(
                models.Q(calories_per_serving=0) | 
                models.Q(fiber_per_serving=0)
            ).exclude(spoonacular_id__isnull=True)
            self.stdout.write(f'Found {recipes_to_fix.count()} recipes with nutrition issues')

        if recipes_to_fix.count() == 0:
            self.stdout.write(self.style.SUCCESS('No recipes need nutrition updates'))
            return

        updated_count = 0
        error_count = 0
        
        # Process recipes in batches
        for i in range(0, recipes_to_fix.count(), batch_size):
            batch = recipes_to_fix[i:i + batch_size]
            
            self.stdout.write(f'Processing batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, recipes_to_fix.count())} of {recipes_to_fix.count()})')
            
            for recipe in batch:
                try:
                    if self._update_recipe_nutrition(recipe, dry_run):
                        updated_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f'Failed to update recipe {recipe.id}: {e}')
                    self.stdout.write(
                        self.style.ERROR(f'Failed to update recipe {recipe.title}: {e}')
                    )
                
                # Rate limiting
                time.sleep(0.1)
            
            # Longer pause between batches
            if i + batch_size < recipes_to_fix.count():
                time.sleep(1)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would update {updated_count} recipes')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} recipes')
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'{error_count} recipes had errors')
            )

    @transaction.atomic
    def _update_recipe_nutrition(self, recipe: Recipe, dry_run: bool = False) -> bool:
        """Update nutrition data for a single recipe"""
        if not recipe.spoonacular_id:
            logger.warning(f'Recipe {recipe.id} has no Spoonacular ID, skipping')
            return False

        try:
            # Get detailed recipe information from Spoonacular
            detailed_recipe = self.spoonacular.get_recipe_information(
                recipe.spoonacular_id,
                include_nutrition=True
            )
            
            if not detailed_recipe:
                logger.warning(f'Could not fetch details for recipe {recipe.spoonacular_id}')
                return False

            # Extract nutrition data
            nutrition = self.spoonacular._extract_nutrition(detailed_recipe)
            
            # Check if we got valid nutrition data
            if nutrition['calories'] == 0 and nutrition['protein'] == 0:
                logger.warning(f'No nutrition data available for recipe {recipe.spoonacular_id}')
                return False

            old_calories = recipe.calories_per_serving
            old_fiber = recipe.fiber_per_serving

            if dry_run:
                self.stdout.write(
                    f'Would update {recipe.title}: '
                    f'calories {old_calories} -> {nutrition["calories"]}, '
                    f'fiber {old_fiber} -> {nutrition["fiber"]}'
                )
                return True
            
            # Update recipe nutrition
            recipe.calories_per_serving = nutrition['calories']
            recipe.protein_per_serving = nutrition['protein']
            recipe.carbs_per_serving = nutrition['carbs']
            recipe.fat_per_serving = nutrition['fat']
            recipe.fiber_per_serving = nutrition['fiber']
            
            recipe.save()
            
            self.stdout.write(
                f'Updated {recipe.title}: '
                f'calories {old_calories} -> {nutrition["calories"]}, '
                f'fiber {old_fiber} -> {nutrition["fiber"]}'
            )
            
            return True

        except Exception as e:
            logger.error(f'Error updating recipe {recipe.spoonacular_id}: {e}')
            raise e