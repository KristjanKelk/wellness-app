# nutrition/services/spoonacular_service.py
import requests
import logging
import time
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import json

logger = logging.getLogger('nutrition.spoonacular')


class SpoonacularAPIError(Exception):
    """Custom exception for Spoonacular API errors"""
    pass


class RateLimitExceeded(SpoonacularAPIError):
    """Raised when API rate limit is exceeded"""
    pass


class SpoonacularService:
    """
    Service class for interacting with Spoonacular API
    Handles rate limiting, caching, and data normalization
    """

    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        self.base_url = settings.SPOONACULAR_BASE_URL
        self.endpoints = settings.SPOONACULAR_ENDPOINTS
        self.rate_limit = settings.SPOONACULAR_RATE_LIMIT

        # Rate limiting tracking
        self.requests_today_key = 'spoonacular_requests_today'
        self.last_request_key = 'spoonacular_last_request'

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        try:
            # Check daily limit
            requests_today = cache.get(self.requests_today_key, 0)
            if requests_today >= self.rate_limit['requests_per_day']:
                logger.warning(f"Daily rate limit exceeded: {requests_today}/{self.rate_limit['requests_per_day']}")
                raise RateLimitExceeded("Daily API rate limit exceeded")

            # Check per-minute limit
            last_request = cache.get(self.last_request_key)
            if last_request:
                time_since_last = time.time() - last_request
                min_interval = 60 / self.rate_limit['requests_per_minute']
                if time_since_last < min_interval:
                    sleep_time = min_interval - time_since_last
                    logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
        except Exception as e:
            logger.warning(f"Cache unavailable for rate limiting, proceeding without cache: {e}")
            # Continue without rate limiting if cache is unavailable

        return True

    def _update_rate_limit_counters(self):
        """Update rate limiting counters after successful request"""
        try:
            # Update daily counter
            requests_today = cache.get(self.requests_today_key, 0)
            cache.set(self.requests_today_key, requests_today + 1, 86400)  # 24 hours

            # Update last request timestamp
            cache.set(self.last_request_key, time.time(), 3600)  # 1 hour
        except Exception as e:
            logger.warning(f"Cache unavailable for updating rate limit counters: {e}")
            # Continue without updating counters if cache is unavailable

    def _make_request(self, endpoint: str, params: Dict = None, use_cache: bool = True) -> Dict:
        """
        Make HTTP request to Spoonacular API with rate limiting and caching
        """
        if params is None:
            params = {}

        # Add API key to params
        params['apiKey'] = self.api_key

        # Create cache key
        cache_key = f"spoonacular_{endpoint}_{hash(str(sorted(params.items())))}"

        # Try to get from cache first
        if use_cache:
            try:
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.debug(f"Cache hit for endpoint: {endpoint}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache unavailable for reading, proceeding without cache: {e}")
                use_cache = False  # Disable caching for this request

        # Check rate limits
        self._check_rate_limit()

        # Make the request
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"Making request to Spoonacular: {endpoint}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Update rate limit counters
            self._update_rate_limit_counters()

            data = response.json()

            # Cache the response
            if use_cache:
                try:
                    cache.set(cache_key, data, self.rate_limit['cache_duration'])
                except Exception as e:
                    logger.warning(f"Cache unavailable for writing, continuing without caching: {e}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Spoonacular API request failed: {e}")
            raise SpoonacularAPIError(f"API request failed: {e}")
        except ValueError as e:
            logger.error(f"Failed to parse Spoonacular response: {e}")
            raise SpoonacularAPIError(f"Invalid JSON response: {e}")

    def search_recipes(self,
                       query: str = "",
                       cuisine: str = "",
                       diet: str = "",
                       intolerances: str = "",
                       ingredients: str = "",
                       number: int = 10,
                       offset: int = 0) -> Dict:
        """
        Search for recipes using Spoonacular's complex search

        Args:
            query: Search query
            cuisine: Cuisine type (e.g., "italian", "mexican")
            diet: Diet type (e.g., "vegetarian", "vegan", "keto")
            intolerances: Comma-separated intolerances
            ingredients: Comma-separated ingredients to include
            number: Number of results to return (max 100)
            offset: Offset for pagination

        Returns:
            Dictionary with search results
        """
        params = {
            'query': query,
            'number': min(number, 100),  # API max is 100
            'offset': offset,
            'addRecipeInformation': True,
            'addRecipeNutrition': True,
            'instructionsRequired': True,
            'fillIngredients': True,
        }

        # Add optional filters
        if cuisine:
            params['cuisine'] = cuisine
        if diet:
            params['diet'] = diet
        if intolerances:
            params['intolerances'] = intolerances
        if ingredients:
            params['includeIngredients'] = ingredients

        return self._make_request(self.endpoints['search_recipes'], params)

    def get_recipe_information(self, recipe_id: int, include_nutrition: bool = True) -> Dict:
        """
        Get detailed information about a specific recipe

        Args:
            recipe_id: Spoonacular recipe ID
            include_nutrition: Whether to include nutrition information

        Returns:
            Dictionary with recipe details
        """
        endpoint = self.endpoints['recipe_information'].format(id=recipe_id)
        params = {
            'includeNutrition': include_nutrition,
        }

        return self._make_request(endpoint, params)

    def get_recipe_nutrition(self, recipe_id: int) -> Dict:
        """
        Get nutrition information for a specific recipe

        Args:
            recipe_id: Spoonacular recipe ID

        Returns:
            Dictionary with nutrition data
        """
        endpoint = self.endpoints['recipe_nutrition'].format(id=recipe_id)
        return self._make_request(endpoint)

    def search_ingredients(self, query: str, number: int = 10) -> Dict:
        """
        Search for ingredients

        Args:
            query: Ingredient search query
            number: Number of results to return

        Returns:
            Dictionary with ingredient search results
        """
        params = {
            'query': query,
            'number': number,
            'metaInformation': True,
        }

        return self._make_request(self.endpoints['ingredient_search'], params)

    def get_ingredient_information(self, ingredient_id: int, unit: str = "grams", amount: int = 100) -> Dict:
        """
        Get detailed information about a specific ingredient

        Args:
            ingredient_id: Spoonacular ingredient ID
            unit: Unit for nutrition calculation
            amount: Amount for nutrition calculation

        Returns:
            Dictionary with ingredient details
        """
        endpoint = self.endpoints['ingredient_information'].format(id=ingredient_id)
        params = {
            'unit': unit,
            'amount': amount,
        }

        return self._make_request(endpoint, params)

    def generate_meal_plan(self,
                           target_calories: int,
                           diet: str = "",
                           exclude: str = "",
                           time_frame: str = "day") -> Dict:
        """
        Generate a meal plan using Spoonacular's meal planner

        Args:
            target_calories: Target daily calories
            diet: Diet type
            exclude: Comma-separated ingredients to exclude
            time_frame: "day" or "week"

        Returns:
            Dictionary with meal plan
        """
        params = {
            'timeFrame': time_frame,
            'targetCalories': target_calories,
        }

        if diet:
            params['diet'] = diet
        if exclude:
            params['exclude'] = exclude

        return self._make_request(self.endpoints['generate_meal_plan'], params)

    def connect_user(self, username: str, first_name: str = "", last_name: str = "", email: str = "") -> Dict:
        """
        Connect a user to Spoonacular to enable user-specific meal planning

        Args:
            username: User's name in your system
            first_name: User's first name
            last_name: User's last name  
            email: User's email

        Returns:
            Dictionary with Spoonacular username, password, and hash
        """
        data = {
            'username': username,
            'firstName': first_name,
            'lastName': last_name,
            'email': email
        }

        try:
            url = f"{self.base_url}/users/connect"
            params = {'apiKey': self.api_key}
            
            logger.info(f"Connecting user to Spoonacular: {username}")
            response = requests.post(url, json=data, params=params, timeout=30)
            response.raise_for_status()

            # Update rate limit counters
            self._update_rate_limit_counters()

            result = response.json()
            logger.info(f"Successfully connected user {username} to Spoonacular")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Spoonacular user connection failed: {e}")
            raise SpoonacularAPIError(f"User connection failed: {e}")
        except ValueError as e:
            logger.error(f"Failed to parse Spoonacular user connection response: {e}")
            raise SpoonacularAPIError(f"Invalid JSON response: {e}")

    def get_meal_plan_week(self, spoonacular_username: str, start_date: str, user_hash: str) -> Dict:
        """
        Get a user's meal plan for a specific week

        Args:
            spoonacular_username: Spoonacular username from connect_user
            start_date: Start date in format YYYY-MM-DD
            user_hash: User hash from connect_user

        Returns:
            Dictionary with weekly meal plan
        """
        endpoint = f"/mealplanner/{spoonacular_username}/week/{start_date}"
        params = {'hash': user_hash}

        return self._make_request(endpoint, params, use_cache=False)

    def add_to_meal_plan(self, spoonacular_username: str, user_hash: str, date: str, slot: int, 
                        position: int, item_type: str, value: Dict) -> Dict:
        """
        Add an item to user's meal plan

        Args:
            spoonacular_username: Spoonacular username
            user_hash: User hash
            date: Date in format YYYY-MM-DD
            slot: Meal slot (1=breakfast, 2=lunch, 3=dinner)
            position: Position in the slot
            item_type: Type of item (RECIPE, INGREDIENTS, CUSTOM_FOOD, MENU_ITEM)
            value: Item data (recipe ID, ingredients list, etc.)

        Returns:
            Dictionary with add result
        """
        endpoint = f"/mealplanner/{spoonacular_username}/items"
        params = {'hash': user_hash}
        
        data = {
            'date': date,
            'slot': slot,
            'position': position,
            'type': item_type,
            'value': value
        }

        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, params=params, timeout=30)
            response.raise_for_status()

            # Update rate limit counters
            self._update_rate_limit_counters()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add item to meal plan: {e}")
            raise SpoonacularAPIError(f"Add to meal plan failed: {e}")

    def generate_shopping_list(self, spoonacular_username: str, start_date: str, end_date: str, user_hash: str) -> Dict:
        """
        Generate shopping list for user's meal plan

        Args:
            spoonacular_username: Spoonacular username
            start_date: Start date in format YYYY-MM-DD
            end_date: End date in format YYYY-MM-DD
            user_hash: User hash

        Returns:
            Dictionary with shopping list
        """
        endpoint = f"/mealplanner/{spoonacular_username}/shopping-list/{start_date}/{end_date}"
        params = {'hash': user_hash}

        return self._make_request(endpoint, params, use_cache=False)

    def get_shopping_list(self, spoonacular_username: str, user_hash: str) -> Dict:
        """
        Get user's current shopping list

        Args:
            spoonacular_username: Spoonacular username
            user_hash: User hash

        Returns:
            Dictionary with shopping list
        """
        endpoint = f"/mealplanner/{spoonacular_username}/shopping-list"
        params = {'hash': user_hash}

        return self._make_request(endpoint, params, use_cache=False)

    def delete_from_shopping_list(self, spoonacular_username: str, user_hash: str, item_id: int) -> Dict:
        """
        Delete item from shopping list

        Args:
            spoonacular_username: Spoonacular username
            user_hash: User hash
            item_id: Shopping list item ID

        Returns:
            Dictionary with deletion result
        """
        endpoint = f"/mealplanner/{spoonacular_username}/shopping-list/items/{item_id}"
        params = {'hash': user_hash}

        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.delete(url, params=params, timeout=30)
            response.raise_for_status()

            # Update rate limit counters
            self._update_rate_limit_counters()

            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete from shopping list: {e}")
            raise SpoonacularAPIError(f"Delete from shopping list failed: {e}")

    def get_meal_plan_templates(self) -> Dict:
        """
        Get available meal plan templates (vegetarian, keto, etc.)

        Returns:
            Dictionary with meal plan templates
        """
        endpoint = "/mealplanner/templates"
        return self._make_request(endpoint, {}, use_cache=True)

    def normalize_recipe_data(self, spoonacular_recipe: Dict) -> Dict:
        """
        Normalize Spoonacular recipe data to our internal format

        Args:
            spoonacular_recipe: Raw recipe data from Spoonacular

        Returns:
            Normalized recipe data
        """
        try:
            # Extract basic recipe information
            normalized = {
                'spoonacular_id': spoonacular_recipe.get('id'),
                'title': spoonacular_recipe.get('title', ''),
                'summary': spoonacular_recipe.get('summary', ''),
                'cuisine': self._extract_cuisine(spoonacular_recipe.get('cuisines', [])),
                'meal_type': self._determine_meal_type(spoonacular_recipe),
                'servings': spoonacular_recipe.get('servings', 4),
                'prep_time_minutes': spoonacular_recipe.get('preparationMinutes') or 0,
                'cook_time_minutes': spoonacular_recipe.get('cookingMinutes') or 0,
                'total_time_minutes': spoonacular_recipe.get('readyInMinutes') or 30,
                'image_url': spoonacular_recipe.get('image', ''),
                'source_url': spoonacular_recipe.get('sourceUrl', ''),
                'source_type': 'spoonacular',
            }

            # Extract and normalize ingredients
            normalized['ingredients_data'] = self._normalize_ingredients(
                spoonacular_recipe.get('extendedIngredients', [])
            )

            # Extract and normalize instructions
            normalized['instructions'] = self._normalize_instructions(
                spoonacular_recipe.get('analyzedInstructions', [])
            )

            # Extract nutrition information
            nutrition = spoonacular_recipe.get('nutrition', {})
            if nutrition:
                nutrients = {n['name']: n['amount'] for n in nutrition.get('nutrients', [])}

                normalized.update({
                    'calories_per_serving': nutrients.get('Calories', 0),
                    'protein_per_serving': nutrients.get('Protein', 0),
                    'carbs_per_serving': nutrients.get('Carbohydrates', 0),
                    'fat_per_serving': nutrients.get('Fat', 0),
                    'fiber_per_serving': nutrients.get('Fiber', 0),
                })

            # Extract dietary tags
            normalized['dietary_tags'] = self._extract_dietary_tags(spoonacular_recipe)

            # Extract allergens
            normalized['allergens'] = self._extract_allergens(spoonacular_recipe)

            # Determine difficulty level
            normalized['difficulty_level'] = self._determine_difficulty(spoonacular_recipe)

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing recipe data: {e}")
            raise SpoonacularAPIError(f"Failed to normalize recipe data: {e}")

    def normalize_ingredient_data(self, spoonacular_ingredient: Dict) -> Dict:
        """
        Normalize Spoonacular ingredient data to our internal format

        Args:
            spoonacular_ingredient: Raw ingredient data from Spoonacular

        Returns:
            Normalized ingredient data
        """
        try:
            # Extract nutrition per 100g
            nutrition = spoonacular_ingredient.get('nutrition', {})
            nutrients = {}

            if nutrition:
                for nutrient in nutrition.get('nutrients', []):
                    nutrients[nutrient['name']] = nutrient['amount']

            normalized = {
                'spoonacular_id': spoonacular_ingredient.get('id'),
                'name': spoonacular_ingredient.get('name', ''),
                'name_clean': spoonacular_ingredient.get('name', '').lower().replace(' ', '_'),
                'calories_per_100g': nutrients.get('Calories', 0),
                'protein_per_100g': nutrients.get('Protein', 0),
                'carbs_per_100g': nutrients.get('Carbohydrates', 0),
                'fat_per_100g': nutrients.get('Fat', 0),
                'fiber_per_100g': nutrients.get('Fiber', 0),
                'sugar_per_100g': nutrients.get('Sugar', 0),
                'sodium_per_100g': nutrients.get('Sodium', 0),
                'category': self._categorize_ingredient(spoonacular_ingredient),
                'dietary_tags': self._extract_ingredient_dietary_tags(spoonacular_ingredient),
                'allergens': self._extract_ingredient_allergens(spoonacular_ingredient),
                'is_verified': True,  # Spoonacular data is verified
            }

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing ingredient data: {e}")
            raise SpoonacularAPIError(f"Failed to normalize ingredient data: {e}")

    def _extract_cuisine(self, cuisines: List[str]) -> str:
        """Extract primary cuisine from list"""
        if not cuisines:
            return ''
        return cuisines[0].lower()

    def _determine_meal_type(self, recipe: Dict) -> str:
        """Determine meal type based on recipe data"""
        dish_types = recipe.get('dishTypes', [])

        # Map Spoonacular dish types to our meal types
        meal_type_mapping = {
            'breakfast': 'breakfast',
            'brunch': 'breakfast',
            'lunch': 'lunch',
            'dinner': 'dinner',
            'main course': 'dinner',
            'side dish': 'lunch',
            'dessert': 'dessert',
            'appetizer': 'appetizer',
            'snack': 'snack',
            'drink': 'snack'
        }

        for dish_type in dish_types:
            if dish_type.lower() in meal_type_mapping:
                return meal_type_mapping[dish_type.lower()]

        # Default based on preparation time
        prep_time = recipe.get('readyInMinutes') or 30
        if prep_time <= 15:
            return 'snack'
        elif prep_time <= 30:
            return 'lunch'
        else:
            return 'dinner'

    def _normalize_ingredients(self, ingredients: List[Dict]) -> List[Dict]:
        """Normalize ingredient list from Spoonacular format"""
        normalized_ingredients = []

        for ingredient in ingredients:
            # Convert to grams/ml (standardized units)
            amount_metric = self._convert_to_metric(
                ingredient.get('amount', 0),
                ingredient.get('unit', 'serving')
            )

            normalized_ingredient = {
                'id': f"ing_{ingredient.get('id', '')}",
                'name': ingredient.get('name', ''),
                'quantity': amount_metric,
                'unit': 'gram',  # Standardized to grams
                'original_string': ingredient.get('original', '')
            }

            normalized_ingredients.append(normalized_ingredient)

        return normalized_ingredients

    def _normalize_instructions(self, instructions: List[Dict]) -> List[Dict]:
        """Normalize cooking instructions from Spoonacular format"""
        normalized_instructions = []

        for instruction_group in instructions:
            steps = instruction_group.get('steps', [])

            for step in steps:
                normalized_step = {
                    'step': f"Step {step.get('number', 1)}",
                    'description': step.get('step', ''),
                    'ingredients': [ing.get('name', '') for ing in step.get('ingredients', [])],
                    'equipment': [eq.get('name', '') for eq in step.get('equipment', [])]
                }
                normalized_instructions.append(normalized_step)

        return normalized_instructions

    def _extract_dietary_tags(self, recipe: Dict) -> List[str]:
        """Extract dietary tags from recipe data"""
        tags = []

        # Check diet types
        diets = recipe.get('diets', [])
        for diet in diets:
            tags.append(diet.lower().replace(' ', '_'))

        # Check specific flags
        if recipe.get('vegetarian'):
            tags.append('vegetarian')
        if recipe.get('vegan'):
            tags.append('vegan')
        if recipe.get('glutenFree'):
            tags.append('gluten_free')
        if recipe.get('dairyFree'):
            tags.append('dairy_free')
        if recipe.get('veryHealthy'):
            tags.append('healthy')
        if recipe.get('cheap'):
            tags.append('budget_friendly')
        if recipe.get('veryPopular'):
            tags.append('popular')

        return list(set(tags))  # Remove duplicates

    def _extract_allergens(self, recipe: Dict) -> List[str]:
        """Extract allergens from recipe data"""
        allergens = []

        # Check for common allergens in ingredients
        ingredients_text = ' '.join([
            ing.get('name', '').lower()
            for ing in recipe.get('extendedIngredients', [])
        ])

        allergen_keywords = {
            'nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut'],
            'peanuts': ['peanut', 'peanut butter'],
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt'],
            'eggs': ['egg', 'eggs'],
            'fish': ['fish', 'salmon', 'tuna', 'cod'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'oyster'],
            'soy': ['soy', 'tofu', 'soy sauce'],
            'gluten': ['wheat', 'flour', 'bread', 'pasta']
        }

        for allergen, keywords in allergen_keywords.items():
            if any(keyword in ingredients_text for keyword in keywords):
                allergens.append(allergen)

        return allergens

    def _determine_difficulty(self, recipe: Dict) -> str:
        """Determine recipe difficulty based on various factors"""
        prep_time = recipe.get('preparationMinutes') or 0
        cook_time = recipe.get('cookingMinutes') or 0
        total_time = recipe.get('readyInMinutes') or 30
        ingredient_count = len(recipe.get('extendedIngredients', []))
        instruction_count = sum(
            len(group.get('steps', []))
            for group in recipe.get('analyzedInstructions', [])
        )

        # Calculate difficulty score
        difficulty_score = 0

        if total_time > 60:
            difficulty_score += 2
        elif total_time > 30:
            difficulty_score += 1

        if ingredient_count > 15:
            difficulty_score += 2
        elif ingredient_count > 10:
            difficulty_score += 1

        if instruction_count > 10:
            difficulty_score += 2
        elif instruction_count > 5:
            difficulty_score += 1

        if difficulty_score >= 4:
            return 'hard'
        elif difficulty_score >= 2:
            return 'medium'
        else:
            return 'easy'

    def _convert_to_metric(self, amount: float, unit: str) -> float:
        """Convert ingredient amounts to metric (grams/ml)"""
        # Basic conversion factors to grams/ml
        conversions = {
            'cup': 240,  # ml
            'cups': 240,
            'tablespoon': 15,  # ml
            'tablespoons': 15,
            'tbsp': 15,
            'teaspoon': 5,  # ml
            'teaspoons': 5,
            'tsp': 5,
            'ounce': 28.35,  # grams
            'ounces': 28.35,
            'oz': 28.35,
            'pound': 453.6,  # grams
            'pounds': 453.6,
            'lb': 453.6,
            'gram': 1,
            'grams': 1,
            'g': 1,
            'kilogram': 1000,
            'kg': 1000,
            'milliliter': 1,  # ml
            'ml': 1,
            'liter': 1000,  # ml
            'l': 1000,
            'fluid ounce': 29.57,  # ml
            'fl oz': 29.57,
        }

        unit_lower = unit.lower().strip()
        conversion_factor = conversions.get(unit_lower, 1)

        return amount * conversion_factor

    def _categorize_ingredient(self, ingredient: Dict) -> str:
        """Categorize ingredient for shopping list organization"""
        name = ingredient.get('name', '').lower()

        # Define category keywords
        categories = {
            'produce': ['lettuce', 'tomato', 'onion', 'garlic', 'carrot', 'potato',
                        'apple', 'banana', 'orange', 'spinach', 'broccoli', 'pepper'],
            'proteins': ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna',
                         'turkey', 'lamb', 'tofu', 'tempeh'],
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'eggs'],
            'grains': ['rice', 'pasta', 'bread', 'flour', 'oats', 'quinoa',
                       'barley', 'wheat'],
            'pantry': ['oil', 'vinegar', 'salt', 'pepper', 'sugar', 'honey',
                       'spice', 'herb', 'sauce'],
            'beverages': ['water', 'juice', 'milk', 'coffee', 'tea'],
        }

        for category, keywords in categories.items():
            if any(keyword in name for keyword in keywords):
                return category

        return 'other'

    def _extract_ingredient_dietary_tags(self, ingredient: Dict) -> List[str]:
        """Extract dietary tags for ingredient"""
        tags = []
        name = ingredient.get('name', '').lower()

        # Common vegetarian/vegan ingredients
        if not any(meat in name for meat in ['chicken', 'beef', 'pork', 'fish']):
            tags.append('vegetarian')

            if not any(dairy in name for dairy in ['milk', 'cheese', 'butter', 'cream']):
                tags.append('vegan')

        return tags

    def _extract_ingredient_allergens(self, ingredient: Dict) -> List[str]:
        """Extract allergens for ingredient"""
        allergens = []
        name = ingredient.get('name', '').lower()

        allergen_patterns = {
            'nuts': ['almond', 'walnut', 'pecan', 'cashew'],
            'dairy': ['milk', 'cheese', 'butter', 'cream'],
            'gluten': ['wheat', 'flour'],
            'soy': ['soy', 'tofu'],
        }

        for allergen, patterns in allergen_patterns.items():
            if any(pattern in name for pattern in patterns):
                allergens.append(allergen)

        return allergens


