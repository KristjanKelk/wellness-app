import openai
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from .enhanced_spoonacular_service import EnhancedSpoonacularService, SpoonacularAPIError
from ..models import NutritionProfile, MealPlan, Recipe
from datetime import datetime, timedelta, date
import json
from decouple import config

logger = logging.getLogger('nutrition.ai_enhanced_meal')


class AIEnhancedMealService:
    """
    AI-Enhanced Meal Planning Service that combines:
    1. Spoonacular's native meal plan generation
    2. OpenAI's nutritional analysis and recommendations
    3. Seamless user experience
    """

    def __init__(self):
        self.spoonacular_service = EnhancedSpoonacularService()
        openai.api_key = config('OPENAI_API_KEY')

    def generate_smart_meal_plan(self, nutrition_profile: NutritionProfile, days: int = 7, generation_options: Dict = None) -> Dict:
        """
        Generate an intelligent meal plan using sequential AI prompting approach
        
        Sequential Prompting Steps:
        1. Initial Assessment: Analyze user profile to define meal plan strategy
        2. Meal Structure: Design specific meals and timing based on nutrition profile
        3. Recipe Generation: Create detailed recipes with nutritional analysis  
        4. Nutritional Analysis: Evaluate nutritional balance and make adjustments
        5. Refinement: Final optimization and recommendations
        
        Args:
            nutrition_profile: User's nutrition profile
            days: Number of days to plan for
            generation_options: Optional generation parameters (max_cook_time, etc.)
        
        Returns:
            Complete meal plan with AI insights
        """
        try:
            logger.info(f"Generating {days}-day meal plan using sequential AI prompting for user {nutrition_profile.user.id}")
            
            # Sequential Prompting Step 1: Initial Assessment
            meal_strategy = self._step1_analyze_profile(nutrition_profile, days, generation_options)
            
            # Sequential Prompting Step 2: Meal Structure Design
            meal_structure = self._step2_design_meal_structure(meal_strategy, nutrition_profile)
            
            # Sequential Prompting Step 3: Recipe Generation
            detailed_meal_plan = self._step3_generate_recipes(meal_structure, nutrition_profile)
            
            # Sequential Prompting Step 4: Nutritional Analysis
            analyzed_plan = self._step4_nutritional_analysis(detailed_meal_plan, nutrition_profile)
            
            # Sequential Prompting Step 5: Refinement
            final_plan = self._step5_refinement(analyzed_plan, nutrition_profile)
            
            logger.info("Successfully generated AI-enhanced meal plan using sequential prompting")
            return final_plan
            
        except SpoonacularAPIError as e:
            logger.error(f"Spoonacular API error: {str(e)}")
            # Fallback to basic meal plan if Spoonacular fails
            return self._generate_fallback_meal_plan(nutrition_profile, days)
        except Exception as e:
            logger.error(f"Unexpected error generating meal plan: {str(e)}")
            # Fallback to traditional approach
            return self._generate_traditional_meal_plan(nutrition_profile, days, generation_options)

    def _add_ai_analysis(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Add OpenAI nutritional analysis to the meal plan"""
        try:
            # Prepare context for AI analysis
            context = self._prepare_ai_context(meal_plan, nutrition_profile)
            
            # Get AI analysis
            ai_insights = self._get_openai_analysis(context)
            
            # Add insights to meal plan
            meal_plan['ai_insights'] = ai_insights
            
            # Add recommendations for each meal if it's a multi-day plan
            if 'days' in meal_plan:
                for day in meal_plan['days']:
                    day['recommendations'] = self._get_daily_recommendations(day, nutrition_profile)
            elif 'meals' in meal_plan:
                meal_plan['recommendations'] = self._get_daily_recommendations(meal_plan, nutrition_profile)
            
            return meal_plan
            
        except Exception as e:
            logger.warning(f"AI analysis failed, continuing without insights: {str(e)}")
            meal_plan['ai_insights'] = {
                'summary': 'AI analysis temporarily unavailable',
                'recommendations': []
            }
            return meal_plan

    # ===== SEQUENTIAL PROMPTING IMPLEMENTATION =====
    
    def _step1_analyze_profile(self, nutrition_profile: NutritionProfile, days: int, generation_options: Dict) -> Dict:
        """
        Step 1: Analyze user profile to define meal plan strategy
        """
        try:
            prompt = f"""
            As a certified nutritionist, analyze this user profile and recommend a meal planning strategy:

            USER PROFILE:
            - Age: {getattr(nutrition_profile.user, 'age', 'N/A')}
            - Calorie Target: {nutrition_profile.calorie_target} kcal/day
            - Protein Target: {nutrition_profile.protein_target}g
            - Carb Target: {nutrition_profile.carb_target}g  
            - Fat Target: {nutrition_profile.fat_target}g
            - Meals per day: {nutrition_profile.meals_per_day}
            - Dietary Preferences: {', '.join(nutrition_profile.dietary_preferences or ['None'])}
            - Allergies/Intolerances: {', '.join(nutrition_profile.allergies_intolerances or ['None'])}
            - Cuisine Preferences: {', '.join(nutrition_profile.cuisine_preferences or ['None'])}
            - Disliked Ingredients: {', '.join(nutrition_profile.disliked_ingredients or ['None'])}

            PLAN REQUIREMENTS:
            - Duration: {days} days
            - Max cooking time: {generation_options.get('max_cook_time', 'flexible')} minutes
            - Budget consideration: {generation_options.get('budget_level', 'moderate')}

            Please provide a strategic analysis including:
            1. Recommended macro distribution strategy
            2. Optimal meal timing and frequency
            3. Key nutritional priorities
            4. Potential challenges and solutions
            5. Meal prep recommendations
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )

            strategy_text = response.choices[0].message.content
            
            return {
                'strategy_analysis': strategy_text,
                'calorie_target': nutrition_profile.calorie_target,
                'macro_targets': {
                    'protein': nutrition_profile.protein_target,
                    'carbs': nutrition_profile.carb_target,
                    'fat': nutrition_profile.fat_target
                },
                'meals_per_day': nutrition_profile.meals_per_day,
                'days': days,
                'preferences': {
                    'dietary': nutrition_profile.dietary_preferences or [],
                    'allergies': nutrition_profile.allergies_intolerances or [],
                    'cuisines': nutrition_profile.cuisine_preferences or [],
                    'dislikes': nutrition_profile.disliked_ingredients or []
                }
            }

        except Exception as e:
            logger.error(f"Step 1 analysis failed: {str(e)}")
            # Return basic strategy
            return {
                'strategy_analysis': 'Using standard balanced nutrition approach',
                'calorie_target': nutrition_profile.calorie_target,
                'macro_targets': {
                    'protein': nutrition_profile.protein_target,
                    'carbs': nutrition_profile.carb_target,
                    'fat': nutrition_profile.fat_target
                },
                'meals_per_day': nutrition_profile.meals_per_day,
                'days': days
            }

    def _step2_design_meal_structure(self, meal_strategy: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """
        Step 2: Design specific meal structure and timing
        """
        try:
            prompt = f"""
            Based on this nutritional strategy, design a detailed meal structure:

            STRATEGY ANALYSIS:
            {meal_strategy['strategy_analysis']}

            TARGETS:
            - Daily Calories: {meal_strategy['calorie_target']}
            - Protein: {meal_strategy['macro_targets']['protein']}g
            - Carbs: {meal_strategy['macro_targets']['carbs']}g
            - Fat: {meal_strategy['macro_targets']['fat']}g
            - Meals per day: {meal_strategy['meals_per_day']}

            Please design a {meal_strategy['days']}-day meal structure with:
            1. Specific meal types (breakfast, lunch, dinner, snacks)
            2. Calorie distribution per meal
            3. Macro distribution per meal
            4. Optimal timing suggestions
            5. Meal complexity levels (simple/moderate/complex)

            Format as a structured plan for each day.
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )

            structure_text = response.choices[0].message.content

            # Create structured meal framework
            meal_structure = {
                'structure_design': structure_text,
                'daily_framework': self._create_meal_framework(meal_strategy),
                'strategy': meal_strategy
            }

            return meal_structure

        except Exception as e:
            logger.error(f"Step 2 structure design failed: {str(e)}")
            return {
                'structure_design': 'Using standard meal structure',
                'daily_framework': self._create_meal_framework(meal_strategy),
                'strategy': meal_strategy
            }

    def _step3_generate_recipes(self, meal_structure: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """
        Step 3: Generate specific recipes for each meal
        """
        try:
            # Use Spoonacular to get actual recipes
            spoonacular_meal_plan = self.spoonacular_service.create_personalized_meal_plan(
                nutrition_profile, meal_structure['strategy']['days'], {}
            )
            
            # Normalize the data
            time_frame = "week" if meal_structure['strategy']['days'] > 1 else "day"
            normalized_plan = self.spoonacular_service.normalize_meal_plan_data(
                spoonacular_meal_plan, time_frame, nutrition_profile.user
            )

            # Enhance with AI recipe suggestions
            prompt = f"""
            Review these generated recipes and suggest improvements:

            MEAL STRUCTURE PLAN:
            {meal_structure['structure_design']}

            GENERATED RECIPES:
            {self._format_recipes_for_ai(normalized_plan)}

            Please provide:
            1. Recipe quality assessment
            2. Nutritional balance evaluation
            3. Variety and appeal rating
            4. Suggestions for recipe swaps or modifications
            5. Cooking complexity analysis
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )

            recipe_analysis = response.choices[0].message.content

            normalized_plan['recipe_analysis'] = recipe_analysis
            normalized_plan['meal_structure'] = meal_structure

            return normalized_plan

        except Exception as e:
            logger.error(f"Step 3 recipe generation failed: {str(e)}")
            return self._generate_fallback_meal_plan(nutrition_profile, meal_structure['strategy']['days'])

    def _step4_nutritional_analysis(self, detailed_meal_plan: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """
        Step 4: Comprehensive nutritional analysis and evaluation
        """
        try:
            prompt = f"""
            As a registered dietitian, perform a comprehensive nutritional analysis:

            USER TARGETS:
            - Calories: {nutrition_profile.calorie_target}
            - Protein: {nutrition_profile.protein_target}g
            - Carbs: {nutrition_profile.carb_target}g  
            - Fat: {nutrition_profile.fat_target}g

            MEAL PLAN:
            {self._format_nutrition_for_ai(detailed_meal_plan)}

            PREVIOUS ANALYSIS:
            {detailed_meal_plan.get('recipe_analysis', 'No previous analysis')}

            Please provide:
            1. Target vs actual nutritional comparison
            2. Micronutrient analysis (vitamins, minerals)
            3. Fiber and sodium content evaluation
            4. Overall nutritional quality score (1-10)
            5. Specific recommendations for improvement
            6. Health benefits and potential concerns
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )

            nutritional_analysis = response.choices[0].message.content

            # Calculate nutritional scores
            scores = self._calculate_nutritional_scores(detailed_meal_plan, nutrition_profile)
            
            detailed_meal_plan['nutritional_analysis'] = nutritional_analysis
            detailed_meal_plan['scores'] = scores

            return detailed_meal_plan

        except Exception as e:
            logger.error(f"Step 4 nutritional analysis failed: {str(e)}")
            detailed_meal_plan['nutritional_analysis'] = 'Nutritional analysis temporarily unavailable'
            detailed_meal_plan['scores'] = self._calculate_nutritional_scores(detailed_meal_plan, nutrition_profile)
            return detailed_meal_plan

    def _step5_refinement(self, analyzed_plan: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """
        Step 5: Final refinement and optimization
        """
        try:
            prompt = f"""
            Provide final optimization recommendations for this meal plan:

            NUTRITIONAL ANALYSIS:
            {analyzed_plan.get('nutritional_analysis', 'No analysis available')}

            NUTRITIONAL SCORES:
            - Balance Score: {analyzed_plan.get('scores', {}).get('balance_score', 'N/A')}
            - Variety Score: {analyzed_plan.get('scores', {}).get('variety_score', 'N/A')}
            - Preference Match: {analyzed_plan.get('scores', {}).get('preference_match_score', 'N/A')}

            Please provide:
            1. Overall meal plan rating (1-10)
            2. Top 3 strengths of this plan
            3. Top 3 areas for improvement
            4. Practical tips for meal prep and execution
            5. Long-term sustainability assessment
            6. Personalized motivational message for the user
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.4
            )

            final_insights = response.choices[0].message.content

            analyzed_plan['ai_insights'] = {
                'final_optimization': final_insights,
                'generation_method': 'sequential_prompting',
                'analysis_steps': [
                    'Profile Strategy Analysis',
                    'Meal Structure Design', 
                    'Recipe Generation',
                    'Nutritional Analysis',
                    'Final Refinement'
                ]
            }

            return analyzed_plan

        except Exception as e:
            logger.error(f"Step 5 refinement failed: {str(e)}")
            analyzed_plan['ai_insights'] = {
                'final_optimization': 'Final optimization temporarily unavailable',
                'generation_method': 'sequential_prompting_partial'
            }
            return analyzed_plan

    def _create_meal_framework(self, meal_strategy: Dict) -> Dict:
        """Create basic meal framework structure"""
        meals_per_day = meal_strategy['meals_per_day']
        daily_calories = meal_strategy['calorie_target']
        
        if meals_per_day == 3:
            framework = {
                'breakfast': {'calories': int(daily_calories * 0.25), 'complexity': 'simple'},
                'lunch': {'calories': int(daily_calories * 0.35), 'complexity': 'moderate'},
                'dinner': {'calories': int(daily_calories * 0.40), 'complexity': 'moderate'}
            }
        elif meals_per_day == 4:
            framework = {
                'breakfast': {'calories': int(daily_calories * 0.20), 'complexity': 'simple'},
                'lunch': {'calories': int(daily_calories * 0.30), 'complexity': 'moderate'},
                'snack': {'calories': int(daily_calories * 0.15), 'complexity': 'simple'},
                'dinner': {'calories': int(daily_calories * 0.35), 'complexity': 'moderate'}
            }
        else:
            # Default 3-meal structure
            framework = {
                'breakfast': {'calories': int(daily_calories * 0.25), 'complexity': 'simple'},
                'lunch': {'calories': int(daily_calories * 0.35), 'complexity': 'moderate'},
                'dinner': {'calories': int(daily_calories * 0.40), 'complexity': 'moderate'}
            }
        
        return framework

    def _format_recipes_for_ai(self, meal_plan: Dict) -> str:
        """Format recipe data for AI analysis"""
        formatted = ""
        if 'meals' in meal_plan:
            for date, meals in meal_plan['meals'].items():
                formatted += f"\nDay {date}:\n"
                for meal in meals:
                    formatted += f"- {meal.get('title', 'Unknown')} ({meal.get('meal_type', 'Unknown type')})\n"
        return formatted

    def _format_nutrition_for_ai(self, meal_plan: Dict) -> str:
        """Format nutritional data for AI analysis"""
        nutrition = meal_plan.get('nutrition', {})
        return f"""
        Total Calories: {nutrition.get('calories', 0)}
        Protein: {nutrition.get('protein', 0)}g
        Carbs: {nutrition.get('carbs', 0)}g
        Fat: {nutrition.get('fat', 0)}g
        Fiber: {nutrition.get('fiber', 0)}g
        """

    def _generate_traditional_meal_plan(self, nutrition_profile: NutritionProfile, days: int, generation_options: Dict) -> Dict:
        """Fallback to traditional meal plan generation"""
        try:
            spoonacular_meal_plan = self.spoonacular_service.create_personalized_meal_plan(
                nutrition_profile, days, generation_options or {}
            )
            
            time_frame = "week" if days > 1 else "day"
            normalized_plan = self.spoonacular_service.normalize_meal_plan_data(
                spoonacular_meal_plan, time_frame, nutrition_profile.user
            )
            
            # Add basic AI analysis
            ai_enhanced_plan = self._add_ai_analysis(normalized_plan, nutrition_profile)
            
            scores = self._calculate_nutritional_scores(ai_enhanced_plan, nutrition_profile)
            ai_enhanced_plan['scores'] = scores
            
            return ai_enhanced_plan
        except Exception as e:
            logger.error(f"Traditional meal plan generation failed: {str(e)}")
            return self._generate_fallback_meal_plan(nutrition_profile, days)

    def _prepare_ai_context(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> str:
        """Prepare context for OpenAI analysis"""
        context = f"""
        Nutrition Profile:
        - Calorie Target: {nutrition_profile.calorie_target}
        - Protein Target: {nutrition_profile.protein_target}g
        - Carb Target: {nutrition_profile.carb_target}g
        - Fat Target: {nutrition_profile.fat_target}g
        - Dietary Preferences: {', '.join(nutrition_profile.dietary_preferences or [])}
        - Allergies/Intolerances: {', '.join(nutrition_profile.allergies_intolerances or [])}
        - Cuisine Preferences: {', '.join(nutrition_profile.cuisine_preferences or [])}
        
        Meal Plan:
        """
        
        if 'days' in meal_plan:
            for day in meal_plan['days']:
                context += f"\n{day.get('day', 'Day')}:\n"
                context += self._format_day_for_ai(day)
        else:
            context += self._format_day_for_ai(meal_plan)
        
        return context

    def _format_day_for_ai(self, day_data: Dict) -> str:
        """Format a single day's data for AI analysis"""
        formatted = ""
        nutrition = day_data.get('nutrition', {})
        formatted += f"Total: {nutrition.get('calories', 0)} cal, {nutrition.get('protein', 0)}g protein, {nutrition.get('carbs', 0)}g carbs, {nutrition.get('fat', 0)}g fat\n"
        
        for meal_type, meals in day_data.get('meals', {}).items():
            if meals:
                formatted += f"{meal_type.title()}:\n"
                for meal in meals:
                    formatted += f"  - {meal.get('title', 'Unknown')}\n"
        
        return formatted

    def _get_openai_analysis(self, context: str) -> Dict:
        """Get nutritional analysis from OpenAI"""
        try:
            prompt = f"""
            As a registered dietitian, analyze this meal plan and provide insights:

            {context}

            Please provide:
            1. Overall nutritional balance assessment
            2. Specific recommendations for improvement
            3. Potential nutritional gaps or excesses
            4. Tips for meal prep and variety
            5. Overall healthiness score (1-10)

            Respond in JSON format with keys: summary, recommendations, nutritional_gaps, meal_prep_tips, healthiness_score
            """

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a registered dietitian providing nutritional analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured data
                return {
                    "summary": content,
                    "recommendations": [],
                    "nutritional_gaps": [],
                    "meal_prep_tips": [],
                    "healthiness_score": 7
                }

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            return {
                "summary": "AI analysis temporarily unavailable",
                "recommendations": [],
                "nutritional_gaps": [],
                "meal_prep_tips": [],
                "healthiness_score": 5
            }

    def _get_daily_recommendations(self, day_data: Dict, nutrition_profile: NutritionProfile) -> List[str]:
        """Get AI recommendations for a specific day"""
        try:
            nutrition = day_data.get('nutrition', {})
            recommendations = []
            
            # Check calorie targets
            calories = nutrition.get('calories', 0)
            target_calories = nutrition_profile.calorie_target
            
            if calories < target_calories * 0.8:
                recommendations.append("Consider adding a healthy snack to meet your calorie goals")
            elif calories > target_calories * 1.2:
                recommendations.append("Consider smaller portions to stay within calorie targets")
            
            # Check protein targets
            protein = nutrition.get('protein', 0)
            target_protein = nutrition_profile.protein_target
            
            if protein < target_protein * 0.8:
                recommendations.append("Add more protein-rich foods like lean meats, fish, or legumes")
            
            # Check for meal variety
            meals = day_data.get('meals', {})
            total_meals = sum(len(meal_list) for meal_list in meals.values())
            
            if total_meals < 3:
                recommendations.append("Consider adding more meals or snacks for better nutrient distribution")
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to generate daily recommendations: {str(e)}")
            return []

    def _calculate_nutritional_scores(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Calculate nutritional quality scores"""
        scores = {
            'balance_score': 5.0,
            'variety_score': 5.0,
            'preference_match_score': 5.0,
            'overall_score': 5.0
        }
        
        try:
            # Calculate balance score based on macro targets
            if 'days' in meal_plan:
                daily_scores = []
                for day in meal_plan['days']:
                    daily_score = self._calculate_daily_balance_score(day, nutrition_profile)
                    daily_scores.append(daily_score)
                scores['balance_score'] = sum(daily_scores) / len(daily_scores)
            else:
                scores['balance_score'] = self._calculate_daily_balance_score(meal_plan, nutrition_profile)
            
            # Calculate variety score
            scores['variety_score'] = self._calculate_variety_score(meal_plan)
            
            # Calculate preference match score
            scores['preference_match_score'] = self._calculate_preference_match_score(meal_plan, nutrition_profile)
            
            # Overall score is weighted average
            scores['overall_score'] = (
                scores['balance_score'] * 0.4 +
                scores['variety_score'] * 0.3 +
                scores['preference_match_score'] * 0.3
            )
            
        except Exception as e:
            logger.warning(f"Error calculating nutritional scores: {str(e)}")
        
        return scores

    def _calculate_daily_balance_score(self, day_data: Dict, nutrition_profile: NutritionProfile) -> float:
        """Calculate nutritional balance score for a single day"""
        nutrition = day_data.get('nutrition', {})
        
        # Compare actual vs target macros
        calorie_ratio = min(nutrition.get('calories', 0) / nutrition_profile.calorie_target, 2.0)
        protein_ratio = min(nutrition.get('protein', 0) / nutrition_profile.protein_target, 2.0)
        carb_ratio = min(nutrition.get('carbs', 0) / nutrition_profile.carb_target, 2.0)
        fat_ratio = min(nutrition.get('fat', 0) / nutrition_profile.fat_target, 2.0)
        
        # Score based on how close to targets (ideal is 1.0)
        calorie_score = 10 - abs(1.0 - calorie_ratio) * 5
        protein_score = 10 - abs(1.0 - protein_ratio) * 5
        carb_score = 10 - abs(1.0 - carb_ratio) * 5
        fat_score = 10 - abs(1.0 - fat_ratio) * 5
        
        # Average and normalize to 0-10 scale
        balance_score = (calorie_score + protein_score + carb_score + fat_score) / 4
        return max(0, min(10, balance_score))

    def _calculate_variety_score(self, meal_plan: Dict) -> float:
        """Calculate variety score based on meal diversity"""
        unique_meals = set()
        total_meals = 0
        
        if 'days' in meal_plan:
            for day in meal_plan['days']:
                for meal_type, meals in day.get('meals', {}).items():
                    for meal in meals:
                        unique_meals.add(meal.get('title', ''))
                        total_meals += 1
        else:
            for meal_type, meals in meal_plan.get('meals', {}).items():
                for meal in meals:
                    unique_meals.add(meal.get('title', ''))
                    total_meals += 1
        
        if total_meals == 0:
            return 5.0
        
        variety_ratio = len(unique_meals) / total_meals
        return min(10, variety_ratio * 10)

    def _calculate_preference_match_score(self, meal_plan: Dict, nutrition_profile: NutritionProfile) -> float:
        """Calculate how well the meal plan matches user preferences"""
        # This is a simplified implementation
        # In a real system, you'd check ingredients against preferences/allergies
        return 8.0  # Default good score

    def _generate_fallback_meal_plan(self, nutrition_profile: NutritionProfile, days: int) -> Dict:
        """Generate a basic meal plan when Spoonacular is unavailable"""
        logger.info("Generating fallback meal plan")
        
        # Create basic meals for each day
        from datetime import date, timedelta
        
        # Basic meal templates
        basic_meals = {
            'breakfast': [
                {
                    'id': 'fallback_breakfast_1',
                    'title': 'Healthy Oatmeal with Berries',
                    'meal_type': 'breakfast',
                    'time': '08:00',
                    'calories_per_serving': 350,
                    'protein_per_serving': 12,
                    'carbs_per_serving': 65,
                    'fat_per_serving': 8,
                    'servings': 1,
                    'readyInMinutes': 10,
                    'image': '',
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
                    'id': 'fallback_breakfast_2',
                    'title': 'Scrambled Eggs with Toast',
                    'meal_type': 'breakfast',
                    'time': '08:00',
                    'calories_per_serving': 320,
                    'protein_per_serving': 18,
                    'carbs_per_serving': 25,
                    'fat_per_serving': 16,
                    'servings': 1,
                    'readyInMinutes': 8,
                    'image': '',
                    'summary': 'Classic protein-rich breakfast with scrambled eggs and whole grain toast.',
                    'ingredients_data': [
                        {'original': '2 large eggs'},
                        {'original': '2 slices whole grain bread'},
                        {'original': '1 tbsp butter'},
                        {'original': 'Salt and pepper to taste'},
                        {'original': '1 tbsp milk'}
                    ],
                    'instructions': [
                        {'step': 'Whisk eggs with milk, salt, and pepper'},
                        {'step': 'Heat butter in pan and scramble eggs'},
                        {'step': 'Toast bread and serve alongside eggs'}
                    ]
                }
            ],
            'lunch': [
                {
                    'id': 'fallback_lunch_1',
                    'title': 'Mediterranean Quinoa Bowl',
                    'meal_type': 'lunch',
                    'time': '12:30',
                    'calories_per_serving': 450,
                    'protein_per_serving': 16,
                    'carbs_per_serving': 58,
                    'fat_per_serving': 18,
                    'servings': 1,
                    'readyInMinutes': 15,
                    'image': '',
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
                    'id': 'fallback_lunch_2',
                    'title': 'Grilled Chicken Salad',
                    'meal_type': 'lunch',
                    'time': '12:30',
                    'calories_per_serving': 380,
                    'protein_per_serving': 32,
                    'carbs_per_serving': 15,
                    'fat_per_serving': 22,
                    'servings': 1,
                    'readyInMinutes': 20,
                    'image': '',
                    'summary': 'Protein-packed salad with grilled chicken and fresh vegetables.',
                    'ingredients_data': [
                        {'original': '4 oz grilled chicken breast'},
                        {'original': '2 cups mixed greens'},
                        {'original': '1/4 cup cherry tomatoes'},
                        {'original': '1/4 avocado, sliced'},
                        {'original': '2 tbsp olive oil vinaigrette'}
                    ],
                    'instructions': [
                        {'step': 'Grill chicken breast until cooked through'},
                        {'step': 'Arrange mixed greens in bowl'},
                        {'step': 'Top with sliced chicken, tomatoes, and avocado'},
                        {'step': 'Drizzle with vinaigrette and serve'}
                    ]
                }
            ],
            'dinner': [
                {
                    'id': 'fallback_dinner_1',
                    'title': 'Baked Salmon with Vegetables',
                    'meal_type': 'dinner',
                    'time': '19:00',
                    'calories_per_serving': 520,
                    'protein_per_serving': 35,
                    'carbs_per_serving': 25,
                    'fat_per_serving': 28,
                    'servings': 1,
                    'readyInMinutes': 25,
                    'image': '',
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
                    'id': 'fallback_dinner_2',
                    'title': 'Lean Beef Stir-Fry',
                    'meal_type': 'dinner',
                    'time': '19:00',
                    'calories_per_serving': 480,
                    'protein_per_serving': 30,
                    'carbs_per_serving': 35,
                    'fat_per_serving': 22,
                    'servings': 1,
                    'readyInMinutes': 15,
                    'image': '',
                    'summary': 'Quick and nutritious stir-fry with lean beef and colorful vegetables.',
                    'ingredients_data': [
                        {'original': '4 oz lean beef strips'},
                        {'original': '1 cup mixed stir-fry vegetables'},
                        {'original': '1/2 cup brown rice, cooked'},
                        {'original': '1 tbsp olive oil'},
                        {'original': '2 tbsp low-sodium soy sauce'}
                    ],
                    'instructions': [
                        {'step': 'Heat oil in wok or large pan'},
                        {'step': 'Stir-fry beef until browned'},
                        {'step': 'Add vegetables and cook until tender-crisp'},
                        {'step': 'Add soy sauce and serve over brown rice'}
                    ]
                }
            ]
        }
        
        # Generate meals for each day
        import random
        meals_by_day = {}
        start_date = date.today()
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.isoformat()
            
            daily_meals = []
            
            # Select random meals for each meal type
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                if meal_type in basic_meals:
                    selected_meal = random.choice(basic_meals[meal_type]).copy()
                    daily_meals.append(selected_meal)
            
            meals_by_day[date_str] = daily_meals
        
        # Calculate basic nutrition totals
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        
        for day_meals in meals_by_day.values():
            for meal in day_meals:
                total_calories += meal.get('calories_per_serving', 0)
                total_protein += meal.get('protein_per_serving', 0)
                total_carbs += meal.get('carbs_per_serving', 0)
                total_fat += meal.get('fat_per_serving', 0)
        
        return {
            'status': 'fallback',
            'message': 'Generated basic meal plan due to API limitations',
            'days': days,
            'meals': meals_by_day,
            'nutrition': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat
            },
            'ai_insights': {
                'final_optimization': 'Basic meal plan generated. Try regenerating for enhanced AI features.',
                'generation_method': 'fallback'
            },
            'nutritional_analysis': 'Basic nutritional balance provided. Regenerate for detailed analysis.',
            'scores': {
                'balance_score': 7,
                'variety_score': 6,
                'preference_match_score': 6,
                'overall_score': 6.3
            }
        }

    def analyze_meal_plan_with_ai(self, meal_plan_data: Dict, nutrition_profile: NutritionProfile) -> Dict:
        """Standalone method to analyze any meal plan with AI"""
        try:
            context = self._prepare_ai_context(meal_plan_data, nutrition_profile)
            ai_insights = self._get_openai_analysis(context)
            
            return {
                'ai_analysis': ai_insights,
                'scores': self._calculate_nutritional_scores(meal_plan_data, nutrition_profile),
                'recommendations': self._get_daily_recommendations(meal_plan_data, nutrition_profile)
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                'ai_analysis': {'summary': 'Analysis failed', 'recommendations': []},
                'scores': {'overall_score': 5.0},
                'recommendations': []
            }

    def get_spoonacular_meal_plan(self, nutrition_profile: NutritionProfile, start_date: str = None) -> Dict:
        """Get meal plan from Spoonacular with user connection"""
        try:
            if not nutrition_profile.spoonacular_username or not nutrition_profile.spoonacular_user_hash:
                # Connect user to Spoonacular
                connection = self.spoonacular_service.connect_user(
                    username=f"user_{nutrition_profile.user.id}",
                    first_name=nutrition_profile.user.first_name,
                    last_name=nutrition_profile.user.last_name,
                    email=nutrition_profile.user.email
                )
                
                # Save connection details
                nutrition_profile.spoonacular_username = connection.get('username')
                nutrition_profile.spoonacular_user_hash = connection.get('hash')
                nutrition_profile.save()
            
            # Get meal plan from Spoonacular
            if not start_date:
                start_date = date.today().isoformat()
            
            meal_plan = self.spoonacular_service.get_meal_plan_week(
                username=nutrition_profile.spoonacular_username,
                start_date=start_date,
                hash_value=nutrition_profile.spoonacular_user_hash
            )
            
            # Add AI analysis
            enhanced_plan = self._add_ai_analysis(meal_plan, nutrition_profile)
            
            return enhanced_plan
            
        except SpoonacularAPIError as e:
            logger.error(f"Failed to get Spoonacular meal plan: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def get_spoonacular_shopping_list(self, nutrition_profile: NutritionProfile) -> Dict:
        """Get shopping list from Spoonacular"""
        try:
            if not nutrition_profile.spoonacular_username or not nutrition_profile.spoonacular_user_hash:
                raise SpoonacularAPIError("User not connected to Spoonacular")
            
            shopping_list = self.spoonacular_service.get_shopping_list(
                username=nutrition_profile.spoonacular_username,
                hash_value=nutrition_profile.spoonacular_user_hash
            )
            
            return shopping_list
            
        except Exception as e:
            logger.error(f"Failed to get shopping list: {str(e)}")
            raise