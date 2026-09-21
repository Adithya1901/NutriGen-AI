import os
import requests
import re
import json
import urllib.parse
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# -----------------------------------
# CENTRALIZED PRODUCTION GROQ MODEL CONFIGURATION
# Single Source of Truth
# -----------------------------------
DEFAULT_PRIMARY_MODEL = "openai/gpt-oss-120b"
DEFAULT_SECONDARY_MODEL = "openai/gpt-oss-20b"

GROQ_MODEL = os.getenv("GROQ_MODEL", DEFAULT_PRIMARY_MODEL).strip()

_cached_selected_model = None
_cached_active_models = []

GENERIC_MEAL_NAMES = {
    "breakfast", "lunch", "dinner", "snack", "snacks",
    "nutritious healthy meal", "healthy meal", "healthy breakfast",
    "healthy lunch", "healthy dinner", "nutritious meal", "indian meal",
    "meal", "nutritious indian home meal", "nutritious indian meal",
    "healthy food", "home meal", "nutritious food"
}

def get_groq_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        print("[AI ERROR] GROQ_API_KEY environment variable is missing.")
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing in backend environment"
        )
    return api_key.strip()

def fetch_active_groq_models(api_key: str) -> list:
    """Fetch active supported models dynamically from Groq Models API (GET /v1/models)."""
    global _cached_active_models
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", [])
            _cached_active_models = [m.get("id") for m in items if isinstance(m, dict) and "id" in m]
            return _cached_active_models
        elif res.status_code == 401:
            raise HTTPException(status_code=401, detail="Groq API authentication error: Invalid API key")
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[AI WARNING] Could not fetch active Groq models: {e}")
    return _cached_active_models

def get_selected_groq_model(force_refresh: bool = False) -> str:
    """
    SINGLE SOURCE OF TRUTH FOR GROQ MODEL SELECTION.
    Validates model against active Groq models API with safe production fallbacks.
    """
    global _cached_selected_model
    if _cached_selected_model and not force_refresh:
        return _cached_selected_model

    api_key = get_groq_api_key()
    env_model = os.getenv("GROQ_MODEL", "").strip()
    
    candidate_models = []
    if env_model:
        candidate_models.append(env_model)
    candidate_models.extend([
        DEFAULT_PRIMARY_MODEL,
        DEFAULT_SECONDARY_MODEL
    ])
    
    unique_candidates = []
    for m in candidate_models:
        if m and m not in unique_candidates:
            unique_candidates.append(m)
            
    active_models = fetch_active_groq_models(api_key)
    
    if active_models:
        for model_id in unique_candidates:
            if model_id in active_models:
                _cached_selected_model = model_id
                print(f"[AI SUCCESS] Groq model selected: {model_id}")
                return model_id
                
        first_active = active_models[0]
        _cached_selected_model = first_first_active if 'first_first_active' in locals() else first_active
        print(f"[AI NOTICE] Configured model unavailable. Selected active Groq model: {first_active}")
        return first_active

    selected = unique_candidates[0]
    _cached_selected_model = selected
    print(f"[AI NOTICE] Groq model selected (unverified): {selected}")
    return selected

def validate_groq_startup() -> bool:
    """Startup fail-fast validation check called when FastAPI app launches."""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[STARTUP WARNING] GROQ_API_KEY environment variable is missing.")
            return False
        selected = get_selected_groq_model(force_refresh=True)
        print(f"[STARTUP SUCCESS] Groq model selected: {selected}")
        return True
    except Exception as e:
        print(f"[STARTUP ERROR] Groq initialization failed: {e}")
        return False

def is_valid_dish_name(name: str) -> bool:
    if not name or not isinstance(name, str):
        return False
    clean = name.strip().lower()
    if len(clean) < 3:
        return False
    if clean in GENERIC_MEAL_NAMES:
        return False
    for gen in ["healthy meal", "nutritious meal", "indian meal", "delicious meal", "healthy breakfast", "healthy lunch", "healthy dinner"]:
        if clean == gen:
            return False
    return True


