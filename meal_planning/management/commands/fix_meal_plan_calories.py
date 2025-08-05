from django.core.management.base import BaseCommand
from django.db import transaction
from meal_planning.models import MealPlan
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix calorie calculations for existing meal plans'

    def handle(self, *args, **options):
        """Fix calorie calculations for all meal plans"""
        meal_plans = MealPlan.objects.all()
        fixed_count = 0
        
        self.stdout.write(f"Found {meal_plans.count()} meal plans to check")
        
        with transaction.atomic():
            for meal_plan in meal_plans:
                try:
                    meal_plan_data = meal_plan.meal_plan_data or {}
                    meals = meal_plan_data.get('meals', {})
                    
                    if not meals:
                        continue
                    
                    # Calculate totals from meal data
                    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
                    meal_count = 0
                    
                    for day_meals in meals.values():
                        for meal in day_meals:
                            totals['calories'] += float(meal.get('calories_per_serving', 0))
                            totals['protein'] += float(meal.get('protein_per_serving', 0))
                            totals['carbs'] += float(meal.get('carbs_per_serving', 0))
                            totals['fat'] += float(meal.get('fat_per_serving', 0))
                            meal_count += 1
                    
                    # Calculate averages
                    days = len(meals)
                    if days > 0:
                        avg_daily_calories = round(totals['calories'] / days, 1)
                        avg_daily_protein = round(totals['protein'] / days, 1)
                        avg_daily_carbs = round(totals['carbs'] / days, 1)
                        avg_daily_fat = round(totals['fat'] / days, 1)
                    else:
                        avg_daily_calories = 0
                        avg_daily_protein = 0
                        avg_daily_carbs = 0
                        avg_daily_fat = 0
                    
                    # Update nutrition in meal_plan_data
                    if 'nutrition' not in meal_plan_data:
                        meal_plan_data['nutrition'] = {}
                    
                    meal_plan_data['nutrition'].update({
                        'calories': totals['calories'],
                        'protein': totals['protein'],
                        'carbs': totals['carbs'],
                        'fat': totals['fat'],
                        'avg_daily_calories': avg_daily_calories,
                        'avg_daily_protein': avg_daily_protein,
                        'avg_daily_carbs': avg_daily_carbs,
                        'avg_daily_fat': avg_daily_fat
                    })
                    
                    # Update meal plan fields
                    updated = False
                    if meal_plan.total_calories != totals['calories']:
                        meal_plan.total_calories = totals['calories']
                        updated = True
                    if meal_plan.avg_daily_calories != avg_daily_calories:
                        meal_plan.avg_daily_calories = avg_daily_calories
                        updated = True
                    if meal_plan.total_protein != totals['protein']:
                        meal_plan.total_protein = totals['protein']
                        updated = True
                    if meal_plan.total_carbs != totals['carbs']:
                        meal_plan.total_carbs = totals['carbs']
                        updated = True
                    if meal_plan.total_fat != totals['fat']:
                        meal_plan.total_fat = totals['fat']
                        updated = True
                    
                    if updated:
                        meal_plan.meal_plan_data = meal_plan_data
                        meal_plan.save()
                        fixed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Fixed meal plan {meal_plan.id}: "
                                f"total_calories={totals['calories']}, "
                                f"avg_daily_calories={avg_daily_calories}"
                            )
                        )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error fixing meal plan {meal_plan.id}: {str(e)}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully fixed {fixed_count} meal plans")
        )