import openai
import logging
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from decouple import config
from ..models import NutritionProfile
from datetime import datetime, timedelta, date
import json

logger = logging.getLogger('nutrition.enhanced_profile_service')


class EnhancedNutritionProfileService:
    """
    Advanced nutrition profile analysis service that uses AI to optimize
    nutrition targets based on user goals, health metrics, and lifestyle factors.
    """

    def __init__(self):
        openai.api_key = config('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"

    def analyze_and_optimize_profile(self, nutrition_profile: NutritionProfile, 
                                   force_recalculate: bool = False) -> Dict:
        """
        Analyze user's complete profile and provide optimized nutrition recommendations
        
        Args:
            nutrition_profile: User's nutrition profile
            force_recalculate: Whether to force recalculation even if recent analysis exists
            
        Returns:
            Comprehensive nutrition analysis with optimized targets
        """
        try:
            logger.info(f"Analyzing nutrition profile for user {nutrition_profile.user.id}")
            
            # Get comprehensive user context
            user_context = self._build_comprehensive_context(nutrition_profile)
            
            # Perform AI-driven analysis
            ai_analysis = self._perform_ai_nutrition_analysis(user_context)
            
            # Calculate optimized nutrition targets
            optimized_targets = self._calculate_optimized_targets(ai_analysis, nutrition_profile)
            
            # Generate personalized recommendations
            recommendations = self._generate_personalized_recommendations(ai_analysis, nutrition_profile)
            
            # Create comprehensive analysis report
            analysis_report = {
                'user_context': user_context,
                'ai_analysis': ai_analysis,
                'optimized_targets': optimized_targets,
                'recommendations': recommendations,
                'analysis_date': datetime.now().isoformat(),
                'confidence_score': self._calculate_confidence_score(ai_analysis, user_context)
            }
            
            logger.info("Successfully completed nutrition profile analysis")
            return analysis_report
            
        except Exception as e:
            logger.error(f"Error analyzing nutrition profile: {str(e)}")
            return self._generate_fallback_analysis(nutrition_profile)

    def get_dynamic_macro_distribution(self, nutrition_profile: NutritionProfile, 
                                     fitness_goal: str = None, activity_level: str = None) -> Dict:
        """
        Get dynamically adjusted macro distribution based on specific goals and activity
        
        Args:
            nutrition_profile: User's nutrition profile
            fitness_goal: Override fitness goal (optional)
            activity_level: Override activity level (optional)
            
        Returns:
            Optimized macro distribution percentages
        """
        try:
            # Get user context with overrides
            context = self._build_context_with_overrides(nutrition_profile, fitness_goal, activity_level)
            
            # Use AI to determine optimal macro distribution
            macro_analysis = self._analyze_macro_distribution(context)
            
            return macro_analysis
            
        except Exception as e:
            logger.warning(f"Dynamic macro distribution failed: {str(e)}. Using rule-based fallback.")
            return self._get_rule_based_macro_distribution(nutrition_profile, fitness_goal, activity_level)

    def calculate_adjusted_calorie_needs(self, nutrition_profile: NutritionProfile, 
                                       custom_factors: Dict = None) -> Dict:
        """
        Calculate precisely adjusted calorie needs using AI analysis
        
        Args:
            nutrition_profile: User's nutrition profile
            custom_factors: Additional factors to consider
            
        Returns:
            Detailed calorie needs analysis
        """
        try:
            health_profile = getattr(nutrition_profile.user, 'health_profile', None)
            
            # Build calorie calculation context
            context = {
                'current_targets': {
                    'calories': nutrition_profile.calorie_target,
                    'protein': nutrition_profile.protein_target,
                    'carbs': nutrition_profile.carb_target,
                    'fat': nutrition_profile.fat_target
                },
                'user_metrics': self._extract_user_metrics(health_profile),
                'lifestyle_factors': self._extract_lifestyle_factors(nutrition_profile),
                'goals': self._extract_user_goals(health_profile),
                'custom_factors': custom_factors or {}
            }
            
            # Use AI to analyze calorie needs
            calorie_analysis = self._perform_calorie_analysis(context)
            
            return calorie_analysis
            
        except Exception as e:
            logger.warning(f"Calorie analysis failed: {str(e)}. Using standard calculation.")
            return self._calculate_standard_calories(nutrition_profile)

    def generate_nutrition_strategy(self, nutrition_profile: NutritionProfile, 
                                  meal_plan_duration: int = 7) -> Dict:
        """
        Generate comprehensive nutrition strategy for meal planning
        
        Args:
            nutrition_profile: User's nutrition profile
            meal_plan_duration: Duration in days for the strategy
            
        Returns:
            Comprehensive nutrition strategy
        """
        try:
            # Get complete analysis
            profile_analysis = self.analyze_and_optimize_profile(nutrition_profile)
            
            # Generate strategy using AI
            strategy_prompt = f"""
            Create a comprehensive nutrition strategy for meal planning based on this analysis:

            USER ANALYSIS:
            {json.dumps(profile_analysis, indent=2)}

            MEAL PLAN DURATION: {meal_plan_duration} days

            Generate a detailed strategy in JSON format:
            {{
                "nutrition_philosophy": {{
                    "primary_approach": "main nutritional approach based on user goals",
                    "key_principles": ["core principles guiding food choices"],
                    "success_factors": ["factors most important for user success"]
                }},
                "meal_timing_strategy": {{
                    "optimal_schedule": "recommended meal timing pattern",
                    "pre_workout": "pre-workout nutrition if applicable",
                    "post_workout": "post-workout nutrition if applicable",
                    "meal_distribution": {{
                        "breakfast_percent": "percentage of daily calories",
                        "lunch_percent": "percentage of daily calories",
                        "dinner_percent": "percentage of daily calories",
                        "snack_percent": "percentage of daily calories if applicable"
                    }}
                }},
                "food_selection_strategy": {{
                    "prioritized_foods": ["foods to emphasize"],
                    "limited_foods": ["foods to limit or avoid"],
                    "cooking_methods": ["preferred cooking methods"],
                    "portion_control": "strategy for managing portions"
                }},
                "adaptation_guidelines": {{
                    "flexibility_rules": ["how to adapt the plan when needed"],
                    "substitution_principles": ["how to make healthy substitutions"],
                    "dining_out_tips": ["tips for maintaining nutrition when eating out"]
                }},
                "monitoring_metrics": {{
                    "key_indicators": ["what to track for success"],
                    "adjustment_triggers": ["when to modify the plan"],
                    "progress_milestones": ["milestones to celebrate"]
                }}
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": strategy_prompt}],
                max_tokens=1200,
                temperature=0.3
            )

            strategy_text = response.choices[0].message.content
            try:
                strategy = json.loads(strategy_text)
                strategy['generated_date'] = datetime.now().isoformat()
                strategy['profile_analysis'] = profile_analysis
                return strategy
            except json.JSONDecodeError:
                return self._generate_default_strategy(nutrition_profile, profile_analysis)

        except Exception as e:
            logger.error(f"Strategy generation failed: {str(e)}")
            return self._generate_fallback_strategy(nutrition_profile)

    # === CORE ANALYSIS METHODS ===

    def _build_comprehensive_context(self, nutrition_profile: NutritionProfile) -> Dict:
        """Build comprehensive context for AI analysis"""
        health_profile = getattr(nutrition_profile.user, 'health_profile', None)
        
        context = {
            'user_info': {
                'age': health_profile.age if health_profile else None,
                'gender': health_profile.get_gender_display() if health_profile and hasattr(health_profile, 'get_gender_display') else (health_profile.gender if health_profile else None),
                'weight_kg': float(health_profile.weight_kg) if health_profile and health_profile.weight_kg else None,
                'height_cm': float(health_profile.height_cm) if health_profile and health_profile.height_cm else None,
                'bmi': health_profile.calculate_bmi() if health_profile and hasattr(health_profile, 'calculate_bmi') else None,
                'activity_level': health_profile.get_activity_level_display() if health_profile and hasattr(health_profile, 'get_activity_level_display') else (health_profile.activity_level if health_profile else None),
                'fitness_goal': health_profile.get_fitness_goal_display() if health_profile and hasattr(health_profile, 'get_fitness_goal_display') else (health_profile.fitness_goal if health_profile else None),
                'target_weight_kg': float(health_profile.target_weight_kg) if health_profile and health_profile.target_weight_kg else None
            },
            'current_nutrition_targets': {
                'calories': nutrition_profile.calorie_target,
                'protein': nutrition_profile.protein_target,
                'carbs': nutrition_profile.carb_target,
                'fat': nutrition_profile.fat_target
            },
            'dietary_preferences': {
                'preferences': nutrition_profile.dietary_preferences or [],
                'allergies_intolerances': nutrition_profile.allergies_intolerances or [],
                'cuisine_preferences': nutrition_profile.cuisine_preferences or [],
                'disliked_ingredients': nutrition_profile.disliked_ingredients or []
            },
            'meal_patterns': {
                'meals_per_day': nutrition_profile.meals_per_day,
                'snacks_per_day': nutrition_profile.snacks_per_day,
                'breakfast_time': nutrition_profile.breakfast_time.strftime('%H:%M') if nutrition_profile.breakfast_time else None,
                'lunch_time': nutrition_profile.lunch_time.strftime('%H:%M') if nutrition_profile.lunch_time else None,
                'dinner_time': nutrition_profile.dinner_time.strftime('%H:%M') if nutrition_profile.dinner_time else None,
                'timezone': str(nutrition_profile.timezone) if nutrition_profile.timezone else None
            }
        }
        
        return context

    def _perform_ai_nutrition_analysis(self, user_context: Dict) -> Dict:
        """Perform comprehensive AI nutrition analysis"""
        try:
            analysis_prompt = f"""
            As a certified nutritionist and dietitian, perform a comprehensive analysis of this user's profile:

            USER PROFILE:
            {json.dumps(user_context, indent=2)}

            Provide a detailed nutritional analysis in JSON format:
            {{
                "metabolic_analysis": {{
                    "bmr_assessment": "assessment of basal metabolic rate needs",
                    "tdee_estimate": "total daily energy expenditure estimate",
                    "metabolic_factors": ["factors affecting metabolism"],
                    "calorie_adjustment_needed": "whether current calories need adjustment"
                }},
                "macro_optimization": {{
                    "protein_needs": {{
                        "recommended_grams": "optimal protein intake in grams",
                        "rationale": "scientific rationale for protein recommendation"
                    }},
                    "carbohydrate_needs": {{
                        "recommended_grams": "optimal carb intake in grams", 
                        "rationale": "scientific rationale for carb recommendation"
                    }},
                    "fat_needs": {{
                        "recommended_grams": "optimal fat intake in grams",
                        "rationale": "scientific rationale for fat recommendation"
                    }}
                }},
                "goal_alignment": {{
                    "primary_nutrition_goal": "main goal based on user profile",
                    "timeline_realistic": "realistic timeline for achieving goals",
                    "key_strategies": ["specific strategies for this user"],
                    "potential_challenges": ["challenges this user might face"]
                }},
                "health_considerations": {{
                    "bmi_assessment": "assessment of current BMI and implications",
                    "activity_match": "how well nutrition aligns with activity level",
                    "dietary_restriction_impact": "impact of dietary restrictions on nutrition",
                    "recommendations": ["specific health-based recommendations"]
                }},
                "optimization_priorities": {{
                    "immediate_priorities": ["most important changes to make now"],
                    "long_term_goals": ["goals to work toward over time"],
                    "success_indicators": ["metrics that indicate success"]
                }}
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=1500,
                temperature=0.3
            )

            analysis_text = response.choices[0].message.content
            try:
                return json.loads(analysis_text)
            except json.JSONDecodeError:
                return self._parse_analysis_fallback(analysis_text)

        except Exception as e:
            logger.warning(f"AI nutrition analysis failed: {str(e)}")
            return self._generate_rule_based_analysis(user_context)

    def _calculate_optimized_targets(self, ai_analysis: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Calculate optimized nutrition targets based on AI analysis"""
        try:
            # Extract recommendations from AI analysis
            macro_optimization = ai_analysis.get('macro_optimization', {})
            metabolic_analysis = ai_analysis.get('metabolic_analysis', {})
            
            # Calculate optimized calories
            current_calories = nutrition_profile.calorie_target
            calorie_adjustment = metabolic_analysis.get('calorie_adjustment_needed', 'maintain current')
            
            if 'increase' in calorie_adjustment.lower():
                optimized_calories = int(current_calories * 1.1)  # 10% increase
            elif 'decrease' in calorie_adjustment.lower():
                optimized_calories = int(current_calories * 0.9)  # 10% decrease
            else:
                optimized_calories = current_calories
            
            # Extract macro recommendations
            protein_rec = macro_optimization.get('protein_needs', {})
            carb_rec = macro_optimization.get('carbohydrate_needs', {})
            fat_rec = macro_optimization.get('fat_needs', {})
            
            try:
                optimized_protein = float(protein_rec.get('recommended_grams', nutrition_profile.protein_target))
                optimized_carbs = float(carb_rec.get('recommended_grams', nutrition_profile.carb_target))
                optimized_fat = float(fat_rec.get('recommended_grams', nutrition_profile.fat_target))
            except (ValueError, TypeError):
                # Fallback to current targets
                optimized_protein = nutrition_profile.protein_target
                optimized_carbs = nutrition_profile.carb_target
                optimized_fat = nutrition_profile.fat_target
            
            return {
                'calories': optimized_calories,
                'protein': round(optimized_protein, 1),
                'carbs': round(optimized_carbs, 1),
                'fat': round(optimized_fat, 1),
                'optimization_rationale': {
                    'protein': protein_rec.get('rationale', 'Maintaining current protein target'),
                    'carbs': carb_rec.get('rationale', 'Maintaining current carb target'),
                    'fat': fat_rec.get('rationale', 'Maintaining current fat target'),
                    'calories': f"Calories adjusted based on metabolic analysis: {calorie_adjustment}"
                }
            }

        except Exception as e:
            logger.warning(f"Target optimization failed: {str(e)}")
            return self._get_current_targets(nutrition_profile)

    def _generate_personalized_recommendations(self, ai_analysis: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Generate personalized recommendations based on analysis"""
        try:
            optimization_priorities = ai_analysis.get('optimization_priorities', {})
            health_considerations = ai_analysis.get('health_considerations', {})
            goal_alignment = ai_analysis.get('goal_alignment', {})
            
            return {
                'immediate_actions': optimization_priorities.get('immediate_priorities', []),
                'long_term_goals': optimization_priorities.get('long_term_goals', []),
                'health_recommendations': health_considerations.get('recommendations', []),
                'success_strategies': goal_alignment.get('key_strategies', []),
                'potential_challenges': goal_alignment.get('potential_challenges', []),
                'monitoring_suggestions': optimization_priorities.get('success_indicators', [])
            }

        except Exception as e:
            logger.warning(f"Recommendation generation failed: {str(e)}")
            return self._generate_basic_recommendations(nutrition_profile)

    def _analyze_macro_distribution(self, context: Dict) -> Dict:
        """Analyze optimal macro distribution using AI"""
        try:
            macro_prompt = f"""
            Determine the optimal macronutrient distribution for this user:

            USER CONTEXT:
            {json.dumps(context, indent=2)}

            Provide optimal macro percentages in JSON format:
            {{
                "protein_percent": "optimal protein percentage of total calories",
                "carbohydrate_percent": "optimal carb percentage of total calories",
                "fat_percent": "optimal fat percentage of total calories",
                "rationale": {{
                    "protein": "scientific rationale for protein percentage",
                    "carbs": "scientific rationale for carb percentage", 
                    "fat": "scientific rationale for fat percentage"
                }},
                "timing_considerations": {{
                    "pre_workout": "macro emphasis before workouts",
                    "post_workout": "macro emphasis after workouts",
                    "evening": "macro considerations for evening meals"
                }},
                "adjustment_factors": ["factors that might require macro adjustments"]
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": macro_prompt}],
                max_tokens=600,
                temperature=0.3
            )

            macro_text = response.choices[0].message.content
            try:
                return json.loads(macro_text)
            except json.JSONDecodeError:
                return self._get_default_macro_distribution()

        except Exception as e:
            logger.warning(f"Macro analysis failed: {str(e)}")
            return self._get_default_macro_distribution()

    def _perform_calorie_analysis(self, context: Dict) -> Dict:
        """Perform detailed calorie needs analysis"""
        try:
            calorie_prompt = f"""
            Analyze precise calorie needs for this user:

            CONTEXT:
            {json.dumps(context, indent=2)}

            Provide detailed calorie analysis in JSON format:
            {{
                "bmr_calculation": {{
                    "estimated_bmr": "estimated basal metabolic rate",
                    "calculation_method": "method used for calculation"
                }},
                "activity_adjustment": {{
                    "activity_multiplier": "multiplier for activity level",
                    "total_daily_expenditure": "estimated TDEE"
                }},
                "goal_adjustment": {{
                    "goal_modifier": "adjustment for specific goals",
                    "recommended_calories": "final recommended daily calories"
                }},
                "calorie_distribution": {{
                    "minimum_safe": "minimum safe calories for this user",
                    "maximum_effective": "maximum effective calories for goals",
                    "optimal_range": "optimal calorie range"
                }},
                "factors_considered": ["factors that influenced the calculation"]
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": calorie_prompt}],
                max_tokens=600,
                temperature=0.3
            )

            calorie_text = response.choices[0].message.content
            try:
                return json.loads(calorie_text)
            except json.JSONDecodeError:
                return self._get_default_calorie_analysis(context)

        except Exception as e:
            logger.warning(f"Calorie analysis failed: {str(e)}")
            return self._get_default_calorie_analysis(context)

    # === HELPER METHODS ===

    def _build_context_with_overrides(self, nutrition_profile: NutritionProfile, 
                                    fitness_goal: str = None, activity_level: str = None) -> Dict:
        """Build context with optional overrides"""
        context = self._build_comprehensive_context(nutrition_profile)
        
        if fitness_goal:
            context['user_info']['fitness_goal'] = fitness_goal
        if activity_level:
            context['user_info']['activity_level'] = activity_level
            
        return context

    def _extract_user_metrics(self, health_profile) -> Dict:
        """Extract key user metrics from health profile"""
        if not health_profile:
            return {}
            
        return {
            'age': health_profile.age,
            'weight_kg': float(health_profile.weight_kg) if health_profile.weight_kg else None,
            'height_cm': float(health_profile.height_cm) if health_profile.height_cm else None,
            'bmi': health_profile.calculate_bmi() if hasattr(health_profile, 'calculate_bmi') else None,
            'gender': health_profile.gender
        }

    def _extract_lifestyle_factors(self, nutrition_profile: NutritionProfile) -> Dict:
        """Extract lifestyle factors from nutrition profile"""
        return {
            'meal_frequency': nutrition_profile.meals_per_day,
            'snack_frequency': nutrition_profile.snacks_per_day,
            'meal_timing': {
                'breakfast': nutrition_profile.breakfast_time.strftime('%H:%M') if nutrition_profile.breakfast_time else None,
                'lunch': nutrition_profile.lunch_time.strftime('%H:%M') if nutrition_profile.lunch_time else None,
                'dinner': nutrition_profile.dinner_time.strftime('%H:%M') if nutrition_profile.dinner_time else None
            },
            'dietary_restrictions': nutrition_profile.dietary_preferences + nutrition_profile.allergies_intolerances
        }

    def _extract_user_goals(self, health_profile) -> Dict:
        """Extract user goals from health profile"""
        if not health_profile:
            return {}
            
        return {
            'fitness_goal': health_profile.fitness_goal if hasattr(health_profile, 'fitness_goal') else None,
            'target_weight': float(health_profile.target_weight_kg) if hasattr(health_profile, 'target_weight_kg') and health_profile.target_weight_kg else None,
            'activity_level': health_profile.activity_level if hasattr(health_profile, 'activity_level') else None
        }

    def _calculate_confidence_score(self, ai_analysis: Dict, user_context: Dict) -> float:
        """Calculate confidence score for the analysis"""
        confidence = 5.0  # Base confidence
        
        # Increase confidence if we have more user data
        user_info = user_context.get('user_info', {})
        if user_info.get('age') and user_info.get('weight_kg') and user_info.get('height_cm'):
            confidence += 2.0
        if user_info.get('activity_level') and user_info.get('fitness_goal'):
            confidence += 2.0
        if user_context.get('dietary_preferences', {}).get('preferences'):
            confidence += 1.0
            
        return min(confidence, 10.0)

    # === FALLBACK METHODS ===

    def _generate_fallback_analysis(self, nutrition_profile: NutritionProfile) -> Dict:
        """Generate fallback analysis when AI fails"""
        return {
            'ai_analysis': self._generate_rule_based_analysis({}),
            'optimized_targets': self._get_current_targets(nutrition_profile),
            'recommendations': self._generate_basic_recommendations(nutrition_profile),
            'analysis_date': datetime.now().isoformat(),
            'confidence_score': 5.0,
            'generation_method': 'rule_based_fallback'
        }

    def _generate_rule_based_analysis(self, user_context: Dict) -> Dict:
        """Generate rule-based analysis as fallback"""
        return {
            'metabolic_analysis': {
                'bmr_assessment': 'Standard metabolic rate assumed',
                'calorie_adjustment_needed': 'maintain current'
            },
            'macro_optimization': {
                'protein_needs': {'recommended_grams': user_context.get('current_nutrition_targets', {}).get('protein', 100)},
                'carbohydrate_needs': {'recommended_grams': user_context.get('current_nutrition_targets', {}).get('carbs', 200)},
                'fat_needs': {'recommended_grams': user_context.get('current_nutrition_targets', {}).get('fat', 60)}
            },
            'goal_alignment': {
                'primary_nutrition_goal': 'balanced nutrition',
                'key_strategies': ['Follow balanced diet', 'Stay consistent', 'Monitor progress']
            },
            'optimization_priorities': {
                'immediate_priorities': ['Maintain current targets'],
                'success_indicators': ['Energy levels', 'Satisfaction with meals']
            }
        }

    def _get_current_targets(self, nutrition_profile: NutritionProfile) -> Dict:
        """Get current nutrition targets as fallback"""
        return {
            'calories': nutrition_profile.calorie_target,
            'protein': nutrition_profile.protein_target,
            'carbs': nutrition_profile.carb_target,
            'fat': nutrition_profile.fat_target,
            'optimization_rationale': {
                'protein': 'Maintaining current protein target',
                'carbs': 'Maintaining current carb target',
                'fat': 'Maintaining current fat target',
                'calories': 'Maintaining current calorie target'
            }
        }

    def _generate_basic_recommendations(self, nutrition_profile: NutritionProfile) -> Dict:
        """Generate basic recommendations as fallback"""
        return {
            'immediate_actions': ['Follow current nutrition targets', 'Stay consistent with meal timing'],
            'long_term_goals': ['Maintain healthy eating habits', 'Monitor progress regularly'],
            'health_recommendations': ['Stay hydrated', 'Include variety in diet'],
            'success_strategies': ['Meal planning', 'Portion control', 'Regular monitoring'],
            'potential_challenges': ['Consistency', 'Time management'],
            'monitoring_suggestions': ['Track energy levels', 'Monitor satisfaction']
        }

    def _get_rule_based_macro_distribution(self, nutrition_profile: NutritionProfile, 
                                         fitness_goal: str = None, activity_level: str = None) -> Dict:
        """Get rule-based macro distribution as fallback"""
        # Default distribution
        protein_percent = 25
        carb_percent = 45
        fat_percent = 30
        
        # Adjust based on goals
        if fitness_goal:
            if 'muscle' in fitness_goal.lower() or 'gain' in fitness_goal.lower():
                protein_percent = 30
                carb_percent = 40
                fat_percent = 30
            elif 'weight_loss' in fitness_goal.lower() or 'lose' in fitness_goal.lower():
                protein_percent = 30
                carb_percent = 35
                fat_percent = 35
                
        return {
            'protein_percent': protein_percent,
            'carbohydrate_percent': carb_percent,
            'fat_percent': fat_percent,
            'rationale': {
                'protein': f'{protein_percent}% protein for {fitness_goal or "general health"}',
                'carbs': f'{carb_percent}% carbs for energy needs',
                'fat': f'{fat_percent}% fat for hormone production and satiety'
            }
        }

    def _get_default_macro_distribution(self) -> Dict:
        """Get default macro distribution"""
        return {
            'protein_percent': 25,
            'carbohydrate_percent': 45,
            'fat_percent': 30,
            'rationale': {
                'protein': 'Standard protein needs for general population',
                'carbs': 'Adequate carbs for energy and brain function',
                'fat': 'Essential fats for hormone production'
            }
        }

    def _calculate_standard_calories(self, nutrition_profile: NutritionProfile) -> Dict:
        """Calculate standard calories as fallback"""
        return {
            'bmr_calculation': {'estimated_bmr': 'Not calculated'},
            'activity_adjustment': {'total_daily_expenditure': nutrition_profile.calorie_target},
            'goal_adjustment': {'recommended_calories': nutrition_profile.calorie_target},
            'calorie_distribution': {
                'minimum_safe': max(1200, nutrition_profile.calorie_target - 300),
                'maximum_effective': nutrition_profile.calorie_target + 300,
                'optimal_range': f"{nutrition_profile.calorie_target - 100} - {nutrition_profile.calorie_target + 100}"
            }
        }

    def _get_default_calorie_analysis(self, context: Dict) -> Dict:
        """Get default calorie analysis"""
        current_calories = context.get('current_targets', {}).get('calories', 2000)
        return {
            'bmr_calculation': {'estimated_bmr': current_calories * 0.7},
            'activity_adjustment': {'total_daily_expenditure': current_calories},
            'goal_adjustment': {'recommended_calories': current_calories},
            'calorie_distribution': {
                'minimum_safe': max(1200, current_calories - 300),
                'maximum_effective': current_calories + 300,
                'optimal_range': f"{current_calories - 100} - {current_calories + 100}"
            }
        }

    def _parse_analysis_fallback(self, text: str) -> Dict:
        """Parse analysis text when JSON fails"""
        return {
            'metabolic_analysis': {'bmr_assessment': 'Analysis available', 'calorie_adjustment_needed': 'maintain current'},
            'macro_optimization': {
                'protein_needs': {'recommended_grams': 100},
                'carbohydrate_needs': {'recommended_grams': 200},
                'fat_needs': {'recommended_grams': 60}
            },
            'goal_alignment': {'primary_nutrition_goal': 'balanced nutrition'},
            'optimization_priorities': {'immediate_priorities': ['Maintain balanced nutrition']}
        }

    def _generate_default_strategy(self, nutrition_profile: NutritionProfile, profile_analysis: Dict) -> Dict:
        """Generate default strategy when AI fails"""
        return {
            'nutrition_philosophy': {
                'primary_approach': 'balanced nutrition approach',
                'key_principles': ['Balanced macronutrients', 'Adequate hydration', 'Regular meal timing'],
                'success_factors': ['Consistency', 'Portion control', 'Variety']
            },
            'meal_timing_strategy': {
                'optimal_schedule': 'Regular meal times with balanced distribution',
                'meal_distribution': {
                    'breakfast_percent': 25,
                    'lunch_percent': 35,
                    'dinner_percent': 40
                }
            },
            'food_selection_strategy': {
                'prioritized_foods': ['Whole grains', 'Lean proteins', 'Fruits and vegetables'],
                'limited_foods': ['Processed foods', 'Added sugars', 'Excessive saturated fats'],
                'cooking_methods': ['Grilling', 'Steaming', 'Roasting', 'Sautéing']
            }
        }

    def _generate_fallback_strategy(self, nutrition_profile: NutritionProfile) -> Dict:
        """Generate fallback strategy when full generation fails"""
        return {
            'nutrition_philosophy': {
                'primary_approach': 'standard balanced nutrition',
                'key_principles': ['Meet daily nutritional needs', 'Follow dietary preferences'],
                'success_factors': ['Consistency', 'Balance']
            },
            'generation_method': 'fallback_strategy',
            'generated_date': datetime.now().isoformat()
        }