# -----------------------------------
# CORE GROQ TEXT FUNCTION
# -----------------------------------
def ask_groq(prompt: str, system_prompt: str = None) -> str:
    api_key = get_groq_api_key()
    selected_model = get_selected_groq_model()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": selected_model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 4096
    }
    
    try:
        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)
        
        if res.status_code == 401:
            print(f"[AI ERROR] Groq 401 Auth Error on model {selected_model}")
            raise HTTPException(status_code=401, detail="Groq API authentication error: Invalid API key")
        elif res.status_code == 403:
            print(f"[AI ERROR] Groq 403 Permission Error on model {selected_model}")
            raise HTTPException(status_code=403, detail="Groq API permission error")
        elif res.status_code == 429:
            print(f"[AI ERROR] Groq 429 Rate Limit Error on model {selected_model}")
            raise HTTPException(status_code=429, detail="Groq API rate limit error. Please try again in a few moments.")
        elif res.status_code == 400:
            result = res.json() if res.text else {}
            err_msg = result.get("error", {}).get("message", "Invalid request or model schema")
            print(f"[AI ERROR] Groq 400 Error on model {selected_model}: {err_msg}")
            raise HTTPException(status_code=400, detail=f"Configured Groq model error: {err_msg}")
        elif res.status_code >= 500:
            print(f"[AI ERROR] Groq {res.status_code} Server Error on model {selected_model}")
            raise HTTPException(status_code=500, detail="Groq AI service error. Please try again later.")

        result = res.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"] or ""
            if "<think>" in content:
                content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()
            return content.strip()
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[AI ERROR] Request exception on model {selected_model}: {e}")
        raise HTTPException(status_code=500, detail=f"Groq AI service call failed: {str(e)}")

    raise HTTPException(status_code=500, detail="Groq AI returned an empty response.")


# -----------------------------------
# GROQ STRUCTURED JSON FUNCTION
# -----------------------------------
def ask_groq_json(prompt: str, system_prompt: str = None) -> dict:
    api_key = get_groq_api_key()
    selected_model = get_selected_groq_model()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": selected_model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    try:
        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)

        if res.status_code == 401:
            print(f"[AI ERROR] Groq 401 Auth Error on model {selected_model}")
            raise HTTPException(status_code=401, detail="Groq API authentication error: Invalid API key")
        elif res.status_code == 403:
            print(f"[AI ERROR] Groq 403 Permission Error on model {selected_model}")
            raise HTTPException(status_code=403, detail="Groq API permission error")
        elif res.status_code == 429:
            print(f"[AI ERROR] Groq 429 Rate Limit Error on model {selected_model}")
            raise HTTPException(status_code=429, detail="Groq API rate limit error. Please try again in a few moments.")
        elif res.status_code == 400:
            result = res.json() if res.text else {}
            err_msg = result.get("error", {}).get("message", "Invalid request or model schema")
            print(f"[AI ERROR] Groq 400 Error on model {selected_model}: {err_msg}")
            raise HTTPException(status_code=400, detail=f"Configured Groq model error: {err_msg}")
        elif res.status_code >= 500:
            print(f"[AI ERROR] Groq {res.status_code} Server Error on model {selected_model}")
            raise HTTPException(status_code=500, detail="Groq AI service error. Please try again later.")

        result = res.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"] or ""
            if "<think>" in content:
                content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    return json.loads(match.group(0))
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[AI ERROR] JSON request exception on model {selected_model}: {e}")
        raise HTTPException(status_code=500, detail=f"Groq AI service call failed: {str(e)}")

    raise HTTPException(status_code=500, detail="Failed to parse valid JSON from Groq AI response.")


# -----------------------------------
# FAMILY MEMBER PROFILE PROMPT HELPER
# -----------------------------------
def build_family_prompt_context(family) -> tuple:
    members = getattr(family, "members", []) or []
    num_members = len(members) if len(members) > 0 else 1
    
    info_lines = []
    if members:
        for m in members:
            weight_str = f", Weight: {m.weight}" if getattr(m, "weight", None) else ""
            height_str = f", Height: {m.height}" if getattr(m, "height", None) else ""
            pref_str = f", Meal Preferences: {m.meal_preferences}" if getattr(m, "meal_preferences", None) else ""
            
            line = (
                f"- {m.name} (Age: {m.age}{weight_str}{height_str}, "
                f"Diet: {m.diet}, Goal: {m.goal}, "
                f"Health Condition: {m.health_condition}{pref_str})"
            )
            info_lines.append(line)
    
    members_text = "\n".join(info_lines) if info_lines else "General family meal plan."
    return members_text, num_members


