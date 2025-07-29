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

    def _save_recipe_to_database(self, recipe_data: Dict, created_by=None) -> Optional['Recipe']:
        """
        Save a recipe from Spoonacular to our Recipe database
        
        Args:
            recipe_data: Recipe data from Spoonacular API
            created_by: User who saved this recipe (optional)
        
        Returns:
            Saved Recipe instance or None if failed
        """
        try:
            from ..models import Recipe
            
            # Check if recipe already exists
            spoonacular_id = recipe_data.get('id')
            if spoonacular_id:
                existing_recipe = Recipe.objects.filter(spoonacular_id=spoonacular_id).first()
                if existing_recipe:
                    logger.debug(f"Recipe {spoonacular_id} already exists in database")
                    return existing_recipe
            
            # Extract recipe information
            title = recipe_data.get('title', 'Untitled Recipe')
            summary = recipe_data.get('summary', '')
            
            # Determine meal type - this might need to be inferred or passed as parameter
            meal_type = self._infer_meal_type(title, recipe_data)
            
            # Extract nutrition information
            nutrition = self._extract_nutrition(recipe_data)
            
            # Extract timing information
            prep_time = recipe_data.get('preparationMinutes', 0)
            cook_time = recipe_data.get('cookingMinutes', 0)
            ready_in_minutes = recipe_data.get('readyInMinutes', prep_time + cook_time)
            
            # Extract dietary tags
            dietary_tags = self._extract_dietary_tags(recipe_data)
            
            # Extract allergens
            allergens = self._extract_allergens(recipe_data)
            
            # Create recipe instance with better error handling
            recipe = Recipe.objects.create(
                title=title[:300],  # Ensure title fits in field
                summary=summary[:1000] if summary else '',  # Limit summary length
                meal_type=meal_type,
                servings=max(1, recipe_data.get('servings', 1)),  # Ensure positive servings
                prep_time_minutes=max(0, prep_time),
                cook_time_minutes=max(0, cook_time),
                total_time_minutes=max(0, ready_in_minutes),
                difficulty_level='medium',  # Default, could be inferred
                spoonacular_id=spoonacular_id,
                ingredients_data=self._extract_ingredients_data(recipe_data),
                instructions=self._extract_instructions(recipe_data),
                calories_per_serving=max(0, nutrition.get('calories', 0)),
                protein_per_serving=max(0, nutrition.get('protein', 0)),
                carbs_per_serving=max(0, nutrition.get('carbs', 0)),
                fat_per_serving=max(0, nutrition.get('fat', 0)),
                fiber_per_serving=max(0, nutrition.get('fiber', 0)),
                dietary_tags=dietary_tags,
                allergens=allergens,
                image_url=recipe_data.get('image', '')[:500] if recipe_data.get('image') else '',  # Limit URL length
                source_url=recipe_data.get('sourceUrl', '')[:500] if recipe_data.get('sourceUrl') else '',
                source_type='spoonacular',
                is_verified=True,
                is_public=True,
                created_by=created_by
            )
            
            logger.info(f"Successfully saved recipe '{title}' to database")
            return recipe
            
        except Exception as e:
            logger.error(f"Failed to save recipe to database: {str(e)}")
            return None

    def _infer_meal_type(self, title: str, recipe_data: Dict) -> str:
        """
        Infer meal type from recipe title and data
        
        Args:
            title: Recipe title
            recipe_data: Full recipe data
        
        Returns:
            Meal type string
        """
        title_lower = title.lower()
        
        # Breakfast keywords
        if any(word in title_lower for word in ['breakfast', 'morning', 'pancake', 'waffle', 'oat', 'cereal', 'toast', 'egg', 'omelet']):
            return 'breakfast'
        
        # Dinner keywords (more substantial meals)
        if any(word in title_lower for word in ['dinner', 'roast', 'steak', 'pasta', 'curry', 'stew', 'casserole']):
            return 'dinner'
        
        # Snack keywords
        if any(word in title_lower for word in ['snack', 'chip', 'dip', 'cookie', 'bar', 'bite']):
            return 'snack'
        
        # Default to lunch
        return 'lunch'

    def _extract_dietary_tags(self, recipe_data: Dict) -> List[str]:
        """Extract dietary tags from recipe data"""
        tags = []
        
        # Check recipe data for dietary information
        if recipe_data.get('vegetarian'):
            tags.append('vegetarian')
        if recipe_data.get('vegan'):
            tags.append('vegan')
        if recipe_data.get('glutenFree'):
            tags.append('gluten_free')
        if recipe_data.get('dairyFree'):
            tags.append('dairy_free')
        if recipe_data.get('veryHealthy'):
            tags.append('healthy')
        if recipe_data.get('cheap'):
            tags.append('budget_friendly')
        if recipe_data.get('veryPopular'):
            tags.append('popular')
        
        # Check dish types
        dish_types = recipe_data.get('dishTypes', [])
        for dish_type in dish_types:
            if dish_type in ['salad', 'soup', 'dessert']:
                tags.append(dish_type)
        
        return tags

    def _extract_allergens(self, recipe_data: Dict) -> List[str]:
        """Extract potential allergens from recipe data"""
        allergens = []
        
        # This is a basic implementation - could be enhanced with ingredient analysis
        if not recipe_data.get('glutenFree', True):
            allergens.append('gluten')
        if not recipe_data.get('dairyFree', True):
            allergens.append('dairy')
        
        return allergens

    def _extract_ingredients_data(self, recipe_data: Dict) -> List[Dict]:
        """Extract ingredients data in our format"""
        ingredients = []
        
        # Extract from extendedIngredients if available
        extended_ingredients = recipe_data.get('extendedIngredients', [])
        for ingredient in extended_ingredients:
            ingredients.append({
                'id': ingredient.get('id'),
                'name': ingredient.get('name', ''),
                'original': ingredient.get('original', ''),
                'amount': ingredient.get('amount', 0),
                'unit': ingredient.get('unit', ''),
                'measures': ingredient.get('measures', {})
            })
        
        return ingredients

    def _extract_instructions(self, recipe_data: Dict) -> List[Dict]:
        """Extract cooking instructions in our format"""
        instructions = []
        
        # Extract from analyzedInstructions if available
        analyzed_instructions = recipe_data.get('analyzedInstructions', [])
        for instruction_group in analyzed_instructions:
            steps = instruction_group.get('steps', [])
            for step in steps:
                instructions.append({
                    'number': step.get('number', 0),
                    'step': step.get('step', ''),
                    'ingredients': step.get('ingredients', []),
                    'equipment': step.get('equipment', []),
                    'length': step.get('length', {})
                })
        
        # Fallback to simple instructions if no analyzed instructions
        if not instructions and 'instructions' in recipe_data:
            simple_instructions = recipe_data.get('instructions', '')
            if simple_instructions:
                instructions.append({
                    'number': 1,
                    'step': simple_instructions,
                    'ingredients': [],
                    'equipment': [],
                    'length': {}
                })
        
        return instructions

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

    def create_personalized_meal_plan(self, nutrition_profile, days: int = 7, generation_options: Dict = None) -> Dict:
        """
        Create a personalized meal plan based on user's nutrition profile
        
        Args:
            nutrition_profile: User's nutrition profile
            days: Number of days to plan for
            generation_options: Optional generation parameters (max_cook_time, etc.)
        
        Returns:
            Personalized meal plan
        """
        generation_options = generation_options or {}
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

        # For now, use recipe search instead of meal plan generator to get better control over filters
        # This gives us more control over cuisine and cooking time
        if days == 1:
            meal_plan = self._generate_custom_meal_plan(
                nutrition_profile=nutrition_profile,
                days=1,
                diet=diet,
                exclusions=exclusions,
                generation_options=generation_options
            )
        else:
            meal_plan = self._generate_custom_meal_plan(
                nutrition_profile=nutrition_profile,
                days=days,
                diet=diet,
                exclusions=exclusions,
                generation_options=generation_options
            )

        return meal_plan

    def _generate_custom_meal_plan(self, nutrition_profile, days: int, diet: str, exclusions: list, generation_options: Dict) -> Dict:
        """
        Generate a custom meal plan using recipe search with full filter control
        """
        import random
        from datetime import date, timedelta
        
        # Use meals_per_day from nutrition profile
        meals_per_day = getattr(nutrition_profile, 'meals_per_day', 3)
        snacks_per_day = getattr(nutrition_profile, 'snacks_per_day', 0)
        
        # Generate meal types based on meals_per_day
        if meals_per_day >= 3:
            meal_types = ['breakfast', 'lunch', 'dinner']
        else:
            meal_types = ['breakfast', 'dinner'] if meals_per_day == 2 else ['lunch']
            
        # Add additional meals if meals_per_day > 3
        if meals_per_day > 3:
            additional_meals = meals_per_day - 3
            for i in range(additional_meals):
                meal_types.append(f'meal_{i+4}')  # meal_4, meal_5, etc.
        
        # Add snacks if specified
        total_eating_occasions = meals_per_day + snacks_per_day
        snack_types = []
        if snacks_per_day > 0:
            for i in range(snacks_per_day):
                snack_types.append(f'snack_{i+1}')
        
        all_meal_types = meal_types + snack_types
        
        meal_type_queries = {
            'breakfast': ['breakfast', 'morning meal', 'brunch'],
            'lunch': ['lunch', 'salad', 'soup', 'sandwich'],
            'dinner': ['dinner', 'main course', 'entree'],
            'meal_4': ['main course', 'entree', 'lunch'],  # Mid-afternoon meal
            'meal_5': ['dinner', 'main course', 'light meal'],  # Evening meal
            'meal_6': ['main course', 'light meal'],  # Late evening meal
            'snack_1': ['snack', 'light meal', 'appetizer'],
            'snack_2': ['snack', 'light meal', 'appetizer'],
            'snack_3': ['snack', 'light meal', 'appetizer']
        }
        
        # Calculate calories per meal/snack
        daily_calories = nutrition_profile.calorie_target
        
        # Distribute calories: 80% for main meals, 20% for snacks
        if snacks_per_day > 0:
            main_meal_calories = int(daily_calories * 0.8)
            snack_calories = int(daily_calories * 0.2)
            calories_per_meal = main_meal_calories // meals_per_day
            calories_per_snack = snack_calories // snacks_per_day if snacks_per_day > 0 else 0
        else:
            calories_per_meal = daily_calories // meals_per_day
            calories_per_snack = 0
        
        meals = []
        start_date = date.today()
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            for meal_type in all_meal_types:
                # Determine if this is a meal or snack and set calorie target accordingly
                is_snack = meal_type.startswith('snack_')
                target_calories = calories_per_snack if is_snack else calories_per_meal
                
                # Build search filters
                search_filters = {
                    'number': 5,  # Get multiple options
                    'addRecipeInformation': True,
                    'addRecipeNutrition': True,
                    'minCalories': max(target_calories - (100 if is_snack else 200), 50 if is_snack else 100),
                    'maxCalories': target_calories + (100 if is_snack else 200),
                }
                
                # Add diet filter
                if diet:
                    search_filters['diet'] = diet
                
                # Add exclusions
                if exclusions:
                    search_filters['intolerances'] = ','.join(exclusions)
                
                # Add cuisine filter if specified
                if nutrition_profile.cuisine_preferences:
                    search_filters['cuisine'] = ','.join(nutrition_profile.cuisine_preferences)
                
                # Add max cooking time filter if specified
                if generation_options.get('max_cook_time'):
                    search_filters['maxReadyTime'] = generation_options['max_cook_time']
                
                # Search for recipes
                query = random.choice(meal_type_queries[meal_type])
                response = self.search_recipes(query, **search_filters)
                
                if response and response.get('results'):
                    # Pick a random recipe from results
                    recipe = random.choice(response['results'])
                    
                    # Add meal type and time info
                    recipe['meal_type'] = meal_type
                    
                    # Get meal times from nutrition profile
                    breakfast_time = getattr(nutrition_profile, 'breakfast_time', '08:00:00')
                    lunch_time = getattr(nutrition_profile, 'lunch_time', '12:30:00')
                    dinner_time = getattr(nutrition_profile, 'dinner_time', '19:00:00')
                    
                    # Convert time format if needed (remove seconds)
                    if len(str(breakfast_time)) > 5:
                        breakfast_time = str(breakfast_time)[:5]
                    if len(str(lunch_time)) > 5:
                        lunch_time = str(lunch_time)[:5]
                    if len(str(dinner_time)) > 5:
                        dinner_time = str(dinner_time)[:5]
                    
                    time_mapping = {
                        'breakfast': breakfast_time,
                        'lunch': lunch_time,
                        'dinner': dinner_time,
                        'meal_4': '15:00',  # Mid-afternoon
                        'meal_5': '17:30',  # Early evening
                        'meal_6': '21:00',  # Late evening
                        'snack_1': '10:00',  # Morning snack
                        'snack_2': '15:30',  # Afternoon snack
                        'snack_3': '20:30'   # Evening snack
                    }
                    
                    recipe['time'] = time_mapping.get(meal_type, '12:00')
                    
                    meals.append(recipe)
        
        # Format as meal plan
        return {
            'meals': meals,
            'nutrients': {
                'calories': daily_calories * days,
                'protein': 0,  # Would need to calculate from individual meals
                'carbs': 0,
                'fat': 0
            }
        }

    def normalize_meal_plan_data(self, spoonacular_data: Dict, time_frame: str = "day", created_by=None) -> Dict:
        """
        Normalize Spoonacular meal plan data to our internal format and save recipes to database
        
        Args:
            spoonacular_data: Raw data from Spoonacular
            time_frame: "day" or "week"
            created_by: User who created this meal plan (for recipe saving)
        
        Returns:
            Normalized meal plan data
        """
        if time_frame == "day":
            return self._normalize_day_meal_plan(spoonacular_data, created_by)
        else:
            return self._normalize_week_meal_plan(spoonacular_data, created_by)

    def _normalize_day_meal_plan(self, data: Dict, created_by=None) -> Dict:
        """Normalize a single day meal plan and save recipes to database"""
        from datetime import date
        
        date_str = date.today().isoformat()
        
        normalized = {
            'date': date_str,
            'meals': {
                date_str: []  # Use date as key instead of meal types
            },
            'nutrition': {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0
            }
        }

        # Create a list to hold all meals for the day
        daily_meals = []
        
        meals_data = data.get('meals', [])
        
        for i, meal in enumerate(meals_data):
            # Get detailed recipe information if not already complete
            detailed_meal = meal
            recipe_id = meal.get('id')
            
            # If meal data is incomplete (common with meal plan generation), fetch detailed info
            if recipe_id and not meal.get('extendedIngredients'):
                try:
                    logger.info(f"Fetching detailed recipe information for recipe ID: {recipe_id}")
                    detailed_meal = self.get_recipe_information(recipe_id, include_nutrition=True)
                    # Merge with original meal data to preserve any meal plan specific info
                    detailed_meal.update({
                        key: value for key, value in meal.items() 
                        if key not in detailed_meal or not detailed_meal[key]
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch detailed recipe info for {recipe_id}: {str(e)}")
                    detailed_meal = meal
            
            # Save recipe to database with detailed information
            saved_recipe = self._save_recipe_to_database(detailed_meal, created_by)
            
            # Use meal type and time from the meal data (already set in generate_custom_meal_plan)
            meal_type = meal.get('meal_type', f'meal_{i+1}')
            meal_time = meal.get('time', '12:00')
            
            meal_data = {
                'meal_type': meal_type,
                'time': meal_time,
                'recipe': {
                    'id': detailed_meal.get('id'),
                    'title': detailed_meal.get('title', ''),
                    'name': detailed_meal.get('title', ''),  # Add name field for compatibility
                    'readyInMinutes': detailed_meal.get('readyInMinutes', 0),
                    'prep_time': detailed_meal.get('preparationMinutes', 0),
                    'cook_time': detailed_meal.get('cookingMinutes', 0),
                    'total_time': detailed_meal.get('readyInMinutes', 0),
                    'servings': detailed_meal.get('servings', 1),
                    'sourceUrl': detailed_meal.get('sourceUrl', ''),
                    'image': detailed_meal.get('image', ''),
                    'cuisine': detailed_meal.get('cuisines', [None])[0] if detailed_meal.get('cuisines') else None,
                    'estimated_nutrition': self._extract_nutrition(detailed_meal),
                    'nutrition': self._extract_nutrition(detailed_meal),  # Add both for compatibility
                    'ingredients': self._extract_ingredients_data(detailed_meal),
                    'instructions': self._extract_instructions(detailed_meal),
                    'database_id': str(saved_recipe.id) if saved_recipe else None
                },
                'cuisine': detailed_meal.get('cuisines', [None])[0] if detailed_meal.get('cuisines') else 'International',
                'target_calories': detailed_meal.get('nutrition', {}).get('calories', 0),
                'target_protein': detailed_meal.get('nutrition', {}).get('protein', 0),
                'target_carbs': detailed_meal.get('nutrition', {}).get('carbs', 0),
                'target_fat': detailed_meal.get('nutrition', {}).get('fat', 0)
            }

            daily_meals.append(meal_data)

            # Add to total nutrition
            nutrition = meal_data['recipe']['nutrition']
            normalized['nutrition']['calories'] += nutrition.get('calories', 0)
            normalized['nutrition']['protein'] += nutrition.get('protein', 0)
            normalized['nutrition']['carbs'] += nutrition.get('carbs', 0)
            normalized['nutrition']['fat'] += nutrition.get('fat', 0)

        # Assign the complete daily meals to the date key
        normalized['meals'][date_str] = daily_meals

        return normalized

    def _normalize_week_meal_plan(self, data: Dict, created_by=None) -> Dict:
        """Normalize a week meal plan and save recipes to database"""
        from datetime import date, timedelta
        
        base_date = date.today()
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        normalized = {
            'week': data.get('week', {}),
            'meals': {},  # Use meals structure for consistency
            'nutrition': {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0
            }
        }

        week_data = data.get('week', {})
        
        for day_key in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            if day_key in week_data:
                # Calculate the actual date for this day
                days_offset = day_mapping[day_key]
                actual_date = base_date + timedelta(days=days_offset)
                date_str = actual_date.isoformat()
                
                # Normalize the day's meals with the actual date
                day_meals_data = week_data[day_key].get('meals', [])
                
                if day_meals_data:
                    # Create daily meals structure similar to day plan
                    daily_meals = []
                    meal_types = ['breakfast', 'lunch', 'dinner']
                    meal_times = ['08:00', '12:30', '19:00']
                    
                    for i, meal in enumerate(day_meals_data):
                        # Save recipe to database
                        saved_recipe = self._save_recipe_to_database(meal, created_by)
                        
                        meal_type = meal_types[i] if i < len(meal_types) else 'snack'
                        meal_time = meal_times[i] if i < len(meal_times) else '15:00'
                        
                        meal_data = {
                            'meal_type': meal_type,
                            'time': meal_time,
                            'recipe': {
                                'id': meal.get('id'),
                                'title': meal.get('title', ''),
                                'name': meal.get('title', ''),
                                'readyInMinutes': meal.get('readyInMinutes', 0),
                                'prep_time': meal.get('preparationMinutes', 0),
                                'cook_time': meal.get('cookingMinutes', 0),
                                'total_time': meal.get('readyInMinutes', 0),
                                'servings': meal.get('servings', 1),
                                'sourceUrl': meal.get('sourceUrl', ''),
                                'image': meal.get('image', ''),
                                'cuisine': meal.get('cuisines', [None])[0] if meal.get('cuisines') else None,
                                'estimated_nutrition': self._extract_nutrition(meal),
                                'nutrition': self._extract_nutrition(meal),
                                'ingredients': self._extract_ingredients_data(meal),
                                'instructions': self._extract_instructions(meal),
                                'database_id': str(saved_recipe.id) if saved_recipe else None
                            },
                            'cuisine': meal.get('cuisines', [None])[0] if meal.get('cuisines') else 'International',
                            'target_calories': meal.get('nutrition', {}).get('calories', 0),
                            'target_protein': meal.get('nutrition', {}).get('protein', 0),
                            'target_carbs': meal.get('nutrition', {}).get('carbs', 0),
                            'target_fat': meal.get('nutrition', {}).get('fat', 0)
                        }
                        
                        daily_meals.append(meal_data)
                        
                        # Add to weekly nutrition totals
                        nutrition = meal_data['recipe']['nutrition']
                        normalized['nutrition']['calories'] += nutrition.get('calories', 0)
                        normalized['nutrition']['protein'] += nutrition.get('protein', 0)
                        normalized['nutrition']['carbs'] += nutrition.get('carbs', 0)
                        normalized['nutrition']['fat'] += nutrition.get('fat', 0)
                    
                    # Add the day's meals to the normalized structure
                    normalized['meals'][date_str] = daily_meals

        return normalized

    def _extract_nutrition(self, meal: Dict) -> Dict:
        """Extract nutrition information from meal data"""
        nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0  # Add fiber support
        }

        # Try to get nutrition from different possible locations
        if 'nutrition' in meal:
            nutr_data = meal['nutrition']
            if isinstance(nutr_data, dict):
                # Direct nutrition values (sometimes available)
                nutrition['calories'] = nutr_data.get('calories', 0)
                
                # Look for nutrients in different formats
                nutrients = nutr_data.get('nutrients', [])
                if isinstance(nutrients, list):
                    for nutrient in nutrients:
                        if isinstance(nutrient, dict):
                            name = nutrient.get('name', '').lower()
                            amount = nutrient.get('amount', 0)
                            
                            # Map nutrient names to our nutrition structure
                            if 'calorie' in name or name == 'energy':
                                nutrition['calories'] = amount
                            elif 'protein' in name:
                                nutrition['protein'] = amount
                            elif 'carbohydrate' in name or 'carbs' in name or name == 'net carbohydrates':
                                nutrition['carbs'] = amount
                            elif 'fat' in name and 'saturated' not in name and 'trans' not in name:
                                nutrition['fat'] = amount
                            elif 'fiber' in name or name == 'dietary fiber':
                                nutrition['fiber'] = amount

        # Fallback: try to extract from other locations in the meal data
        if nutrition['calories'] == 0:
            # Sometimes calories are directly in the meal data
            if 'calories' in meal:
                nutrition['calories'] = meal.get('calories', 0)
            
            # Or in summary/analyzed recipe data
            if 'summary' in meal and isinstance(meal['summary'], str):
                import re
                calories_match = re.search(r'(\d+)\s*calories', meal['summary'])
                if calories_match:
                    nutrition['calories'] = int(calories_match.group(1))

        # Convert string values with units to numbers (e.g., "25g" -> 25)
        for key in nutrition:
            if isinstance(nutrition[key], str):
                import re
                # Extract numbers from strings like "25g", "1.5oz", etc.
                match = re.search(r'(\d+\.?\d*)', str(nutrition[key]))
                if match:
                    nutrition[key] = float(match.group(1))
                else:
                    nutrition[key] = 0

        # Ensure all values are numeric
        for key in nutrition:
            try:
                nutrition[key] = float(nutrition[key]) if nutrition[key] else 0
            except (ValueError, TypeError):
                nutrition[key] = 0

        return nutrition