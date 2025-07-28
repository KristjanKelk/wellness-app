from django.core.management.base import BaseCommand
from meal_planning.models import MealPlan
from datetime import date, timedelta
import json


class Command(BaseCommand):
    help = 'Migrate meal plans from old meal-type-based structure to new date-based structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Find meal plans with old structure (meal types as keys)
        old_structure_plans = []
        
        for meal_plan in MealPlan.objects.all():
            if meal_plan.meal_plan_data and 'meals' in meal_plan.meal_plan_data:
                meals = meal_plan.meal_plan_data['meals']
                
                # Check if it has meal type keys (old structure)
                if any(key in meals for key in ['breakfast', 'lunch', 'dinner']):
                    old_structure_plans.append(meal_plan)
        
        if not old_structure_plans:
            self.stdout.write(self.style.SUCCESS('No meal plans need migration.'))
            return
        
        self.stdout.write(f'Found {len(old_structure_plans)} meal plans with old structure')
        
        for meal_plan in old_structure_plans:
            self.stdout.write(f'Migrating meal plan {meal_plan.id} for user {meal_plan.user.username}')
            
            if dry_run:
                self.stdout.write(f'  Current structure: {list(meal_plan.meal_plan_data["meals"].keys())}')
                continue
            
            try:
                migrated_data = self.migrate_meal_plan_structure(meal_plan.meal_plan_data, meal_plan.start_date)
                meal_plan.meal_plan_data = migrated_data
                meal_plan.save()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully migrated meal plan {meal_plan.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to migrate meal plan {meal_plan.id}: {str(e)}'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Migration completed. {len(old_structure_plans)} meal plans updated.'))

    def migrate_meal_plan_structure(self, meal_plan_data, start_date):
        """Convert old meal-type-based structure to new date-based structure"""
        old_meals = meal_plan_data.get('meals', {})
        new_meals = {}
        
        # Default meal times
        meal_times = {
            'breakfast': '08:00',
            'lunch': '12:30', 
            'dinner': '19:00',
            'snack': '15:00'
        }
        
        # Use the meal plan's start date or today if not available
        if start_date:
            base_date = start_date
        else:
            base_date = date.today()
        
        date_str = base_date.isoformat()
        daily_meals = []
        
        # Convert each meal type to the new structure
        for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
            if meal_type in old_meals:
                meals_of_type = old_meals[meal_type]
                
                # Handle both single meal and array of meals
                if not isinstance(meals_of_type, list):
                    meals_of_type = [meals_of_type] if meals_of_type else []
                
                for meal in meals_of_type:
                    if not meal:  # Skip empty meals
                        continue
                        
                    # Convert to new structure
                    new_meal = {
                        'meal_type': meal_type,
                        'time': meal_times.get(meal_type, '12:00'),
                        'cuisine': meal.get('cuisine', 'International'),
                        'target_calories': meal.get('calories', 0),
                        'target_protein': meal.get('protein', 0),
                        'target_carbs': meal.get('carbs', 0),
                        'target_fat': meal.get('fat', 0)
                    }
                    
                    # Handle recipe data - check if it's already nested or direct
                    if 'recipe' in meal:
                        new_meal['recipe'] = meal['recipe']
                    else:
                        # Create recipe structure from direct meal data
                        new_meal['recipe'] = {
                            'id': meal.get('id'),
                            'title': meal.get('title', meal.get('name', f'{meal_type.title()} Meal')),
                            'name': meal.get('name', meal.get('title', f'{meal_type.title()} Meal')),
                            'readyInMinutes': meal.get('readyInMinutes', 0),
                            'prep_time': meal.get('prep_time', 0),
                            'cook_time': meal.get('cook_time', 0),
                            'total_time': meal.get('total_time', meal.get('readyInMinutes', 0)),
                            'servings': meal.get('servings', 1),
                            'sourceUrl': meal.get('sourceUrl', ''),
                            'image': meal.get('image', ''),
                            'cuisine': meal.get('cuisine'),
                            'nutrition': {
                                'calories': meal.get('calories', 0),
                                'protein': meal.get('protein', 0),
                                'carbs': meal.get('carbs', 0),
                                'fat': meal.get('fat', 0)
                            },
                            'estimated_nutrition': {
                                'calories': meal.get('calories', 0),
                                'protein': meal.get('protein', 0),
                                'carbs': meal.get('carbs', 0),
                                'fat': meal.get('fat', 0)
                            },
                            'ingredients': meal.get('ingredients', []),
                            'instructions': meal.get('instructions', []),
                            'database_id': meal.get('database_id')
                        }
                    
                    daily_meals.append(new_meal)
        
        # Create new structure
        new_meals[date_str] = daily_meals
        
        # Update the meal plan data
        new_meal_plan_data = meal_plan_data.copy()
        new_meal_plan_data['meals'] = new_meals
        
        return new_meal_plan_data