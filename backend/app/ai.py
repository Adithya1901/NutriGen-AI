import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]


# -----------------------------------
# CORE GROQ FUNCTION
# -----------------------------------
def ask_groq(prompt):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("[AI] GROQ_API_KEY environment variable is missing.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    last_error = None

    for model_name in FALLBACK_MODELS:
        data = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4096
        }

        try:
            response = requests.post(
                GROQ_URL,
                headers=headers,
                json=data,
                timeout=60
            )

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"] or ""
                if "<think>" in content:
                    if "</think>" in content:
                        content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()
                    else:
                        content = re.sub(r'^\s*<think>[\s\S]*?(?:</think>|\n\n|\r\n\r\n)', '', content, flags=re.IGNORECASE).strip()
                        content = re.sub(r'<think>', '', content, flags=re.IGNORECASE).strip()
                return content.strip()

            if "error" in result:
                message = result["error"].get("message", str(result["error"]))
                last_error = message
                print(f"[AI] Groq error on model {model_name}: {message}")

                if "does not exist" in message.lower() or "access to it" in message.lower():
                    continue

                break

        except Exception as e:
            print(f"[AI] Request exception on model {model_name}: {e}")
            last_error = str(e)

    return None


# -----------------------------------
# DYNAMIC FALLBACK HELPERS
# -----------------------------------
def get_smart_fallback_meals(diet="Vegetarian"):
    d = (diet or "").lower()
    if "non" in d:
        return {
            "Breakfast": "Egg Bhurji with Whole Wheat Toast and Fresh Fruit Juice",
            "Lunch": "Chicken Curry with Basmati Rice, Steamed Cauliflower, and Cucumber Raita",
            "Dinner": "Grilled Fish Tikka with Chapati, Dal Tadka, and Green Salad",
            "Snacks": "Boiled Eggs with Black Pepper and Roasted Makhana"
        }
    elif "vegan" in d:
        return {
            "Breakfast": "Spiced Oats Porridge with Almond Milk and Chia Seeds",
            "Lunch": "Tofu Palak Subzi with Brown Rice and Sprouted Moong Salad",
            "Dinner": "Mixed Vegetable Poriyal with Chana Dal and Roti",
            "Snacks": "Roasted Chickpeas with Lemon Juice and Mint Chutney"
        }
    else:
        return {
            "Breakfast": "Moong Dal Chilla with Mint Chutney and Warm Golden Milk",
            "Lunch": "Paneer Butter Masala with Whole Wheat Chapati and Jeera Rice",
            "Dinner": "Lauki Chana Dal with Phulka Roti and Mixed Veg Salad",
            "Snacks": "Sprouted Sprouts Chaat with Pomegranate and Roasted Peanuts"
        }


# -----------------------------------
# WEEKLY MEAL PLAN
# -----------------------------------
def generate_weekly_meal_plan(family, budget: str = "Medium"):
    family_name = family.name
    members_info = []
    diet = "Vegetarian"
    if getattr(family, "members", None) and len(family.members) > 0:
        diet = family.members[0].diet
        for m in family.members:
            info = f"- {m.name} (Age: {m.age}, Diet: {m.diet}, Goal: {m.goal}, Health Condition: {m.health_condition})"
            members_info.append(info)
    
    members_str = "\n".join(members_info) if members_info else "No specific members registered."

    prompt = f"""
Generate a professional 7 day weekly Indian meal plan
for family name: {family_name}

Family Members and their Health/Diet Requirements:
{members_str}

Budget Setting: {budget}. STRICTLY keep the meal plan and ingredients aligned with a {budget} budget!
You MUST consider all the health conditions, diet preferences, and goals of each family member listed above.

Output format:

Monday:
Breakfast:
Lunch:
Dinner:

Tuesday:
Breakfast:
Lunch:
Dinner:

Continue till Sunday.

Use healthy family foods matching the budget level and dietary requirements.
"""

    res = ask_groq(prompt)
    if res:
        return res

    # Smart fallback if GROQ_API_KEY is not configured
    fallback = get_smart_fallback_meals(diet)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    text = ""
    for d in days:
        text += f"{d}:\nBreakfast: {fallback['Breakfast']}\nLunch: {fallback['Lunch']}\nDinner: {fallback['Dinner']}\n\n"
    return text