# Utility functions for external use
def get_spoonacular_service() -> SpoonacularService:
    """Get configured Spoonacular service instance"""
    return SpoonacularService()


def search_recipes_by_dietary_preferences(preferences: Dict) -> List[Dict]:
    """
    Search recipes based on user dietary preferences

    Args:
        preferences: Dictionary with dietary preferences, allergies, etc.

    Returns:
        List of normalized recipe dictionaries
    """
    service = get_spoonacular_service()

    # Build search parameters from preferences
    diet = ','.join(preferences.get('dietary_preferences', []))
    intolerances = ','.join(preferences.get('allergies_intolerances', []))
    cuisine = ','.join(preferences.get('cuisine_preferences', [])[:3])  # Limit to 3

    try:
        results = service.search_recipes(
            diet=diet,
            intolerances=intolerances,
            cuisine=cuisine,
            number=20  # Get more options
        )

        # Normalize all recipes
        normalized_recipes = []
        for recipe in results.get('results', []):
            try:
                normalized = service.normalize_recipe_data(recipe)
                normalized_recipes.append(normalized)
            except Exception as e:
                logger.warning(f"Failed to normalize recipe {recipe.get('id')}: {e}")
                continue

        return normalized_recipes

    except SpoonacularAPIError as e:
        logger.error(f"Failed to search recipes: {e}")
        return []


def bulk_import_ingredients(ingredient_names: List[str]) -> List[Dict]:
    """
    Import multiple ingredients from Spoonacular

    Args:
        ingredient_names: List of ingredient names to import

    Returns:
        List of normalized ingredient dictionaries
    """
    service = get_spoonacular_service()
    normalized_ingredients = []

    for name in ingredient_names:
        try:
            # Search for ingredient
            search_results = service.search_ingredients(name, number=1)

            if search_results.get('results'):
                ingredient_id = search_results['results'][0]['id']

                # Get detailed information
                ingredient_info = service.get_ingredient_information(ingredient_id)

                # Normalize the data
                normalized = service.normalize_ingredient_data(ingredient_info)
                normalized_ingredients.append(normalized)

        except Exception as e:
            logger.warning(f"Failed to import ingredient '{name}': {e}")
            continue

    return normalized_ingredients