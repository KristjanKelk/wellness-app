from django.core.management.base import BaseCommand
from meal_planning.models import Recipe, Ingredient
import uuid


class Command(BaseCommand):
    help = 'Populate sample recipes for testing when Spoonacular API is not available'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate sample recipes...'))

        # Sample recipes data
        sample_recipes = [
            {
                'title': 'Classic Grilled Chicken Salad',
                'summary': 'A healthy and delicious grilled chicken salad with mixed greens, cherry tomatoes, and balsamic dressing.',
                'cuisine': 'American',
                'meal_type': 'lunch',
                'servings': 2,
                'prep_time_minutes': 15,
                'cook_time_minutes': 20,
                'total_time_minutes': 35,
                'difficulty_level': 'easy',
                'ingredients_data': [
                    {'name': 'chicken breast', 'amount': 300, 'unit': 'grams'},
                    {'name': 'mixed greens', 'amount': 100, 'unit': 'grams'},
                    {'name': 'cherry tomatoes', 'amount': 150, 'unit': 'grams'},
                    {'name': 'balsamic vinegar', 'amount': 30, 'unit': 'ml'},
                    {'name': 'olive oil', 'amount': 15, 'unit': 'ml'},
                ],
                'instructions': [
                    'Season chicken breast with salt and pepper',
                    'Grill chicken for 8-10 minutes per side until cooked through',
                    'Let chicken rest for 5 minutes, then slice',
                    'Combine mixed greens and cherry tomatoes in a bowl',
                    'Whisk together balsamic vinegar and olive oil',
                    'Top salad with sliced chicken and drizzle with dressing'
                ],
                'calories_per_serving': 380,
                'protein_per_serving': 35,
                'carbs_per_serving': 12,
                'fat_per_serving': 18,
                'fiber_per_serving': 4,
                'dietary_tags': ['high_protein', 'gluten_free', 'low_carb'],
                'allergens': [],
                'image_url': 'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400',
            },
            {
                'title': 'Vegetarian Buddha Bowl',
                'summary': 'A nutritious bowl packed with quinoa, roasted vegetables, avocado, and tahini dressing.',
                'cuisine': 'Mediterranean',
                'meal_type': 'dinner',
                'servings': 2,
                'prep_time_minutes': 20,
                'cook_time_minutes': 25,
                'total_time_minutes': 45,
                'difficulty_level': 'medium',
                'ingredients_data': [
                    {'name': 'quinoa', 'amount': 100, 'unit': 'grams'},
                    {'name': 'sweet potato', 'amount': 200, 'unit': 'grams'},
                    {'name': 'broccoli', 'amount': 150, 'unit': 'grams'},
                    {'name': 'avocado', 'amount': 1, 'unit': 'piece'},
                    {'name': 'tahini', 'amount': 30, 'unit': 'grams'},
                    {'name': 'lemon juice', 'amount': 20, 'unit': 'ml'},
                ],
                'instructions': [
                    'Cook quinoa according to package directions',
                    'Cube sweet potato and roast at 400°F for 20 minutes',
                    'Steam broccoli until tender, about 8 minutes',
                    'Slice avocado',
                    'Mix tahini with lemon juice and water to make dressing',
                    'Assemble bowls with quinoa, vegetables, and avocado',
                    'Drizzle with tahini dressing'
                ],
                'calories_per_serving': 420,
                'protein_per_serving': 15,
                'carbs_per_serving': 45,
                'fat_per_serving': 22,
                'fiber_per_serving': 12,
                'dietary_tags': ['vegetarian', 'vegan', 'gluten_free', 'high_fiber'],
                'allergens': ['sesame'],
                'image_url': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400',
            },
            {
                'title': 'Overnight Oats with Berries',
                'summary': 'A quick and healthy breakfast option with rolled oats, Greek yogurt, and fresh berries.',
                'cuisine': 'American',
                'meal_type': 'breakfast',
                'servings': 1,
                'prep_time_minutes': 5,
                'cook_time_minutes': 0,
                'total_time_minutes': 5,
                'difficulty_level': 'easy',
                'ingredients_data': [
                    {'name': 'rolled oats', 'amount': 50, 'unit': 'grams'},
                    {'name': 'Greek yogurt', 'amount': 100, 'unit': 'grams'},
                    {'name': 'milk', 'amount': 120, 'unit': 'ml'},
                    {'name': 'mixed berries', 'amount': 80, 'unit': 'grams'},
                    {'name': 'honey', 'amount': 15, 'unit': 'ml'},
                    {'name': 'chia seeds', 'amount': 10, 'unit': 'grams'},
                ],
                'instructions': [
                    'Combine oats, milk, and chia seeds in a jar',
                    'Stir in Greek yogurt and honey',
                    'Refrigerate overnight or at least 4 hours',
                    'Top with fresh berries before serving',
                    'Enjoy cold or warm slightly'
                ],
                'calories_per_serving': 290,
                'protein_per_serving': 18,
                'carbs_per_serving': 45,
                'fat_per_serving': 6,
                'fiber_per_serving': 8,
                'dietary_tags': ['vegetarian', 'high_protein', 'high_fiber'],
                'allergens': ['dairy'],
                'image_url': 'https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=400',
            },
            {
                'title': 'Spaghetti Aglio e Olio',
                'summary': 'A simple Italian pasta dish with garlic, olive oil, and red pepper flakes.',
                'cuisine': 'Italian',
                'meal_type': 'dinner',
                'servings': 4,
                'prep_time_minutes': 10,
                'cook_time_minutes': 15,
                'total_time_minutes': 25,
                'difficulty_level': 'easy',
                'ingredients_data': [
                    {'name': 'spaghetti', 'amount': 400, 'unit': 'grams'},
                    {'name': 'garlic', 'amount': 6, 'unit': 'cloves'},
                    {'name': 'olive oil', 'amount': 60, 'unit': 'ml'},
                    {'name': 'red pepper flakes', 'amount': 1, 'unit': 'tsp'},
                    {'name': 'parsley', 'amount': 30, 'unit': 'grams'},
                    {'name': 'parmesan cheese', 'amount': 50, 'unit': 'grams'},
                ],
                'instructions': [
                    'Cook spaghetti according to package directions until al dente',
                    'While pasta cooks, heat olive oil in a large pan',
                    'Add sliced garlic and red pepper flakes, cook until fragrant',
                    'Drain pasta, reserving 1 cup pasta water',
                    'Add pasta to the pan with garlic oil',
                    'Toss with pasta water as needed to create a silky sauce',
                    'Remove from heat, add parsley and parmesan',
                    'Serve immediately'
                ],
                'calories_per_serving': 450,
                'protein_per_serving': 15,
                'carbs_per_serving': 75,
                'fat_per_serving': 12,
                'fiber_per_serving': 3,
                'dietary_tags': ['vegetarian'],
                'allergens': ['dairy', 'gluten'],
                'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400',
            },
            {
                'title': 'Green Smoothie Bowl',
                'summary': 'A nutrient-packed smoothie bowl with spinach, banana, and tropical toppings.',
                'cuisine': 'American',
                'meal_type': 'breakfast',
                'servings': 1,
                'prep_time_minutes': 10,
                'cook_time_minutes': 0,
                'total_time_minutes': 10,
                'difficulty_level': 'easy',
                'ingredients_data': [
                    {'name': 'frozen banana', 'amount': 150, 'unit': 'grams'},
                    {'name': 'spinach', 'amount': 30, 'unit': 'grams'},
                    {'name': 'mango', 'amount': 100, 'unit': 'grams'},
                    {'name': 'coconut milk', 'amount': 100, 'unit': 'ml'},
                    {'name': 'granola', 'amount': 30, 'unit': 'grams'},
                    {'name': 'coconut flakes', 'amount': 10, 'unit': 'grams'},
                ],
                'instructions': [
                    'Blend frozen banana, spinach, half the mango, and coconut milk until smooth',
                    'Pour into a bowl',
                    'Top with remaining mango pieces, granola, and coconut flakes',
                    'Serve immediately'
                ],
                'calories_per_serving': 320,
                'protein_per_serving': 8,
                'carbs_per_serving': 55,
                'fat_per_serving': 12,
                'fiber_per_serving': 9,
                'dietary_tags': ['vegan', 'gluten_free', 'high_fiber'],
                'allergens': [],
                'image_url': 'https://images.unsplash.com/photo-1511690743698-d9d85f2fbf38?w=400',
            }
        ]

        created_count = 0
        for recipe_data in sample_recipes:
            # Check if recipe already exists
            if Recipe.objects.filter(title=recipe_data['title']).exists():
                self.stdout.write(f'Recipe "{recipe_data["title"]}" already exists, skipping...')
                continue

            # Create the recipe
            recipe = Recipe.objects.create(
                id=uuid.uuid4(),
                title=recipe_data['title'],
                summary=recipe_data['summary'],
                cuisine=recipe_data['cuisine'],
                meal_type=recipe_data['meal_type'],
                servings=recipe_data['servings'],
                prep_time_minutes=recipe_data['prep_time_minutes'],
                cook_time_minutes=recipe_data['cook_time_minutes'],
                total_time_minutes=recipe_data['total_time_minutes'],
                difficulty_level=recipe_data['difficulty_level'],
                ingredients_data=recipe_data['ingredients_data'],
                instructions=recipe_data['instructions'],
                calories_per_serving=recipe_data['calories_per_serving'],
                protein_per_serving=recipe_data['protein_per_serving'],
                carbs_per_serving=recipe_data['carbs_per_serving'],
                fat_per_serving=recipe_data['fat_per_serving'],
                fiber_per_serving=recipe_data['fiber_per_serving'],
                dietary_tags=recipe_data['dietary_tags'],
                allergens=recipe_data['allergens'],
                image_url=recipe_data['image_url'],
                source_type='user_submitted',
                is_verified=True,
                rating_avg=4.2,  # Give them good ratings
                rating_count=15
            )
            
            created_count += 1
            self.stdout.write(f'✅ Created recipe: {recipe.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample recipes!')
        )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS('Your meal planning app now has sample recipes to display!')
            )