import requests
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta, date
import json
from decouple import config

logger = logging.getLogger('nutrition.spoonacular')


class SpoonacularAPIError(Exception):
    """Custom exception for Spoonacular API errors"""
    pass


class RateLimitExceeded(SpoonacularAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class EnhancedSpoonacularService:
    """
    Enhanced Spoonacular service for seamless meal planning integration
    This service replaces custom meal plan generation with Spoonacular's native capabilities
    """

    def __init__(self):
        self.api_key = config('SPOONACULAR_API_KEY')
        self.base_url = 'https://api.spoonacular.com'
        
        # Rate limiting - Spoonacular free tier: 150 requests/day, 1 request/second
        self.rate_limit = {
            'requests_per_day': 150,
            'requests_per_second': 1
        }

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        try:
            # Check daily limit
            requests_today = cache.get('spoonacular_requests_today', 0)
            if requests_today >= self.rate_limit['requests_per_day']:
                logger.warning(f"Daily rate limit exceeded: {requests_today}/{self.rate_limit['requests_per_day']}")
                raise RateLimitExceeded("Daily API rate limit exceeded")

            # Check per-second limit
            last_request = cache.get('spoonacular_last_request')
            if last_request:
                time_since_last = time.time() - last_request
                if time_since_last < 1:  # 1 second minimum
                    sleep_time = 1 - time_since_last
                    logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
        except Exception as e:
            logger.warning(f"Cache unavailable for rate limiting: {e}")

        return True

    def _update_rate_limit_counters(self):
        """Update rate limiting counters after successful request"""
        try:
            requests_today = cache.get('spoonacular_requests_today', 0)
            cache.set('spoonacular_requests_today', requests_today + 1, 86400)  # 24 hours
            cache.set('spoonacular_last_request', time.time(), 3600)  # 1 hour
        except Exception as e:
            logger.warning(f"Cache unavailable for updating rate limit counters: {e}")

    def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET', data: Dict = None) -> Dict:
        """Make HTTP request to Spoonacular API with rate limiting"""
        if params is None:
            params = {}

        # Add API key to params
        params['apiKey'] = self.api_key
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Check rate limit
        self._check_rate_limit()

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, params=params, json=data, timeout=30)
            else:
                raise SpoonacularAPIError(f"Unsupported HTTP method: {method}")

            # Update rate limit counters
            self._update_rate_limit_counters()

            if response.status_code == 401:
                raise SpoonacularAPIError("Invalid API key")
            elif response.status_code == 402:
                raise RateLimitExceeded("API quota exceeded")
            elif response.status_code == 429:
                raise RateLimitExceeded("Rate limit exceeded")
            elif not response.ok:
                raise SpoonacularAPIError(f"API request failed: {response.status_code} - {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise SpoonacularAPIError(f"Request failed: {str(e)}")

    def search_recipes(self, query: str = "", **filters) -> Dict:
        """
        Search for recipes using Spoonacular's complex search
        
        Args:
            query: Recipe search query
            **filters: Additional filters (diet, cuisine, intolerances, etc.)
        
        Returns:
            Dictionary with search results
        """
        params = {
            'query': query,
            'number': filters.get('number', 12),
            'addRecipeInformation': True,
            'addRecipeNutrition': True,
            'fillIngredients': True
        }

        # Add dietary filters
        if filters.get('diet'):
            params['diet'] = ','.join(filters['diet']) if isinstance(filters['diet'], list) else filters['diet']
        
        if filters.get('intolerances'):
            params['intolerances'] = ','.join(filters['intolerances']) if isinstance(filters['intolerances'], list) else filters['intolerances']
        
        if filters.get('cuisine'):
            params['cuisine'] = ','.join(filters['cuisine']) if isinstance(filters['cuisine'], list) else filters['cuisine']

        # Add nutritional filters
        for param in ['minCalories', 'maxCalories', 'minProtein', 'maxProtein', 'minCarbs', 'maxCarbs', 'minFat', 'maxFat']:
            if filters.get(param):
                params[param] = filters[param]

        # Add other filters
        if filters.get('maxReadyTime'):
            params['maxReadyTime'] = filters['maxReadyTime']
        
        if filters.get('includeIngredients'):
            params['includeIngredients'] = ','.join(filters['includeIngredients']) if isinstance(filters['includeIngredients'], list) else filters['includeIngredients']

        return self._make_request('recipes/complexSearch', params)

    def generate_meal_plan(self, 
                          time_frame: str = "day",
                          target_calories: int = 2000,
                          diet: str = "",
                          exclude: str = "") -> Dict:
        """
        Generate a meal plan using Spoonacular's meal plan generator
        
        Args:
            time_frame: "day" or "week"
            target_calories: Target daily calories
            diet: Diet type (vegetarian, vegan, keto, etc.)
            exclude: Comma-separated ingredients to exclude
        
        Returns:
            Generated meal plan
        """
        params = {
            'timeFrame': time_frame,
            'targetCalories': target_calories,
        }

        if diet:
            params['diet'] = diet
        if exclude:
            params['exclude'] = exclude

        return self._make_request('mealplanner/generate', params)

    def connect_user(self, username: str, first_name: str = "", last_name: str = "", email: str = "") -> Dict:
        """
        Connect a user to Spoonacular for personalized meal planning
        
        Args:
            username: User's username
            first_name: User's first name
            last_name: User's last name
            email: User's email
        
        Returns:
            Connection details including spoonacular username and hash
        """
        data = {
            'username': username,
            'firstName': first_name,
            'lastName': last_name,
            'email': email
        }

        return self._make_request('users/connect', method='POST', data=data)

    def get_meal_plan_week(self, username: str, start_date: str, hash_value: str) -> Dict:
        """
        Get a user's meal plan for a specific week
        
        Args:
            username: Spoonacular username
            start_date: Start date in YYYY-MM-DD format
            hash_value: User hash from Spoonacular
        
        Returns:
            Week's meal plan
        """
        params = {
            'username': username,
            'startDate': start_date,
            'hash': hash_value
        }

        return self._make_request('mealplanner/week', params)

    def get_meal_plan_day(self, username: str, date_str: str, hash_value: str) -> Dict:
        """
        Get a user's meal plan for a specific day
        
        Args:
            username: Spoonacular username
            date_str: Date in YYYY-MM-DD format
            hash_value: User hash from Spoonacular
        
        Returns:
            Day's meal plan
        """
        params = {
            'username': username,
            'date': date_str,
            'hash': hash_value
        }

        return self._make_request('mealplanner/day', params)

    def add_to_meal_plan(self, username: str, date_str: str, slot: int, position: int, 
                        item_type: str, value: Dict, hash_value: str) -> Dict:
        """
        Add an item to a user's meal plan
        
        Args:
            username: Spoonacular username
            date_str: Date in YYYY-MM-DD format
            slot: Meal slot (1=breakfast, 2=lunch, 3=dinner)
            position: Position in the slot
            item_type: Type of item (RECIPE, INGREDIENTS, CUSTOM_FOOD)
            value: Item details
            hash_value: User hash
        
        Returns:
            Success confirmation
        """
        data = {
            'username': username,
            'date': date_str,
            'slot': slot,
            'position': position,
            'type': item_type,
            'value': value,
            'hash': hash_value
        }

        return self._make_request('mealplanner/items', method='POST', data=data)

    def get_shopping_list(self, username: str, hash_value: str) -> Dict:
        """
        Get a user's shopping list
        
        Args:
            username: Spoonacular username
            hash_value: User hash
        
        Returns:
            Shopping list
        """
        params = {
            'username': username,
            'hash': hash_value
        }

        return self._make_request('mealplanner/shopping-list', params)

    def add_to_shopping_list(self, username: str, hash_value: str, item: str, aisle: str = "", parse: bool = True) -> Dict:
        """
        Add an item to the shopping list
        
        Args:
            username: Spoonacular username
            hash_value: User hash
            item: Item to add
            aisle: Grocery aisle
            parse: Whether to parse the item
        
        Returns:
            Updated shopping list
        """
        data = {
            'username': username,
            'hash': hash_value,
            'item': item,
            'aisle': aisle,
            'parse': parse
        }

        return self._make_request('mealplanner/shopping-list/items', method='POST', data=data)

    def generate_shopping_list(self, username: str, start_date: str, end_date: str, hash_value: str) -> Dict:
        """
        Generate shopping list from meal plan
        
        Args:
            username: Spoonacular username
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            hash_value: User hash
        
        Returns:
            Generated shopping list
        """
        data = {
            'username': username,
            'startDate': start_date,
            'endDate': end_date,
            'hash': hash_value
        }

        return self._make_request('mealplanner/shopping-list/generate', method='POST', data=data)

    def get_recipe_information(self, recipe_id: int, include_nutrition: bool = True) -> Dict:
        """
        Get detailed recipe information
        
        Args:
            recipe_id: Spoonacular recipe ID
            include_nutrition: Whether to include nutrition data
        
        Returns:
            Recipe details
        """
        params = {
            'includeNutrition': include_nutrition
        }

        return self._make_request(f'recipes/{recipe_id}/information', params)

    def get_random_recipes(self, number: int = 1, include_tags: List[str] = None, exclude_tags: List[str] = None) -> Dict:
        """
        Get random recipes
        
        Args:
            number: Number of recipes to return
            include_tags: Tags that recipes must have
            exclude_tags: Tags that recipes must not have
        
        Returns:
            Random recipes
        """
        params = {
            'number': number
        }

        if include_tags:
            params['include-tags'] = ','.join(include_tags)
        if exclude_tags:
            params['exclude-tags'] = ','.join(exclude_tags)

        return self._make_request('recipes/random', params)

    def create_personalized_meal_plan(self, nutrition_profile, days: int = 7) -> Dict:
        """
        Create a personalized meal plan based on user's nutrition profile
        
        Args:
            nutrition_profile: User's nutrition profile
            days: Number of days to plan for
        
        Returns:
            Personalized meal plan
        """
        # Convert nutrition profile to Spoonacular parameters
        diet_mapping = {
            'vegetarian': 'vegetarian',
            'vegan': 'vegan',
            'pescatarian': 'pescatarian',
            'keto': 'ketogenic',
            'paleo': 'paleo',
            'mediterranean': 'mediterranean',
            'low_carb': 'ketogenic',
            'gluten_free': 'gluten free',
            'dairy_free': 'dairy free'
        }

        # Get primary diet
        diet = None
        if nutrition_profile.dietary_preferences:
            for pref in nutrition_profile.dietary_preferences:
                if pref in diet_mapping:
                    diet = diet_mapping[pref]
                    break

        # Create exclusions from allergies and intolerances
        exclusions = []
        intolerance_mapping = {
            'nuts': 'tree nuts',
            'peanuts': 'peanuts',
            'dairy': 'dairy',
            'gluten': 'gluten',
            'eggs': 'eggs',
            'fish': 'fish',
            'shellfish': 'shellfish',
            'soy': 'soy',
            'sesame': 'sesame'
        }

        for allergy in nutrition_profile.allergies_intolerances or []:
            if allergy in intolerance_mapping:
                exclusions.append(intolerance_mapping[allergy])

        # Add disliked ingredients
        if nutrition_profile.disliked_ingredients:
            exclusions.extend(nutrition_profile.disliked_ingredients)

        # Generate meal plan
        if days == 1:
            meal_plan = self.generate_meal_plan(
                time_frame="day",
                target_calories=nutrition_profile.calorie_target,
                diet=diet or "",
                exclude=','.join(exclusions) if exclusions else ""
            )
        else:
            meal_plan = self.generate_meal_plan(
                time_frame="week",
                target_calories=nutrition_profile.calorie_target,
                diet=diet or "",
                exclude=','.join(exclusions) if exclusions else ""
            )

        return meal_plan

    def normalize_meal_plan_data(self, spoonacular_data: Dict, time_frame: str = "day") -> Dict:
        """
        Normalize Spoonacular meal plan data to our internal format
        
        Args:
            spoonacular_data: Raw data from Spoonacular
            time_frame: "day" or "week"
        
        Returns:
            Normalized meal plan data
        """
        if time_frame == "day":
            return self._normalize_day_meal_plan(spoonacular_data)
        else:
            return self._normalize_week_meal_plan(spoonacular_data)

    def _normalize_day_meal_plan(self, data: Dict) -> Dict:
        """Normalize a single day meal plan"""
        normalized = {
            'date': date.today().isoformat(),
            'meals': {
                'breakfast': [],
                'lunch': [],
                'dinner': []
            },
            'nutrition': {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0
            }
        }

        for meal in data.get('meals', []):
            meal_data = {
                'id': meal.get('id'),
                'title': meal.get('title', ''),
                'readyInMinutes': meal.get('readyInMinutes', 0),
                'servings': meal.get('servings', 1),
                'sourceUrl': meal.get('sourceUrl', ''),
                'image': meal.get('image', ''),
                'nutrition': self._extract_nutrition(meal)
            }

            # Determine meal type based on meal plan structure
            meal_type = 'lunch'  # Default
            if len(normalized['meals']['breakfast']) == 0:
                meal_type = 'breakfast'
            elif len(normalized['meals']['lunch']) == 0:
                meal_type = 'lunch'
            else:
                meal_type = 'dinner'

            normalized['meals'][meal_type].append(meal_data)

            # Add to total nutrition
            nutrition = meal_data['nutrition']
            normalized['nutrition']['calories'] += nutrition.get('calories', 0)
            normalized['nutrition']['protein'] += nutrition.get('protein', 0)
            normalized['nutrition']['carbs'] += nutrition.get('carbs', 0)
            normalized['nutrition']['fat'] += nutrition.get('fat', 0)

        return normalized

    def _normalize_week_meal_plan(self, data: Dict) -> Dict:
        """Normalize a week meal plan"""
        normalized = {
            'week': data.get('week', {}),
            'days': []
        }

        week_data = data.get('week', {})
        for day_key in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            if day_key in week_data:
                day_data = self._normalize_day_meal_plan({'meals': week_data[day_key].get('meals', [])})
                day_data['day'] = day_key
                normalized['days'].append(day_data)

        return normalized

    def _extract_nutrition(self, meal: Dict) -> Dict:
        """Extract nutrition information from meal data"""
        nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        }

        # Try to get nutrition from different possible locations
        if 'nutrition' in meal:
            nutr_data = meal['nutrition']
            if isinstance(nutr_data, dict):
                nutrition['calories'] = nutr_data.get('calories', 0)
                
                # Look for nutrients in different formats
                nutrients = nutr_data.get('nutrients', [])
                if isinstance(nutrients, list):
                    for nutrient in nutrients:
                        name = nutrient.get('name', '').lower()
                        amount = nutrient.get('amount', 0)
                        
                        if 'protein' in name:
                            nutrition['protein'] = amount
                        elif 'carbohydrate' in name or 'carbs' in name:
                            nutrition['carbs'] = amount
                        elif 'fat' in name and 'saturated' not in name:
                            nutrition['fat'] = amount

        return nutrition