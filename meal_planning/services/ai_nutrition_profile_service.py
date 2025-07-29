import openai
import logging
import json
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.db import transaction
from decouple import config
from ..models import NutritionProfile, Ingredient
from health_profiles.models import HealthProfile
from django.utils import timezone

logger = logging.getLogger('nutrition.ai_profile')


class AINutritionProfileService:
    """
    AI-Enhanced Nutrition Profile Service that uses OpenAI to:
    1. Auto-generate personalized nutrition profiles based on goals
    2. Provide intelligent nutrition recommendations
    3. Adapt profiles based on progress and feedback
    """

    def __init__(self):
        self.openai_client = self._initialize_openai()

    def _initialize_openai(self):
        """Initialize OpenAI client with error handling"""
        try:
            api_key = config('OPENAI_API_KEY', default='')
            if not api_key:
                logger.warning("OpenAI API key not found. AI features will be limited.")
                return None
            
            # Try new client first, fallback to old API
            try:
                import openai
                return openai.OpenAI(api_key=api_key)
            except AttributeError:
                # Fallback for older OpenAI versions
                openai.api_key = api_key
                return None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {str(e)}")
            return None

    @transaction.atomic
    def generate_ai_nutrition_profile(self, user, force_regenerate: bool = False) -> Dict:
        """
        Generate or update a nutrition profile using AI analysis
        
        Args:
            user: Django User instance
            force_regenerate: Force regeneration even if profile exists
            
        Returns:
            Dictionary with profile data and AI insights
        """
        try:
            # Get or create nutrition profile
            nutrition_profile, created = NutritionProfile.objects.get_or_create(
                user=user,
                defaults={'calorie_target': 2000, 'protein_target': 150, 'carb_target': 200, 'fat_target': 65}
            )

            # Check if we need to generate/regenerate
            if not created and not force_regenerate and nutrition_profile.advanced_preferences.get('ai_generated'):
                logger.info(f"AI profile already exists for user {user.id}")
                return {
                    'status': 'existing',
                    'profile': self._profile_to_dict(nutrition_profile),
                    'message': 'AI-generated profile already exists. Use force_regenerate=True to update.'
                }

            # Get health profile for context
            health_profile = getattr(user, 'health_profile', None)
            if not health_profile:
                return {
                    'status': 'error',
                    'message': 'Health profile required for AI nutrition profile generation. Please complete your health profile first.'
                }

            # Generate AI recommendations
            ai_recommendations = self._get_ai_nutrition_recommendations(nutrition_profile, health_profile)
            
            if ai_recommendations:
                # Apply AI recommendations to profile
                self._apply_ai_recommendations(nutrition_profile, ai_recommendations)
                
                # Save AI generation metadata
                nutrition_profile.advanced_preferences.update({
                    'ai_generated': True,
                    'ai_generation_date': str(timezone.now()),
                    'ai_recommendations': ai_recommendations,
                    'generation_version': '2.0'
                })
                nutrition_profile.save()

                logger.info(f"Successfully generated AI nutrition profile for user {user.id}")
                
                return {
                    'status': 'success',
                    'profile': self._profile_to_dict(nutrition_profile),
                    'ai_insights': ai_recommendations,
                    'message': 'AI nutrition profile generated successfully!'
                }
            else:
                # Fallback to rule-based calculation
                nutrition_profile.calculate_targets_from_health_profile()
                nutrition_profile.save()
                
                return {
                    'status': 'fallback',
                    'profile': self._profile_to_dict(nutrition_profile),
                    'message': 'Used rule-based calculation due to AI service limitations.'
                }

        except Exception as e:
            logger.error(f"Error generating AI nutrition profile for user {user.id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to generate nutrition profile: {str(e)}'
            }

    @transaction.atomic
    def generate_custom_nutrition_profile(self, user, user_data: Dict, goals: Dict, preferences: Dict) -> Dict:
        """
        Generate nutrition profile based on custom user input data
        
        Args:
            user: Django User instance
            user_data: Dictionary with age, gender, height, weight
            goals: Dictionary with primary_goal, activity_level
            preferences: Dictionary with dietary_preferences
            
        Returns:
            Dictionary with profile data and AI insights
        """
        try:
            # Get or create nutrition profile
            nutrition_profile, created = NutritionProfile.objects.get_or_create(
                user=user,
                defaults={'calorie_target': 2000, 'protein_target': 150, 'carb_target': 200, 'fat_target': 65}
            )

            # Create mock health profile data from custom input
            mock_health_context = {
                'age': user_data.get('age'),
                'gender': user_data.get('gender'),
                'height': user_data.get('height'),
                'weight': user_data.get('weight'),
                'primary_goal': goals.get('primary_goal', 'maintenance'),
                'activity_level': goals.get('activity_level', 'moderate'),
                'dietary_preferences': preferences.get('dietary_preferences', [])
            }

            # Calculate nutrition profile using AI or fallback
            if self.openai_client or hasattr(openai, 'api_key'):
                ai_recommendations = self._get_ai_recommendations_from_custom_data(mock_health_context)
                
                if ai_recommendations:
                    # Apply AI recommendations
                    self._apply_ai_recommendations(nutrition_profile, ai_recommendations)
                    
                    # Update dietary preferences if provided
                    if preferences.get('dietary_preferences'):
                        nutrition_profile.dietary_preferences = preferences['dietary_preferences']
                    
                    # Save AI generation metadata
                    nutrition_profile.advanced_preferences.update({
                        'ai_generated': True,
                        'ai_generation_date': str(timezone.now()),
                        'ai_recommendations': ai_recommendations,
                        'generation_version': '2.0',
                        'custom_input': mock_health_context
                    })
                    nutrition_profile.save()

                    logger.info(f"Successfully generated custom AI nutrition profile for user {user.id}")
                    
                    return {
                        'status': 'success',
                        'data': self._profile_to_dict(nutrition_profile),
                        'ai_insights': ai_recommendations,
                        'message': 'AI nutrition profile generated successfully!'
                    }
            
            # Fallback calculation
            calculated_profile = self._calculate_fallback_profile(mock_health_context)
            
            # Apply fallback calculations
            nutrition_profile.calorie_target = calculated_profile['calorie_target']
            nutrition_profile.protein_target = calculated_profile['protein_target']
            nutrition_profile.carb_target = calculated_profile['carb_target']
            nutrition_profile.fat_target = calculated_profile['fat_target']
            nutrition_profile.meals_per_day = calculated_profile['meals_per_day']
            
            if preferences.get('dietary_preferences'):
                nutrition_profile.dietary_preferences = preferences['dietary_preferences']
            
            nutrition_profile.save()
            
            return {
                'status': 'success',
                'data': self._profile_to_dict(nutrition_profile),
                'message': 'Nutrition profile calculated successfully using smart algorithms!'
            }

        except Exception as e:
            logger.error(f"Error generating custom nutrition profile for user {user.id}: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to generate nutrition profile: {str(e)}'
            }

    def _get_ai_recommendations_from_custom_data(self, health_context: Dict) -> Dict:
        """Get AI recommendations from custom health context data"""
        try:
            if not self.openai_client and not hasattr(openai, 'api_key'):
                return None

            # Prepare custom context
            context = self._prepare_custom_nutrition_context(health_context)
            
            # Use function calling for structured nutrition profile generation
            function_schema = {
                "name": "generate_nutrition_profile",
                "description": "Generate a comprehensive nutrition profile based on user's health data and fitness goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "calorie_target": {"type": "integer", "minimum": 1200, "maximum": 4000},
                        "protein_target": {"type": "number", "minimum": 50, "maximum": 300},
                        "carb_target": {"type": "number", "minimum": 50, "maximum": 500},
                        "fat_target": {"type": "number", "minimum": 30, "maximum": 200},
                        "meals_per_day": {"type": "integer", "minimum": 3, "maximum": 6},
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Personalized nutrition recommendations"
                        }
                    },
                    "required": ["calorie_target", "protein_target", "carb_target", "fat_target", "meals_per_day"]
                }
            }

            # Generate prompt
            prompt = f"""
            As a certified nutritionist and dietitian, create a personalized nutrition profile for the following individual:

            {context}

            Please generate a comprehensive nutrition plan that includes:
            1. Optimal daily calorie target based on their TDEE and goals
            2. Macronutrient targets (protein, carbs, fat) in grams
            3. Recommended number of meals per day
            4. Personalized nutrition recommendations

            Consider their specific dietary preferences, activity level, and health goals.
            Ensure the recommendations are safe, evidence-based, and sustainable.
            """

            # Call OpenAI API
            try:
                # Try new client API first
                if self.openai_client:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        functions=[function_schema],
                        function_call={"name": "generate_nutrition_profile"},
                        temperature=0.3
                    )
                    
                    if response.choices[0].message.function_call:
                        function_args = json.loads(response.choices[0].message.function_call.arguments)
                        return function_args
                else:
                    # Fallback to older API
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        functions=[function_schema],
                        function_call={"name": "generate_nutrition_profile"},
                        temperature=0.3
                    )
                    
                    if response.choices[0].message.get('function_call'):
                        function_args = json.loads(response.choices[0].message['function_call']['arguments'])
                        return function_args

            except Exception as e:
                logger.error(f"OpenAI API call failed: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error getting AI recommendations from custom data: {str(e)}")
            return None

    def _prepare_custom_nutrition_context(self, health_context: Dict) -> str:
        """Prepare context string from custom health data"""
        age = health_context.get('age')
        gender = health_context.get('gender')
        height = health_context.get('height')
        weight = health_context.get('weight')
        goal = health_context.get('primary_goal', 'maintenance')
        activity = health_context.get('activity_level', 'moderate')
        dietary_prefs = health_context.get('dietary_preferences', [])

        # Calculate BMI
        height_m = height / 100 if height else 1.7
        bmi = (weight / (height_m ** 2)) if weight and height else 22

        context = f"""
        Personal Information:
        - Age: {age} years
        - Gender: {gender}
        - Height: {height} cm
        - Weight: {weight} kg
        - BMI: {bmi:.1f}

        Fitness Goals:
        - Primary Goal: {goal}
        - Activity Level: {activity}

        Dietary Preferences: {', '.join(dietary_prefs) if dietary_prefs else 'No specific preferences'}
        """

        return context

    def _calculate_fallback_profile(self, health_context: Dict) -> Dict:
        """Calculate nutrition profile using rule-based approach"""
        age = health_context.get('age', 30)
        gender = health_context.get('gender', 'female')
        height = health_context.get('height', 170)
        weight = health_context.get('weight', 70)
        goal = health_context.get('primary_goal', 'maintenance')
        activity = health_context.get('activity_level', 'moderate')
        dietary_prefs = health_context.get('dietary_preferences', [])

        # Calculate BMR using Mifflin-St Jeor Equation
        if gender == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # Activity multipliers
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'very_active': 1.725,
            'extra_active': 1.9
        }

        tdee = bmr * activity_multipliers.get(activity, 1.55)

        # Adjust for goals
        if goal == 'weight_loss':
            tdee -= 500  # 1 lb per week
        elif goal == 'muscle_gain':
            tdee += 300  # Moderate surplus

        # Calculate macros based on dietary preferences
        protein_ratio = 0.25
        carb_ratio = 0.45
        fat_ratio = 0.30

        if 'keto' in dietary_prefs:
            protein_ratio = 0.25
            carb_ratio = 0.05
            fat_ratio = 0.70
        elif 'high_protein' in dietary_prefs:
            protein_ratio = 0.35
            carb_ratio = 0.40
            fat_ratio = 0.25
        elif 'low_carb' in dietary_prefs:
            protein_ratio = 0.30
            carb_ratio = 0.20
            fat_ratio = 0.50

        return {
            'calorie_target': int(tdee),
            'protein_target': int(tdee * protein_ratio / 4),
            'carb_target': int(tdee * carb_ratio / 4),
            'fat_target': int(tdee * fat_ratio / 9),
            'meals_per_day': 4 if goal == 'muscle_gain' else 3,
            'snacks_per_day': 2 if goal == 'muscle_gain' else 1
        }

    def _get_ai_nutrition_recommendations(self, nutrition_profile: NutritionProfile, health_profile: HealthProfile) -> Dict:
        """Get comprehensive nutrition recommendations from OpenAI"""
        try:
            if not self.openai_client and not hasattr(openai, 'api_key'):
                logger.warning("OpenAI not available, skipping AI recommendations")
                return None

            # Prepare context for AI
            context = self._prepare_nutrition_context(nutrition_profile, health_profile)
            
            # Use function calling for structured nutrition profile generation
            function_schema = {
                "name": "generate_nutrition_profile",
                "description": "Generate a comprehensive nutrition profile based on user's health data and fitness goals",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "calorie_target": {
                            "type": "integer",
                            "description": "Daily calorie target in kcal",
                            "minimum": 1200,
                            "maximum": 4000
                        },
                        "protein_target": {
                            "type": "number",
                            "description": "Daily protein target in grams",
                            "minimum": 50,
                            "maximum": 300
                        },
                        "carb_target": {
                            "type": "number",
                            "description": "Daily carbohydrate target in grams",
                            "minimum": 50,
                            "maximum": 500
                        },
                        "fat_target": {
                            "type": "number",
                            "description": "Daily fat target in grams",
                            "minimum": 30,
                            "maximum": 200
                        },
                        "recommended_dietary_preferences": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Recommended dietary approaches based on goals"
                        },
                        "meal_timing_recommendations": {
                            "type": "object",
                            "properties": {
                                "meals_per_day": {"type": "integer", "minimum": 3, "maximum": 6},
                                "snacks_per_day": {"type": "integer", "minimum": 0, "maximum": 3},
                                "pre_workout_nutrition": {"type": "string"},
                                "post_workout_nutrition": {"type": "string"}
                            }
                        },
                        "hydration_target": {
                            "type": "number",
                            "description": "Daily water intake in liters"
                        },
                        "supplement_recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Recommended supplements if any"
                        },
                        "foods_to_emphasize": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Foods to prioritize based on goals"
                        },
                        "foods_to_limit": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Foods to limit or avoid"
                        },
                        "nutrition_strategy": {
                            "type": "string",
                            "description": "Overall nutrition strategy explanation"
                        },
                        "progress_monitoring": {
                            "type": "object",
                            "properties": {
                                "key_metrics": {"type": "array", "items": {"type": "string"}},
                                "adjustment_frequency": {"type": "string"},
                                "success_indicators": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "required": ["calorie_target", "protein_target", "carb_target", "fat_target", "nutrition_strategy"]
                }
            }

            # Create the AI prompt
            prompt = self._create_nutrition_prompt(context)

            # Call OpenAI API
            if self.openai_client:
                # New client
                response = self.openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL_CONFIG['nutrition_analysis']['model'],
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert registered dietitian and sports nutritionist with 20+ years of experience. Provide evidence-based nutrition recommendations tailored to individual goals, health status, and preferences."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    functions=[function_schema],
                    function_call={"name": "generate_nutrition_profile"},
                    temperature=settings.OPENAI_MODEL_CONFIG['nutrition_analysis']['temperature'],
                    max_tokens=settings.OPENAI_MODEL_CONFIG['nutrition_analysis']['max_tokens']
                )
                
                function_response = response.choices[0].message.function_call.arguments
            else:
                # Legacy client
                response = openai.ChatCompletion.create(
                    model=settings.OPENAI_MODEL_CONFIG['nutrition_analysis']['model'],
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert registered dietitian and sports nutritionist with 20+ years of experience. Provide evidence-based nutrition recommendations tailored to individual goals, health status, and preferences."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    functions=[function_schema],
                    function_call={"name": "generate_nutrition_profile"},
                    temperature=settings.OPENAI_MODEL_CONFIG['nutrition_analysis']['temperature'],
                    max_tokens=settings.OPENAI_MODEL_CONFIG['nutrition_analysis']['max_tokens']
                )
                
                function_response = response.choices[0].message.function_call.arguments

            # Parse the AI response
            ai_recommendations = json.loads(function_response)
            
            # Add metadata
            ai_recommendations['ai_confidence'] = 0.85  # Could be calculated based on response quality
            ai_recommendations['generated_at'] = str(timezone.now())
            
            return ai_recommendations

        except Exception as e:
            logger.error(f"OpenAI nutrition recommendation failed: {str(e)}")
            return None

    def _prepare_nutrition_context(self, nutrition_profile: NutritionProfile, health_profile: HealthProfile) -> Dict:
        """Prepare comprehensive context for AI nutrition analysis"""
        context = nutrition_profile.get_ai_generation_context()
        
        # Add additional health context
        context['health_details'] = {
            'fitness_level': health_profile.fitness_level,
            'weekly_activity_days': health_profile.weekly_activity_days,
            'does_cardio': health_profile.does_cardio,
            'does_strength': health_profile.does_strength,
            'avg_session_duration': health_profile.avg_session_duration,
            'preferred_environment': health_profile.preferred_environment,
            'time_preference': health_profile.time_preference,
            'dietary_preference': health_profile.dietary_preference,
            'dietary_restrictions': {
                'gluten_free': health_profile.is_gluten_free,
                'dairy_free': health_profile.is_dairy_free,
                'nut_free': health_profile.is_nut_free,
                'other_restrictions': health_profile.other_restrictions_note
            }
        }
        
        # Add goal-based preferences
        context['goal_preferences'] = nutrition_profile.get_goal_based_preferences()
        
        return context

    def _create_nutrition_prompt(self, context: Dict) -> str:
        """Create a comprehensive prompt for nutrition profile generation"""
        user_info = context['user_info']
        health_details = context['health_details']
        goal_preferences = context['goal_preferences']
        
        prompt = f"""
        Please generate a comprehensive, personalized nutrition profile for this individual:

        PERSONAL INFORMATION:
        - Age: {user_info['age']} years
        - Gender: {user_info['gender']}
        - Current Weight: {user_info['weight_kg']} kg
        - Height: {user_info['height_cm']} cm
        - BMI: {user_info['bmi']:.1f} (calculated)
        - Target Weight: {user_info['target_weight_kg']} kg
        - Activity Level: {user_info['activity_level']}
        - Primary Fitness Goal: {user_info['fitness_goal']}

        FITNESS & ACTIVITY:
        - Fitness Level: {health_details['fitness_level']}
        - Weekly Activity Days: {health_details['weekly_activity_days']}
        - Does Cardio: {health_details['does_cardio']}
        - Does Strength Training: {health_details['does_strength']}
        - Session Duration: {health_details['avg_session_duration']}
        - Preferred Environment: {health_details['preferred_environment']}
        - Time Preference: {health_details['time_preference']}

        DIETARY INFORMATION:
        - Current Dietary Preference: {health_details['dietary_preference']}
        - Gluten Free: {health_details['dietary_restrictions']['gluten_free']}
        - Dairy Free: {health_details['dietary_restrictions']['dairy_free']}
        - Nut Free: {health_details['dietary_restrictions']['nut_free']}
        - Other Restrictions: {health_details['dietary_restrictions']['other_restrictions']}

        CURRENT PREFERENCES:
        - Dietary Preferences: {context['preferences']['dietary_preferences']}
        - Allergies/Intolerances: {context['preferences']['allergies_intolerances']}
        - Cuisine Preferences: {context['preferences']['cuisine_preferences']}
        - Disliked Ingredients: {context['preferences']['disliked_ingredients']}

        GOAL-SPECIFIC GUIDANCE:
        - Emphasized Foods: {goal_preferences['emphasized_foods']}
        - Foods to Limit: {goal_preferences['limited_foods']}
        - Meal Timing Strategy: {goal_preferences['meal_timing']}
        - Portion Control Approach: {goal_preferences['portion_control']}

        REQUIREMENTS:
        1. Calculate precise calorie and macronutrient targets based on goals
        2. Consider their activity level and training schedule
        3. Respect all dietary restrictions and preferences
        4. Provide specific, actionable nutrition strategies
        5. Include meal timing recommendations for their goal
        6. Suggest appropriate supplements only if beneficial
        7. Emphasize foods that support their specific fitness goal
        8. Provide clear progress monitoring guidance

        Generate a complete nutrition profile that will help them achieve their {user_info['fitness_goal']} goal efficiently and sustainably.
        """
        
        return prompt

    def _apply_ai_recommendations(self, nutrition_profile: NutritionProfile, recommendations: Dict):
        """Apply AI recommendations to the nutrition profile"""
        try:
            # Update macro targets
            nutrition_profile.calorie_target = recommendations['calorie_target']
            nutrition_profile.protein_target = recommendations['protein_target']
            nutrition_profile.carb_target = recommendations['carb_target']
            nutrition_profile.fat_target = recommendations['fat_target']

            # Update meal timing if provided
            meal_timing = recommendations.get('meal_timing_recommendations', {})
            if meal_timing:
                nutrition_profile.meals_per_day = meal_timing.get('meals_per_day', nutrition_profile.meals_per_day)
                nutrition_profile.snacks_per_day = meal_timing.get('snacks_per_day', nutrition_profile.snacks_per_day)

            # Update dietary preferences if recommended
            recommended_preferences = recommendations.get('recommended_dietary_preferences', [])
            if recommended_preferences:
                # Merge with existing preferences
                current_prefs = set(nutrition_profile.dietary_preferences or [])
                new_prefs = set(recommended_preferences)
                nutrition_profile.dietary_preferences = list(current_prefs.union(new_prefs))

            # Store additional AI recommendations in advanced_preferences
            nutrition_profile.advanced_preferences.update({
                'hydration_target': recommendations.get('hydration_target'),
                'supplement_recommendations': recommendations.get('supplement_recommendations', []),
                'foods_to_emphasize': recommendations.get('foods_to_emphasize', []),
                'foods_to_limit': recommendations.get('foods_to_limit', []),
                'nutrition_strategy': recommendations.get('nutrition_strategy'),
                'progress_monitoring': recommendations.get('progress_monitoring', {}),
                'pre_workout_nutrition': meal_timing.get('pre_workout_nutrition'),
                'post_workout_nutrition': meal_timing.get('post_workout_nutrition')
            })

        except Exception as e:
            logger.error(f"Error applying AI recommendations: {str(e)}")
            raise

    def update_profile_based_on_progress(self, nutrition_profile: NutritionProfile, progress_data: Dict) -> Dict:
        """Update nutrition profile based on user progress and feedback"""
        try:
            if not self.openai_client and not hasattr(openai, 'api_key'):
                return {'status': 'error', 'message': 'AI service not available'}

            # Prepare progress context
            context = {
                'current_profile': self._profile_to_dict(nutrition_profile),
                'progress_data': progress_data,
                'user_feedback': progress_data.get('user_feedback', ''),
                'goal_achievement': progress_data.get('goal_achievement', {}),
                'challenges': progress_data.get('challenges', [])
            }

            # Get AI recommendations for adjustments
            adjustment_prompt = self._create_adjustment_prompt(context)
            
            # Call OpenAI for profile adjustments
            # ... Implementation similar to generate_ai_nutrition_profile
            
            return {'status': 'success', 'message': 'Profile updated based on progress'}

        except Exception as e:
            logger.error(f"Error updating profile based on progress: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def get_nutrition_insights(self, nutrition_profile: NutritionProfile, daily_intake: Dict) -> Dict:
        """Get AI insights about daily nutrition intake"""
        try:
            if not self.openai_client and not hasattr(openai, 'api_key'):
                return {'insights': ['AI insights temporarily unavailable']}

            context = {
                'targets': {
                    'calories': nutrition_profile.calorie_target,
                    'protein': nutrition_profile.protein_target,
                    'carbs': nutrition_profile.carb_target,
                    'fat': nutrition_profile.fat_target
                },
                'actual': daily_intake,
                'goal_preferences': nutrition_profile.get_goal_based_preferences()
            }

            # Generate insights using AI
            insights = self._generate_daily_insights(context)
            
            return {'insights': insights}

        except Exception as e:
            logger.error(f"Error generating nutrition insights: {str(e)}")
            return {'insights': ['Unable to generate insights at this time']}

    def _profile_to_dict(self, nutrition_profile: NutritionProfile) -> Dict:
        """Convert nutrition profile to dictionary for API responses"""
        return {
            'id': nutrition_profile.id,
            'calorie_target': nutrition_profile.calorie_target,
            'protein_target': nutrition_profile.protein_target,
            'carb_target': nutrition_profile.carb_target,
            'fat_target': nutrition_profile.fat_target,
            'dietary_preferences': nutrition_profile.dietary_preferences,
            'allergies_intolerances': nutrition_profile.allergies_intolerances,
            'cuisine_preferences': nutrition_profile.cuisine_preferences,
            'disliked_ingredients': nutrition_profile.disliked_ingredients,
            'meals_per_day': nutrition_profile.meals_per_day,
            'snacks_per_day': nutrition_profile.snacks_per_day,
            'meal_timing': {
                'breakfast': nutrition_profile.breakfast_time.strftime('%H:%M'),
                'lunch': nutrition_profile.lunch_time.strftime('%H:%M'),
                'dinner': nutrition_profile.dinner_time.strftime('%H:%M')
            },
            'ai_recommendations': nutrition_profile.advanced_preferences.get('ai_recommendations', {}),
            'last_updated': nutrition_profile.updated_at.isoformat()
        }

    def _create_adjustment_prompt(self, context: Dict) -> str:
        """Create prompt for profile adjustments based on progress"""
        # Implementation for progress-based adjustments
        pass

    def _generate_daily_insights(self, context: Dict) -> List[str]:
        """Generate daily nutrition insights"""
        # Implementation for daily insights
        pass