# -----------------------------------
# WEEKLY STRUCTURED MEAL PLAN
# -----------------------------------
def generate_weekly_meal_plan_structured(family, budget: str = "Medium") -> dict:
    members_text, num_members = build_family_prompt_context(family)

    system_prompt = (
        "You are an expert Indian nutritionist and master culinary chef. "
        "You generate detailed, highly personalized, realistic Indian family meal plans in valid JSON. "
        "Every single meal name MUST be a real, specific, authentic Indian dish (e.g. 'Vegetable Upma', 'Ragi Dosa', 'Palak Paneer', 'Brown Rice Dal', 'Vegetable Sambar', 'Chana Sundal', 'Moong Dal Chilla', 'Idli Sambar'). "
        "NEVER generate generic meal names like 'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Nutritious Healthy Meal', 'Healthy Meal'."
    )

    prompt = f"""
Generate a 7-day weekly Indian family meal plan for household '{family.name}' with {num_members} family member(s).

FAMILY MEMBERS PROFILE ({num_members} members):
{members_text}

Budget Setting: {budget}. Keep meal ingredients aligned with a {budget} budget!

CRITICAL MANDATORY INSTRUCTIONS:
1. You MUST consider ALL {num_members} family members listed above, including their age, weight, height, dietary preferences, health conditions, and meal preferences.
2. Generate ONE unified meal plan for the entire family.
3. Every single meal name MUST be a real Indian dish.
4. DO NOT output generic meal names like "Breakfast", "Lunch", "Dinner", "Snack", "Nutritious Healthy Meal", "Healthy Meal".
5. Return 7 days: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday.

Return JSON matching this EXACT schema:
{{
  "week": [
    {{
      "day": "Monday",
      "breakfast": {{
        "name": "Vegetable Upma with Mint Chutney",
        "description": "Flavorful semolina cooked with fresh vegetables and tempered mustard seeds.",
        "ingredients": ["Semolina", "Carrots", "Peas", "Mustard Seeds", "Curry Leaves"],
        "calories": 280
      }},
      "lunch": {{
        "name": "Palak Paneer with Whole Wheat Roti",
        "description": "Cottage cheese cubes cooked in a mild spinach curry served with hot phulkas.",
        "ingredients": ["Paneer", "Spinach", "Garlic", "Whole Wheat Flour"],
        "calories": 450
      }},
      "dinner": {{
        "name": "Brown Rice Dal Tadka",
        "description": "Nutritious brown rice served with tempered yellow lentils and a cucumber salad.",
        "ingredients": ["Brown Rice", "Toor Dal", "Tomatoes", "Cumin Seeds"],
        "calories": 380
      }},
      "snacks": [
        {{
          "name": "Chana Sundal",
          "description": "Steamed chickpeas tossed with mustard seeds, fresh coconut, and curry leaves.",
          "ingredients": ["Chickpeas", "Grated Coconut", "Mustard Seeds"],
          "calories": 160
        }}
      ]
    }}
  ]
}}
"""

    for attempt in range(3):
        data = ask_groq_json(prompt, system_prompt)
        if data and isinstance(data, dict) and "week" in data and isinstance(data["week"], list):
            week = data["week"]
            if len(week) >= 7:
                valid = True
                for day in week[:7]:
                    b = day.get("breakfast", {})
                    l = day.get("lunch", {})
                    d = day.get("dinner", {})
                    sn = day.get("snacks", [])
                    
                    b_name = b.get("name") if isinstance(b, dict) else None
                    l_name = l.get("name") if isinstance(l, dict) else None
                    d_name = d.get("name") if isinstance(d, dict) else None
                    sn_name = sn[0].get("name") if (isinstance(sn, list) and len(sn) > 0 and isinstance(sn[0], dict)) else None
                    
                    if not (is_valid_dish_name(b_name) and is_valid_dish_name(l_name) and is_valid_dish_name(d_name) and is_valid_dish_name(sn_name)):
                        valid = False
                        print(f"[AI VALIDATION ATTEMPT {attempt+1}] Rejected generic dish names in week plan: B='{b_name}', L='{l_name}', D='{d_name}', S='{sn_name}'")
                        break
                if valid:
                    return data

    raise HTTPException(status_code=500, detail="AI meal generation failed to generate valid real dish names after 3 attempts.")


def generate_weekly_meal_plan(family, budget: str = "Medium") -> str:
    plan_dict = generate_weekly_meal_plan_structured(family, budget)
    return json.dumps(plan_dict)


