import openai
import logging
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from decouple import config
from ..models import NutritionProfile, MealPlan, Recipe
from datetime import datetime, timedelta, date
import json
import random

logger = logging.getLogger('nutrition.dynamic_meal_planning')


class DynamicMealPlanningService:
    """
    Advanced AI-driven meal planning service that creates truly personalized meal plans
    by analyzing user profiles, goals, and preferences using OpenAI's sophisticated 
    understanding of nutrition science.
    """

    def __init__(self):
        openai.api_key = config('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"  # Can be upgraded to gpt-4 for better analysis

    def generate_personalized_meal_plan(self, nutrition_profile: NutritionProfile, 
                                      days: int = 1, custom_options: Dict = None) -> Dict:
        """
        Generate a fully personalized meal plan using AI analysis of user profile
        
        Args:
            nutrition_profile: User's complete nutrition profile
            days: Number of days to plan for
            custom_options: Additional customization options
        
        Returns:
            Complete personalized meal plan with AI insights
        """
        try:
            logger.info(f"Generating personalized {days}-day meal plan for user {nutrition_profile.user.id}")
            
            # Step 1: Deep profile analysis
            profile_analysis = self._analyze_user_profile(nutrition_profile, custom_options)
            
            # Step 2: Generate meal strategy based on analysis
            meal_strategy = self._create_meal_strategy(profile_analysis, nutrition_profile, days)
            
            # Step 3: Generate specific meals using the strategy
            meal_plan = self._generate_strategic_meals(meal_strategy, nutrition_profile, days)
            
            # Step 4: Nutritional analysis and optimization
            optimized_plan = self._optimize_nutritional_balance(meal_plan, nutrition_profile)
            
            # Step 5: Add comprehensive scoring and insights
            final_plan = self._add_comprehensive_analysis(optimized_plan, nutrition_profile)
            
            logger.info("Successfully generated personalized meal plan with AI analysis")
            return final_plan
            
        except Exception as e:
            logger.error(f"Error generating personalized meal plan: {str(e)}")
            # Use intelligent fallback that still considers user profile
            return self._generate_profile_aware_fallback(nutrition_profile, days, custom_options)

    def _analyze_user_profile(self, nutrition_profile: NutritionProfile, custom_options: Dict = None) -> Dict:
        """Use OpenAI to deeply analyze user profile and extract nutrition insights"""
        try:
            health_profile = getattr(nutrition_profile.user, 'health_profile', None)
            
            # Prepare comprehensive profile context
            profile_context = self._build_profile_context(nutrition_profile, health_profile, custom_options)
            
            prompt = f"""
            As an expert nutritionist and meal planning specialist, analyze this user profile and provide 
            a comprehensive assessment for personalized meal planning:

            USER PROFILE:
            {json.dumps(profile_context, indent=2)}

            Please provide a detailed analysis in JSON format with the following structure:
            {{
                "nutrition_strategy": {{
                    "primary_goal": "detailed description of main nutrition goal",
                    "macro_distribution": {{
                        "protein_percent": "recommended protein percentage of calories",
                        "carb_percent": "recommended carb percentage of calories", 
                        "fat_percent": "recommended fat percentage of calories",
                        "rationale": "scientific rationale for this distribution"
                    }},
                    "calorie_adjustment": {{
                        "recommended_calories": "adjusted calorie target based on goals",
                        "adjustment_reason": "explanation for any adjustments"
                    }}
                }},
                "meal_timing": {{
                    "optimal_schedule": "recommended meal timing based on goals and lifestyle",
                    "pre_workout": "pre-workout meal recommendations if applicable",
                    "post_workout": "post-workout meal recommendations if applicable"
                }},
                "food_preferences": {{
                    "emphasized_foods": ["foods to emphasize based on goals and preferences"],
                    "limited_foods": ["foods to limit based on goals and health"],
                    "cooking_methods": ["recommended cooking methods"],
                    "portion_strategy": "strategy for portion control and meal sizing"
                }},
                "special_considerations": {{
                    "dietary_restrictions": "how to handle allergies and intolerances",
                    "health_conditions": "nutrition considerations for any health conditions",
                    "lifestyle_factors": "how to adapt meals to lifestyle and activity level"
                }},
                "success_metrics": {{
                    "key_indicators": ["metrics to track for success"],
                    "expected_outcomes": "what the user can expect from this plan"
                }}
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )

            # Parse the AI analysis
            analysis_text = response.choices[0].message.content
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = self._parse_analysis_text(analysis_text)

            return analysis

        except Exception as e:
            logger.warning(f"AI profile analysis failed: {str(e)}. Using rule-based analysis.")
            return self._rule_based_profile_analysis(nutrition_profile)

    def _create_meal_strategy(self, profile_analysis: Dict, nutrition_profile: NutritionProfile, days: int) -> Dict:
        """Create specific meal planning strategy based on AI analysis"""
        try:
            # Extract strategy from analysis
            nutrition_strategy = profile_analysis.get('nutrition_strategy', {})
            meal_timing = profile_analysis.get('meal_timing', {})
            food_preferences = profile_analysis.get('food_preferences', {})
            
            # Calculate adjusted macros based on AI recommendations
            adjusted_macros = self._calculate_adjusted_macros(nutrition_strategy, nutrition_profile)
            
            # Create meal distribution strategy
            meal_distribution = self._plan_meal_distribution(adjusted_macros, nutrition_profile, meal_timing)
            
            prompt = f"""
            Based on this nutritional analysis, create a specific meal planning strategy:

            NUTRITION ANALYSIS:
            {json.dumps(profile_analysis, indent=2)}

            USER TARGETS:
            - Daily Calories: {adjusted_macros['calories']}
            - Protein: {adjusted_macros['protein']}g
            - Carbs: {adjusted_macros['carbs']}g  
            - Fat: {adjusted_macros['fat']}g
            - Meals per day: {nutrition_profile.meals_per_day}

            PLAN DURATION: {days} days

            Create a strategic meal plan template in JSON format:
            {{
                "meal_strategy": {{
                    "breakfast": {{
                        "calorie_target": "calories for breakfast",
                        "protein_target": "protein grams",
                        "carb_target": "carb grams",
                        "fat_target": "fat grams",
                        "food_types": ["recommended food categories"],
                        "cooking_methods": ["preferred cooking methods"],
                        "timing": "optimal timing"
                    }},
                    "lunch": {{
                        "calorie_target": "calories for lunch",
                        "protein_target": "protein grams", 
                        "carb_target": "carb grams",
                        "fat_target": "fat grams",
                        "food_types": ["recommended food categories"],
                        "cooking_methods": ["preferred cooking methods"],
                        "timing": "optimal timing"
                    }},
                    "dinner": {{
                        "calorie_target": "calories for dinner",
                        "protein_target": "protein grams",
                        "carb_target": "carb grams", 
                        "fat_target": "fat grams",
                        "food_types": ["recommended food categories"],
                        "cooking_methods": ["preferred cooking methods"],
                        "timing": "optimal timing"
                    }}
                }},
                "daily_themes": ["theme for each day to ensure variety"],
                "key_principles": ["core principles guiding meal selection"],
                "flexibility_options": ["ways to adapt meals based on circumstances"]
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.4
            )

            strategy_text = response.choices[0].message.content
            try:
                strategy = json.loads(strategy_text)
            except json.JSONDecodeError:
                strategy = self._create_default_strategy(adjusted_macros, nutrition_profile)

            # Add calculated macros to strategy
            strategy['adjusted_macros'] = adjusted_macros
            strategy['profile_analysis'] = profile_analysis

            return strategy

        except Exception as e:
            logger.warning(f"Strategy creation failed: {str(e)}. Using default strategy.")
            return self._create_default_strategy(
                self._calculate_adjusted_macros({}, nutrition_profile), 
                nutrition_profile
            )

    def _generate_strategic_meals(self, meal_strategy: Dict, nutrition_profile: NutritionProfile, days: int) -> Dict:
        """Generate specific meals based on the strategic framework"""
        try:
            meal_plan_data = {
                'status': 'ai_generated',
                'message': 'Personalized meal plan generated using AI analysis',
                'days': days,
                'meals': {},
                'strategy_used': meal_strategy.get('key_principles', []),
                'generation_method': 'ai_strategic_planning'
            }

            # Generate meals for each day
            start_date = date.today()
            daily_themes = meal_strategy.get('daily_themes', [])
            
            for day_offset in range(days):
                current_date = start_date + timedelta(days=day_offset)
                date_str = current_date.isoformat()
                
                # Get theme for this day
                theme = daily_themes[day_offset % len(daily_themes)] if daily_themes else "balanced_nutrition"
                
                # Generate meals for this day
                daily_meals = self._generate_daily_meals(meal_strategy, nutrition_profile, theme, day_offset)
                meal_plan_data['meals'][date_str] = daily_meals

            return meal_plan_data

        except Exception as e:
            logger.error(f"Strategic meal generation failed: {str(e)}")
            return self._generate_basic_strategic_meals(nutrition_profile, days)

    def _generate_daily_meals(self, meal_strategy: Dict, nutrition_profile: NutritionProfile, 
                            theme: str, day_offset: int) -> List[Dict]:
        """Generate meals for a specific day using the meal strategy"""
        daily_meals = []
        strategy = meal_strategy.get('meal_strategy', {})
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            meal_template = strategy.get(meal_type, {})
            
            # Generate meal using AI with specific targets
            meal = self._generate_strategic_meal(
                meal_type, meal_template, nutrition_profile, theme, day_offset
            )
            
            if meal:
                daily_meals.append(meal)
            else:
                # Fallback to profile-aware meal
                fallback_meal = self._generate_profile_aware_meal(meal_type, nutrition_profile, meal_template)
                daily_meals.append(fallback_meal)
        
        return daily_meals

    def _generate_strategic_meal(self, meal_type: str, meal_template: Dict, 
                               nutrition_profile: NutritionProfile, theme: str, day_offset: int) -> Dict:
        """Generate a specific meal using AI with strategic constraints"""
        try:
            # Build context for meal generation
            context = {
                'meal_type': meal_type,
                'targets': meal_template,
                'dietary_preferences': nutrition_profile.dietary_preferences,
                'allergies_intolerances': nutrition_profile.allergies_intolerances,
                'cuisine_preferences': nutrition_profile.cuisine_preferences,
                'disliked_ingredients': nutrition_profile.disliked_ingredients,
                'theme': theme,
                'day_number': day_offset + 1
            }

            prompt = f"""
            Create a specific {meal_type} recipe that fits these requirements:

            REQUIREMENTS:
            {json.dumps(context, indent=2)}

            Generate a complete meal in JSON format:
            {{
                "id": "unique_meal_id",
                "title": "appealing meal title",
                "meal_type": "{meal_type}",
                "time": "recommended time to eat",
                "calories_per_serving": "calories matching target",
                "protein_per_serving": "protein in grams",
                "carbs_per_serving": "carbs in grams", 
                "fat_per_serving": "fat in grams",
                "servings": 1,
                "readyInMinutes": "prep and cook time",
                "image": "",
                "summary": "appealing description highlighting nutrition benefits",
                "ingredients_data": [
                    {{"original": "ingredient with quantity"}}
                ],
                "instructions": [
                    {{"step": "clear cooking instruction"}}
                ],
                "nutrition_highlights": ["key nutritional benefits"],
                "theme_connection": "how this meal fits the daily theme"
            }}

            Ensure the meal:
            1. Meets the calorie and macro targets within 10%
            2. Avoids all allergies and intolerances
            3. Follows dietary preferences strictly
            4. Uses preferred cuisines when possible
            5. Avoids disliked ingredients
            6. Fits the daily theme
            7. Is practical to prepare
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.6
            )

            meal_text = response.choices[0].message.content
            try:
                meal = json.loads(meal_text)
                # Validate nutrition targets
                if self._validate_meal_nutrition(meal, meal_template):
                    return meal
                else:
                    return None
            except json.JSONDecodeError:
                return None

        except Exception as e:
            logger.warning(f"Strategic meal generation failed for {meal_type}: {str(e)}")
            return None

    def _optimize_nutritional_balance(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Analyze and optimize the nutritional balance of the generated meal plan"""
        try:
            # Calculate total nutrition
            total_nutrition = self._calculate_total_nutrition(meal_plan)
            
            # Get targets
            targets = {
                'calories': nutrition_profile.calorie_target,
                'protein': nutrition_profile.protein_target,
                'carbs': nutrition_profile.carb_target,
                'fat': nutrition_profile.fat_target
            }

            # Use AI to analyze nutritional balance
            analysis_prompt = f"""
            Analyze this meal plan's nutritional balance:

            TARGETS:
            {json.dumps(targets, indent=2)}

            ACTUAL TOTALS:
            {json.dumps(total_nutrition, indent=2)}

            MEAL PLAN:
            {json.dumps(meal_plan.get('meals', {}), indent=2)}

            Provide optimization recommendations in JSON format:
            {{
                "balance_analysis": {{
                    "overall_balance": "assessment of nutritional balance (1-10 scale)",
                    "calorie_accuracy": "how well calories match target",
                    "macro_balance": "assessment of macro distribution",
                    "micronutrient_diversity": "assessment of vitamin/mineral diversity"
                }},
                "optimization_suggestions": [
                    "specific suggestions to improve balance"
                ],
                "adjusted_scores": {{
                    "balance_score": "1-10 rating",
                    "variety_score": "1-10 rating", 
                    "preference_match_score": "1-10 rating"
                }},
                "nutritional_highlights": [
                    "positive aspects of this meal plan"
                ],
                "areas_for_improvement": [
                    "specific areas that could be improved"
                ]
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.3
            )

            optimization_text = response.choices[0].message.content
            try:
                optimization = json.loads(optimization_text)
                
                # Add optimization data to meal plan
                meal_plan['nutritional_optimization'] = optimization
                meal_plan['nutrition'] = total_nutrition
                
                # Update scores
                scores = optimization.get('adjusted_scores', {})
                meal_plan['scores'] = {
                    'balance_score': float(scores.get('balance_score', 7)),
                    'variety_score': float(scores.get('variety_score', 7)),
                    'preference_match_score': float(scores.get('preference_match_score', 7)),
                    'overall_score': float(scores.get('balance_score', 7))
                }

                return meal_plan

            except json.JSONDecodeError:
                # Fallback scoring
                return self._add_fallback_scoring(meal_plan, total_nutrition, targets)

        except Exception as e:
            logger.warning(f"Nutritional optimization failed: {str(e)}")
            return self._add_fallback_scoring(meal_plan, {}, {})

    def _add_comprehensive_analysis(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Add final comprehensive analysis and insights"""
        try:
            # Generate final insights
            insights_prompt = f"""
            Provide comprehensive insights for this personalized meal plan:

            USER PROFILE:
            - Calorie Target: {nutrition_profile.calorie_target}
            - Dietary Preferences: {nutrition_profile.dietary_preferences}
            - Health Goals: Based on targets and preferences

            MEAL PLAN RESULTS:
            {json.dumps(meal_plan.get('nutrition', {}), indent=2)}

            Provide final insights in JSON format:
            {{
                "final_optimization": "overall assessment of how well the plan meets user needs",
                "adherence_tips": [
                    "practical tips for following this meal plan"
                ],
                "customization_options": [
                    "ways the user can customize or modify the plan"
                ],
                "expected_benefits": [
                    "benefits the user can expect from following this plan"
                ],
                "monitoring_suggestions": [
                    "what the user should track to measure success"
                ]
            }}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.4
            )

            insights_text = response.choices[0].message.content
            try:
                insights = json.loads(insights_text)
                meal_plan['ai_insights'] = insights
            except json.JSONDecodeError:
                meal_plan['ai_insights'] = {
                    'final_optimization': 'Personalized meal plan generated successfully',
                    'generation_method': 'ai_enhanced_strategic_planning'
                }

            # Add nutritional analysis summary
            meal_plan['nutritional_analysis'] = self._create_nutritional_summary(meal_plan, nutrition_profile)

            return meal_plan

        except Exception as e:
            logger.warning(f"Comprehensive analysis failed: {str(e)}")
            meal_plan['ai_insights'] = {
                'final_optimization': 'Meal plan generated with profile considerations',
                'generation_method': 'ai_enhanced_with_fallback'
            }
            return meal_plan

    # === HELPER METHODS ===

    def _build_profile_context(self, nutrition_profile: NutritionProfile, health_profile, custom_options: Dict = None) -> Dict:
        """Build comprehensive context from user profiles"""
        context = {
            'nutrition_targets': {
                'calories': nutrition_profile.calorie_target,
                'protein': nutrition_profile.protein_target,
                'carbs': nutrition_profile.carb_target,
                'fat': nutrition_profile.fat_target
            },
            'dietary_preferences': nutrition_profile.dietary_preferences or [],
            'allergies_intolerances': nutrition_profile.allergies_intolerances or [],
            'cuisine_preferences': nutrition_profile.cuisine_preferences or [],
            'disliked_ingredients': nutrition_profile.disliked_ingredients or [],
            'meal_schedule': {
                'meals_per_day': nutrition_profile.meals_per_day,
                'snacks_per_day': nutrition_profile.snacks_per_day,
                'breakfast_time': nutrition_profile.breakfast_time.strftime('%H:%M') if nutrition_profile.breakfast_time else '08:00',
                'lunch_time': nutrition_profile.lunch_time.strftime('%H:%M') if nutrition_profile.lunch_time else '12:30',
                'dinner_time': nutrition_profile.dinner_time.strftime('%H:%M') if nutrition_profile.dinner_time else '19:00'
            }
        }

        if health_profile:
            context['health_profile'] = {
                'age': health_profile.age,
                'gender': health_profile.get_gender_display() if hasattr(health_profile, 'get_gender_display') else health_profile.gender,
                'weight_kg': float(health_profile.weight_kg) if health_profile.weight_kg else None,
                'height_cm': float(health_profile.height_cm) if health_profile.height_cm else None,
                'activity_level': health_profile.get_activity_level_display() if hasattr(health_profile, 'get_activity_level_display') else health_profile.activity_level,
                'fitness_goal': health_profile.get_fitness_goal_display() if hasattr(health_profile, 'get_fitness_goal_display') else health_profile.fitness_goal,
                'bmi': health_profile.calculate_bmi() if hasattr(health_profile, 'calculate_bmi') else None
            }

        if custom_options:
            context['custom_options'] = custom_options

        return context

    def _calculate_adjusted_macros(self, nutrition_strategy: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Calculate adjusted macro targets based on AI recommendations"""
        base_calories = nutrition_profile.calorie_target
        
        # Use AI recommendations if available
        calorie_adjustment = nutrition_strategy.get('calorie_adjustment', {})
        recommended_calories = calorie_adjustment.get('recommended_calories', base_calories)
        
        if isinstance(recommended_calories, str):
            try:
                recommended_calories = float(recommended_calories)
            except ValueError:
                recommended_calories = base_calories
                
        macro_dist = nutrition_strategy.get('macro_distribution', {})
        
        try:
            protein_percent = float(macro_dist.get('protein_percent', 25)) / 100
            carb_percent = float(macro_dist.get('carb_percent', 45)) / 100  
            fat_percent = float(macro_dist.get('fat_percent', 30)) / 100
        except (ValueError, TypeError):
            # Fallback percentages
            protein_percent = 0.25
            carb_percent = 0.45
            fat_percent = 0.30

        return {
            'calories': int(recommended_calories),
            'protein': round((recommended_calories * protein_percent) / 4, 1),  # 4 cal/g
            'carbs': round((recommended_calories * carb_percent) / 4, 1),      # 4 cal/g
            'fat': round((recommended_calories * fat_percent) / 9, 1)          # 9 cal/g
        }

    def _plan_meal_distribution(self, adjusted_macros: Dict, nutrition_profile: NutritionProfile, meal_timing: Dict) -> Dict:
        """Plan how to distribute calories and macros across meals"""
        total_calories = adjusted_macros['calories']
        
        # Standard distribution (can be customized based on meal_timing analysis)
        distribution = {
            'breakfast': 0.25,  # 25% of daily calories
            'lunch': 0.35,      # 35% of daily calories  
            'dinner': 0.40      # 40% of daily calories
        }
        
        # Adjust distribution based on meal timing preferences
        optimal_schedule = meal_timing.get('optimal_schedule', '')
        if 'larger breakfast' in optimal_schedule.lower():
            distribution = {'breakfast': 0.30, 'lunch': 0.35, 'dinner': 0.35}
        elif 'lighter dinner' in optimal_schedule.lower():
            distribution = {'breakfast': 0.30, 'lunch': 0.40, 'dinner': 0.30}
            
        return distribution

    def _validate_meal_nutrition(self, meal: Dict, target: Dict) -> bool:
        """Validate that meal nutrition meets targets within tolerance"""
        if not meal or not target:
            return False
            
        target_calories = float(target.get('calorie_target', 0))
        meal_calories = float(meal.get('calories_per_serving', 0))
        
        # Allow 15% variance
        if target_calories > 0:
            variance = abs(meal_calories - target_calories) / target_calories
            return variance <= 0.15
            
        return True

    def _calculate_total_nutrition(self, meal_plan: Dict) -> Dict:
        """Calculate total nutrition for the meal plan"""
        totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        meal_count = 0
        
        meals = meal_plan.get('meals', {})
        for day_meals in meals.values():
            for meal in day_meals:
                totals['calories'] += float(meal.get('calories_per_serving', 0))
                totals['protein'] += float(meal.get('protein_per_serving', 0))
                totals['carbs'] += float(meal.get('carbs_per_serving', 0))
                totals['fat'] += float(meal.get('fat_per_serving', 0))
                meal_count += 1
        
        # Calculate averages if multi-day plan
        days = len(meals)
        if days > 1:
            for key in totals:
                totals[f'avg_daily_{key}'] = round(totals[key] / days, 1)
                
        return totals

    def _generate_profile_aware_fallback(self, nutrition_profile: NutritionProfile, days: int, custom_options: Dict = None) -> Dict:
        """Generate fallback meal plan that still considers user profile"""
        logger.info("Generating profile-aware fallback meal plan")
        
        # Use rule-based system that considers profile
        meal_plan_data = {
            'status': 'profile_aware_fallback',
            'message': 'Generated meal plan using profile data with fallback recipes',
            'days': days,
            'meals': {},
            'generation_method': 'profile_aware_fallback'
        }

        # Generate meals considering dietary preferences
        for day_offset in range(days):
            current_date = date.today() + timedelta(days=day_offset)
            date_str = current_date.isoformat()
            
            daily_meals = []
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                meal = self._generate_profile_aware_meal(meal_type, nutrition_profile)
                daily_meals.append(meal)
            
            meal_plan_data['meals'][date_str] = daily_meals

        # Add basic nutrition calculation
        total_nutrition = self._calculate_total_nutrition(meal_plan_data)
        meal_plan_data['nutrition'] = total_nutrition
        meal_plan_data['scores'] = {
            'balance_score': 6,
            'variety_score': 5,
            'preference_match_score': 7,
            'overall_score': 6
        }
        meal_plan_data['ai_insights'] = {
            'final_optimization': 'Profile-aware meal plan generated with basic customization',
            'generation_method': 'rule_based_with_profile'
        }
        meal_plan_data['nutritional_analysis'] = 'Basic nutritional analysis applied'

        return meal_plan_data

    def _generate_profile_aware_meal(self, meal_type: str, nutrition_profile: NutritionProfile, meal_template: Dict = None) -> Dict:
        """Generate a meal that considers user profile even in fallback mode"""
        
        # Base meal calories distribution
        calorie_distribution = {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.40}
        target_calories = int(nutrition_profile.calorie_target * calorie_distribution.get(meal_type, 0.33))
        
        # Adjust base meal templates based on dietary preferences
        base_meals = self._get_dietary_appropriate_meals(meal_type, nutrition_profile)
        
        # Select appropriate meal
        selected_meal = random.choice(base_meals) if base_meals else self._get_default_meal(meal_type)
        
        # Adjust calories to match target
        calorie_ratio = target_calories / selected_meal.get('calories_per_serving', target_calories)
        
        # Scale nutrition proportionally
        adjusted_meal = selected_meal.copy()
        adjusted_meal.update({
            'calories_per_serving': target_calories,
            'protein_per_serving': round(adjusted_meal.get('protein_per_serving', 0) * calorie_ratio, 1),
            'carbs_per_serving': round(adjusted_meal.get('carbs_per_serving', 0) * calorie_ratio, 1),
            'fat_per_serving': round(adjusted_meal.get('fat_per_serving', 0) * calorie_ratio, 1),
            'id': f"profile_aware_{meal_type}_{random.randint(1000, 9999)}",
            'time': {
                'breakfast': nutrition_profile.breakfast_time.strftime('%H:%M') if nutrition_profile.breakfast_time else '08:00',
                'lunch': nutrition_profile.lunch_time.strftime('%H:%M') if nutrition_profile.lunch_time else '12:30',
                'dinner': nutrition_profile.dinner_time.strftime('%H:%M') if nutrition_profile.dinner_time else '19:00'
            }.get(meal_type, '12:00')
        })
        
        return adjusted_meal

    def _get_dietary_appropriate_meals(self, meal_type: str, nutrition_profile: NutritionProfile) -> List[Dict]:
        """Get meals that are appropriate for user's dietary preferences"""
        all_meals = self._get_base_meal_templates()
        type_meals = all_meals.get(meal_type, [])
        
        appropriate_meals = []
        for meal in type_meals:
            # Check dietary preferences
            if self._meal_matches_dietary_preferences(meal, nutrition_profile):
                appropriate_meals.append(meal)
        
        return appropriate_meals

    def _meal_matches_dietary_preferences(self, meal: Dict, nutrition_profile: NutritionProfile) -> bool:
        """Check if a meal matches user's dietary preferences and restrictions"""
        
        # Check for allergens
        meal_ingredients = [ing.get('original', '').lower() for ing in meal.get('ingredients_data', [])]
        meal_text = ' '.join(meal_ingredients + [meal.get('title', '').lower(), meal.get('summary', '').lower()])
        
        # Check allergies and intolerances
        for allergen in nutrition_profile.allergies_intolerances:
            allergen_keywords = {
                'nuts': ['nuts', 'almond', 'walnut', 'pecan', 'cashew'],
                'dairy': ['milk', 'cheese', 'butter', 'yogurt', 'cream'],
                'gluten': ['wheat', 'bread', 'flour', 'pasta'],
                'eggs': ['egg', 'eggs'],
                'fish': ['fish', 'salmon', 'tuna', 'cod'],
                'shellfish': ['shrimp', 'crab', 'lobster', 'shellfish'],
                'soy': ['soy', 'tofu', 'soybean']
            }.get(allergen, [allergen])
            
            if any(keyword in meal_text for keyword in allergen_keywords):
                return False

        # Check dietary preferences
        for preference in nutrition_profile.dietary_preferences:
            if preference == 'vegetarian' and any(meat in meal_text for meat in ['chicken', 'beef', 'pork', 'fish', 'meat']):
                return False
            elif preference == 'vegan' and any(animal in meal_text for animal in ['milk', 'cheese', 'butter', 'egg', 'meat', 'chicken', 'fish']):
                return False

        # Check disliked ingredients
        for disliked in nutrition_profile.disliked_ingredients:
            if disliked.lower() in meal_text:
                return False

        return True

    def _get_base_meal_templates(self) -> Dict[str, List[Dict]]:
        """Get base meal templates for different meal types"""
        return {
            'breakfast': [
                {
                    'title': 'Healthy Oatmeal with Berries',
                    'meal_type': 'breakfast',
                    'calories_per_serving': 350,
                    'protein_per_serving': 12,
                    'carbs_per_serving': 65,
                    'fat_per_serving': 8,
                    'servings': 1,
                    'readyInMinutes': 10,
                    'summary': 'A nutritious breakfast with oats, fresh berries, and a drizzle of honey.',
                    'ingredients_data': [
                        {'original': '1 cup rolled oats'},
                        {'original': '1 cup milk or almond milk'},
                        {'original': '1/2 cup mixed berries'},
                        {'original': '1 tbsp honey'},
                        {'original': '1 tbsp chopped nuts'}
                    ],
                    'instructions': [
                        {'step': 'Cook oats with milk according to package directions'},
                        {'step': 'Top with berries, honey, and nuts'},
                        {'step': 'Serve warm'}
                    ]
                },
                {
                    'title': 'Avocado Toast with Eggs',
                    'meal_type': 'breakfast',
                    'calories_per_serving': 380,
                    'protein_per_serving': 18,
                    'carbs_per_serving': 30,
                    'fat_per_serving': 22,
                    'servings': 1,
                    'readyInMinutes': 12,
                    'summary': 'Protein-rich breakfast with healthy fats from avocado.',
                    'ingredients_data': [
                        {'original': '2 slices whole grain bread'},
                        {'original': '1 ripe avocado'},
                        {'original': '2 eggs'},
                        {'original': 'Salt and pepper to taste'},
                        {'original': '1 tsp olive oil'}
                    ],
                    'instructions': [
                        {'step': 'Toast bread to desired doneness'},
                        {'step': 'Mash avocado with salt and pepper'},
                        {'step': 'Cook eggs as preferred'},
                        {'step': 'Spread avocado on toast and top with eggs'}
                    ]
                },
                {
                    'title': 'Greek Yogurt Parfait',
                    'meal_type': 'breakfast',
                    'calories_per_serving': 320,
                    'protein_per_serving': 20,
                    'carbs_per_serving': 35,
                    'fat_per_serving': 10,
                    'servings': 1,
                    'readyInMinutes': 5,
                    'summary': 'High-protein breakfast with probiotics and fresh fruit.',
                    'ingredients_data': [
                        {'original': '1 cup Greek yogurt'},
                        {'original': '1/4 cup granola'},
                        {'original': '1/2 cup fresh berries'},
                        {'original': '1 tbsp honey'},
                        {'original': '1 tbsp chia seeds'}
                    ],
                    'instructions': [
                        {'step': 'Layer yogurt, granola, and berries in a bowl'},
                        {'step': 'Drizzle with honey'},
                        {'step': 'Sprinkle chia seeds on top'}
                    ]
                }
            ],
            'lunch': [
                {
                    'title': 'Mediterranean Quinoa Bowl',
                    'meal_type': 'lunch',
                    'calories_per_serving': 450,
                    'protein_per_serving': 16,
                    'carbs_per_serving': 58,
                    'fat_per_serving': 18,
                    'servings': 1,
                    'readyInMinutes': 15,
                    'summary': 'A healthy bowl with quinoa, vegetables, and Mediterranean flavors.',
                    'ingredients_data': [
                        {'original': '1 cup cooked quinoa'},
                        {'original': '1/4 cup cucumber, diced'},
                        {'original': '1/4 cup cherry tomatoes'},
                        {'original': '2 tbsp feta cheese'},
                        {'original': '2 tbsp olive oil'},
                        {'original': '1 tbsp lemon juice'}
                    ],
                    'instructions': [
                        {'step': 'Cook quinoa according to package directions'},
                        {'step': 'Dice cucumber and halve cherry tomatoes'},
                        {'step': 'Mix olive oil and lemon juice for dressing'},
                        {'step': 'Combine all ingredients and serve'}
                    ]
                },
                {
                    'title': 'Chicken and Vegetable Wrap',
                    'meal_type': 'lunch',
                    'calories_per_serving': 420,
                    'protein_per_serving': 28,
                    'carbs_per_serving': 35,
                    'fat_per_serving': 18,
                    'servings': 1,
                    'readyInMinutes': 10,
                    'summary': 'Protein-packed wrap with fresh vegetables and lean chicken.',
                    'ingredients_data': [
                        {'original': '1 large whole wheat tortilla'},
                        {'original': '4 oz grilled chicken breast'},
                        {'original': '1/4 cup shredded lettuce'},
                        {'original': '2 tbsp hummus'},
                        {'original': '1/4 cup diced tomatoes'},
                        {'original': '2 tbsp avocado'}
                    ],
                    'instructions': [
                        {'step': 'Spread hummus on tortilla'},
                        {'step': 'Add chicken, lettuce, tomatoes, and avocado'},
                        {'step': 'Roll tightly and slice in half'}
                    ]
                },
                {
                    'title': 'Lentil and Vegetable Soup',
                    'meal_type': 'lunch',
                    'calories_per_serving': 380,
                    'protein_per_serving': 18,
                    'carbs_per_serving': 55,
                    'fat_per_serving': 8,
                    'servings': 1,
                    'readyInMinutes': 25,
                    'summary': 'Hearty plant-based soup rich in fiber and protein.',
                    'ingredients_data': [
                        {'original': '1 cup red lentils'},
                        {'original': '2 cups vegetable broth'},
                        {'original': '1/2 cup diced carrots'},
                        {'original': '1/2 cup diced celery'},
                        {'original': '1 tsp olive oil'},
                        {'original': 'Herbs and spices to taste'}
                    ],
                    'instructions': [
                        {'step': 'Sauté vegetables in olive oil'},
                        {'step': 'Add lentils and broth, bring to boil'},
                        {'step': 'Simmer for 20 minutes until lentils are soft'},
                        {'step': 'Season with herbs and spices'}
                    ]
                }
            ],
            'dinner': [
                {
                    'title': 'Baked Salmon with Vegetables',
                    'meal_type': 'dinner',
                    'calories_per_serving': 520,
                    'protein_per_serving': 35,
                    'carbs_per_serving': 25,
                    'fat_per_serving': 28,
                    'servings': 1,
                    'readyInMinutes': 25,
                    'summary': 'Healthy dinner with omega-3 rich salmon and roasted vegetables.',
                    'ingredients_data': [
                        {'original': '5 oz salmon fillet'},
                        {'original': '1 cup broccoli florets'},
                        {'original': '1/2 cup sweet potato, cubed'},
                        {'original': '2 tbsp olive oil'},
                        {'original': 'Salt, pepper, and herbs to taste'}
                    ],
                    'instructions': [
                        {'step': 'Preheat oven to 400°F'},
                        {'step': 'Toss vegetables with 1 tbsp olive oil'},
                        {'step': 'Place salmon and vegetables on baking sheet'},
                        {'step': 'Bake for 15-20 minutes until salmon flakes easily'}
                    ]
                },
                {
                    'title': 'Chicken Stir-Fry with Brown Rice',
                    'meal_type': 'dinner',
                    'calories_per_serving': 480,
                    'protein_per_serving': 32,
                    'carbs_per_serving': 45,
                    'fat_per_serving': 18,
                    'servings': 1,
                    'readyInMinutes': 20,
                    'summary': 'Quick and nutritious stir-fry with lean protein and vegetables.',
                    'ingredients_data': [
                        {'original': '4 oz chicken breast, sliced'},
                        {'original': '3/4 cup cooked brown rice'},
                        {'original': '1 cup mixed vegetables'},
                        {'original': '2 tbsp stir-fry sauce'},
                        {'original': '1 tbsp sesame oil'}
                    ],
                    'instructions': [
                        {'step': 'Heat oil in wok or large pan'},
                        {'step': 'Cook chicken until done, remove'},
                        {'step': 'Stir-fry vegetables until crisp-tender'},
                        {'step': 'Return chicken, add sauce, serve over rice'}
                    ]
                },
                {
                    'title': 'Vegetarian Black Bean Bowl',
                    'meal_type': 'dinner',
                    'calories_per_serving': 460,
                    'protein_per_serving': 20,
                    'carbs_per_serving': 68,
                    'fat_per_serving': 14,
                    'servings': 1,
                    'readyInMinutes': 15,
                    'summary': 'Plant-based protein bowl with fiber-rich black beans.',
                    'ingredients_data': [
                        {'original': '1 cup cooked black beans'},
                        {'original': '3/4 cup cooked brown rice'},
                        {'original': '1/4 cup corn kernels'},
                        {'original': '1/4 cup diced bell peppers'},
                        {'original': '2 tbsp salsa'},
                        {'original': '1/4 avocado, sliced'}
                    ],
                    'instructions': [
                        {'step': 'Heat black beans and season to taste'},
                        {'step': 'Prepare rice according to package directions'},
                        {'step': 'Combine beans, rice, corn, and peppers'},
                        {'step': 'Top with salsa and avocado'}
                    ]
                }
            ]
        }

    def _get_default_meal(self, meal_type: str) -> Dict:
        """Get a safe default meal if no appropriate meals found"""
        defaults = {
            'breakfast': {
                'title': 'Simple Oatmeal',
                'meal_type': 'breakfast',
                'calories_per_serving': 300,
                'protein_per_serving': 10,
                'carbs_per_serving': 50,
                'fat_per_serving': 6,
                'servings': 1,
                'readyInMinutes': 5,
                'summary': 'Simple and nutritious oatmeal.',
                'ingredients_data': [{'original': '1 cup oats'}, {'original': '1 cup water'}],
                'instructions': [{'step': 'Cook oats with water'}]
            },
            'lunch': {
                'title': 'Simple Salad',
                'meal_type': 'lunch',
                'calories_per_serving': 350,
                'protein_per_serving': 12,
                'carbs_per_serving': 40,
                'fat_per_serving': 15,
                'servings': 1,
                'readyInMinutes': 5,
                'summary': 'Fresh and healthy salad.',
                'ingredients_data': [{'original': 'Mixed greens'}, {'original': 'Olive oil dressing'}],
                'instructions': [{'step': 'Toss greens with dressing'}]
            },
            'dinner': {
                'title': 'Simple Rice Bowl',
                'meal_type': 'dinner',
                'calories_per_serving': 400,
                'protein_per_serving': 15,
                'carbs_per_serving': 60,
                'fat_per_serving': 12,
                'servings': 1,
                'readyInMinutes': 10,
                'summary': 'Simple and filling rice bowl.',
                'ingredients_data': [{'original': '1 cup cooked rice'}, {'original': 'Mixed vegetables'}],
                'instructions': [{'step': 'Combine rice and vegetables'}]
            }
        }
        return defaults.get(meal_type, defaults['lunch'])

    # === MORE HELPER METHODS ===

    def _parse_analysis_text(self, text: str) -> Dict:
        """Parse AI analysis text when JSON parsing fails"""
        return {
            'nutrition_strategy': {
                'primary_goal': 'balanced nutrition',
                'macro_distribution': {'protein_percent': 25, 'carb_percent': 45, 'fat_percent': 30}
            },
            'meal_timing': {'optimal_schedule': 'regular meal times'},
            'food_preferences': {'emphasized_foods': [], 'limited_foods': []}
        }

    def _rule_based_profile_analysis(self, nutrition_profile: NutritionProfile) -> Dict:
        """Generate profile analysis using rules when AI fails"""
        return {
            'nutrition_strategy': {
                'primary_goal': 'Meet user nutritional targets with dietary preferences',
                'macro_distribution': {
                    'protein_percent': 25,
                    'carb_percent': 45,
                    'fat_percent': 30,
                    'rationale': 'Balanced macronutrient distribution'
                },
                'calorie_adjustment': {
                    'recommended_calories': nutrition_profile.calorie_target,
                    'adjustment_reason': 'Using existing calorie target'
                }
            },
            'meal_timing': {
                'optimal_schedule': 'Regular meal times based on user preferences'
            },
            'food_preferences': {
                'emphasized_foods': list(nutrition_profile.cuisine_preferences) if nutrition_profile.cuisine_preferences else [],
                'limited_foods': list(nutrition_profile.disliked_ingredients) if nutrition_profile.disliked_ingredients else [],
                'cooking_methods': ['healthy cooking methods'],
                'portion_strategy': 'Balanced portion sizes'
            }
        }

    def _create_default_strategy(self, adjusted_macros: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Create default meal strategy when AI generation fails"""
        total_calories = adjusted_macros['calories']
        
        return {
            'meal_strategy': {
                'breakfast': {
                    'calorie_target': int(total_calories * 0.25),
                    'protein_target': round(adjusted_macros['protein'] * 0.25, 1),
                    'carb_target': round(adjusted_macros['carbs'] * 0.25, 1),
                    'fat_target': round(adjusted_macros['fat'] * 0.25, 1),
                    'food_types': ['whole grains', 'protein', 'fruits'],
                    'cooking_methods': ['quick preparation'],
                    'timing': nutrition_profile.breakfast_time.strftime('%H:%M') if nutrition_profile.breakfast_time else '08:00'
                },
                'lunch': {
                    'calorie_target': int(total_calories * 0.35),
                    'protein_target': round(adjusted_macros['protein'] * 0.35, 1),
                    'carb_target': round(adjusted_macros['carbs'] * 0.35, 1),
                    'fat_target': round(adjusted_macros['fat'] * 0.35, 1),
                    'food_types': ['lean protein', 'vegetables', 'complex carbs'],
                    'cooking_methods': ['balanced preparation'],
                    'timing': nutrition_profile.lunch_time.strftime('%H:%M') if nutrition_profile.lunch_time else '12:30'
                },
                'dinner': {
                    'calorie_target': int(total_calories * 0.40),
                    'protein_target': round(adjusted_macros['protein'] * 0.40, 1),
                    'carb_target': round(adjusted_macros['carbs'] * 0.40, 1),
                    'fat_target': round(adjusted_macros['fat'] * 0.40, 1),
                    'food_types': ['protein', 'vegetables', 'healthy fats'],
                    'cooking_methods': ['satisfying preparation'],
                    'timing': nutrition_profile.dinner_time.strftime('%H:%M') if nutrition_profile.dinner_time else '19:00'
                }
            },
            'daily_themes': ['balanced_nutrition'],
            'key_principles': ['Meet nutritional targets', 'Follow dietary preferences', 'Ensure variety'],
            'adjusted_macros': adjusted_macros
        }

    def _generate_basic_strategic_meals(self, nutrition_profile: NutritionProfile, days: int) -> Dict:
        """Generate basic strategic meals when full AI generation fails"""
        return {
            'status': 'basic_strategic',
            'message': 'Generated strategic meal plan with basic AI enhancement',
            'days': days,
            'meals': {},
            'generation_method': 'basic_strategic_planning'
        }

    def _add_fallback_scoring(self, meal_plan: Dict, total_nutrition: Dict, targets: Dict) -> Dict:
        """Add fallback scoring when AI optimization fails"""
        meal_plan['scores'] = {
            'balance_score': 6.0,
            'variety_score': 6.0,
            'preference_match_score': 7.0,
            'overall_score': 6.3
        }
        meal_plan['nutrition'] = total_nutrition
        return meal_plan

    def _create_nutritional_summary(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> str:
        """Create nutritional analysis summary"""
        nutrition = meal_plan.get('nutrition', {})
        targets = {
            'calories': nutrition_profile.calorie_target,
            'protein': nutrition_profile.protein_target,
            'carbs': nutrition_profile.carb_target,
            'fat': nutrition_profile.fat_target
        }
        
        summary_parts = []
        for nutrient, value in nutrition.items():
            if nutrient in targets and targets[nutrient] > 0:
                percentage = (value / targets[nutrient]) * 100
                summary_parts.append(f"{nutrient}: {value}g ({percentage:.0f}% of target)")
        
        return "Nutritional targets: " + ", ".join(summary_parts) if summary_parts else "Basic nutritional analysis applied"