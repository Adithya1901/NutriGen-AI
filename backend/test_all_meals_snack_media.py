import os
import json
from dotenv import load_dotenv

load_dotenv()

from app.ai import (
    generate_daily_meals_structured,
    generate_recipe,
    normalize_meal,
    get_component_media
)
class MockFamily:
    def __init__(self):
        self.id = 1
        self.name = "Test Household"
        self.members = [
            type("Member", (), {
                "name": "Adithya", "age": 25, "weight": "70 kg", "height": "175 cm",
                "goal": "Muscle Gain", "health_condition": "None", "diet": "Non Vegetarian",
                "meal_preferences": "South Indian"
            })()
        ]

print("================ AUTOMATED SNACK & MEAL TESTS ================")
fam = MockFamily()

meals_to_test = ["Breakfast", "Lunch", "Dinner", "Snacks"]
res_dict = generate_daily_meals_structured(fam, "2026-09-22", meals_to_test, "Medium")

print(f"Generated Meal Types Count: {len(res_dict)}")
for m_type in meals_to_test:
    m = res_dict.get(m_type)
    assert m is not None, f"FAIL: Meal object for '{m_type}' is missing!"
    assert isinstance(m, dict), f"FAIL: Meal object for '{m_type}' is not a dict!"
    
    # 15 Canonical Fields Validation
    required_fields = [
        "meal_type", "name", "description", "ingredients", "steps",
        "prep_time", "cook_time", "servings", "calories", "protein_g",
        "carbs_g", "fat_g", "estimated_price_inr", "image_url", "youtube_url"
    ]
    for field in required_fields:
        assert field in m, f"FAIL: Field '{field}' missing from meal object for '{m_type}'!"

    assert m["meal_type"] == m_type, f"FAIL: Meal type mismatch for '{m_type}'!"
    assert m["name"], f"FAIL: Name for '{m_type}' is empty!"
    assert isinstance(m["ingredients"], list), f"FAIL: Ingredients for '{m_type}' is not a list!"
    assert isinstance(m["steps"], list), f"FAIL: Steps for '{m_type}' is not a list!"
    assert isinstance(m["estimated_price_inr"], (int, float)) and m["estimated_price_inr"] > 0, f"FAIL: Price for '{m_type}' invalid!"
    assert m["image_url"].startswith("http"), f"FAIL: Invalid image_url for '{m_type}'!"
    assert "youtube.com/results" in m["youtube_url"], f"FAIL: Invalid youtube_url for '{m_type}'!"
    
    print(f"[OK] {m_type}: '{m['name']}' | Price: INR {m['estimated_price_inr']} | Calories: {m['calories']} kcal | Image: OK | YouTube: OK")

print("\n================ COMPONENT MEDIA & RECIPE TEST ================")

test_meal_str = json.dumps({
    "meal_name": "Ragi Dosa with Vegetable Sambar and Coconut Chutney",
    "components": [
        {"component_name": "Ragi Dosa", "ingredients": ["Ragi flour", "Urad dal"]},
        {"component_name": "Vegetable Sambar", "ingredients": ["Toor dal", "Mixed veggies"]},
        {"component_name": "Coconut Chutney", "ingredients": ["Fresh coconut", "Green chillies"]}
    ]
})

rec = generate_recipe(test_meal_str, "Breakfast", "English")
comps = rec.get("components", [])
print(f"Recipe Components Count: {len(comps)}")
for idx, c in enumerate(comps):
    c_name = c.get("name")
    img = c.get("image_url")
    yt = c.get("youtube_search_url")
    print(f"Component {idx+1}: '{c_name}'")
    print(f"   Image URL: {img[:60]}...")
    print(f"   YouTube Search URL: {yt}")
    assert img, f"FAIL: Missing image_url for component {c_name}"
    assert yt and "youtube.com/results" in yt, f"FAIL: Invalid youtube_search_url for component {c_name}"

print("\n[OK] ALL AUTOMATED TESTS PASSED SUCCESSFULLY!")

