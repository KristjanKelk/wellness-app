from collections import defaultdict
from decimal import Decimal
import logging
import re
from typing import Dict, List, Any, Tuple
from ..models import Recipe, MealPlan, Ingredient

logger = logging.getLogger(__name__)


class ShoppingListService:
    """Service for generating and managing shopping lists from recipes and meal plans"""
    
    # Unit conversion mappings
    UNIT_CONVERSIONS = {
        # Weight conversions to grams
        'kg': 1000,
        'gram': 1,
        'grams': 1,
        'g': 1,
        'lb': 453.592,
        'pound': 453.592,
        'pounds': 453.592,
        'oz': 28.3495,
        'ounce': 28.3495,
        'ounces': 28.3495,
        
        # Volume conversions to ml
        'l': 1000,
        'liter': 1000,
        'liters': 1000,
        'ml': 1,
        'milliliter': 1,
        'milliliters': 1,
        'cup': 240,
        'cups': 240,
        'tbsp': 15,
        'tablespoon': 15,
        'tablespoons': 15,
        'tsp': 5,
        'teaspoon': 5,
        'teaspoons': 5,
        'fl oz': 29.5735,
        'fluid ounce': 29.5735,
        'fluid ounces': 29.5735,
        'pint': 473.176,
        'pints': 473.176,
        'quart': 946.353,
        'quarts': 946.353,
        'gallon': 3785.41,
        'gallons': 3785.41,
        
        # Piece/count items
        'piece': 1,
        'pieces': 1,
        'item': 1,
        'items': 1,
        'whole': 1,
        'each': 1,
        'clove': 1,
        'cloves': 1,
        'slice': 1,
        'slices': 1,
        'bunch': 1,
        'bunches': 1,
        'head': 1,
        'heads': 1,
        'can': 1,
        'cans': 1,
        'jar': 1,
        'jars': 1,
        'bottle': 1,
        'bottles': 1,
        'package': 1,
        'packages': 1,
        'pack': 1,
        'packs': 1,
    }
    
    def generate_shopping_list_from_recipes(self, recipe_ids: List[str], servings_multiplier: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Generate shopping list from a list of recipe IDs
        
        Args:
            recipe_ids: List of recipe UUIDs
            servings_multiplier: Dict mapping recipe_id to serving multiplier (e.g., {'recipe_id': 2.0} for double servings)
            
        Returns:
            Dict containing organized shopping list data
        """
        try:
            recipes = Recipe.objects.filter(id__in=recipe_ids)
            if not recipes.exists():
                raise ValueError("No valid recipes found")
            
            # Aggregate ingredients from all recipes
            aggregated_ingredients = self._aggregate_ingredients_from_recipes(recipes, servings_multiplier)
            
            # Organize by categories
            shopping_list = self._organize_by_categories(aggregated_ingredients)
            
            # Add metadata
            shopping_list['metadata'] = {
                'recipe_count': len(recipes),
                'recipe_names': [recipe.title for recipe in recipes],
                'generated_from': 'recipes',
                'total_items': sum(len(category['items']) for category in shopping_list['categories'].values())
            }
            
            return shopping_list
            
        except Exception as e:
            logger.error(f"Error generating shopping list from recipes: {str(e)}")
            raise
    
    def generate_shopping_list_from_meal_plan(self, meal_plan_id: str) -> Dict[str, Any]:
        """
        Generate shopping list from a meal plan
        
        Args:
            meal_plan_id: MealPlan UUID
            
        Returns:
            Dict containing organized shopping list data
        """
        try:
            meal_plan = MealPlan.objects.get(id=meal_plan_id)
            meal_plan_data = meal_plan.meal_plan_data
            
            # Extract recipes from meal plan data
            recipe_ingredients = []
            recipe_names = []
            
            # Handle different meal plan data structures
            if isinstance(meal_plan_data, dict):
                if 'meals' in meal_plan_data:
                    # Multi-day meal plan structure
                    for day_data in meal_plan_data['meals']:
                        if isinstance(day_data, dict):
                            for meal_type, meal_data in day_data.items():
                                if isinstance(meal_data, dict) and 'ingredients' in meal_data:
                                    recipe_ingredients.extend(meal_data['ingredients'])
                                    if 'recipe_name' in meal_data:
                                        recipe_names.append(meal_data['recipe_name'])
                                elif isinstance(meal_data, list):
                                    # Array of meals
                                    for meal in meal_data:
                                        if isinstance(meal, dict) and 'ingredients' in meal:
                                            recipe_ingredients.extend(meal['ingredients'])
                                            if 'recipe_name' in meal:
                                                recipe_names.append(meal['recipe_name'])
                
                elif 'recipes' in meal_plan_data:
                    # Recipe-based meal plan structure
                    for recipe_data in meal_plan_data['recipes']:
                        if 'ingredients' in recipe_data:
                            recipe_ingredients.extend(recipe_data['ingredients'])
                            if 'name' in recipe_data:
                                recipe_names.append(recipe_data['name'])
                
                # Try to extract from daily_meals if present
                elif 'daily_meals' in meal_plan_data:
                    for daily_meal in meal_plan_data['daily_meals']:
                        if isinstance(daily_meal, dict):
                            for meal in daily_meal.get('meals', []):
                                if 'ingredients' in meal:
                                    recipe_ingredients.extend(meal['ingredients'])
                                    if 'name' in meal:
                                        recipe_names.append(meal['name'])
            
            # Aggregate ingredients
            aggregated_ingredients = self._aggregate_ingredients_from_data(recipe_ingredients)
            
            # Organize by categories
            shopping_list = self._organize_by_categories(aggregated_ingredients)
            
            # Add metadata
            shopping_list['metadata'] = {
                'meal_plan_id': str(meal_plan_id),
                'plan_type': meal_plan.plan_type,
                'start_date': meal_plan.start_date.isoformat(),
                'end_date': meal_plan.end_date.isoformat(),
                'recipe_names': recipe_names,
                'generated_from': 'meal_plan',
                'total_items': sum(len(category['items']) for category in shopping_list['categories'].values())
            }
            
            return shopping_list
            
        except MealPlan.DoesNotExist:
            raise ValueError(f"Meal plan {meal_plan_id} not found")
        except Exception as e:
            logger.error(f"Error generating shopping list from meal plan: {str(e)}")
            raise
    
    def _aggregate_ingredients_from_recipes(self, recipes, servings_multiplier=None) -> Dict[str, Dict]:
        """Aggregate ingredients from multiple recipes with quantity consolidation"""
        aggregated = defaultdict(lambda: {
            'quantity': 0,
            'unit': None,
            'name': '',
            'category': 'other',
            'notes': []
        })
        
        for recipe in recipes:
            multiplier = servings_multiplier.get(str(recipe.id), 1.0) if servings_multiplier else 1.0
            
            ingredients_data = recipe.ingredients_data or []
            for ingredient_data in ingredients_data:
                ingredient_name = ingredient_data.get('name', '').lower().strip()
                if not ingredient_name:
                    continue
                
                # Safely convert amount to float, handling various input types
                amount_value = ingredient_data.get('amount', 0)
                try:
                    if isinstance(amount_value, (int, float)):
                        base_quantity = float(amount_value)
                    elif isinstance(amount_value, str):
                        # Handle string amounts that might contain fractions or ranges
                        amount_str = amount_value.strip()
                        if not amount_str or amount_str.lower() in ['to taste', 'as needed', 'optional']:
                            base_quantity = 0
                        else:
                            # Try to extract first number from string (handles cases like "1-2", "1/2", etc.)
                            number_match = re.search(r'(\d+(?:\.\d+)?)', amount_str)
                            if number_match:
                                base_quantity = float(number_match.group(1))
                            else:
                                base_quantity = 0
                    else:
                        base_quantity = 0
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse ingredient amount '{amount_value}' for recipe {recipe.id}, defaulting to 0")
                    base_quantity = 0
                
                quantity = base_quantity * multiplier
                unit = ingredient_data.get('unit', '').lower().strip()
                
                # Try to find the ingredient in our database for category info
                ingredient_obj = self._find_ingredient_by_name(ingredient_name)
                category = ingredient_obj.category if ingredient_obj else 'other'
                
                # Normalize the ingredient name for aggregation
                normalized_name = self._normalize_ingredient_name(ingredient_name)
                
                if normalized_name in aggregated:
                    # Aggregate quantities (convert to common unit if possible)
                    existing_unit = aggregated[normalized_name]['unit']
                    if existing_unit and unit and self._can_convert_units(existing_unit, unit):
                        # Convert to common unit and add
                        converted_quantity = self._convert_quantity(quantity, unit, existing_unit)
                        aggregated[normalized_name]['quantity'] += converted_quantity
                    else:
                        # Can't convert, just add as separate note
                        note = f"{quantity} {unit}".strip()
                        if note not in aggregated[normalized_name]['notes']:
                            aggregated[normalized_name]['notes'].append(note)
                else:
                    # First occurrence
                    aggregated[normalized_name] = {
                        'quantity': quantity,
                        'unit': unit,
                        'name': ingredient_data.get('name', ingredient_name),
                        'category': category,
                        'notes': []
                    }
        
        return dict(aggregated)
    
    def _aggregate_ingredients_from_data(self, ingredients_data: List[Dict]) -> Dict[str, Dict]:
        """Aggregate ingredients from raw ingredient data"""
        aggregated = defaultdict(lambda: {
            'quantity': 0,
            'unit': None,
            'name': '',
            'category': 'other',
            'notes': []
        })
        
        for ingredient_data in ingredients_data:
            ingredient_name = ingredient_data.get('name', '').lower().strip()
            if not ingredient_name:
                continue
            
            # Safely convert amount to float, handling various input types
            amount_value = ingredient_data.get('amount', 0)
            try:
                if isinstance(amount_value, (int, float)):
                    quantity = float(amount_value)
                elif isinstance(amount_value, str):
                    # Handle string amounts that might contain fractions or ranges
                    amount_str = amount_value.strip()
                    if not amount_str or amount_str.lower() in ['to taste', 'as needed', 'optional']:
                        quantity = 0
                    else:
                        # Try to extract first number from string (handles cases like "1-2", "1/2", etc.)
                        number_match = re.search(r'(\d+(?:\.\d+)?)', amount_str)
                        if number_match:
                            quantity = float(number_match.group(1))
                        else:
                            quantity = 0
                else:
                    quantity = 0
            except (ValueError, TypeError):
                logger.warning(f"Could not parse ingredient amount '{amount_value}' for '{ingredient_name}', defaulting to 0")
                quantity = 0
                
            unit = ingredient_data.get('unit', '').lower().strip()
            
            # Try to find the ingredient in our database for category info
            ingredient_obj = self._find_ingredient_by_name(ingredient_name)
            category = ingredient_obj.category if ingredient_obj else 'other'
            
            # Normalize the ingredient name for aggregation
            normalized_name = self._normalize_ingredient_name(ingredient_name)
            
            if normalized_name in aggregated:
                # Aggregate quantities (convert to common unit if possible)
                existing_unit = aggregated[normalized_name]['unit']
                if existing_unit and unit and self._can_convert_units(existing_unit, unit):
                    # Convert to common unit and add
                    converted_quantity = self._convert_quantity(quantity, unit, existing_unit)
                    aggregated[normalized_name]['quantity'] += converted_quantity
                else:
                    # Can't convert, just add as separate note
                    note = f"{quantity} {unit}".strip()
                    if note not in aggregated[normalized_name]['notes']:
                        aggregated[normalized_name]['notes'].append(note)
            else:
                # First occurrence
                aggregated[normalized_name] = {
                    'quantity': quantity,
                    'unit': unit,
                    'name': ingredient_data.get('name', ingredient_name),
                    'category': category,
                    'notes': []
                }
        
        return dict(aggregated)
    
    def _organize_by_categories(self, aggregated_ingredients: Dict[str, Dict]) -> Dict[str, Any]:
        """Organize ingredients by food categories for easier shopping"""
        categories = defaultdict(list)
        
        for ingredient_key, ingredient_data in aggregated_ingredients.items():
            category = ingredient_data['category']
            
            # Format quantity display
            quantity_display = self._format_quantity_display(
                ingredient_data['quantity'],
                ingredient_data['unit'],
                ingredient_data['notes']
            )
            
            categories[category].append({
                'name': ingredient_data['name'],
                'quantity': quantity_display,
                'raw_quantity': ingredient_data['quantity'],
                'unit': ingredient_data['unit'],
                'notes': ingredient_data['notes'],
                'checked': False  # For frontend shopping list interaction
            })
        
        # Convert to proper structure with category metadata
        category_mapping = {
            'produce': {'name': 'Fruits & Vegetables', 'icon': '🥬', 'order': 1},
            'proteins': {'name': 'Meat & Seafood', 'icon': '🥩', 'order': 2},
            'dairy': {'name': 'Dairy & Eggs', 'icon': '🥛', 'order': 3},
            'grains': {'name': 'Grains & Bread', 'icon': '🍞', 'order': 4},
            'pantry': {'name': 'Pantry Staples', 'icon': '🥫', 'order': 5},
            'condiments': {'name': 'Condiments & Sauces', 'icon': '🧂', 'order': 6},
            'beverages': {'name': 'Beverages', 'icon': '🥤', 'order': 7},
            'snacks': {'name': 'Snacks', 'icon': '🍿', 'order': 8},
            'frozen': {'name': 'Frozen Foods', 'icon': '🧊', 'order': 9},
            'other': {'name': 'Other', 'icon': '📦', 'order': 10},
        }
        
        organized_categories = {}
        for category, items in categories.items():
            category_info = category_mapping.get(category, category_mapping['other'])
            organized_categories[category] = {
                'name': category_info['name'],
                'icon': category_info['icon'],
                'order': category_info['order'],
                'items': sorted(items, key=lambda x: x['name'].lower()),
                'item_count': len(items)
            }
        
        return {
            'categories': organized_categories,
            'total_categories': len(organized_categories)
        }
    
    def _find_ingredient_by_name(self, ingredient_name: str):
        """Find ingredient in database by name (fuzzy matching)"""
        try:
            # Try exact match first
            ingredient = Ingredient.objects.filter(
                name_clean=ingredient_name.lower().replace(' ', '')
            ).first()
            
            if not ingredient:
                # Try partial match
                ingredient = Ingredient.objects.filter(
                    name__icontains=ingredient_name
                ).first()
            
            return ingredient
        except Exception:
            return None
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalize ingredient name for aggregation (remove plurals, common variations)"""
        name = name.lower().strip()
        
        # Common normalizations
        normalizations = {
            'tomatoes': 'tomato',
            'onions': 'onion',
            'carrots': 'carrot',
            'potatoes': 'potato',
            'garlic cloves': 'garlic',
            'cloves garlic': 'garlic',
            'olive oil': 'olive oil',
            'vegetable oil': 'vegetable oil',
            'chicken breast': 'chicken breast',
            'chicken breasts': 'chicken breast',
            'ground beef': 'ground beef',
            'bell pepper': 'bell pepper',
            'bell peppers': 'bell pepper',
        }
        
        return normalizations.get(name, name)
    
    def _can_convert_units(self, unit1: str, unit2: str) -> bool:
        """Check if two units can be converted to each other"""
        if not unit1 or not unit2:
            return False
        
        unit1 = unit1.lower().strip()
        unit2 = unit2.lower().strip()
        
        # Check if both are weight units
        weight_units = {'kg', 'gram', 'grams', 'g', 'lb', 'pound', 'pounds', 'oz', 'ounce', 'ounces'}
        if unit1 in weight_units and unit2 in weight_units:
            return True
        
        # Check if both are volume units
        volume_units = {'l', 'liter', 'liters', 'ml', 'milliliter', 'milliliters', 'cup', 'cups', 
                       'tbsp', 'tablespoon', 'tablespoons', 'tsp', 'teaspoon', 'teaspoons',
                       'fl oz', 'fluid ounce', 'fluid ounces', 'pint', 'pints', 'quart', 'quarts',
                       'gallon', 'gallons'}
        if unit1 in volume_units and unit2 in volume_units:
            return True
        
        # Check if both are count units
        count_units = {'piece', 'pieces', 'item', 'items', 'whole', 'each', 'clove', 'cloves',
                      'slice', 'slices', 'can', 'cans', 'jar', 'jars'}
        if unit1 in count_units and unit2 in count_units:
            return True
        
        return False
    
    def _convert_quantity(self, quantity: float, from_unit: str, to_unit: str) -> float:
        """Convert quantity from one unit to another"""
        if not from_unit or not to_unit:
            return quantity
        
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        if from_unit == to_unit:
            return quantity
        
        # Convert to base unit first, then to target unit
        if from_unit in self.UNIT_CONVERSIONS and to_unit in self.UNIT_CONVERSIONS:
            # Convert to base unit
            base_quantity = quantity * self.UNIT_CONVERSIONS[from_unit]
            # Convert from base unit to target
            converted_quantity = base_quantity / self.UNIT_CONVERSIONS[to_unit]
            return round(converted_quantity, 2)
        
        return quantity
    
    def _format_quantity_display(self, quantity: float, unit: str, notes: List[str]) -> str:
        """Format quantity for display in shopping list"""
        if notes:
            # If we have notes (unconvertible units), show them
            if quantity > 0 and unit:
                return f"{quantity:.1f} {unit}, {', '.join(notes)}"
            else:
                return ', '.join(notes)
        
        if quantity <= 0:
            return "As needed"
        
        # Format based on quantity magnitude
        if quantity == int(quantity):
            quantity_str = str(int(quantity))
        else:
            quantity_str = f"{quantity:.1f}"
        
        if unit:
            return f"{quantity_str} {unit}"
        else:
            return quantity_str
    
    def save_shopping_list_to_meal_plan(self, meal_plan_id: str, shopping_list_data: Dict) -> bool:
        """Save generated shopping list to meal plan model"""
        try:
            meal_plan = MealPlan.objects.get(id=meal_plan_id)
            meal_plan.shopping_list_data = shopping_list_data
            meal_plan.shopping_list_generated = True
            meal_plan.save()
            return True
        except MealPlan.DoesNotExist:
            logger.error(f"Meal plan {meal_plan_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error saving shopping list to meal plan: {str(e)}")
            return False