# -----------------------------------
# WEEKLY GROCERY LIST
# -----------------------------------
def generate_weekly_grocery(family, meal_plan: str = None, budget: str = "Medium", num_days: int = 7):
    if not meal_plan:
        meal_plan = generate_weekly_meal_plan(family, budget)

    family_name = family.name
    members_count = len(family.members) if getattr(family, "members", None) else 1
    members_info = []
    if getattr(family, "members", None):
        for m in family.members:
            info = f"- {m.name} (Age: {m.age}, Diet: {m.diet}, Goal: {m.goal}, Health Condition: {m.health_condition})"
            members_info.append(info)
    members_str = "\n".join(members_info) if members_info else "No specific members registered."

    prompt = f"""
You are an expert Indian household grocery manager.
Generate ONE clean, consolidated grocery list for the family '{family_name}' ({members_count} members):
{members_str}

Based STRICTLY on this meal schedule:
{meal_plan}

CRITICAL FORMAT RULES:
1. DO NOT include any preamble, thinking process, analysis, notes, calculations, day headers (like 'Day 1', 'Breakfast:'), or meal plan text!
2. Output ONLY category headers (ending with a colon) and individual ingredient lines.
3. Ingredient items MUST be clean and smartly named (e.g. 'Fresh Eggs', 'Basmati Rice', 'Moong Dal', 'Fresh Spinach').
4. Format EVERY ingredient line strictly as:
   Clean Item Name - Quantity - ₹Estimated Price
   Example:
   Fresh Eggs - 6 pcs - ₹42
   Whole Wheat Atta - 500g - ₹30
5. Scale quantities smartly for {members_count} family members. Avoid excessive bulk buying.
6. Provide a final line: "Estimated Total Cost: ₹XXX"

Format MUST be exactly:
Category Name:
Clean Item Name - Quantity - ₹Cost
Clean Item Name - Quantity - ₹Cost

Estimated Total Cost: ₹XXX
"""

    res = ask_groq(prompt)
    if res and "Estimated" in res:
        return res

    # Smart fallback grocery list matching expected frontend format
    qty_multiplier = max(1, members_count)
    return f"""Grains & Flours:
Whole Wheat Atta - {1 * qty_multiplier}kg - ₹45
Basmati Rice - {1 * qty_multiplier}kg - ₹70
Yellow Moong Dal - {500 * qty_multiplier}g - ₹65

Fresh Vegetables & Herbs:
Fresh Spinach (Palak) - {250 * qty_multiplier}g - ₹25
Tomatoes & Onions - {1 * qty_multiplier}kg - ₹50
Cucumber & Carrots - {500 * qty_multiplier}g - ₹30

Dairy & Proteins:
Fresh Paneer - {250 * qty_multiplier}g - ₹90
Low Fat Milk - {2 * qty_multiplier}L - ₹110
Fresh Curd (Dahi) - {500 * qty_multiplier}g - ₹40

Spices & Pantry Oils:
Cold Pressed Mustard Oil - 500ml - ₹85
Turmeric & Cumin Seeds - 100g - ₹40
Rock Salt & Black Pepper - 100g - ₹25

Estimated Total Cost: ₹{575 * qty_multiplier}"""