# -----------------------------------
# DAILY STRUCTURED MEAL GENERATION
# -----------------------------------
def generate_daily_meals_structured(family, date: str, meals: list, budget: str = "Medium") -> dict:
    members_text, num_members = build_family_prompt_context(family)

    system_prompt = (
        "You are an expert Indian chef and nutritionist. "
        "Generate structured JSON meal objects for specified meal types. "
        "Every dish name MUST be an actual, real Indian dish (e.g. 'Ragi Dosa', 'Palak Paneer', 'Chana Sundal', 'Moong Dal Chilla'). "
        "NEVER output generic meal titles like 'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Nutritious Healthy Meal'."
    )

    prompt = f"""
Generate an Indian meal plan for date {date} for family '{family.name}' ({num_members} family members).

FAMILY MEMBERS PROFILE ({num_members} members):
{members_text}

Budget Setting: {budget}.
Requested Meal Types: {', '.join(meals)}

Return JSON containing a top-level key "meals", mapping each requested meal type ({', '.join(meals)}) to a structured meal object.

Schema MUST be:
{{
  "meals": {{
    "Breakfast": {{
      "name": "Moong Dal Chilla with Mint Chutney",
      "description": "Crispy savory lentil pancakes served with refreshing mint chutney.",
      "ingredients": ["Yellow Moong Dal", "Spices", "Mint", "Coriander"],
      "calories": 250
    }},
    "Lunch": {{
      "name": "Paneer Butter Masala with Whole Wheat Roti",
      "description": "Cottage cheese in rich tomato gravy with soft flatbreads.",
      "ingredients": ["Paneer", "Tomatoes", "Butter", "Whole Wheat Atta"],
      "calories": 480
    }}
  }}
}}
"""

    for attempt in range(3):
        data = ask_groq_json(prompt, system_prompt)
        if data and isinstance(data, dict) and "meals" in data and isinstance(data["meals"], dict):
            res_meals = data["meals"]
            valid = True
            for m in meals:
                meal_obj = res_meals.get(m) or res_meals.get(m.lower()) or res_meals.get(m.capitalize())
                if not meal_obj or not isinstance(meal_obj, dict):
                    valid = False
                    break
                dish_name = meal_obj.get("name")
                if not is_valid_dish_name(dish_name):
                    valid = False
                    print(f"[AI VALIDATION ATTEMPT {attempt+1}] Generic dish name rejected for {m}: '{dish_name}'")
                    break
            if valid:
                return res_meals

    raise HTTPException(status_code=500, detail=f"AI generation failed to produce valid dish names for {date} after retries.")


def generate_daily_meal_plan(family, date: str, meals: list, budget: str = "Medium") -> str:
    res_dict = generate_daily_meals_structured(family, date, meals, budget)
    return json.dumps(res_dict)


# -----------------------------------
# WEEKLY GROCERY LIST
# -----------------------------------
def generate_weekly_grocery(family, meal_plan: str = None, budget: str = "Medium", num_days: int = 7) -> str:
    members_text, num_members = build_family_prompt_context(family)

    system_prompt = (
        "You are an expert Indian household grocery manager. "
        "Generate a clean, structured grocery list without preamble or thinking process."
    )

    prompt = f"""
Generate ONE clean, consolidated grocery list for household '{family.name}' ({num_members} members):
{members_text}

Based on this meal schedule:
{meal_plan}

CRITICAL FORMAT RULES:
1. Output ONLY category headers (ending with a colon) and individual ingredient lines.
2. Ingredient items MUST be clean and smartly named (e.g. 'Fresh Eggs', 'Basmati Rice', 'Moong Dal', 'Fresh Spinach').
3. Format EVERY ingredient line strictly as:
   Clean Item Name - Quantity - ₹Estimated Price
   Example:
   Fresh Eggs - 6 pcs - ₹42
   Whole Wheat Atta - 500g - ₹30
4. Scale quantities smartly for {num_members} family members.
5. Provide a final line: "Estimated Total Cost: ₹XXX"

Format:
Category Name:
Clean Item Name - Quantity - ₹Cost
Clean Item Name - Quantity - ₹Cost

Estimated Total Cost: ₹XXX
"""

    res = ask_groq(prompt, system_prompt)
    if res and "Estimated" in res:
        return res

    raise HTTPException(status_code=500, detail="Failed to generate grocery list from Groq AI.")


# -----------------------------------
# YOUTUBE SEARCH URL HELPER
# -----------------------------------
def get_youtube_url(query: str) -> str:
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
            print(f"[AI] YouTube API Search error: {e}")

    encoded_query = urllib.parse.quote_plus(query_str)
    return f"https://www.youtube.com/results?search_query={encoded_query}"


# -----------------------------------
# DAILY RECIPE GENERATOR
# -----------------------------------
def generate_recipe(dish_name: str, meal_type: str = "Breakfast", language: str = "English") -> dict:
    clean_dish_name = str(dish_name or "").strip()
    if not is_valid_dish_name(clean_dish_name):
        clean_dish_name = "Vegetable Masala Omelette"

    system_prompt = (
        "You are an expert master chef and culinary nutritionist. "
        "Generate a complete, structured JSON recipe response. "
        "You MUST respond ONLY in valid JSON matching the exact schema."
    )

    prompt = f"""
Generate a complete, professional, detailed recipe for the dish: "{clean_dish_name}".
Meal Type: {meal_type}
Language: {language}

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
    "Step 2..."
  ],
  "cooking_steps": [
    "Step 1...",
    "Step 2..."
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
        if not is_valid_dish_name(r_name):
            res["recipe_name"] = clean_dish_name

        query = res.get("youtube_search_query") or f"{clean_dish_name} recipe in {language}"
        res["youtube_url"] = get_youtube_url(query)
        return res

    raise HTTPException(status_code=500, detail=f"Failed to generate recipe for {clean_dish_name} from Groq AI.")