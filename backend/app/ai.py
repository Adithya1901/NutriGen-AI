# backend/app/ai.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"


# -----------------------------------
# CORE GROQ FUNCTION
# -----------------------------------
def ask_groq(prompt):

    if not GROQ_API_KEY:
        return "ERROR: GROQ_API_KEY missing in .env file"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]

        if "error" in result:
            return f"GROQ ERROR: {result['error']['message']}"

        return str(result)

    except Exception as e:
        return f"REQUEST ERROR: {str(e)}"


# -----------------------------------
# WEEKLY MEAL PLAN
# -----------------------------------
def generate_weekly_meal_plan(family, budget: str = "Medium"):

    family_name = family.name
    members_info = []
    if getattr(family, "members", None):
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

    return ask_groq(prompt)


# -----------------------------------
# WEEKLY GROCERY LIST
# -----------------------------------
def generate_weekly_grocery(family, meal_plan: str = None):

    if not meal_plan:
        meal_plan = generate_weekly_meal_plan(family)

    prompt = f"""
Based on this weekly meal plan:

{meal_plan}

Generate one combined grocery list.
CRITICAL RULES:
1. ONLY list ingredients that are STRICTLY necessary for the meals mentioned above. Do not include extra or random items.
2. Group them by category (e.g., Vegetables, Spices, Dairy).
3. Include explicit quantities for each item based on average family portions.
4. Add the estimated cost in INR (₹) for each item.
5. Provide a final "Estimated Total Cost: ₹XXX" at the bottom.

Format exactly like this:
Category Name:
Item 1 - Quantity - ₹Cost
Item 2 - Quantity - ₹Cost

Estimated Total Cost: ₹XXX

Keep it Budget friendly and tailored for Indian households.
"""

    return ask_groq(prompt)


# -----------------------------------
# DAILY RECIPE
# -----------------------------------
def generate_recipe(day, meal, language="English", servings="4"):

    prompt = f"""
I need a step-by-step professional cooking recipe for the following meal: {meal} (for {day}).

The meal might contain multiple individual items. For EACH item in the meal, keep the preparation completely separate.
Generate the recipe content in this language: {language}.
Adjust all ingredient quantities to strictly serve {servings} people.

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

    return ask_groq(prompt)

# -----------------------------------
# DAILY MEAL PLAN
# -----------------------------------
def generate_daily_meal_plan(family, date: str, meals: list, budget: str = "Medium"):
    family_name = family.name

    members_info = []
    if getattr(family, "members", None):
        for m in family.members:
            info = f"- {m.name} (Age: {m.age}, Diet: {m.diet}, Goal: {m.goal}, Health Condition: {m.health_condition})"
            members_info.append(info)
    
    members_str = "\n".join(members_info) if members_info else "No specific members registered."

    prompt = f"""
Generate a professional Indian meal plan for {date}.
For family name: {family_name}.

Family Members and their Health/Diet Requirements:
{members_str}

Budget Setting: {budget}. Keep the ingredients strictly aligned with a {budget} budget!
You MUST consider all the health conditions, diet preferences, and goals of each family member listed above.

The user only requested the following meals: {', '.join(meals)}.

Output format MUST be EXACTLY:

"""
    for meal in meals:
        prompt += f"{meal}:\n[Provide the meal details here]\n\n"

    prompt += "Use healthy family foods matching the budget level and dietary requirements. Output ONLY the plan."

    return ask_groq(prompt)