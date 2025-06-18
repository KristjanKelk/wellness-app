# nutrition/services/nutrition_calculation_service.py
import logging
from typing import Dict, List, Any, Optional
from django.db.models import Q
from meal_planning.models import Ingredient

logger = logging.getLogger('nutrition')


class NutritionCalculationService:
    """
    Service for calculating nutrition information using function calling
    This handles the backend of OpenAI function calls for nutrition calculations
    """

    def __init__(self):
        self.allergen_mappings = {
            'nuts': ['almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'hazelnut', 'macadamia'],
            'peanuts': ['peanut', 'groundnut'],
            'dairy': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein', 'lactose'],
            'eggs': ['egg', 'albumin', 'ovalbumin'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'mackerel', 'sardine', 'anchovy'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'oyster', 'clam', 'mussel', 'scallop'],
            'soy': ['soy', 'soya', 'tofu', 'tempeh', 'miso', 'edamame'],
            'gluten': ['wheat', 'barley', 'rye', 'spelt', 'kamut', 'triticale'],
            'sesame': ['sesame', 'tahini'],
            'sulfites': ['sulfite', 'sulfur dioxide'],
            'nightshades': ['tomato', 'potato', 'eggplant', 'pepper', 'paprika'],
            'histamine': ['aged cheese', 'wine', 'sauerkraut', 'salami']
        }
        self.dietary_restrictions = {
            'vegetarian': {
                'forbidden': ['beef', 'pork', 'chicken', 'turkey', 'fish', 'seafood', 'meat', 'gelatin'],
                'allowed': ['vegetables', 'fruits', 'grains', 'dairy', 'eggs']
            },
            'vegan': {
                'forbidden': ['beef', 'pork', 'chicken', 'turkey', 'fish', 'seafood', 'meat',
                              'dairy', 'milk', 'cheese', 'butter', 'eggs', 'honey', 'gelatin'],
                'allowed': ['vegetables', 'fruits', 'grains', 'legumes', 'nuts', 'seeds']
            },
            'pescatarian': {
                'forbidden': ['beef', 'pork', 'chicken', 'turkey', 'meat'],
                'allowed': ['fish', 'seafood', 'vegetables', 'fruits', 'grains', 'dairy', 'eggs']
            },
            'keto': {
                'high_carb_forbidden': ['bread', 'rice', 'pasta', 'potato', 'sugar', 'fruit'],
                'encouraged': ['meat', 'fish', 'eggs', 'cheese', 'nuts', 'oils', 'low-carb vegetables']
            },
            'paleo': {
                'forbidden': ['grains', 'legumes', 'dairy', 'processed foods', 'sugar'],
                'allowed': ['meat', 'fish', 'eggs', 'vegetables', 'fruits', 'nuts', 'seeds']
            },
            'gluten_free': {
                'forbidden': ['wheat', 'barley', 'rye', 'spelt', 'bread', 'pasta', 'flour'],
                'allowed': ['rice', 'quinoa', 'corn', 'potatoes', 'meat', 'dairy', 'vegetables']
            },
            'dairy_free': {
                'forbidden': ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey', 'casein'],
                'allowed': ['plant-based alternatives', 'coconut milk', 'almond milk', 'oat milk']
            }
        }

    def calculate_recipe_nutrition(self, ingredients: List[Dict], servings: int = 1) -> Dict:
        """
        Calculate nutritional information for a recipe

        Args:
            ingredients: List of ingredients with name, quantity, and unit
            servings: Number of servings the recipe makes

        Returns:
            Dictionary with nutritional information per serving
        """
        try:
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            total_fiber = 0
            total_sodium = 0

            calculated_ingredients = []

            for ingredient_data in ingredients:
                ingredient_name = ingredient_data.get('name', '').strip().lower()
                quantity = float(ingredient_data.get('quantity', 0))
                unit = ingredient_data.get('unit', 'gram').lower()

                # Find ingredient in database
                ingredient = self._find_ingredient(ingredient_name)

                if ingredient:
                    # Convert quantity to grams (our standard unit)
                    quantity_grams = self._convert_to_grams(quantity, unit, ingredient_name)

                    # Calculate nutrition for this quantity (per 100g in database)
                    multiplier = quantity_grams / 100.0

                    ingredient_calories = ingredient.calories_per_100g * multiplier
                    ingredient_protein = ingredient.protein_per_100g * multiplier
                    ingredient_carbs = ingredient.carbs_per_100g * multiplier
                    ingredient_fat = ingredient.fat_per_100g * multiplier
                    ingredient_fiber = ingredient.fiber_per_100g * multiplier
                    ingredient_sodium = ingredient.sodium_per_100g * multiplier

                    total_calories += ingredient_calories
                    total_protein += ingredient_protein
                    total_carbs += ingredient_carbs
                    total_fat += ingredient_fat
                    total_fiber += ingredient_fiber
                    total_sodium += ingredient_sodium

                    calculated_ingredients.append({
                        'name': ingredient_name,
                        'quantity_grams': quantity_grams,
                        'calories': ingredient_calories,
                        'protein': ingredient_protein,
                        'carbs': ingredient_carbs,
                        'fat': ingredient_fat,
                        'found_in_db': True
                    })
                else:
                    # Use estimated nutrition for unknown ingredients
                    estimated_nutrition = self._estimate_ingredient_nutrition(ingredient_name, quantity, unit)

                    total_calories += estimated_nutrition['calories']
                    total_protein += estimated_nutrition['protein']
                    total_carbs += estimated_nutrition['carbs']
                    total_fat += estimated_nutrition['fat']
                    total_fiber += estimated_nutrition['fiber']

                    calculated_ingredients.append({
                        'name': ingredient_name,
                        'quantity_grams': self._convert_to_grams(quantity, unit, ingredient_name),
                        'calories': estimated_nutrition['calories'],
                        'protein': estimated_nutrition['protein'],
                        'carbs': estimated_nutrition['carbs'],
                        'fat': estimated_nutrition['fat'],
                        'found_in_db': False,
                        'estimated': True
                    })

            # Calculate per serving
            per_serving = {
                'calories': round(total_calories / servings, 1),
                'protein': round(total_protein / servings, 1),
                'carbs': round(total_carbs / servings, 1),
                'fat': round(total_fat / servings, 1),
                'fiber': round(total_fiber / servings, 1),
                'sodium': round(total_sodium / servings, 1)
            }

            return {
                'nutrition_per_serving': per_serving,
                'total_nutrition': {
                    'calories': round(total_calories, 1),
                    'protein': round(total_protein, 1),
                    'carbs': round(total_carbs, 1),
                    'fat': round(total_fat, 1),
                    'fiber': round(total_fiber, 1),
                    'sodium': round(total_sodium, 1)
                },
                'servings': servings,
                'ingredient_breakdown': calculated_ingredients,
                'calculation_confidence': self._calculate_confidence(calculated_ingredients)
            }

        except Exception as e:
            logger.error(f"Error calculating recipe nutrition: {e}")
            return {
                'nutrition_per_serving': {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0, 'sodium': 0},
                'error': str(e)
            }

    def validate_dietary_restrictions(self, ingredients: List[str],
                                      dietary_preferences: List[str],
                                      allergies: List[str]) -> Dict:
        """
        Validate if ingredients meet dietary restrictions and allergies

        Args:
            ingredients: List of ingredient names
            dietary_preferences: List of dietary preferences (vegetarian, vegan, etc.)
            allergies: List of allergies and intolerances

        Returns:
            Dictionary with validation results
        """
        try:
            validation_results = {
                'is_compliant': True,
                'violations': [],
                'warnings': [],
                'allergen_alerts': [],
                'dietary_compliance': {},
                'suggestions': []
            }

            # Normalize ingredient names
            normalized_ingredients = [ing.lower().strip() for ing in ingredients]

            # Check dietary restrictions
            for preference in dietary_preferences:
                preference_key = preference.lower().replace(' ', '_')
                compliance = self._check_dietary_preference(normalized_ingredients, preference_key)
                validation_results['dietary_compliance'][preference] = compliance

                if not compliance['compliant']:
                    validation_results['is_compliant'] = False
                    validation_results['violations'].extend(compliance['violations'])
                    validation_results['suggestions'].extend(compliance['suggestions'])

            # Check allergies
            for allergen in allergies:
                allergen_check = self._check_allergen(normalized_ingredients, allergen)

                if allergen_check['contains_allergen']:
                    validation_results['is_compliant'] = False
                    validation_results['allergen_alerts'].append({
                        'allergen': allergen,
                        'found_in': allergen_check['sources'],
                        'severity': 'high'
                    })

            # Add positive feedback for compliant recipes
            if validation_results['is_compliant']:
                validation_results['compliance_highlights'] = self._get_compliance_highlights(
                    normalized_ingredients, dietary_preferences
                )

            return validation_results

        except Exception as e:
            logger.error(f"Error validating dietary restrictions: {e}")
            return {
                'is_compliant': False,
                'error': str(e),
                'violations': ['Unable to validate dietary restrictions']
            }

    def calculate_ingredient_substitutions(self, original_ingredient: str,
                                           dietary_preferences: List[str],
                                           allergies: List[str]) -> List[Dict]:
        """
        Suggest ingredient substitutions based on dietary needs

        Args:
            original_ingredient: Name of ingredient to substitute
            dietary_preferences: User's dietary preferences
            allergies: User's allergies

        Returns:
            List of suitable substitutions
        """
        try:
            substitutions = []
            original_ingredient = original_ingredient.lower().strip()

            # Find the original ingredient in database
            original_ing_obj = self._find_ingredient(original_ingredient)

            if original_ing_obj:
                # Find ingredients with similar nutritional profile
                similar_ingredients = Ingredient.objects.filter(
                    category=original_ing_obj.category
                ).exclude(
                    id=original_ing_obj.id
                )

                # Filter by dietary preferences
                for preference in dietary_preferences:
                    preference_key = preference.lower().replace(' ', '_')
                    if preference_key in ['vegetarian', 'vegan']:
                        similar_ingredients = similar_ingredients.filter(
                            dietary_tags__contains=[preference_key]
                        )

                # Exclude allergens
                for allergen in allergies:
                    similar_ingredients = similar_ingredients.exclude(
                        allergens__contains=[allergen]
                    )

                # Create substitution recommendations
                for ingredient in similar_ingredients[:5]:  # Top 5 substitutions
                    # Calculate nutrition similarity score
                    similarity_score = self._calculate_nutrition_similarity(
                        original_ing_obj, ingredient
                    )

                    substitutions.append({
                        'ingredient_name': ingredient.name,
                        'conversion_ratio': 1.0,  # 1:1 substitution by default
                        'similarity_score': similarity_score,
                        'nutritional_difference': {
                            'calories': ingredient.calories_per_100g - original_ing_obj.calories_per_100g,
                            'protein': ingredient.protein_per_100g - original_ing_obj.protein_per_100g,
                            'carbs': ingredient.carbs_per_100g - original_ing_obj.carbs_per_100g,
                            'fat': ingredient.fat_per_100g - original_ing_obj.fat_per_100g
                        },
                        'category': ingredient.category,
                        'dietary_tags': ingredient.dietary_tags,
                        'notes': self._get_substitution_notes(original_ingredient, ingredient.name)
                    })

                # Sort by similarity score
                substitutions.sort(key=lambda x: x['similarity_score'], reverse=True)

            return substitutions

        except Exception as e:
            logger.error(f"Error calculating substitutions: {e}")
            return []

    def _find_ingredient(self, ingredient_name: str) -> Optional[Ingredient]:
        """Find ingredient in database with fuzzy matching"""
        try:
            # Direct match first
            ingredient = Ingredient.objects.filter(
                Q(name__iexact=ingredient_name) |
                Q(name_clean__iexact=ingredient_name.replace(' ', '_'))
            ).first()

            if ingredient:
                return ingredient

            # Partial match
            ingredient = Ingredient.objects.filter(
                Q(name__icontains=ingredient_name) |
                Q(name_clean__icontains=ingredient_name.replace(' ', '_'))
            ).first()

            if ingredient:
                return ingredient

            # Check for common variations
            variations = self._get_ingredient_variations(ingredient_name)
            for variation in variations:
                ingredient = Ingredient.objects.filter(
                    Q(name__icontains=variation) |
                    Q(name_clean__icontains=variation.replace(' ', '_'))
                ).first()

                if ingredient:
                    return ingredient

            return None

        except Exception as e:
            logger.error(f"Error finding ingredient '{ingredient_name}': {e}")
            return None

    def _convert_to_grams(self, quantity: float, unit: str, ingredient_name: str) -> float:
        """Convert quantity to grams based on unit and ingredient type"""
        unit = unit.lower().strip()

        # Direct gram conversions
        gram_conversions = {
            'gram': 1, 'grams': 1, 'g': 1,
            'kilogram': 1000, 'kg': 1000,
            'ounce': 28.35, 'ounces': 28.35, 'oz': 28.35,
            'pound': 453.6, 'pounds': 453.6, 'lb': 453.6, 'lbs': 453.6
        }

        if unit in gram_conversions:
            return quantity * gram_conversions[unit]

        # Volume conversions (approximate for common ingredients)
        volume_conversions = {
            'cup': 240, 'cups': 240,
            'tablespoon': 15, 'tablespoons': 15, 'tbsp': 15,
            'teaspoon': 5, 'teaspoons': 5, 'tsp': 5,
            'milliliter': 1, 'ml': 1,
            'liter': 1000, 'l': 1000,
            'fluid ounce': 29.57, 'fl oz': 29.57
        }

        if unit in volume_conversions:
            ml_amount = quantity * volume_conversions[unit]
            # Convert ml to grams based on ingredient density
            return ml_amount * self._get_ingredient_density(ingredient_name)

        # Piece/item conversions (very approximate)
        piece_conversions = {
            'piece': 100, 'pieces': 100,
            'item': 100, 'items': 100,
            'medium': 150, 'large': 200, 'small': 75
        }

        if unit in piece_conversions:
            return quantity * piece_conversions[unit]

        # Default fallback
        logger.warning(f"Unknown unit '{unit}' for ingredient '{ingredient_name}', assuming grams")
        return quantity

    def _get_ingredient_density(self, ingredient_name: str) -> float:
        """Get approximate density for volume to weight conversion"""
        ingredient_name = ingredient_name.lower()

        # Density multipliers (ml to grams)
        densities = {
            'water': 1.0,
            'milk': 1.03,
            'oil': 0.92,
            'honey': 1.4,
            'flour': 0.6,
            'sugar': 0.8,
            'rice': 0.75,
            'oats': 0.4,
            'butter': 0.91,
            'cream': 1.0,
            'yogurt': 1.05
        }

        for key, density in densities.items():
            if key in ingredient_name:
                return density

        # Default density (similar to water)
        return 1.0

    def _estimate_ingredient_nutrition(self, ingredient_name: str, quantity: float, unit: str) -> Dict:
        """Estimate nutrition for unknown ingredients"""
        quantity_grams = self._convert_to_grams(quantity, unit, ingredient_name)
        ingredient_name = ingredient_name.lower()

        # Basic nutrition estimates per 100g
        nutrition_estimates = {
            # Proteins
            'chicken': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'fiber': 0},
            'beef': {'calories': 250, 'protein': 26, 'carbs': 0, 'fat': 15, 'fiber': 0},
            'fish': {'calories': 150, 'protein': 25, 'carbs': 0, 'fat': 5, 'fiber': 0},

            # Vegetables
            'vegetables': {'calories': 25, 'protein': 2, 'carbs': 5, 'fat': 0.3, 'fiber': 3},
            'leafy greens': {'calories': 20, 'protein': 2.5, 'carbs': 3, 'fat': 0.2, 'fiber': 2.5},

            # Fruits
            'fruit': {'calories': 60, 'protein': 1, 'carbs': 15, 'fat': 0.2, 'fiber': 3},

            # Grains
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fat': 0.3, 'fiber': 0.4},
            'bread': {'calories': 265, 'protein': 9, 'carbs': 49, 'fat': 3.2, 'fiber': 2.7},

            # Dairy
            'cheese': {'calories': 350, 'protein': 25, 'carbs': 1, 'fat': 28, 'fiber': 0},
            'milk': {'calories': 60, 'protein': 3.2, 'carbs': 4.8, 'fat': 3.2, 'fiber': 0},

            # Fats
            'oil': {'calories': 900, 'protein': 0, 'carbs': 0, 'fat': 100, 'fiber': 0},
            'nuts': {'calories': 600, 'protein': 15, 'carbs': 15, 'fat': 50, 'fiber': 8}
        }

        # Find best match
        estimated_nutrition = nutrition_estimates.get('vegetables')  # Default

        for category, nutrition in nutrition_estimates.items():
            if category in ingredient_name:
                estimated_nutrition = nutrition
                break

        # Scale by quantity
        multiplier = quantity_grams / 100.0

        return {
            'calories': estimated_nutrition['calories'] * multiplier,
            'protein': estimated_nutrition['protein'] * multiplier,
            'carbs': estimated_nutrition['carbs'] * multiplier,
            'fat': estimated_nutrition['fat'] * multiplier,
            'fiber': estimated_nutrition['fiber'] * multiplier
        }

    def _check_dietary_preference(self, ingredients: List[str], preference: str) -> Dict:
        """Check if ingredients comply with dietary preference"""
        compliance = {
            'compliant': True,
            'violations': [],
            'suggestions': []
        }

        if preference not in self.dietary_restrictions:
            return compliance

        restriction_data = self.dietary_restrictions[preference]
        forbidden_items = restriction_data.get('forbidden', [])

        for ingredient in ingredients:
            for forbidden in forbidden_items:
                if forbidden in ingredient:
                    compliance['compliant'] = False
                    compliance['violations'].append(f"'{ingredient}' contains {forbidden} (not {preference})")

                    # Suggest alternatives
                    if preference == 'vegetarian' and any(meat in forbidden for meat in ['beef', 'pork', 'chicken']):
                        compliance['suggestions'].append(
                            f"Replace '{ingredient}' with tofu, tempeh, or plant-based protein")
                    elif preference == 'vegan' and 'dairy' in forbidden:
                        compliance['suggestions'].append(f"Replace '{ingredient}' with plant-based alternative")

        return compliance

    def _check_allergen(self, ingredients: List[str], allergen: str) -> Dict:
        """Check if ingredients contain specific allergen"""
        allergen_result = {
            'contains_allergen': False,
            'sources': []
        }

        if allergen not in self.allergen_mappings:
            return allergen_result

        allergen_keywords = self.allergen_mappings[allergen]

        for ingredient in ingredients:
            for keyword in allergen_keywords:
                if keyword in ingredient:
                    allergen_result['contains_allergen'] = True
                    allergen_result['sources'].append(ingredient)
                    break

        return allergen_result

    def _calculate_confidence(self, ingredient_breakdown: List[Dict]) -> float:
        """Calculate confidence score for nutrition calculation"""
        if not ingredient_breakdown:
            return 0.0

        found_in_db = sum(1 for ing in ingredient_breakdown if ing.get('found_in_db', False))
        total_ingredients = len(ingredient_breakdown)

        confidence = (found_in_db / total_ingredients) * 100
        return round(confidence, 1)

    def _get_ingredient_variations(self, ingredient_name: str) -> List[str]:
        """Get common variations of ingredient name"""
        variations = [ingredient_name]

        # Common variations
        if 'chicken' in ingredient_name:
            variations.extend(['poultry', 'fowl'])
        elif 'beef' in ingredient_name:
            variations.extend(['meat', 'steak'])
        elif 'tomato' in ingredient_name:
            variations.extend(['tomatoes'])
        elif 'onion' in ingredient_name:
            variations.extend(['onions'])

        return variations

    def _calculate_nutrition_similarity(self, ingredient1: Ingredient, ingredient2: Ingredient) -> float:
        """Calculate nutritional similarity between two ingredients"""
        # Compare key nutritional values
        calories_diff = abs(ingredient1.calories_per_100g - ingredient2.calories_per_100g)
        protein_diff = abs(ingredient1.protein_per_100g - ingredient2.protein_per_100g)
        carbs_diff = abs(ingredient1.carbs_per_100g - ingredient2.carbs_per_100g)
        fat_diff = abs(ingredient1.fat_per_100g - ingredient2.fat_per_100g)

        # Calculate similarity score (0-1, where 1 is identical)
        max_calories = max(ingredient1.calories_per_100g, ingredient2.calories_per_100g, 1)
        max_protein = max(ingredient1.protein_per_100g, ingredient2.protein_per_100g, 1)
        max_carbs = max(ingredient1.carbs_per_100g, ingredient2.carbs_per_100g, 1)
        max_fat = max(ingredient1.fat_per_100g, ingredient2.fat_per_100g, 1)

        calories_similarity = 1 - (calories_diff / max_calories)
        protein_similarity = 1 - (protein_diff / max_protein)
        carbs_similarity = 1 - (carbs_diff / max_carbs)
        fat_similarity = 1 - (fat_diff / max_fat)

        # Weighted average (calories most important)
        similarity = (calories_similarity * 0.4 + protein_similarity * 0.3 +
                      carbs_similarity * 0.2 + fat_similarity * 0.1)

        return max(0, min(1, similarity))

    def _get_substitution_notes(self, original: str, substitute: str) -> str:
        """Get helpful notes about ingredient substitution"""
        notes = []

        if 'flour' in original and 'flour' in substitute:
            notes.append("May affect texture slightly")
        elif 'milk' in original and 'milk' in substitute:
            notes.append("Plant-based alternative may change flavor profile")
        elif 'butter' in original:
            notes.append("May need to adjust liquid content")

        return "; ".join(notes) if notes else "Direct 1:1 substitution"

    def _get_compliance_highlights(self, ingredients: List[str], dietary_preferences: List[str]) -> List[str]:
        """Get positive highlights for compliant recipes"""
        highlights = []

        if 'vegetarian' in dietary_preferences:
            plant_count = sum(
                1 for ing in ingredients if any(plant in ing for plant in ['vegetable', 'fruit', 'grain', 'legume']))
            if plant_count >= 3:
                highlights.append("Rich in plant-based ingredients")

        if 'vegan' in dietary_preferences:
            highlights.append("100% plant-based recipe")

        if 'gluten_free' in dietary_preferences:
            highlights.append("Naturally gluten-free")

        return highlights