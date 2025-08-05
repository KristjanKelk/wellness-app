# ai_assistant/services.py
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
import openai
from .models import Conversation, Message, UserPreference
from health_profiles.models import HealthProfile, WeightHistory, Activity
from meal_planning.models import NutritionProfile, MealPlan, Recipe, NutritionLog
from analytics.models import WellnessScore


class AIAssistantService:
    """Main service for handling AI assistant interactions"""
    
    def __init__(self, user):
        self.user = user
        self.health_profile = getattr(user, 'health_profile', None)
        self.nutrition_profile = getattr(user, 'nutrition_profile', None)
        self.preferences = self._get_or_create_preferences()
        
    def _get_or_create_preferences(self):
        """Get or create user preferences for AI assistant"""
        preferences, _ = UserPreference.objects.get_or_create(user=self.user)
        return preferences
    
    def get_system_prompt(self):
        """Generate the system prompt for the AI assistant"""
        user_name = self.user.first_name or self.user.username
        
        system_prompt = f"""You are a wellness assistant helping {user_name} with health analytics and nutrition planning.

## Your capabilities include:
- Answering questions about health metrics (BMI, weight, wellness score, activity level)
- Providing information about meal plans and recipes
- Offering nutritional analysis and recommendations
- Providing general wellness guidance
- Describing trends from health data
- Comparing current metrics to targets and historical data

## Tone and personality:
- Friendly and encouraging
- Clear and straightforward
- Empathetic but not overly casual
- Use the user's name naturally in responses

## Response formatting:
- Use short, focused paragraphs
- Use bullet points for lists
- Use **bold** for key metrics and important information
- Present numerical data clearly with appropriate units (weight in kg, height in cm)
- For detailed mode: provide more context and explanations
- For concise mode: focus on key information only

## Important boundaries:
- You are NOT a medical professional and cannot provide medical advice
- For health concerns, suggest consulting with healthcare providers
- Stay within the scope of wellness guidance and data presentation
- Do not access or discuss other users' data
- Only provide information based on the user's own data

## Context about the user:
- Response preference: {self.preferences.response_mode}
- Has health profile: {'Yes' if self.health_profile else 'No'}
- Has nutrition profile: {'Yes' if self.nutrition_profile else 'No'}

Remember to be helpful, accurate, and encouraging while maintaining appropriate boundaries."""
        
        return system_prompt
    
    def get_available_functions(self):
        """Define available functions for the AI assistant"""
        return [
            {
                "name": "get_health_metrics",
                "description": "Retrieves user's current health metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_type": {
                            "type": "string",
                            "enum": ["bmi", "weight", "wellness_score", "all"],
                            "description": "The specific metric to retrieve"
                        },
                        "time_period": {
                            "type": "string",
                            "enum": ["current", "weekly", "monthly"],
                            "description": "Time period for the metrics"
                        }
                    },
                    "required": ["metric_type"]
                }
            },
            {
                "name": "get_meal_plan",
                "description": "Retrieves user's meal plan for specified time period",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_frame": {
                            "type": "string",
                            "enum": ["today", "tomorrow", "week"],
                            "description": "Time frame for meal plan"
                        },
                        "meal_type": {
                            "type": "string",
                            "enum": ["breakfast", "lunch", "dinner", "snack", "all"],
                            "description": "Specific meal type to retrieve"
                        }
                    },
                    "required": ["time_frame"]
                }
            },
            {
                "name": "get_nutrition_analysis",
                "description": "Analyzes nutritional intake for specified period",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["today", "yesterday", "week", "month"],
                            "description": "Period to analyze"
                        },
                        "nutrient": {
                            "type": "string",
                            "enum": ["calories", "protein", "carbs", "fat", "all"],
                            "description": "Specific nutrient to analyze"
                        }
                    },
                    "required": ["period"]
                }
            },
            {
                "name": "get_recipe_info",
                "description": "Retrieves detailed information about a recipe",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe_identifier": {
                            "type": "string",
                            "description": "Recipe name or meal identifier (e.g., 'tonight's dinner')"
                        },
                        "info_type": {
                            "type": "string",
                            "enum": ["ingredients", "instructions", "nutrition", "all"],
                            "description": "Type of information to retrieve"
                        }
                    },
                    "required": ["recipe_identifier"]
                }
            },
            {
                "name": "get_activity_summary",
                "description": "Retrieves user's activity and exercise summary",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_period": {
                            "type": "string",
                            "enum": ["today", "week", "month"],
                            "description": "Time period for activity summary"
                        },
                        "activity_type": {
                            "type": "string",
                            "enum": ["cardio", "strength", "flexibility", "all"],
                            "description": "Type of activity to summarize"
                        }
                    },
                    "required": ["time_period"]
                }
            },
            {
                "name": "get_progress_report",
                "description": "Generates a progress report towards user's goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal_type": {
                            "type": "string",
                            "enum": ["weight", "fitness", "nutrition", "all"],
                            "description": "Type of goal to report on"
                        },
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Whether to include recommendations"
                        }
                    },
                    "required": ["goal_type"]
                }
            }
        ]
    
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call and return results"""
        try:
            if function_name == "get_health_metrics":
                return self._get_health_metrics(**arguments)
            elif function_name == "get_meal_plan":
                return self._get_meal_plan(**arguments)
            elif function_name == "get_nutrition_analysis":
                return self._get_nutrition_analysis(**arguments)
            elif function_name == "get_recipe_info":
                return self._get_recipe_info(**arguments)
            elif function_name == "get_activity_summary":
                return self._get_activity_summary(**arguments)
            elif function_name == "get_progress_report":
                return self._get_progress_report(**arguments)
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_health_metrics(self, metric_type: str, time_period: str = "current") -> Dict[str, Any]:
        """Retrieve health metrics based on type and time period"""
        if not self.health_profile:
            return {"error": "No health profile found for user"}
        
        result = {}
        
        if metric_type in ["weight", "all"]:
            if time_period == "current":
                result["weight"] = {
                    "value": float(self.health_profile.weight_kg) if self.health_profile.weight_kg else None,
                    "unit": "kg"
                }
            else:
                # Get weight history
                days = 7 if time_period == "weekly" else 30
                start_date = timezone.now() - timedelta(days=days)
                weight_history = WeightHistory.objects.filter(
                    health_profile=self.health_profile,
                    recorded_at__gte=start_date
                ).order_by('recorded_at')
                
                if weight_history.exists():
                    weights = [{"date": w.recorded_at.isoformat(), "value": float(w.weight_kg)} for w in weight_history]
                    result["weight_history"] = weights
                    result["weight_change"] = float(weight_history.last().weight_kg - weight_history.first().weight_kg)
        
        if metric_type in ["bmi", "all"]:
            bmi = self.health_profile.calculate_bmi()
            if bmi:
                result["bmi"] = {
                    "value": round(bmi, 2),
                    "category": self._get_bmi_category(bmi)
                }
        
        if metric_type in ["wellness_score", "all"]:
            # Get latest wellness score
            latest_score = WellnessScore.objects.filter(
                health_profile=self.health_profile
            ).order_by('-calculated_at').first()
            
            if latest_score:
                result["wellness_score"] = {
                    "total": latest_score.total_score,
                    "components": {
                        "activity": latest_score.activity_score,
                        "nutrition": latest_score.nutrition_score,
                        "sleep": latest_score.sleep_score,
                        "mental": latest_score.mental_wellbeing_score
                    },
                    "calculated_at": latest_score.calculated_at.isoformat()
                }
        
        if metric_type == "all":
            # Add additional profile info
            result["profile"] = {
                "height": float(self.health_profile.height_cm) if self.health_profile.height_cm else None,
                "activity_level": self.health_profile.activity_level,
                "fitness_goal": self.health_profile.fitness_goal,
                "target_weight": float(self.health_profile.target_weight_kg) if self.health_profile.target_weight_kg else None
            }
        
        return result
    
    def _get_bmi_category(self, bmi: float) -> str:
        """Get BMI category based on value"""
        if bmi < 18.5:
            return "underweight"
        elif bmi < 25:
            return "normal"
        elif bmi < 30:
            return "overweight"
        else:
            return "obese"
    
    def _get_meal_plan(self, time_frame: str, meal_type: str = "all") -> Dict[str, Any]:
        """Retrieve meal plan for specified time frame"""
        if not self.nutrition_profile:
            return {"error": "No nutrition profile found for user"}
        
        # Determine date range
        today = timezone.now().date()
        if time_frame == "today":
            start_date = end_date = today
        elif time_frame == "tomorrow":
            start_date = end_date = today + timedelta(days=1)
        else:  # week
            start_date = today
            end_date = today + timedelta(days=6)
        
        # Get meal plans
        meal_plans = MealPlan.objects.filter(
            user=self.user,
            date__range=[start_date, end_date]
        ).order_by('date', 'meal_type')
        
        result = {"meal_plans": []}
        
        for plan in meal_plans:
            if meal_type != "all" and plan.meal_type != meal_type:
                continue
            
            meal_data = {
                "date": plan.date.isoformat(),
                "meal_type": plan.meal_type,
                "recipe": {
                    "name": plan.recipe.title,
                    "id": plan.recipe.id,
                    "ready_in_minutes": plan.recipe.ready_in_minutes,
                    "servings": plan.recipe.servings
                } if plan.recipe else None,
                "status": plan.status
            }
            
            # Add basic nutrition info
            if plan.recipe:
                meal_data["nutrition_summary"] = {
                    "calories": plan.recipe.calories,
                    "protein": plan.recipe.protein,
                    "carbs": plan.recipe.carbs,
                    "fat": plan.recipe.fat
                }
            
            result["meal_plans"].append(meal_data)
        
        return result
    
    def _get_nutrition_analysis(self, period: str, nutrient: str = "all") -> Dict[str, Any]:
        """Analyze nutritional intake for specified period"""
        if not self.nutrition_profile:
            return {"error": "No nutrition profile found for user"}
        
        # Determine date range
        today = timezone.now().date()
        if period == "today":
            start_date = end_date = today
        elif period == "yesterday":
            start_date = end_date = today - timedelta(days=1)
        elif period == "week":
            start_date = today - timedelta(days=6)
            end_date = today
        else:  # month
            start_date = today - timedelta(days=29)
            end_date = today
        
        # Get nutrition logs
        logs = NutritionLog.objects.filter(
            user=self.user,
            date__range=[start_date, end_date]
        )
        
        # Calculate totals and averages
        total_days = (end_date - start_date).days + 1
        
        result = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "targets": {
                "calories": self.nutrition_profile.calorie_target,
                "protein": self.nutrition_profile.protein_target,
                "carbs": self.nutrition_profile.carb_target,
                "fat": self.nutrition_profile.fat_target
            }
        }
        
        if nutrient == "all":
            # Get aggregated data
            daily_totals = {}
            for log in logs:
                date_key = log.date.isoformat()
                if date_key not in daily_totals:
                    daily_totals[date_key] = {
                        "calories": 0,
                        "protein": 0,
                        "carbs": 0,
                        "fat": 0
                    }
                
                daily_totals[date_key]["calories"] += log.calories or 0
                daily_totals[date_key]["protein"] += log.protein or 0
                daily_totals[date_key]["carbs"] += log.carbs or 0
                daily_totals[date_key]["fat"] += log.fat or 0
            
            # Calculate averages
            if daily_totals:
                avg_calories = sum(d["calories"] for d in daily_totals.values()) / len(daily_totals)
                avg_protein = sum(d["protein"] for d in daily_totals.values()) / len(daily_totals)
                avg_carbs = sum(d["carbs"] for d in daily_totals.values()) / len(daily_totals)
                avg_fat = sum(d["fat"] for d in daily_totals.values()) / len(daily_totals)
                
                result["averages"] = {
                    "calories": round(avg_calories, 1),
                    "protein": round(avg_protein, 1),
                    "carbs": round(avg_carbs, 1),
                    "fat": round(avg_fat, 1)
                }
                
                result["daily_data"] = daily_totals
        else:
            # Get specific nutrient data
            nutrient_data = []
            for log in logs:
                value = getattr(log, nutrient, 0) or 0
                nutrient_data.append({
                    "date": log.date.isoformat(),
                    "value": value
                })
            
            result[nutrient] = nutrient_data
            if nutrient_data:
                result[f"{nutrient}_average"] = round(
                    sum(d["value"] for d in nutrient_data) / len(nutrient_data), 1
                )
        
        return result
    
    def _get_recipe_info(self, recipe_identifier: str, info_type: str = "all") -> Dict[str, Any]:
        """Get detailed recipe information"""
        # Try to identify recipe by context
        recipe = None
        
        # Check if it's a reference to a meal time
        if "dinner" in recipe_identifier.lower() or "tonight" in recipe_identifier.lower():
            today = timezone.now().date()
            meal_plan = MealPlan.objects.filter(
                user=self.user,
                date=today,
                meal_type="dinner"
            ).first()
            if meal_plan and meal_plan.recipe:
                recipe = meal_plan.recipe
        elif "lunch" in recipe_identifier.lower():
            today = timezone.now().date()
            meal_plan = MealPlan.objects.filter(
                user=self.user,
                date=today,
                meal_type="lunch"
            ).first()
            if meal_plan and meal_plan.recipe:
                recipe = meal_plan.recipe
        elif "breakfast" in recipe_identifier.lower():
            today = timezone.now().date()
            meal_plan = MealPlan.objects.filter(
                user=self.user,
                date=today,
                meal_type="breakfast"
            ).first()
            if meal_plan and meal_plan.recipe:
                recipe = meal_plan.recipe
        else:
            # Try to find by name
            recipe = Recipe.objects.filter(
                title__icontains=recipe_identifier
            ).first()
        
        if not recipe:
            return {"error": f"Recipe not found for: {recipe_identifier}"}
        
        result = {
            "recipe": {
                "title": recipe.title,
                "ready_in_minutes": recipe.ready_in_minutes,
                "servings": recipe.servings,
                "source_url": recipe.source_url
            }
        }
        
        if info_type in ["ingredients", "all"]:
            result["ingredients"] = recipe.ingredients
        
        if info_type in ["instructions", "all"]:
            result["instructions"] = recipe.instructions
        
        if info_type in ["nutrition", "all"]:
            result["nutrition"] = {
                "calories": recipe.calories,
                "protein": recipe.protein,
                "carbs": recipe.carbs,
                "fat": recipe.fat,
                "fiber": recipe.fiber,
                "sugar": recipe.sugar,
                "sodium": recipe.sodium
            }
        
        return result
    
    def _get_activity_summary(self, time_period: str, activity_type: str = "all") -> Dict[str, Any]:
        """Get activity summary for specified period"""
        if not self.health_profile:
            return {"error": "No health profile found for user"}
        
        # Determine date range
        today = timezone.now()
        if time_period == "today":
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "week":
            start_date = today - timedelta(days=6)
        else:  # month
            start_date = today - timedelta(days=29)
        
        # Get activities
        activities_query = Activity.objects.filter(
            health_profile=self.health_profile,
            performed_at__gte=start_date
        )
        
        if activity_type != "all":
            activities_query = activities_query.filter(activity_type=activity_type)
        
        activities = activities_query.order_by('-performed_at')
        
        # Calculate summary
        total_duration = sum(a.duration_minutes for a in activities)
        total_calories = sum(a.calories_burned or 0 for a in activities)
        
        result = {
            "period": time_period,
            "total_activities": activities.count(),
            "total_duration_minutes": total_duration,
            "total_calories_burned": total_calories,
            "activities": []
        }
        
        # Add activity details
        for activity in activities[:10]:  # Limit to recent 10
            result["activities"].append({
                "name": activity.name,
                "type": activity.activity_type,
                "duration": activity.duration_minutes,
                "calories": activity.calories_burned,
                "date": activity.performed_at.isoformat()
            })
        
        # Add weekly activity days if looking at longer period
        if time_period != "today":
            days_with_activity = activities.values('performed_at__date').distinct().count()
            result["days_active"] = days_with_activity
            result["average_duration_per_day"] = round(total_duration / max(days_with_activity, 1), 1)
        
        return result
    
    def _get_progress_report(self, goal_type: str, include_recommendations: bool = True) -> Dict[str, Any]:
        """Generate progress report towards goals"""
        if not self.health_profile:
            return {"error": "No health profile found for user"}
        
        result = {"goal_type": goal_type, "progress": {}}
        
        if goal_type in ["weight", "all"]:
            if self.health_profile.target_weight_kg:
                current_weight = float(self.health_profile.weight_kg) if self.health_profile.weight_kg else None
                target_weight = float(self.health_profile.target_weight_kg)
                
                if current_weight:
                    difference = current_weight - target_weight
                    progress_percent = abs((current_weight - target_weight) / target_weight * 100)
                    
                    result["progress"]["weight"] = {
                        "current": current_weight,
                        "target": target_weight,
                        "difference": round(difference, 1),
                        "progress_percent": round(progress_percent, 1),
                        "status": "on_track" if abs(difference) < 2 else "needs_attention"
                    }
                    
                    # Get weight trend
                    month_ago = timezone.now() - timedelta(days=30)
                    weight_history = WeightHistory.objects.filter(
                        health_profile=self.health_profile,
                        recorded_at__gte=month_ago
                    ).order_by('recorded_at')
                    
                    if weight_history.count() > 1:
                        monthly_change = float(weight_history.last().weight_kg - weight_history.first().weight_kg)
                        result["progress"]["weight"]["monthly_change"] = round(monthly_change, 1)
        
        if goal_type in ["fitness", "all"]:
            # Activity goals
            week_ago = timezone.now() - timedelta(days=7)
            recent_activities = Activity.objects.filter(
                health_profile=self.health_profile,
                performed_at__gte=week_ago
            )
            
            days_active = recent_activities.values('performed_at__date').distinct().count()
            total_minutes = sum(a.duration_minutes for a in recent_activities)
            
            result["progress"]["fitness"] = {
                "weekly_active_days": days_active,
                "weekly_minutes": total_minutes,
                "goal": self.health_profile.fitness_goal,
                "fitness_level": self.health_profile.fitness_level
            }
        
        if goal_type in ["nutrition", "all"] and self.nutrition_profile:
            # Nutrition goals
            week_ago = timezone.now().date() - timedelta(days=7)
            logs = NutritionLog.objects.filter(
                user=self.user,
                date__gte=week_ago
            )
            
            if logs.exists():
                avg_calories = logs.aggregate(Avg('calories'))['calories__avg'] or 0
                avg_protein = logs.aggregate(Avg('protein'))['protein__avg'] or 0
                
                result["progress"]["nutrition"] = {
                    "average_calories": round(avg_calories, 0),
                    "calorie_target": self.nutrition_profile.calorie_target,
                    "average_protein": round(avg_protein, 1),
                    "protein_target": self.nutrition_profile.protein_target,
                    "adherence_percent": round(
                        (avg_calories / self.nutrition_profile.calorie_target * 100) 
                        if self.nutrition_profile.calorie_target else 0, 1
                    )
                }
        
        if include_recommendations:
            result["recommendations"] = self._generate_recommendations(result["progress"])
        
        return result
    
    def _generate_recommendations(self, progress: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on progress"""
        recommendations = []
        
        if "weight" in progress:
            weight_data = progress["weight"]
            if weight_data["status"] == "needs_attention":
                if weight_data["difference"] > 0:
                    recommendations.append("Consider increasing your daily activity or reviewing your calorie intake to support your weight loss goal.")
                else:
                    recommendations.append("You're below your target weight. Focus on nutrient-dense foods to reach your goal healthily.")
        
        if "fitness" in progress:
            fitness_data = progress["fitness"]
            if fitness_data["weekly_active_days"] < 3:
                recommendations.append("Try to be active at least 3-4 days per week for optimal health benefits.")
            if fitness_data["weekly_minutes"] < 150:
                recommendations.append("Aim for at least 150 minutes of moderate activity per week, as recommended by health guidelines.")
        
        if "nutrition" in progress:
            nutrition_data = progress["nutrition"]
            if nutrition_data["adherence_percent"] < 90 or nutrition_data["adherence_percent"] > 110:
                recommendations.append("Try to stay within 10% of your daily calorie target for consistent progress.")
            if nutrition_data["average_protein"] < nutrition_data["protein_target"] * 0.8:
                recommendations.append("Consider adding more protein-rich foods to meet your daily protein target.")
        
        return recommendations