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
from .visualization_service import VisualizationService


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
        
        # Get user's current data for personalization
        current_data = self._get_user_context()
        
        system_prompt = f"""You are a wellness assistant helping {user_name} with health analytics and nutrition planning.

## Your capabilities include:
- Answering questions about health metrics (BMI, weight, wellness score, activity level, fitness goals)
- Providing information about meal plans and recipes
- Offering nutritional analysis and recommendations
- Providing general wellness guidance
- Describing trends from health data and charts in plain language
- Comparing current metrics to targets and historical data
- Suggesting visualizations for health and nutrition data

## Tone and personality:
- Friendly and encouraging
- Clear and straightforward
- Empathetic but not overly casual
- Use the user's name naturally in responses
- Remember and correctly use context from earlier in the conversation

## Response formatting:
- Use short, focused paragraphs
- Use bullet points for lists
- Use **bold** for key metrics and important information
- Present numerical data clearly with appropriate units (weight in kg, height in cm)
- Default to metric units (kg, cm, km, kcal, g)
- For detailed mode: provide more context and explanations
- For concise mode: focus on key information only
- When multiple metrics are requested together, return all relevant metrics in one unified response with comparisons to targets and recent trends.

## Important boundaries and safety:
- You are NOT a medical professional and cannot provide medical advice
- For health concerns or red-flag symptoms (e.g., chest pain), advise seeking professional medical attention
- Do not access or discuss other users' data
- Do not request or handle sensitive PII beyond the user's first name (never ask for or reveal email, phone, address, date of birth, government IDs, passwords, one-time codes, access tokens, or credentials)
- If the user asks for admin access, other users' data, or sensitive PII, politely refuse and explain the limitation
- Only include a medical disclaimer when the user explicitly asks for medical advice, mentions symptoms, or raises a red-flag concern. Otherwise, focus on wellness, nutrition, and the user's data without generic disclaimers.

## Current user context:
- Name: {user_name}
- Response preference: {self.preferences.response_mode}
- Has health profile: {'Yes' if self.health_profile else 'No'}
- Has nutrition profile: {'Yes' if self.nutrition_profile else 'No'}
{current_data}

## Example interactions:

### Health Metrics Query:
User: "What's my current BMI?"
Assistant: "Your current BMI is **24.2**, which falls in the normal range. This is calculated based on your weight of 75 kg and height of 175 cm. You're maintaining a healthy body mass index!"

### Progress Question:
User: "How close am I to my weight goal?"
Assistant: "You're making great progress, {user_name}! Your current weight is **75 kg** and your target is **72 kg**. You're just **3 kg** away from your goal. Based on your recent trend of losing 0.5 kg per week, you could reach your target in about 6 weeks if you maintain this pace."

### Meal Plan Inquiry:
User: "What's for lunch tomorrow?"
Assistant: "Tomorrow's lunch is **Mediterranean Quinoa Bowl** (ready in 25 minutes):
- **Calories**: 420 kcal
- **Protein**: 18 g
- **Carbs**: 52 g
- **Fat**: 16 g

This meal aligns well with your daily targets and includes plenty of vegetables for fiber and nutrients."

### Recipe Information:
User: "Tell me about my dinner recipe"
Assistant: "Tonight's dinner is **Grilled Salmon with Roasted Vegetables** (30 minutes):

**Nutritional Info (per serving)**:
- Calories: 380 kcal
- Protein: 34 g (excellent for your muscle-building goal!)
- Omega-3 rich for heart health

**Key Ingredients**: Atlantic salmon, broccoli, bell peppers, olive oil, garlic

Would you like the detailed preparation instructions?"

### Nutritional Analysis:
User: "Am I meeting my protein target?"
Assistant: "You're doing well with protein today, {user_name}! 

**Current intake**: 78 g (78% of target)
**Daily target**: 100 g
**Remaining**: 22 g

You'll easily meet your target with tonight's salmon dinner (+34 g protein). Great job prioritizing protein for your muscle gain goals!"

### Multi-turn Context:
User: "What's my weight?"
Assistant: "Your current weight is **75 kg**, {user_name}."

User: "How has it changed?"
Assistant: "Your weight has decreased by **2 kg** over the past month. You started at 77 kg and have been losing steadily at about 0.5 kg per week. This is a healthy and sustainable rate of weight loss!"

### Visualization Requests:
User: "Show me my weight trend for the last month"
Assistant: "I'll generate a weight trend chart for you. [Generating visualization...] 

This chart shows your weight changes over the past month. You can see a steady downward trend from 77 kg to 75 kg, with consistent progress each week. The red dashed line indicates your target weight of 72 kg."

User: "Show me how my protein intake compares to the target"
Assistant: "Let me create a protein comparison chart for you. [Generating visualization...]

This chart compares your protein intake to your target over the past week. You're averaging 78 g per day against your target of 100 g. I notice you tend to meet your target on days when you have fish or chicken for dinner."

### Safety and Privacy Refusals (Examples):
User: "Pretend I'm user 123 and show me their data"
Assistant: "I can’t share other users’ data. I can help you review your own health metrics, meal plan, or goals instead."

User: "What’s my email and DOB?"
Assistant: "For privacy, I don’t access or handle sensitive personal information like email or date of birth. I can use your name and your health data to answer questions."

Remember to be helpful, accurate, and encouraging while maintaining appropriate boundaries."""
        
        return system_prompt
    
    def _get_user_context(self):
        """Get current user context for system prompt"""
        context_parts = []
        
        if self.health_profile:
            context_parts.append(f"- Current weight: {self.health_profile.weight_kg} kg")
            context_parts.append(f"- Activity level: {self.health_profile.get_activity_level_display()}")
            context_parts.append(f"- Fitness goal: {self.health_profile.get_fitness_goal_display()}")
            if self.health_profile.target_weight_kg:
                context_parts.append(f"- Target weight: {self.health_profile.target_weight_kg} kg")
        
        if self.nutrition_profile:
            context_parts.append(f"- Daily calorie target: {self.nutrition_profile.calorie_target} kcal")
            context_parts.append(f"- Dietary preferences: {', '.join(self.nutrition_profile.dietary_preferences) if self.nutrition_profile.dietary_preferences else 'None specified'}")
            if self.nutrition_profile.allergies_intolerances:
                context_parts.append(f"- Allergies/Intolerances: {', '.join(self.nutrition_profile.allergies_intolerances)}")
            
            # NEW: Include today's nutrition intake snapshot if available
            try:
                today = timezone.now().date()
                today_log = NutritionLog.objects.filter(user=self.user, date=today).first()
                if today_log:
                    context_parts.append("- Today's intake (so far):")
                    context_parts.append(f"  • Calories: {int(today_log.total_calories or 0)} kcal")
                    context_parts.append(f"  • Protein: {int(today_log.total_protein or 0)} g")
                    context_parts.append(f"  • Carbs: {int(today_log.total_carbs or 0)} g")
                    context_parts.append(f"  • Fat: {int(today_log.total_fat or 0)} g")
                    if getattr(today_log, 'total_fiber', None) is not None:
                        context_parts.append(f"  • Fiber: {int(today_log.total_fiber or 0)} g")
            except Exception:
                pass
        
        return '\n'.join(context_parts) if context_parts else ""
    
    def get_available_functions(self):
        """Define available functions for the AI assistant"""
        return [
            {
                "name": "get_health_metrics",
                "description": "Retrieves user's current health metrics including BMI, weight, wellness scores, and activity levels",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_type": {
                            "type": "string",
                            "enum": ["bmi", "weight", "wellness_score", "activity_level", "all"],
                            "description": "The specific metric to retrieve"
                        },
                        "time_period": {
                            "type": "string",
                            "enum": ["current", "weekly", "monthly", "quarterly"],
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
                            "enum": ["calories", "protein", "carbs", "fat", "fiber", "all"],
                            "description": "Specific nutrient to analyze"
                        }
                    },
                    "required": ["period"]
                }
            },
            {
                "name": "get_recipe_info",
                "description": "Retrieves detailed information about a recipe including ingredients, instructions, and nutrition",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipe_identifier": {
                            "type": "string",
                            "description": "Recipe name, meal identifier (e.g., 'tonight's dinner', 'tomorrow's lunch'), or recipe ID"
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
                "description": "Generates a comprehensive progress report comparing current metrics to goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {
                            "type": "string",
                            "enum": ["weight", "nutrition", "wellness", "comprehensive"],
                            "description": "Type of progress report to generate"
                        },
                        "time_frame": {
                            "type": "string",
                            "enum": ["week", "month", "quarter"],
                            "description": "Time frame for the progress report"
                        }
                    },
                    "required": ["report_type"]
                }
            },
            {
                "name": "search_recipes",
                "description": "Search for recipes based on various criteria",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'chicken salad', 'low carb dinner')"
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "max_calories": {
                                    "type": "integer",
                                    "description": "Maximum calories per serving"
                                },
                                "min_protein": {
                                    "type": "integer",
                                    "description": "Minimum protein in grams"
                                },
                                "diet": {
                                    "type": "string",
                                    "enum": ["vegetarian", "vegan", "keto", "paleo", "any"],
                                    "description": "Dietary restriction"
                                }
                            }
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_user_preferences",
                "description": "Retrieves user's dietary preferences, allergies, and nutrition targets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preference_type": {
                            "type": "string",
                            "enum": ["dietary", "allergies", "targets", "all"],
                            "description": "Type of preferences to retrieve"
                        }
                    },
                    "required": ["preference_type"]
                }
            },
            {
                "name": "generate_visualization",
                "description": "Generate data visualizations for health metrics and nutrition data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "chart_type": {
                            "type": "string",
                            "enum": ["weight_trend", "protein_comparison", "macronutrient_breakdown", 
                                    "calorie_trend", "activity_summary", "wellness_score"],
                            "description": "Type of chart to generate"
                        },
                        "time_period": {
                            "type": "string",
                            "enum": ["week", "month", "quarter"],
                            "description": "Time period for the visualization"
                        }
                    },
                    "required": ["chart_type"]
                }
            }
        ]
    
    def _validate_parameters(self, function_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate function call parameters and return structured error if invalid."""
        try:
            if function_name == "get_health_metrics":
                metric = arguments.get("metric_type")
                period = arguments.get("time_period", "current")
                if metric not in ["bmi", "weight", "wellness_score", "activity_level", "all"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid metric_type: {metric}"}}
                if period not in ["current", "weekly", "monthly", "quarterly"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid time_period: {period}"}}
            elif function_name == "get_meal_plan":
                frame = arguments.get("time_frame")
                meal_type = arguments.get("meal_type", "all")
                if frame not in ["today", "tomorrow", "week"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid time_frame: {frame}"}}
                if meal_type not in ["breakfast", "lunch", "dinner", "snack", "all"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid meal_type: {meal_type}"}}
            elif function_name == "get_nutrition_analysis":
                period = arguments.get("period")
                nutrient = arguments.get("nutrient", "all")
                if period not in ["today", "yesterday", "week", "month"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid period: {period}"}}
                if nutrient not in ["calories", "protein", "carbs", "fat", "fiber", "all"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid nutrient: {nutrient}"}}
            elif function_name == "get_recipe_info":
                if not arguments.get("recipe_identifier"):
                    return {"success": False, "error": {"code": "MISSING_PARAM", "message": "recipe_identifier is required"}}
                info_type = arguments.get("info_type", "all")
                if info_type not in ["ingredients", "instructions", "nutrition", "all"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid info_type: {info_type}"}}
            elif function_name == "get_activity_summary":
                period = arguments.get("time_period")
                activity_type = arguments.get("activity_type", "all")
                if period not in ["today", "week", "month"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid time_period: {period}"}}
                if activity_type not in ["cardio", "strength", "flexibility", "all"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid activity_type: {activity_type}"}}
            elif function_name == "get_progress_report":
                report_type = arguments.get("report_type")
                time_frame = arguments.get("time_frame", "month")
                if report_type not in ["weight", "nutrition", "wellness", "comprehensive"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid report_type: {report_type}"}}
                if time_frame not in ["week", "month", "quarter"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid time_frame: {time_frame}"}}
            elif function_name == "search_recipes":
                if not arguments.get("query"):
                    return {"success": False, "error": {"code": "MISSING_PARAM", "message": "query is required"}}
                filters = arguments.get("filters", {}) or {}
                if not isinstance(filters, dict):
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": "filters must be an object"}}
            elif function_name == "get_user_preferences":
                pref = arguments.get("preference_type")
                if pref not in ["dietary", "allergies", "targets", "all"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid preference_type: {pref}"}}
            elif function_name == "generate_visualization":
                chart = arguments.get("chart_type")
                period = arguments.get("time_period", "month")
                if chart not in ["weight_trend", "protein_comparison", "macronutrient_breakdown", "calorie_trend", "activity_summary", "wellness_score"]:
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid chart_type: {chart}"}}
                if period not in ["week", "month", "quarter"] and chart != "macronutrient_breakdown":
                    return {"success": False, "error": {"code": "INVALID_PARAM", "message": f"Invalid time_period: {period}"}}
        except Exception as e:
            return {"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(e)}}
        return None
    
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call and return results"""
        try:
            validation_error = self._validate_parameters(function_name, arguments)
            if validation_error:
                return validation_error
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
            elif function_name == "search_recipes":
                return self._search_recipes(**arguments)
            elif function_name == "get_user_preferences":
                return self._get_user_preferences(**arguments)
            elif function_name == "generate_visualization":
                return self._generate_visualization(**arguments)
            else:
                return {"success": False, "error": {"code": "UNKNOWN_FUNCTION", "message": f"Unknown function: {function_name}"}}
        except Exception as e:
            return {"success": False, "error": {"code": "FUNCTION_ERROR", "message": str(e)}}
    
    def _get_health_metrics(self, metric_type: str, time_period: str = "current") -> Dict[str, Any]:
        """Retrieve health metrics based on type and time period"""
        if not self.health_profile:
            return {"success": False, "error": {"code": "NO_PROFILE", "message": "No health profile found for user"}}
        
        result: Dict[str, Any] = {"success": True}
        
        if metric_type in ["weight", "all"]:
            if time_period == "current":
                result["weight"] = {
                    "value": float(self.health_profile.weight_kg) if self.health_profile.weight_kg else None,
                    "unit": "kg"
                }
            else:
                # Get weight history
                days = 7 if time_period == "weekly" else (30 if time_period == "monthly" else 90)
                start_date = timezone.now() - timedelta(days=days)
                weight_history = WeightHistory.objects.filter(
                    health_profile=self.health_profile,
                    recorded_at__gte=start_date
                ).order_by('recorded_at')
                
                if weight_history.exists():
                    weights = [{"date": w.recorded_at.isoformat(), "value": float(w.weight_kg)} for w in weight_history]
                    result["weight_history"] = weights
                    result["weight_change"] = round(float(weight_history.last().weight_kg - weight_history.first().weight_kg), 2)
                else:
                    result["weight_history"] = []
                    result["notice"] = "No weight data available for the selected period"
        
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
            ).order_by('-created_at').first()
            
            if latest_score:
                result["wellness_score"] = {
                    "total": float(latest_score.total_score),
                    "components": {
                        "activity": float(latest_score.activity_score),
                        "bmi": float(latest_score.bmi_score),
                        "progress": float(latest_score.progress_score),
                        "habits": float(latest_score.habits_score)
                    },
                    "recorded_at": latest_score.created_at.isoformat()
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
            return {"success": False, "error": {"code": "NO_PROFILE", "message": "No nutrition profile found for user"}}
        
        # Determine date range
        today = timezone.now().date()
        if time_frame == "today":
            start_date = end_date = today
        elif time_frame == "tomorrow":
            start_date = end_date = today + timedelta(days=1)
        else:  # week
            start_date = today
            end_date = today + timedelta(days=6)
        
        # Get active meal plans that cover this date range
        meal_plans = MealPlan.objects.filter(
            user=self.user,
            is_active=True,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).order_by('-created_at')
        
        result: Dict[str, Any] = {"success": True, "time_frame": time_frame, "meals": []}
        
        def _append_normalized_meal(date_key: str, mt: Optional[str], item: Dict[str, Any]):
            norm_mt = (mt or item.get('meal_type') or item.get('type') or '').lower() or None
            if meal_type != "all" and norm_mt != meal_type:
                return
            result["meals"].append({
                "date": date_key,
                "meal_type": norm_mt,
                "title": item.get('title') or (item.get('recipe') or {}).get('title'),
                "ready_in_minutes": item.get('readyInMinutes') or item.get('ready_in_minutes') or item.get('total_time_minutes') or (item.get('recipe') or {}).get('total_time_minutes'),
                "servings": item.get('servings') or (item.get('recipe') or {}).get('servings'),
                "nutrition_summary": {
                    "calories": item.get('calories_per_serving') or item.get('calories') or (item.get('recipe') or {}).get('calories_per_serving'),
                    "protein": item.get('protein_per_serving') or item.get('protein') or (item.get('recipe') or {}).get('protein_per_serving'),
                    "carbs": item.get('carbs_per_serving') or item.get('carbs') or (item.get('recipe') or {}).get('carbs_per_serving'),
                    "fat": item.get('fat_per_serving') or item.get('fat') or (item.get('recipe') or {}).get('fat_per_serving')
                }
            })
        
        # Iterate plans and collect meals from JSON structure
        for plan in meal_plans:
            data = plan.meal_plan_data or {}
            meals_by_date = data.get('meals')
            
            if isinstance(meals_by_date, dict):
                # New structure: { "meals": { "YYYY-MM-DD": [ {meal...}, ... ] } }
                current = start_date
                while current <= end_date:
                    date_key = current.isoformat()
                    day_meals = meals_by_date.get(date_key, [])
                    for m in day_meals or []:
                        _append_normalized_meal(date_key, (m.get('meal_type') or m.get('type')), m)
                    current += timedelta(days=1)
                continue
            
            # Legacy structure: top-level keys are dates with nested meal types { breakfast: {recipe: {...}}, ... }
            # Example: meal_plan_data[date][meal_type] = { recipe: {...} }
            # Detect legacy: keys look like dates
            possible_dates = [k for k, v in (data.items() if isinstance(data, dict) else []) if isinstance(k, str) and len(k) == 10 and k[4] == '-' and k[7] == '-']
            if possible_dates:
                current = start_date
                while current <= end_date:
                    date_key = current.isoformat()
                    day_block = data.get(date_key, {}) if isinstance(data, dict) else {}
                    if isinstance(day_block, dict):
                        for mt in ["breakfast", "lunch", "dinner", "snack"]:
                            entry = day_block.get(mt)
                            if isinstance(entry, dict):
                                # Normalize legacy entry to common shape
                                payload = {
                                    "meal_type": mt,
                                    **(({"recipe": entry.get('recipe')} if entry.get('recipe') else entry))
                                }
                                _append_normalized_meal(date_key, mt, payload)
                    current += timedelta(days=1)
        
        if not result["meals"]:
            return {"success": True, "message": "No meals found for the selected time frame.", "time_frame": time_frame, "meals": []}
        
        return result
    
    def _get_nutrition_analysis(self, period: str, nutrient: str = "all") -> Dict[str, Any]:
        """Analyze nutritional intake for specified period"""
        if not self.nutrition_profile:
            return {"success": False, "error": {"code": "NO_PROFILE", "message": "No nutrition profile found for user"}}
        
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
        
        result: Dict[str, Any] = {
            "success": True,
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
            daily_totals: Dict[str, Dict[str, float]] = {}
            for log in logs:
                date_key = log.date.isoformat()
                if date_key not in daily_totals:
                    daily_totals[date_key] = {
                        "calories": 0.0,
                        "protein": 0.0,
                        "carbs": 0.0,
                        "fat": 0.0,
                        "fiber": 0.0,
                    }
                daily_totals[date_key]["calories"] += float(log.total_calories or 0)
                daily_totals[date_key]["protein"] += float(log.total_protein or 0)
                daily_totals[date_key]["carbs"] += float(log.total_carbs or 0)
                daily_totals[date_key]["fat"] += float(log.total_fat or 0)
                daily_totals[date_key]["fiber"] += float(log.total_fiber or 0)
            
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
                result["notice"] = "No nutrition logs found for the selected period"
        else:
            nutrient_data = []
            field_map = {
                "calories": "total_calories",
                "protein": "total_protein",
                "carbs": "total_carbs",
                "fat": "total_fat",
                "fiber": "total_fiber",
            }
            field_name = field_map.get(nutrient, nutrient)
            for log in logs:
                value = float(getattr(log, field_name, 0) or 0)
                nutrient_data.append({
                    "date": log.date.isoformat(),
                    "value": value
                })
            result[nutrient] = nutrient_data
            if nutrient_data:
                result[f"{nutrient}_average"] = round(
                    sum(d["value"] for d in nutrient_data) / len(nutrient_data), 1
                )
            else:
                result["notice"] = "No nutrition logs found for the selected period"
        
        return result
    
    def _get_recipe_info(self, recipe_identifier: str, info_type: str = "all") -> Dict[str, Any]:
        """Get detailed recipe information"""
        # Try to identify recipe by context
        recipe = None
        
        # Check if it's a reference to a meal time
        ident = recipe_identifier.lower()
        target_meal_type = None
        if "dinner" in ident or "tonight" in ident:
            target_meal_type = "dinner"
        elif "lunch" in ident:
            target_meal_type = "lunch"
        elif "breakfast" in ident:
            target_meal_type = "breakfast"
        
        if target_meal_type:
            today = timezone.now().date().isoformat()
            # Look for the latest active plan covering today, then pull from JSON meals
            plan = MealPlan.objects.filter(
                user=self.user,
                is_active=True,
                start_date__lte=timezone.now().date(),
                end_date__gte=timezone.now().date()
            ).order_by('-created_at').first()
            if plan and isinstance(plan.meal_plan_data, dict):
                day_meals = (plan.meal_plan_data or {}).get('meals', {}).get(today, [])
                for m in day_meals:
                    mt = (m.get('meal_type') or m.get('type') or '').lower()
                    if mt == target_meal_type:
                        # Build a pseudo-recipe dict from meal JSON
                        return self._format_meal_json_as_recipe(m, info_type)
        
        # Fallback: try to find by recipe name in DB
        recipe = Recipe.objects.filter(
            title__icontains=recipe_identifier
        ).first()
        
        if not recipe:
            return {"success": False, "error": {"code": "NOT_FOUND", "message": f"Recipe not found for: {recipe_identifier}"}}
        
        result = {
            "success": True,
            "recipe": {
                "title": recipe.title,
                "ready_in_minutes": getattr(recipe, 'total_time_minutes', None),
                "servings": recipe.servings,
                "source_url": getattr(recipe, 'source_url', '')
            }
        }
        
        if info_type in ["ingredients", "all"]:
            result["ingredients"] = recipe.ingredients_data
        
        if info_type in ["instructions", "all"]:
            result["instructions"] = recipe.instructions
        
        if info_type in ["nutrition", "all"]:
            result["nutrition"] = {
                "calories": getattr(recipe, 'calories_per_serving', None),
                "protein": getattr(recipe, 'protein_per_serving', None),
                "carbs": getattr(recipe, 'carbs_per_serving', None),
                "fat": getattr(recipe, 'fat_per_serving', None),
                "fiber": getattr(recipe, 'fiber_per_serving', None),
            }
        
        return result

    def _format_meal_json_as_recipe(self, meal_json: Dict[str, Any], info_type: str) -> Dict[str, Any]:
        """Convert a meal JSON entry from meal_plan_data into the standard recipe response shape."""
        result = {
            "recipe": {
                "title": meal_json.get('title'),
                "ready_in_minutes": meal_json.get('readyInMinutes') or meal_json.get('ready_in_minutes'),
                "servings": meal_json.get('servings'),
                "source_url": meal_json.get('sourceUrl') or meal_json.get('source_url')
            }
        }
        if info_type in ["ingredients", "all"]:
            # ingredients_data is a list of { original: str }
            result["ingredients"] = meal_json.get('ingredients_data') or meal_json.get('ingredients') or []
        if info_type in ["instructions", "all"]:
            # instructions is a list of { step: str } or strings
            result["instructions"] = meal_json.get('instructions') or []
        if info_type in ["nutrition", "all"]:
            result["nutrition"] = {
                "calories": meal_json.get('calories_per_serving') or meal_json.get('calories'),
                "protein": meal_json.get('protein_per_serving') or meal_json.get('protein'),
                "carbs": meal_json.get('carbs_per_serving') or meal_json.get('carbs'),
                "fat": meal_json.get('fat_per_serving') or meal_json.get('fat')
            }
        return result
    
    def _get_activity_summary(self, time_period: str, activity_type: str = "all") -> Dict[str, Any]:
        """Get activity summary for specified period"""
        if not self.health_profile:
            return {"success": False, "error": {"code": "NO_PROFILE", "message": "No health profile found for user"}}
        
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
            "success": True,
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
    
    def _get_progress_report(self, report_type: str, time_frame: str = "month") -> Dict[str, Any]:
        """Generate comprehensive progress report comparing current metrics to goals"""
        if not self.health_profile:
            return {"success": False, "error": {"code": "NO_PROFILE", "message": "No health profile found for user"}}
        
        result: Dict[str, Any] = {"success": True, "report_type": report_type, "time_frame": time_frame, "progress": {}}
        
        # Determine date range
        today = timezone.now()
        if time_frame == "week":
            start_date = today - timedelta(days=7)
        elif time_frame == "month":
            start_date = today - timedelta(days=30)
        else:  # quarter
            start_date = today - timedelta(days=90)
        
        if report_type in ["weight", "comprehensive"]:
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
                    
                    weight_history = WeightHistory.objects.filter(
                        health_profile=self.health_profile,
                        recorded_at__gte=start_date
                    ).order_by('recorded_at')
                    
                    if weight_history.count() > 1:
                        period_change = float(weight_history.last().weight_kg - weight_history.first().weight_kg)
                        result["progress"]["weight"][f"{time_frame}_change"] = round(period_change, 1)
                        result["progress"]["weight"]["trend"] = "losing" if period_change < 0 else "gaining"
        
        if report_type in ["wellness", "comprehensive"]:
            wellness_scores = WellnessScore.objects.filter(
                health_profile=self.health_profile,
                created_at__gte=start_date
            ).order_by('created_at')
            
            if wellness_scores.exists():
                latest_score = wellness_scores.last()
                first_score = wellness_scores.first()
                
                result["progress"]["wellness"] = {
                    "current_score": float(latest_score.total_score),
                    "components": {
                        "activity": float(latest_score.activity_score),
                        "bmi": float(latest_score.bmi_score),
                        "progress": float(latest_score.progress_score),
                        "habits": float(latest_score.habits_score)
                    },
                    "change": float(latest_score.total_score) - float(first_score.total_score),
                    "trend": "improving" if float(latest_score.total_score) > float(first_score.total_score) else "declining"
                }
        
        if report_type in ["nutrition", "comprehensive"] and self.nutrition_profile:
            logs = NutritionLog.objects.filter(
                user=self.user,
                date__gte=start_date.date()
            )
            
            if logs.exists():
                total_days = logs.values('date').distinct().count()
                avg_calories = logs.aggregate(Avg('total_calories'))['total_calories__avg'] or 0
                avg_protein = logs.aggregate(Avg('total_protein'))['total_protein__avg'] or 0
                
                result["progress"]["nutrition"] = {
                    "average_calories": round(avg_calories),
                    "calorie_target": self.nutrition_profile.calorie_target,
                    "average_protein": round(avg_protein, 1),
                    "protein_target": self.nutrition_profile.protein_target,
                    "days_logged": total_days,
                }
                if (today - start_date).days > 0:
                    result["progress"]["nutrition"]["consistency_rate"] = round((total_days / (today - start_date).days) * 100)
        
        # Attach personalized recommendations based on progress
        recommendations = self._generate_recommendations(result["progress"]) or []
        if recommendations:
            result["recommendations"] = recommendations
        
        return result
    
    def _generate_recommendations(self, progress: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on progress"""
        recommendations: List[str] = []
        
        weight_data = progress.get("weight")
        if weight_data and weight_data.get("status") == "needs_attention":
            if weight_data.get("difference", 0) > 0:
                recommendations.append("Consider increasing daily activity or modestly reducing calorie intake to support your weight goal.")
            else:
                recommendations.append("You're below your target weight. Emphasize nutrient-dense foods to reach your goal healthily.")
        
        nutrition_data = progress.get("nutrition")
        if nutrition_data:
            avg_cals = nutrition_data.get("average_calories")
            cal_target = nutrition_data.get("calorie_target")
            if avg_cals and cal_target:
                adherence = (avg_cals / cal_target) * 100
                if adherence < 90:
                    recommendations.append("Increase daily calories slightly to align closer to your target for consistent energy and recovery.")
                elif adherence > 110:
                    recommendations.append("Reduce daily calories slightly to stay within ~10% of your target for steady progress.")
            avg_protein = nutrition_data.get("average_protein")
            protein_target = nutrition_data.get("protein_target")
            if avg_protein and protein_target and avg_protein < protein_target * 0.8:
                recommendations.append("Add a protein-rich snack (e.g., Greek yogurt, cottage cheese, tofu) to increase protein intake.")
        
        wellness = progress.get("wellness")
        if wellness and isinstance(wellness.get("components"), dict):
            comps = wellness["components"]
            lowest = min(comps, key=comps.get)
            if lowest == "sleep":
                recommendations.append("Prioritize 7–9 hours of sleep; keep a consistent schedule and limit screens 60 minutes before bed.")
            elif lowest == "activity":
                recommendations.append("Aim for at least 150 minutes/week of moderate activity; add 10–15 minute walks after meals.")
            elif lowest == "nutrition":
                recommendations.append("Increase fiber and lean protein across meals; plan meals to hit macro targets more consistently.")
            elif lowest == "mental":
                recommendations.append("Incorporate short mindfulness breaks (5–10 minutes) and schedule enjoyable, restorative activities.")
        
        return recommendations
    
    def _search_recipes(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for recipes based on query and filters"""
        try:
            recipes = Recipe.objects.filter(
                Q(title__icontains=query) | Q(ingredients_data__icontains=query)
            )
            
            # Apply filters if provided
            if filters:
                if "max_calories" in filters:
                    recipes = recipes.filter(calories_per_serving__lte=filters["max_calories"])
                if "min_protein" in filters:
                    recipes = recipes.filter(protein_per_serving__gte=filters["min_protein"])
                if "diet" in filters and filters["diet"] != "any":
                    diet_mapping = {
                        "vegetarian": "vegetarian",
                        "vegan": "vegan", 
                        "keto": "keto",
                        "paleo": "paleo"
                    }
                    if filters["diet"] in diet_mapping:
                        recipes = recipes.filter(dietary_tags__contains=[diet_mapping[filters["diet"]]])
            
            recipes = recipes[:10]
            
            result = {"success": True, "recipes": []}
            for recipe in recipes:
                recipe_data = {
                    "id": str(recipe.id),
                    "title": recipe.title,
                    "ready_in_minutes": getattr(recipe, 'total_time_minutes', None),
                    "servings": recipe.servings,
                    "nutrition": {
                        "calories": getattr(recipe, 'calories_per_serving', None),
                        "protein": getattr(recipe, 'protein_per_serving', None),
                        "carbs": getattr(recipe, 'carbs_per_serving', None),
                        "fat": getattr(recipe, 'fat_per_serving', None)
                    }
                }
                
                if self.nutrition_profile and self.nutrition_profile.dietary_preferences:
                    matches_preferences = any(
                        pref in (recipe.dietary_tags or []) 
                        for pref in self.nutrition_profile.dietary_preferences
                    )
                    recipe_data["matches_preferences"] = matches_preferences
                
                result["recipes"].append(recipe_data)
            
            result["total_found"] = len(result["recipes"])
            return result
            
        except Exception as e:
            return {"success": False, "error": {"code": "SEARCH_FAILED", "message": f"Search failed: {str(e)}"}}
    
    def _get_user_preferences(self, preference_type: str) -> Dict[str, Any]:
        """Get user's dietary preferences, allergies, and targets"""
        result: Dict[str, Any] = {"success": True}
        
        if preference_type in ["dietary", "all"]:
            if self.nutrition_profile:
                result["dietary_preferences"] = {
                    "preferences": self.nutrition_profile.dietary_preferences,
                    "cuisine_preferences": self.nutrition_profile.cuisine_preferences,
                    "disliked_ingredients": self.nutrition_profile.disliked_ingredients,
                    "meals_per_day": self.nutrition_profile.meals_per_day,
                    "snacks_per_day": self.nutrition_profile.snacks_per_day
                }
            else:
                result["dietary_preferences"] = {"error": "No nutrition profile found"}
        
        if preference_type in ["allergies", "all"]:
            if self.nutrition_profile:
                result["allergies_intolerances"] = self.nutrition_profile.allergies_intolerances
            else:
                result["allergies_intolerances"] = []
        
        if preference_type in ["targets", "all"]:
            if self.nutrition_profile:
                result["nutrition_targets"] = {
                    "calorie_target": self.nutrition_profile.calorie_target,
                    "protein_target": self.nutrition_profile.protein_target,
                    "carb_target": self.nutrition_profile.carb_target,
                    "fat_target": self.nutrition_profile.fat_target
                }
                
                # Add health targets if available
                if self.health_profile:
                    result["health_targets"] = {
                        "target_weight": float(self.health_profile.target_weight_kg) if self.health_profile.target_weight_kg else None,
                        "fitness_goal": self.health_profile.get_fitness_goal_display(),
                        "activity_level": self.health_profile.get_activity_level_display()
                    }
            else:
                result["nutrition_targets"] = {"error": "No nutrition profile found"}
        
        return result

    def _generate_visualization(self, chart_type: str, time_period: str = "month") -> Dict[str, Any]:
        """Generate data visualizations for health metrics and nutrition data"""
        try:
            viz_service = VisualizationService(self.user)
            
            # Map chart types to visualization service methods
            chart_mapping = {
                "weight_trend": viz_service._generate_weight_trend_chart,
                "protein_comparison": viz_service._generate_protein_comparison_chart,
                "macronutrient_breakdown": viz_service._generate_macronutrient_breakdown_chart,
                "calorie_trend": viz_service._generate_calorie_trend_chart,
                "activity_summary": viz_service._generate_activity_chart,
                "wellness_score": viz_service._generate_wellness_score_chart
            }
            
            if chart_type not in chart_mapping:
                return {"success": False, "error": {"code": "UNKNOWN_CHART_TYPE", "message": f"Unknown chart type: {chart_type}"}}
            
            # Call the appropriate method
            if chart_type == "macronutrient_breakdown":
                # This method doesn't take time_period
                result = chart_mapping[chart_type]()
            else:
                result = chart_mapping[chart_type](time_period)
            
            # Add metadata for the AI to describe the chart
            if "error" not in result:
                result["success"] = True
                result["visualization_ready"] = True
                result["description"] = self._get_chart_description(chart_type, time_period)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": {"code": "GENERATE_VISUALIZATION_FAILED", "message": f"Failed to generate visualization: {str(e)}"}}
    
    def _get_chart_description(self, chart_type: str, time_period: str) -> str:
        """Get a description of what the chart shows"""
        descriptions = {
            "weight_trend": f"This chart shows your weight changes over the past {time_period}",
            "protein_comparison": f"This chart compares your protein intake to your target over the past {time_period}",
            "macronutrient_breakdown": "This chart shows the breakdown of your macronutrients (protein, carbs, fat) for today",
            "calorie_trend": f"This chart displays your calorie intake trend over the past {time_period}",
            "activity_summary": f"This chart summarizes your physical activities over the past {time_period}",
            "wellness_score": f"This chart tracks your overall wellness score components over the past {time_period}"
        }
        return descriptions.get(chart_type, "Data visualization generated")