# -----------------------------------
# DAILY RECIPE
# -----------------------------------
def generate_recipe(day, meal, language="English"):
    prompt = f"""
I need a step-by-step professional cooking recipe for the following meal: {meal} (for {day}).

The meal might contain multiple individual items. For EACH item in the meal, keep the preparation completely separate.
Generate the recipe content in this language: {language}.

Format MUST be exactly (repeat this entire block for EACH item in the meal):

Meal Item Name: [Name of the dish in English and {language}]

YouTube Video Search Link: https://www.youtube.com/results?search_query=how+to+make+[Replace_with_English_Dish_Name_using_plus_for_spaces]+recipe+in+{language}

Ingredients:
- [Item 1]
- [Item 2]

Preparation Guide (Brief):
[A short paragraph on preparing the ingredients before cooking]

Step-by-Step Cooking:
Step 1: [Action]
Step 2: [Action]
...

Cooking Time: [Time]
Special Tips: [Brief Tip]
---
"""

    res = ask_groq(prompt)
    if res and "Ingredients:" in res:
        return res

    # Clean fallback recipe parsing structure
    clean_meal_name = meal.split('(')[0].strip() if '(' in meal else meal
    query_name = clean_meal_name.replace(' ', '+')

    return f"""Meal Item Name: {clean_meal_name}

YouTube Video Search Link: https://www.youtube.com/results?search_query=how+to+make+{query_name}+recipe+in+{language}

Ingredients:
- Fresh Main Ingredients - 250g
- Chopped Onions & Tomatoes - 1 cup
- Indian Spices (Turmeric, Cumin, Garam Masala) - 1 tsp each
- Cold Pressed Cooking Oil - 2 tbsp
- Fresh Coriander Leaves - for garnish

Preparation Guide (Brief):
Wash and finely chop all vegetables. Measure spices and keep oil ready in a cooking pan.

Step-by-Step Cooking:
Step 1: Heat oil in a pan over medium flame and saute cumin seeds until fragrant.
Step 2: Add chopped onions and ginger-garlic paste; saute until golden brown.
Step 3: Add tomatoes and spices; cook until oil separates from the masala.
Step 4: Add the main ingredient with 1/2 cup water, cover, and simmer for 10-12 minutes.
Step 5: Garnish with fresh coriander leaves and serve warm.

Cooking Time: 20 mins
Special Tips: Serve fresh with whole wheat rotis or brown rice for maximum nutritional benefit.
---"""


# -----------------------------------
# DAILY MEAL PLAN
# -----------------------------------
def generate_daily_meal_plan(family, date: str, meals: list, budget: str = "Medium"):
    family_name = family.name
    diet = "Vegetarian"

    members_info = []
    if getattr(family, "members", None) and len(family.members) > 0:
        diet = family.members[0].diet
        for m in family.members:
            info = f"- {m.name} (Age: {m.age}, Diet: {m.diet}, Goal: {m.goal}, Health Condition: {m.health_condition})"
            members_info.append(info)
    
    members_str = "\n".join(members_info) if members_info else "No specific members registered."

    prompt = f"""
Generate a professional Indian meal plan for {date} for family name: {family_name}.

Family Members and their Health/Diet Requirements:
{members_str}

Budget Setting: {budget}.
STRICT BUDGET RULES:
- If 'Low': Focus strictly on affordable local ingredients (lentils, local grains like wheat/rice/millets, seasonal vegetables, eggs, standard dairy). Avoid expensive items like paneer, avocados, imported fruits, premium nuts/seeds, mutton, or premium fish.
- If 'Medium': Standard household ingredients (may include paneer, common chicken/fish dishes, basic nuts, standard fruits).
- If 'High': Premium ingredients are allowed (paneer, almonds, walnuts, seeds, olive oil, organic produce, avocados, prawns, mutton, fresh fish, exotic fruits).

CRITICAL REQUIREMENT:
For each meal type, output ONLY the clean recipe/dish name suitable for the family members.
DO NOT include member names, diet labels, health condition tags, or prefixes like "- For [Name]...:".
DO NOT include detailed ingredients, recipes, preparation guides, cooking steps, or instructions! Output ONLY the dish/recipe name.
E.g., "Moong Dal Chilla with Mint Chutney and Buttermilk"

Output format MUST be EXACTLY:

"""
    for meal in meals:
        prompt += f"{meal}:\n"
        prompt += f"[Dish Name]\n\n"

    prompt += "Use healthy family foods matching the budget level and dietary requirements. Output ONLY the plan matching the format, without any introductory or concluding text."

    res = ask_groq(prompt)
    if res:
        return res

    # Smart fallback matching selected meal types
    fallback = get_smart_fallback_meals(diet)
    output = ""
    for m in meals:
        dish_name = fallback.get(m, "Nutritious Indian Meal")
        output += f"{m}:\n{dish_name}\n\n"
    return output