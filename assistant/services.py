from typing import Dict, Any, List, Optional, Tuple
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Avg, Sum
from django.core.exceptions import ValidationError

from health_profiles.models import HealthProfile, WeightHistory, Activity
from analytics.models import WellnessScore
from meal_planning.models import MealPlan, NutritionLog, Recipe


class DataNotFound(Exception):
    pass


class ValidationFailure(Exception):
    pass


class AssistantDAL:
    @staticmethod
    def _require_profile(user) -> HealthProfile:
        try:
            return HealthProfile.objects.get(user=user)
        except HealthProfile.DoesNotExist:
            raise DataNotFound('Health profile not found')

    @staticmethod
    def get_health_overview(user) -> Dict[str, Any]:
        profile = AssistantDAL._require_profile(user)
        bmi = profile.calculate_bmi()
        latest_weight = (
            WeightHistory.objects.filter(health_profile=profile)
            .order_by('-recorded_at')
            .first()
        )
        latest_score = (
            WellnessScore.objects.filter(health_profile=profile)
            .order_by('-created_at')
            .first()
        )
        activity_last_7 = Activity.objects.filter(
            health_profile=profile,
            performed_at__gte=timezone.now() - timedelta(days=7)
        )
        return {
            'name': user.get_full_name() or user.username,
            'bmi': round(bmi, 1) if bmi else None,
            'weight_kg': float(latest_weight.weight_kg) if latest_weight else None,
            'wellness_score': float(latest_score.total_score) if latest_score else None,
            'activity_level': profile.activity_level,
            'goal': profile.fitness_goal,
            'weekly_activity_sessions': activity_last_7.count(),
            'targets': {
                'target_weight_kg': float(profile.target_weight_kg) if profile.target_weight_kg else None,
            }
        }

    @staticmethod
    def get_weight_and_bmi(user, period: str = 'month') -> Dict[str, Any]:
        profile = AssistantDAL._require_profile(user)
        days_map = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365}
        if period not in days_map:
            raise ValidationFailure('period must be one of week, month, quarter, year')
        start = timezone.now() - timedelta(days=days_map[period])
        entries = WeightHistory.objects.filter(health_profile=profile, recorded_at__gte=start).order_by('recorded_at')
        weights = [float(e.weight_kg) for e in entries]
        if not weights:
            raise DataNotFound('No weight data for requested period')
        change = weights[-1] - weights[0]
        bmi = profile.calculate_bmi()
        return {
            'period': period,
            'start_weight_kg': weights[0],
            'end_weight_kg': weights[-1],
            'change_kg': round(change, 2),
            'bmi': round(bmi, 1) if bmi else None,
            'num_entries': len(weights)
        }

    @staticmethod
    def get_meal_plan_for_date(user, target_date: Optional[date] = None) -> Dict[str, Any]:
        if target_date is None:
            target_date = timezone.now().date()
        plan = (
            MealPlan.objects.filter(user=user, start_date__lte=target_date, end_date__gte=target_date, is_active=True)
            .order_by('-created_at')
            .first()
        )
        if not plan:
            raise DataNotFound('No active meal plan for selected date')
        # Return day-specific meals if structure supports multiple days
        data = plan.meal_plan_data or {}
        day_key_candidates = [target_date.isoformat(), target_date.strftime('%Y-%m-%d'), 'day_1', 'today']
        day_data = None
        for key in day_key_candidates:
            if isinstance(data, dict) and key in data:
                day_data = data[key]
                break
        return {
            'plan_id': str(plan.id),
            'date': target_date.isoformat(),
            'plan_type': plan.plan_type,
            'meals': day_data.get('meals') if isinstance(day_data, dict) else data.get('meals', []),
            'nutrition': data.get('nutrition', {}),
        }

    @staticmethod
    def get_meal_plan_for_week(user, start: Optional[date] = None) -> Dict[str, Any]:
        today = timezone.now().date()
        if start is None:
            start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        plan = (
            MealPlan.objects.filter(user=user, start_date__lte=end, end_date__gte=start, is_active=True)
            .order_by('-created_at')
            .first()
        )
        if not plan:
            raise DataNotFound('No active meal plan for this week')
        data = plan.meal_plan_data or {}
        return {
            'plan_id': str(plan.id),
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            'plan_type': plan.plan_type,
            'days': data.get('days') or data,
        }

    @staticmethod
    def get_tonight_dinner_recipe(user, target_date: Optional[date] = None) -> Dict[str, Any]:
        info = AssistantDAL.get_meal_plan_for_date(user, target_date)
        dinner = None
        for meal in info.get('meals', []) or []:
            if str(meal.get('type', '')).lower() == 'dinner':
                dinner = meal
                break
        if not dinner and info.get('meals'):
            dinner = info['meals'][-1]
        if not dinner:
            raise DataNotFound('Dinner not found in today\'s plan')
        recipe_id = dinner.get('recipe_id') or dinner.get('recipe_uuid') or dinner.get('id')
        recipe = None
        if recipe_id:
            try:
                recipe = Recipe.objects.filter(id=recipe_id).first()
            except Exception:
                recipe = None
        if recipe:
            return {
                'title': recipe.title,
                'servings': recipe.servings,
                'ingredients': recipe.ingredients_data,
                'instructions': recipe.instructions,
                'nutrition_per_serving': {
                    'calories': recipe.calories_per_serving,
                    'protein_g': recipe.protein_per_serving,
                    'carbs_g': recipe.carbs_per_serving,
                    'fat_g': recipe.fat_per_serving,
                }
            }
        # Fallback to embedded details in meal
        if 'ingredients' in dinner and 'instructions' in dinner:
            return {
                'title': dinner.get('title', 'Dinner'),
                'servings': dinner.get('servings'),
                'ingredients': dinner.get('ingredients'),
                'instructions': dinner.get('instructions'),
                'nutrition_per_serving': dinner.get('nutrition', {})
            }
        raise DataNotFound('Recipe details unavailable for tonight\'s dinner')

    @staticmethod
    def analyze_protein_intake_vs_target(user, days: int = 7) -> Dict[str, Any]:
        if days < 1 or days > 31:
            raise ValidationFailure('days must be between 1 and 31')
        today = timezone.now().date()
        start = today - timedelta(days=days-1)
        logs = NutritionLog.objects.filter(user=user, date__gte=start, date__lte=today).order_by('date')
        if not logs.exists():
            raise DataNotFound('No nutrition logs available for the selected period')
        total_protein = sum(l.total_protein for l in logs)
        avg_protein = total_protein / logs.count()
        # Attempt target from NutritionProfile if present
        try:
            from meal_planning.models import NutritionProfile
            np = NutritionProfile.objects.get(user=user)
            target = np.protein_target
        except Exception:
            target = None
        return {
            'period_days': days,
            'total_protein_g': round(total_protein, 1),
            'average_protein_g_per_day': round(avg_protein, 1),
            'target_protein_g_per_day': round(target, 1) if target else None,
            'meeting_target': (avg_protein >= target) if target else None,
        }

    @staticmethod
    def summarize_weight_trend(user, days: int = 30) -> Dict[str, Any]:
        if days < 7 or days > 365:
            raise ValidationFailure('days must be between 7 and 365')
        profile = AssistantDAL._require_profile(user)
        start = timezone.now() - timedelta(days=days)
        entries = WeightHistory.objects.filter(health_profile=profile, recorded_at__gte=start).order_by('recorded_at')
        weights = [float(e.weight_kg) for e in entries]
        if len(weights) < 2:
            raise DataNotFound('Insufficient weight data to determine trend')
        change = weights[-1] - weights[0]
        direction = 'decline' if change < -0.5 else 'increase' if change > 0.5 else 'plateau'
        return {
            'period_days': days,
            'start_weight_kg': weights[0],
            'end_weight_kg': weights[-1],
            'change_kg': round(change, 2),
            'trend': direction,
        }

    @staticmethod
    def recommend_wellness_focus(user) -> Dict[str, Any]:
        profile = AssistantDAL._require_profile(user)
        latest = (
            WellnessScore.objects.filter(health_profile=profile)
            .order_by('-created_at')
            .first()
        )
        if not latest:
            raise DataNotFound('No wellness score available. Please calculate your wellness score first.')
        components = {
            'bmi': float(latest.bmi_score),
            'activity': float(latest.activity_score),
            'progress': float(latest.progress_score),
            'habits': float(latest.habits_score),
        }
        lowest_key = min(components, key=components.get)
        recs = {
            'bmi': 'Focus on gradual weight adjustments through balanced nutrition and consistent activity. Consider reviewing your calorie and macro targets.',
            'activity': 'Increase weekly activity frequency and mix in cardio and strength. Aim for at least 150 minutes of moderate activity per week.',
            'progress': 'Set small, specific goals and track milestones weekly to build momentum.',
            'habits': 'Log weight and activities more consistently; build simple daily routines like a 20-minute walk and regular sleep schedule.'
        }
        return {
            'lowest_component': lowest_key,
            'component_scores': components,
            'recommendation': recs[lowest_key]
        }