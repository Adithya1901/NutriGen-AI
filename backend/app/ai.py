import os
import requests
import re
import json
import urllib.parse
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
# CORE GROQ FUNCTION (TEXT)
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
# GROQ STRUCTURED JSON FUNCTION
# -----------------------------------
def ask_groq_json(prompt, system_prompt=None):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("[AI] GROQ_API_KEY environment variable is missing.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for model_name in FALLBACK_MODELS:
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}
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
                    content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()
                
                try:
                    parsed = json.loads(content)
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"[AI] Failed to decode JSON from model {model_name}: {e}")
                    match = re.search(r'\{[\s\S]*\}', content)
                    if match:
                        try:
                            return json.loads(match.group(0))
                        except Exception:
                            pass
                    continue

            if "error" in result:
                message = result["error"].get("message", str(result["error"]))
                print(f"[AI] Groq JSON error on model {model_name}: {message}")
                if "does not exist" in message.lower() or "access to it" in message.lower() or "response_format" in message.lower():
                    continue
                break

        except Exception as e:
            print(f"[AI] Request exception on model {model_name}: {e}")

    return None


# -----------------------------------
# YOUTUBE SEARCH URL / API HELPER
# -----------------------------------
def get_youtube_url(query):
    query_str = str(query or "").strip()
    if not query_str:
        query_str = "healthy recipe"
    
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    if youtube_api_key:
        try:
            yt_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "maxResults": 1,
                "q": query_str,
                "type": "video",
                "key": youtube_api_key
            }
            res = requests.get(yt_url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                if items and len(items) > 0:
                    video_id = items[0]["id"].get("videoId")
                    if video_id:
                        return f"https://www.youtube.com/watch?v={video_id}"
        except Exception as e:
            print(f"[AI] YouTube API Search failed: {e}")

    encoded_query = urllib.parse.quote_plus(query_str)
    return f"https://www.youtube.com/results?search_query={encoded_query}"



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
# STRUCTURED RECIPE FALLBACK HELPER
# -----------------------------------
def get_fallback_structured_recipe(dish_name="Vegetable Masala Omelette", meal_type="Breakfast", language="English"):
    clean_name = str(dish_name or "Nutritious Indian Meal").strip()
    
    # Strip any date or generic prefix if accidentally passed
    if re.match(r'^\d{4}-\d{2}-\d{2}$', clean_name) or clean_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        clean_name = str(meal_type or "Vegetable Masala Omelette").strip()

    # Filter out generic names if passed by accident
    if clean_name.lower() in ["breakfast", "lunch", "dinner", "snack", "snacks", "nutritious healthy meal", "healthy meal"]:
        m_lower = str(meal_type or "").lower()
        if "lunch" in m_lower:
            clean_name = "Vegetable Biryani"
        elif "dinner" in m_lower:
            clean_name = "Paneer Tikka Masala"
        elif "snack" in m_lower:
            clean_name = "Vegetable Sandwich"
        else:
            clean_name = "Vegetable Masala Omelette"

    lower_name = clean_name.lower()

    if "omelette" in lower_name or "egg" in lower_name:
        return {
            "recipe_name": clean_name if clean_name else "Vegetable Masala Omelette",
            "meal_type": meal_type or "Breakfast",
            "description": f"A classic, protein-packed Indian style masala omelette loaded with fresh vegetables and aromatic spices.",
            "servings": 2,
            "cooking_time_minutes": 15,
            "ingredients": [
                {"name": "Eggs", "quantity": "4", "unit": "large"},
                {"name": "Onion", "quantity": "1", "unit": "medium, finely chopped"},
                {"name": "Tomato", "quantity": "1", "unit": "medium, finely chopped"},
                {"name": "Green Chilli", "quantity": "1", "unit": "finely chopped"},
                {"name": "Fresh Coriander", "quantity": "2", "unit": "tbsp chopped"},
                {"name": "Turmeric Powder", "quantity": "1/4", "unit": "tsp"},
                {"name": "Red Chilli Powder", "quantity": "1/4", "unit": "tsp"},
                {"name": "Salt", "quantity": "1/2", "unit": "tsp or to taste"},
                {"name": "Butter or Oil", "quantity": "1", "unit": "tbsp"}
            ],
            "preparation_steps": [
                "Wash all fresh vegetables thoroughly under clean running water.",
                "Finely chop the onion, tomato, green chilli, and fresh coriander leaves.",
                "Crack 4 large eggs into a clean mixing bowl.",
                "Add salt, turmeric powder, and red chilli powder to the bowl.",
                "Whisk vigorously using a fork or whisk for 1-2 minutes until light and frothy.",
                "Fold the chopped onion, tomato, green chilli, and coriander into the egg mixture."
            ],
            "cooking_steps": [
                "Place a non-stick frying pan or tawa over medium heat and melt 1 tbsp of butter or oil.",
                "Tilt the pan to coat the surface evenly with melted butter.",
                "Pour the whisked egg and vegetable mixture into the center of the hot pan.",
                "Swirl the pan gently to spread the eggs into an even circle.",
                "Cook on medium flame for 2–3 minutes until the edges set and the bottom turns golden brown.",
                "Carefully insert a spatula under the omelette and flip it over.",
                "Cook the reverse side for an additional 1–2 minutes until set and cooked through.",
                "Fold the omelette in half and transfer to a serving plate.",
                "Serve hot with toasted whole wheat bread or mint chutney."
            ],
            "nutrition": {
                "calories": "240 kcal",
                "protein": "14g",
                "carbohydrates": "6g",
                "fat": "18g"
            },
            "youtube_search_query": f"{clean_name} recipe in {language}"
        }
    elif "biryani" in lower_name or "pulao" in lower_name or "rice" in lower_name:
        return {
            "recipe_name": clean_name if clean_name else "Vegetable Biryani",
            "meal_type": meal_type or "Lunch",
            "description": "Fragrant Basmati rice layered with spiced mixed vegetables, fresh mint, and saffron.",
            "servings": 4,
            "cooking_time_minutes": 40,
            "ingredients": [
                {"name": "Basmati Rice", "quantity": "1.5", "unit": "cups"},
                {"name": "Mixed Vegetables (Carrot, Peas, Beans)", "quantity": "2", "unit": "cups chopped"},
                {"name": "Onion", "quantity": "2", "unit": "large, sliced"},
                {"name": "Yogurt (Curd)", "quantity": "1/2", "unit": "cup"},
                {"name": "Ginger Garlic Paste", "quantity": "1", "unit": "tbsp"},
                {"name": "Biryani Masala", "quantity": "1.5", "unit": "tbsp"},
                {"name": "Whole Spices (Cinnamon, Bay Leaf, Cardamom)", "quantity": "1", "unit": "set"},
                {"name": "Ghee or Oil", "quantity": "2", "unit": "tbsp"},
                {"name": "Mint & Coriander", "quantity": "1/2", "unit": "cup chopped"}
            ],
            "preparation_steps": [
                "Wash basmati rice thoroughly until water runs clear and soak for 30 minutes.",
                "Chop carrots, French beans, and potatoes into uniform bite-sized cubes.",
                "Thinly slice onions for golden frying.",
                "Whisk yogurt with biryani masala, turmeric, chilli powder, and ginger-garlic paste.",
                "Marinate chopped vegetables in the spiced yogurt mixture for 20 minutes."
            ],
            "cooking_steps": [
                "Boil 6 cups of water with whole spices and salt; cook soaked rice until 80% done, then drain.",
                "Heat oil in a heavy bottomed pot and fry sliced onions until golden crisp; set half aside.",
                "Add marinated vegetables to the pot and sauté over medium heat for 6–8 minutes.",
                "Layer the partially cooked basmati rice evenly over the vegetable curry layer.",
                "Top with chopped mint, coriander, fried onions, and a drizzle of ghee.",
                "Cover tightly with a lid and cook on low heat (Dum) for 15–20 minutes.",
                "Gently fluff the rice with a fork before serving.",
                "Serve hot alongside cucumber raita and crisp papad."
            ],
            "nutrition": {
                "calories": "380 kcal",
                "protein": "9g",
                "carbohydrates": "64g",
                "fat": "10g"
            },
            "youtube_search_query": f"{clean_name} recipe in {language}"
        }
    elif "paneer" in lower_name or "tikka" in lower_name or "curry" in lower_name or "masala" in lower_name:
        return {
            "recipe_name": clean_name if clean_name else "Paneer Tikka Masala",
            "meal_type": meal_type or "Dinner",
            "description": "Succulent cottage cheese cubes simmered in a creamy, rich tomato gravy with aromatic spices.",
            "servings": 3,
            "cooking_time_minutes": 35,
            "ingredients": [
                {"name": "Paneer (Cottage Cheese)", "quantity": "250", "unit": "grams, cubed"},
                {"name": "Tomatoes", "quantity": "3", "unit": "medium, pureed"},
                {"name": "Onions", "quantity": "2", "unit": "medium, finely chopped"},
                {"name": "Heavy Cream or Cashew Paste", "quantity": "2", "unit": "tbsp"},
                {"name": "Butter or Oil", "quantity": "2", "unit": "tbsp"},
                {"name": "Garam Masala", "quantity": "1", "unit": "tsp"},
                {"name": "Kasuri Methi (Dried Fenugreek)", "quantity": "1", "unit": "tsp crushed"}
            ],
            "preparation_steps": [
                "Cut paneer into uniform 1-inch cubes.",
                "Puree fresh tomatoes, ginger, and garlic into a smooth paste.",
                "Finely chop onions and measure all dry ground spices.",
                "Lightly pan-fry paneer cubes in 1 tsp oil until golden on edges."
            ],
            "cooking_steps": [
                "Melt butter in a pan over medium flame and saute cumin seeds until crackling.",
                "Add chopped onions and saute for 4–5 minutes until light golden brown.",
                "Pour in tomato puree and cook until oil separates from the gravy (6–8 minutes).",
                "Add turmeric, coriander powder, Kashmiri red chilli, and salt; mix well.",
                "Add 1/2 cup warm water to adjust gravy consistency and bring to a simmer.",
                "Gently stir in the pan-fried paneer cubes.",
                "Simmer on low heat for 5 minutes allowing paneer to absorb the flavors.",
                "Stir in heavy cream, garam masala, and crushed kasuri methi.",
                "Serve warm with whole wheat phulkas or naan."
            ],
            "nutrition": {
                "calories": "320 kcal",
                "protein": "16g",
                "carbohydrates": "12g",
                "fat": "24g"
            },
            "youtube_search_query": f"{clean_name} recipe in {language}"
        }
    else:
        return {
            "recipe_name": clean_name if clean_name else "Vegetable Sandwich",
            "meal_type": meal_type or "Snack",
            "description": "A fresh, crispy toasted sandwich filled with vibrant sliced vegetables and green mint chutney.",
            "servings": 2,
            "cooking_time_minutes": 15,
            "ingredients": [
                {"name": "Whole Wheat Bread Slices", "quantity": "4", "unit": "slices"},
                {"name": "Cucumber", "quantity": "1", "unit": "sliced"},
                {"name": "Tomato", "quantity": "1", "unit": "sliced"},
                {"name": "Boiled Potato", "quantity": "1", "unit": "sliced"},
                {"name": "Green Mint Chutney", "quantity": "2", "unit": "tbsp"},
                {"name": "Butter", "quantity": "1", "unit": "tbsp"},
                {"name": "Chaat Masala", "quantity": "1/2", "unit": "tsp"}
            ],
            "preparation_steps": [
                "Boil and slice the potato into thin rounds.",
                "Slice cucumber, tomato, and onion into thin rounds.",
                "Trim bread edges if desired and spread butter on one side of each slice.",
                "Spread green mint chutney evenly over the buttered bread slices."
            ],
            "cooking_steps": [
                "Arrange potato, cucumber, and tomato slices evenly on two bread slices.",
                "Sprinkle chaat masala and black salt over the vegetable layers.",
                "Cover with the remaining bread slices, buttered side facing inward.",
                "Heat a sandwich toaster or pan over medium flame with a little butter.",
                "Place sandwiches in the pan and press down gently with a spatula.",
                "Toast for 2–3 minutes on each side until golden and crispy.",
                "Cut diagonally into halves.",
                "Serve immediately with tomato ketchup or fresh mint chutney."
            ],
            "nutrition": {
                "calories": "210 kcal",
                "protein": "6g",
                "carbohydrates": "36g",
                "fat": "5g"
            },
            "youtube_search_query": f"{clean_name} recipe in {language}"
        }


# -----------------------------------
# DAILY RECIPE GENERATOR (STRUCTURED JSON)
# -----------------------------------
def generate_recipe(dish_name, meal_type="Breakfast", language="English"):
    clean_dish_name = str(dish_name or "").strip()
    
    # Handle if dish_name was passed as date or day
    if re.match(r'^\d{4}-\d{2}-\d{2}$', clean_dish_name) or clean_dish_name in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        clean_dish_name = str(meal_type or "Vegetable Masala Omelette").strip()
        meal_type = "Breakfast"

    # If dish_name is generic like "Breakfast", resolve to realistic food dish
    if not clean_dish_name or clean_dish_name.lower() in ["breakfast", "lunch", "dinner", "snack", "snacks", "nutritious healthy meal", "healthy meal"]:
        m_lower = str(meal_type or "").lower()
        if "lunch" in m_lower:
            clean_dish_name = "Vegetable Biryani"
        elif "dinner" in m_lower:
            clean_dish_name = "Paneer Tikka Masala"
        elif "snack" in m_lower:
            clean_dish_name = "Vegetable Sandwich"
        else:
            clean_dish_name = "Vegetable Masala Omelette"

    system_prompt = (
        "You are an expert master chef and culinary nutritionist. "
        "Generate a complete, structured JSON recipe response. "
        "You MUST respond ONLY in valid JSON matching the exact schema."
    )

    prompt = f"""
Generate a complete, professional, detailed recipe for the dish: "{clean_dish_name}".
Meal Type: {meal_type}
Language for instructions, description, and ingredients: {language}

CRITICAL MANDATORY RULES:
1. "recipe_name" MUST be the exact food/dish name (e.g. "{clean_dish_name}"). NEVER use generic meal names like "Breakfast", "Lunch", "Dinner", "Snack", or "Nutritious Healthy Meal".
2. "ingredients" MUST be an array of objects, where each object contains "name", "quantity", and "unit".
3. "preparation_steps" MUST contain 6 to 12 detailed, sequential, actionable steps explaining how to clean, cut, and prep ingredients.
4. "cooking_steps" MUST contain 6 to 12 detailed, sequential, actionable steps describing heat levels, cooking times, and pan actions.
5. "nutrition" MUST be an object with string values for "calories", "protein", "carbohydrates", and "fat".
6. "youtube_search_query" MUST be a clean search query string for YouTube, e.g. "{clean_dish_name} recipe in {language}".

Return JSON matching this exact structure:
{{
  "recipe_name": "{clean_dish_name}",
  "meal_type": "{meal_type}",
  "description": "Appetizing description in {language}",
  "servings": 2,
  "cooking_time_minutes": 25,
  "ingredients": [
    {{
      "name": "Ingredient name",
      "quantity": "1",
      "unit": "cup"
    }}
  ],
  "preparation_steps": [
    "Step 1...",
    "Step 2...",
    "Step 3...",
    "Step 4...",
    "Step 5...",
    "Step 6..."
  ],
  "cooking_steps": [
    "Step 1...",
    "Step 2...",
    "Step 3...",
    "Step 4...",
    "Step 5...",
    "Step 6..."
  ],
  "nutrition": {{
    "calories": "280 kcal",
    "protein": "12g",
    "carbohydrates": "35g",
    "fat": "10g"
  }},
  "youtube_search_query": "{clean_dish_name} recipe in {language}"
}}
"""

    res = ask_groq_json(prompt, system_prompt)

    if res and isinstance(res, dict) and "recipe_name" in res and "ingredients" in res:
        r_name = str(res.get("recipe_name", "")).strip()
        if not r_name or r_name.lower() in ["breakfast", "lunch", "dinner", "snack", "snacks", "nutritious healthy meal"]:
            res["recipe_name"] = clean_dish_name

        if isinstance(res.get("ingredients"), list):
            formatted_ing = []
            for item in res["ingredients"]:
                if isinstance(item, dict):
                    formatted_ing.append({
                        "name": str(item.get("name", "Ingredient")),
                        "quantity": str(item.get("quantity", "1")),
                        "unit": str(item.get("unit", "pcs"))
                    })
                elif isinstance(item, str):
                    formatted_ing.append({
                        "name": item,
                        "quantity": "1",
                        "unit": "unit"
                    })
            res["ingredients"] = formatted_ing

        if not isinstance(res.get("preparation_steps"), list):
            res["preparation_steps"] = [str(res.get("preparation_steps", "Prepare fresh ingredients."))]
        if not isinstance(res.get("cooking_steps"), list):
            res["cooking_steps"] = [str(res.get("cooking_steps", "Cook over medium flame until done."))]

        query = res.get("youtube_search_query") or f"{clean_dish_name} recipe in {language}"
        res["youtube_url"] = get_youtube_url(query)
        return res

    fallback = get_fallback_structured_recipe(clean_dish_name, meal_type, language)
    fallback["youtube_url"] = get_youtube_url(fallback.get("youtube_search_query"))
    return fallback



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