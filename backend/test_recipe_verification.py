from app.ai import generate_recipe
import json

test_cases = [
    ("Vegetable Masala Omelette", "Breakfast", "English"),
    ("Vegetable Biryani", "Lunch", "English"),
    ("Paneer Tikka Masala", "Dinner", "English"),
    ("Vegetable Sandwich", "Snack", "English")
]

print("=== STARTING RECIPE GENERATION TESTS ===")
for dish, meal_type, lang in test_cases:
    res = generate_recipe(dish, meal_type, lang)
    print(f"\n--- TEST: {dish} ({meal_type}) ---")
    print(f"Recipe Name: {res.get('recipe_name')}")
    print(f"Meal Type: {res.get('meal_type')}")
    print(f"Servings: {res.get('servings')}")
    print(f"Cooking Time: {res.get('cooking_time_minutes')} mins")
    print(f"Ingredients Count: {len(res.get('ingredients', []))}")
    print(f"Prep Steps Count: {len(res.get('preparation_steps', []))}")
    print(f"Cooking Steps Count: {len(res.get('cooking_steps', []))}")
    print(f"Nutrition: {res.get('nutrition')}")
    print(f"YouTube Query: {res.get('youtube_search_query')}")
    print(f"YouTube URL: {res.get('youtube_url')}")
    assert res.get('recipe_name') != meal_type, f"FAIL: recipe_name should not be generic {meal_type}"
    assert len(res.get('ingredients', [])) > 0
    assert len(res.get('preparation_steps', [])) >= 4
    assert len(res.get('cooking_steps', [])) >= 4
    print("OK VERIFIED PERFECT")
print("\n=== ALL 4 RECIPE TESTS PASSED SUCCESSFULLY ===")
