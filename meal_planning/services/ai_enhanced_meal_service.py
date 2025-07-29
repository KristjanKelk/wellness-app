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
        Generate an intelligent meal plan using Spoonacular + AI analysis
        
        Args:
            nutrition_profile: User's nutrition profile
            days: Number of days to plan for
            generation_options: Optional generation parameters (max_cook_time, etc.)
        
        Returns:
            Complete meal plan with AI insights
        """
        try:
            # Step 1: Generate meal plan using Spoonacular
            logger.info(f"Generating {days}-day meal plan for user {nutrition_profile.user.id}")
            
            spoonacular_meal_plan = self.spoonacular_service.create_personalized_meal_plan(
                nutrition_profile, days, generation_options or {}
            )
            
            # Step 2: Normalize the data and save recipes to database
            time_frame = "week" if days > 1 else "day"
            normalized_plan = self.spoonacular_service.normalize_meal_plan_data(
                spoonacular_meal_plan, time_frame, nutrition_profile.user
            )
            
            # Step 3: Enhance with AI analysis
            ai_enhanced_plan = self._add_ai_analysis(normalized_plan, nutrition_profile)
            
            # Step 4: Calculate nutritional scores
            scores = self._calculate_nutritional_scores(ai_enhanced_plan, nutrition_profile)
            ai_enhanced_plan['scores'] = scores
            
            logger.info("Successfully generated AI-enhanced meal plan")
            return ai_enhanced_plan
            
        except SpoonacularAPIError as e:
            logger.error(f"Spoonacular API error: {str(e)}")
            # Fallback to basic meal plan if Spoonacular fails
            return self._generate_fallback_meal_plan(nutrition_profile, days)
        except Exception as e:
            logger.error(f"Unexpected error generating meal plan: {str(e)}")
            raise

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
        
        # Simple fallback - you could implement a basic meal plan here
        # or use cached/default recipes
        return {
            'status': 'fallback',
            'message': 'Generated basic meal plan due to API limitations',
            'days': days,
            'meals': {},
            'ai_insights': {
                'summary': 'Basic meal plan generated. Please try again later for enhanced features.',
                'recommendations': ['Ensure you eat balanced meals', 'Stay hydrated', 'Include variety in your diet']
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