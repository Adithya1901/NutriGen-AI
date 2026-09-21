import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "qwen/qwen3.8-27b"
FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound",
]


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

                if "does not exist" in message.lower() or "access to it" in message.lower():
                    continue

                return f"GROQ ERROR: {message}"

            return str(result)

        except Exception as e:
            return f"REQUEST ERROR: {str(e)}"

    if last_error:
        return f"GROQ ERROR: {last_error}"

    return "GROQ ERROR: no valid model available"


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
def generate_weekly_grocery(family, meal_plan: str = None, budget: str = "Medium", num_days: int = 7):

    if not meal_plan:
        meal_plan = generate_weekly_meal_plan(family)

    family_name = family.name
    members_info = []
    if getattr(family, "members", None):
        for m in family.members:
            info = f"- {m.name} (Age: {m.age}, Diet: {m.diet}, Goal: {m.goal}, Health Condition: {m.health_condition})"
            members_info.append(info)
    members_str = "\n".join(members_info) if members_info else "No specific members registered."

    prompt = f"""
You are an expert Indian household grocery manager.
Generate ONE clean, consolidated grocery list for the family '{family_name}' ({len(family.members)} members):
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
5. Scale quantities smartly for {len(family.members)} family members. Avoid excessive bulk buying.
6. Provide a final line: "Estimated Total Cost: ₹XXX"

Format MUST be exactly:
Category Name:
Clean Item Name - Quantity - ₹Cost
Clean Item Name - Quantity - ₹Cost

Estimated Total Cost: ₹XXX
"""

    return ask_groq(prompt)




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

    return ask_groq(prompt)