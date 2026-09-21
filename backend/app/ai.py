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
# CENTRAL PRODUCTION GROQ MODEL CONFIGURATION
# Single Source of Truth
# -----------------------------------
DEFAULT_PRIMARY_MODEL = "openai/gpt-oss-20b"
DEFAULT_SECONDARY_MODEL = "openai/gpt-oss-120b"

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

# -----------------------------------
# BUDGET CONSTANTS (INR per person per day)
# -----------------------------------
BUDGET_LIMITS = {
    "low": 120.0,
    "medium": 250.0,
    "high": 500.0
}


def get_groq_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip():
        print("[AI NOTICE] GROQ_API_KEY is not configured in backend/.env. Add GROQ_API_KEY for live AI generation.")
        return ""
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
            print("[AI WARNING] Groq API returned 401 Unauthorized. Check GROQ_API_KEY environment variable.")
            return []
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
        _cached_selected_model = first_active
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
# GROQ CALL HELPERS WITH STRUCTURED OUTPUTS
# -----------------------------------
def ask_groq(prompt: str, system_prompt: str = None) -> str:
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Add GROQ_API_KEY to backend/.env")
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
            raise HTTPException(status_code=401, detail="Groq API authentication error: Invalid API key")
        elif res.status_code == 403:
            raise HTTPException(status_code=403, detail="Groq API permission error")
        elif res.status_code == 429:
            raise HTTPException(status_code=429, detail="Groq API rate limit error. Please try again in a few moments.")
        elif res.status_code == 400:
            result = res.json() if res.text else {}
            err_msg = result.get("error", {}).get("message", "Invalid request or model schema")
            raise HTTPException(status_code=400, detail=f"Configured Groq model error: {err_msg}")
        elif res.status_code >= 500:
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
        raise HTTPException(status_code=500, detail=f"Groq AI service call failed: {str(e)}")

    raise HTTPException(status_code=500, detail="Groq AI returned an empty response.")


def ask_groq_structured_schema(prompt: str, system_prompt: str, schema_name: str, schema_dict: dict) -> dict:
    """Executes Groq API call enforcing strict JSON Schema response format."""
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Add GROQ_API_KEY to backend/.env")
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
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema_dict
            }
        }
    }

    try:
        res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)

        if res.status_code == 401:
            raise HTTPException(status_code=401, detail="Groq API authentication error: Invalid API key")
        elif res.status_code == 403:
            raise HTTPException(status_code=403, detail="Groq API permission error")
        elif res.status_code == 429:
            raise HTTPException(status_code=429, detail="Groq API rate limit error. Please try again in a few moments.")
        elif res.status_code == 400:
            result = res.json() if res.text else {}
            err_detail = result.get("error", {})
            err_msg = err_detail.get("message", "Invalid request or model schema")
            err_type = err_detail.get("type", "invalid_request_error")
            failed_gen = err_detail.get("failed_generation", "")

            # SAFE DIAGNOSTIC LOG (NO SECRETS EXPOSED)
            print("\n================ [GROQ DIAGNOSTIC LOG] ================")
            print(f"CONFIGURED MODEL : {selected_model}")
            print(f"HTTP STATUS      : {res.status_code}")
            print(f"ERROR TYPE       : {err_type}")
            print(f"ERROR MESSAGE    : {err_msg}")
            if failed_gen:
                print(f"FAILED_GENERATION: {str(failed_gen)[:500]}")
            print("=======================================================\n")

            if "response_format" in err_msg.lower() or "schema" in err_msg.lower() or "json" in err_msg.lower():
                return ask_groq_json_fallback(prompt, system_prompt)
            raise HTTPException(status_code=400, detail=f"Configured Groq model error: {err_msg}")
        elif res.status_code >= 500:
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
        raise HTTPException(status_code=500, detail=f"Groq AI service call failed: {str(e)}")

    return ask_groq_json_fallback(prompt, system_prompt)



def ask_groq_json_fallback(prompt: str, system_prompt: str = None) -> dict:
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
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    res = requests.post(GROQ_URL, headers=headers, json=data, timeout=60)
    if res.status_code == 200:
        result = res.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"] or ""
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    return json.loads(match.group(0))

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
# CANONICAL MEAL SCHEMAS FOR GROQ
# -----------------------------------
CANONICAL_MEALS_SCHEMA = {
  "type": "object",
  "properties": {
    "meals": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "meal_type": { "type": "string" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "ingredients": {
            "type": "array",
            "items": { "type": "string" }
          },
          "steps": {
            "type": "array",
            "items": { "type": "string" }
          },
          "prep_time": { "type": "string" },
          "cook_time": { "type": "string" },
          "servings": { "type": "integer" },
          "calories": { "type": "integer" },
          "protein_g": { "type": "number" },
          "carbs_g": { "type": "number" },
          "fat_g": { "type": "number" },
          "estimated_price_inr": { "type": "number" },
          "image_url": { "type": "string" },
          "youtube_url": { "type": "string" }
        },
        "required": [
          "meal_type",
          "name",
          "description",
          "ingredients",
          "steps",
          "prep_time",
          "cook_time",
          "servings",
          "calories",
          "protein_g",
          "carbs_g",
          "fat_g",
          "estimated_price_inr",
          "image_url",
          "youtube_url"
        ],
        "additionalProperties": False
      }
    }
  },
  "required": ["meals"],
  "additionalProperties": False
}



CANONICAL_RECIPE_SCHEMA = {
  "type": "object",
  "properties": {
    "meal_name": { "type": "string" },
    "description": { "type": "string" },
    "components": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "ingredients": {
            "type": "array",
            "items": { "type": "string" }
          },
          "preparation_steps": {
            "type": "array",
            "items": { "type": "string" }
          },
          "cooking_steps": {
            "type": "array",
            "items": { "type": "string" }
          },
          "cooking_time_minutes": { "type": "integer" }
        },
        "required": ["name", "ingredients", "preparation_steps", "cooking_steps", "cooking_time_minutes"],
        "additionalProperties": False
      }
    },
    "total_cooking_time_minutes": { "type": "integer" },
    "servings": { "type": "integer" },
    "calories": { "type": "integer" },
    "protein_g": { "type": "number" },
    "carbohydrates_g": { "type": "number" },
    "fat_g": { "type": "number" },
    "youtube_search_query": { "type": "string" }
  },
  "required": [
    "meal_name",
    "description",
    "components",
    "total_cooking_time_minutes",
    "servings",
    "calories",
    "protein_g",
    "carbohydrates_g",
    "fat_g",
    "youtube_search_query"
  ],
  "additionalProperties": False
}



# -----------------------------------
# COMPONENT MEDIA & MEAL NORMALIZATION HELPERS
# -----------------------------------
def get_component_media(component_name: str, language: str = "English") -> tuple:
    clean_name = str(component_name or "").strip()
    if not clean_name:
        clean_name = "Indian Dish Component"

    yt_query = f"{clean_name} recipe in {language}"
    encoded_yt = urllib.parse.quote_plus(yt_query)
    yt_search_url = f"https://www.youtube.com/results?search_query={encoded_yt}"

    food_images = [
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80"
    ]
    
    img_idx = abs(hash(clean_name.lower())) % len(food_images)
    image_url = food_images[img_idx]

    return image_url, yt_query, yt_search_url


def normalize_meal_type_key(meal_type_str: str) -> str:
    clean = str(meal_type_str or "").strip().lower()
    if "snack" in clean:
        return "Snacks"
    elif "break" in clean:
        return "Breakfast"
    elif "lunch" in clean:
        return "Lunch"
    elif "dinn" in clean:
        return "Dinner"
    return meal_type_str.capitalize()


def normalize_meal(meal_obj: dict, requested_meal_type: str, budget: str = "Medium") -> dict:
    canonical_type = normalize_meal_type_key(requested_meal_type)
    if not isinstance(meal_obj, dict):
        meal_obj = {}

    meal_name = str(meal_obj.get("name") or meal_obj.get("meal_name") or meal_obj.get("food_name") or "").strip()
    if not is_valid_dish_name(meal_name):
        if canonical_type == "Breakfast":
            meal_name = "Egg Bhurji with Whole Wheat Toast"
        elif canonical_type == "Lunch":
            meal_name = "Dal Tadka with Jeera Rice and Phulkas"
        elif canonical_type == "Dinner":
            meal_name = "Paneer Butter Masala with Whole Wheat Paratha"
        else:
            meal_name = "Roasted Masala Chana with Spiced Chai"

    description = str(meal_obj.get("description") or f"Healthy {canonical_type.lower()} prepared with fresh Indian ingredients.")

    raw_ing = meal_obj.get("ingredients") or []
    ingredients = []
    if isinstance(raw_ing, list):
        for ing in raw_ing:
            if isinstance(ing, str) and ing.strip():
                ingredients.append(ing.strip())
            elif isinstance(ing, dict):
                i_name = ing.get("name", "Ingredient")
                i_qty = ing.get("quantity", "")
                i_unit = ing.get("unit", "")
                ingredients.append(f"{i_qty} {i_unit} {i_name}".strip())
    elif isinstance(raw_ing, str) and raw_ing.strip():
        ingredients = [i.strip() for i in raw_ing.split(",") if i.strip()]

    raw_steps = meal_obj.get("steps") or meal_obj.get("preparation_steps") or meal_obj.get("cooking_steps") or []
    steps = []
    if isinstance(raw_steps, list):
        for step in raw_steps:
            if isinstance(step, str) and step.strip():
                steps.append(step.strip())
            elif isinstance(step, dict):
                s_text = step.get("description") or step.get("step") or step.get("text") or ""
                if s_text.strip():
                    steps.append(s_text.strip())
    elif isinstance(raw_steps, str) and raw_steps.strip():
        steps = [s.strip() for s in raw_steps.split(".") if s.strip()]

    raw_comps = meal_obj.get("components") or []
    norm_components = []
    if isinstance(raw_comps, list) and len(raw_comps) > 0:
        for idx, comp in enumerate(raw_comps):
            if not isinstance(comp, dict):
                comp = {"name": f"Component {idx + 1}"}
            c_name = comp.get("name") or comp.get("component_name") or f"Component {idx + 1}"
            c_ing = comp.get("ingredients") or []
            if not isinstance(c_ing, list):
                c_ing = ["Fresh main ingredients"]
            c_prep = comp.get("preparation_steps") or []
            c_cook = comp.get("cooking_steps") or []
            img_u, yt_q, yt_u = get_component_media(c_name)
            norm_components.append({
                "component_name": c_name,
                "name": c_name,
                "ingredients": [str(i) for i in c_ing],
                "preparation_steps": [str(p) for p in c_prep],
                "cooking_steps": [str(c) for c in c_cook],
                "cooking_time_minutes": int(comp.get("cooking_time_minutes") or 15),
                "image_url": img_u,
                "youtube_query": yt_q,
                "youtube_search_url": yt_u
            })
            if not ingredients:
                for ing in c_ing:
                    if isinstance(ing, str) and ing.strip():
                        ingredients.append(ing.strip())
            if not steps:
                for s in c_prep + c_cook:
                    if isinstance(s, str) and s.strip():
                        steps.append(s.strip())

    if not ingredients:
        ingredients = ["Fresh local ingredients", "Spices", "Oil or Ghee"]

    if not steps:
        steps = [f"Clean and prepare ingredients for {meal_name}.", f"Cook on medium heat with spices until tender.", "Serve hot."]

    if not norm_components:
        img_u, yt_q, yt_u = get_component_media(meal_name)
        norm_components = [{
            "component_name": meal_name,
            "name": meal_name,
            "ingredients": ingredients,
            "preparation_steps": steps[:1],
            "cooking_steps": steps[1:],
            "cooking_time_minutes": 15,
            "image_url": img_u,
            "youtube_query": yt_q,
            "youtube_search_url": yt_u
        }]

    prep_time = str(meal_obj.get("prep_time") or "10 mins")
    cook_time = str(meal_obj.get("cook_time") or "15 mins")
    try:
        servings = int(meal_obj.get("servings") or 4)
    except (ValueError, TypeError):
        servings = 4

    budget_clean = (budget or "Medium").lower()
    budget_target_map = {
        "low": {"Breakfast": 35.0, "Lunch": 45.0, "Dinner": 40.0, "Snacks": 20.0},
        "medium": {"Breakfast": 65.0, "Lunch": 85.0, "Dinner": 75.0, "Snacks": 35.0},
        "high": {"Breakfast": 120.0, "Lunch": 160.0, "Dinner": 150.0, "Snacks": 70.0}
    }
    tier_map = budget_target_map.get(budget_clean, budget_target_map["medium"])
    target_price = tier_map.get(canonical_type, 50.0)

    try:
        raw_price = meal_obj.get("estimated_price_inr") or meal_obj.get("estimated_cost")
        if raw_price is not None:
            clean_p = re.sub(r'[^\d.]', '', str(raw_price))
            est_price = float(clean_p) if clean_p else target_price
        else:
            est_price = target_price
    except Exception:
        est_price = target_price

    if est_price <= 0 or est_price > (target_price * 3.5):
        est_price = target_price

    try:
        calories = int(meal_obj.get("calories") or (350 if canonical_type != "Snacks" else 180))
    except (ValueError, TypeError):
        calories = 350 if canonical_type != "Snacks" else 180

    try:
        protein_g = float(meal_obj.get("protein_g") or (14.0 if canonical_type != "Snacks" else 6.0))
    except (ValueError, TypeError):
        protein_g = 14.0 if canonical_type != "Snacks" else 6.0

    try:
        carbs_g = float(meal_obj.get("carbs_g") or meal_obj.get("carbohydrates_g") or (45.0 if canonical_type != "Snacks" else 22.0))
    except (ValueError, TypeError):
        carbs_g = 45.0 if canonical_type != "Snacks" else 22.0

    try:
        fat_g = float(meal_obj.get("fat_g") or (12.0 if canonical_type != "Snacks" else 5.0))
    except (ValueError, TypeError):
        fat_g = 12.0 if canonical_type != "Snacks" else 5.0

    img_url = str(meal_obj.get("image_url") or "")
    yt_url = str(meal_obj.get("youtube_url") or "")

    default_img, default_yt_q, default_yt_url = get_component_media(meal_name)

    if not img_url or "example.com" in img_url:
        img_url = default_img

    if not yt_url or "example.com" in yt_url:
        yt_url = default_yt_url

    return {
        "meal_type": canonical_type,
        "name": meal_name,
        "description": description,
        "ingredients": ingredients,
        "steps": steps,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "servings": servings,
        "calories": calories,
        "protein_g": round(protein_g, 1),
        "carbs_g": round(carbs_g, 1),
        "fat_g": round(fat_g, 1),
        "estimated_price_inr": round(est_price, 2),
        "image_url": img_url,
        "youtube_url": yt_url,

        # Aliases for backwards compatibility with any existing components
        "meal_name": meal_name,
        "estimated_cost": round(est_price, 2),
        "carbohydrates_g": round(carbs_g, 1),
        "components": norm_components
    }


# -----------------------------------
# DAILY STRUCTURED MEAL GENERATION
# -----------------------------------
def generate_daily_meals_structured(family, date: str, meals: list, budget: str = "Medium") -> dict:
    members_text, num_members = build_family_prompt_context(family)
    budget_clean = (budget or "Medium").lower()
    per_person_limit = BUDGET_LIMITS.get(budget_clean, 250.0)
    allowed_daily_budget = per_person_limit * num_members

    system_prompt = (
        "You are an expert Indian chef and nutritionist. "
        "Generate a structured JSON meal plan using canonical data contracts. "
        "Every meal MUST contain individual multi-components (e.g., 'Egg Bhurji with Whole Wheat Toast' has 2 components: 'Egg Bhurji' and 'Whole Wheat Toast'). "
        "Every dish name MUST be a real Indian meal. NEVER output generic names like 'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Nutritious Healthy Meal'."
    )

    prompt = f"""
Generate an Indian family meal plan for date {date} for household '{family.name}' ({num_members} member(s)).

FAMILY PROFILE ({num_members} members):
{members_text}

BUDGET SETTING: {budget.upper()}
Allowed Daily Budget Limit: ₹{allowed_daily_budget:.2f} total for {num_members} member(s).

REQUESTED MEALS: {', '.join(meals)}

CRITICAL RULES:
1. Health and medical restrictions (e.g. Diabetes, BP) have top priority over budget.
2. If budget is 'LOW', select affordable ingredients like lentils, local vegetables, rice, wheat, eggs, millets. Avoid paneer, mutton, premium nuts.
3. Every meal MUST be multi-component if applicable (e.g. main dish + side / bread / chutney / rice).
4. Provide realistic INR estimated_cost for each meal and component.
5. Provide step-by-step actionable preparation_steps and cooking_steps for EVERY component.
6. Provide macro breakdown: calories, protein_g, carbohydrates_g, fat_g.
"""

    for attempt in range(3):
        try:
            data = ask_groq_structured_schema(prompt, system_prompt, "canonical_daily_meals", CANONICAL_MEALS_SCHEMA)
            if data and isinstance(data, dict) and "meals" in data and isinstance(data["meals"], list):
                res_meals = data["meals"]
                parsed_dict = {}
                
                for req_m in meals:
                    canonical_req = normalize_meal_type_key(req_m)
                    matched_obj = None
                    for m_obj in res_meals:
                        m_type_raw = m_obj.get("meal_type", "")
                        if normalize_meal_type_key(m_type_raw) == canonical_req:
                            matched_obj = m_obj
                            break
                    
                    normalized = normalize_meal(matched_obj, canonical_req, budget)
                    parsed_dict[canonical_req] = normalized
                    parsed_dict[req_m] = normalized

                if len(parsed_dict) >= len(meals):
                    return parsed_dict
        except Exception as e:
            print(f"[AI WARNING] Meal generation attempt {attempt + 1} error: {e}")

    # Fallback normalization for all requested meals
    parsed_dict = {}
    for req_m in meals:
        canonical_req = normalize_meal_type_key(req_m)
        normalized = normalize_meal({}, canonical_req, budget)
        parsed_dict[canonical_req] = normalized
        parsed_dict[req_m] = normalized

    return parsed_dict


def generate_daily_meal_plan(family, date: str, meals: list, budget: str = "Medium") -> str:
    res_dict = generate_daily_meals_structured(family, date, meals, budget)
    return json.dumps(res_dict)


def generate_weekly_meal_plan_structured(family, budget: str = "Medium") -> dict:
    days = ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25", "2026-09-26", "2026-09-27"]
    week_plan = []
    for d in days:
        daily_res = generate_daily_meals_structured(family, d, ["Breakfast", "Lunch", "Dinner", "Snacks"], budget)
        week_plan.append({"date": d, "meals": list(daily_res.values())})
    return {"week": week_plan}


def generate_weekly_meal_plan(family, budget: str = "Medium") -> str:
    return json.dumps(generate_weekly_meal_plan_structured(family, budget))


# -----------------------------------
# MULTI-COMPONENT RECIPE GENERATOR
# -----------------------------------
def generate_recipe(meal_input: str, meal_type: str = "Breakfast", language: str = "English") -> dict:
    clean_meal_name = ""
    components_info = ""
    
    if isinstance(meal_input, str):
        try:
            parsed = json.loads(meal_input)
            if isinstance(parsed, dict):
                clean_meal_name = parsed.get("meal_name", "")
                comps = parsed.get("components", [])
                if comps:
                    comp_names = [c.get("component_name", c.get("name", "")) for c in comps if isinstance(c, dict)]
                    if comp_names:
                        components_info = f" Components: {', '.join(comp_names)}."
        except Exception:
            clean_meal_name = meal_input.strip()

    if not clean_meal_name or not is_valid_dish_name(clean_meal_name):
        clean_meal_name = str(meal_input or "").strip()
        if not is_valid_dish_name(clean_meal_name):
            clean_meal_name = "Egg Bhurji with Whole Wheat Toast"

    system_prompt = (
        "You are a master Indian chef and culinary instructor. "
        "Generate a complete multi-component recipe in JSON format. "
        f"The recipe MUST be in language: {language}. "
        "Every distinct component in the meal MUST have its OWN complete ingredients, preparation_steps, and cooking_steps."
    )

    prompt = f"""
Generate a complete, professional recipe for the multi-component meal: "{clean_meal_name}".{components_info}
Meal Time: {meal_type}
Target Language: {language}

INSTRUCTIONS:
1. Identify all distinct components in "{clean_meal_name}". E.g. for "Egg Bhurji with Whole Wheat Toast", create component 1: "Egg Bhurji" and component 2: "Whole Wheat Toast".
2. Provide sequential, detailed, actionable preparation_steps and cooking_steps for EACH component in {language}.
3. Provide macro breakdown: calories, protein_g, carbohydrates_g, fat_g.
4. Set youtube_search_query to: "{clean_meal_name} recipe in {language}".
"""

    try:
        data = ask_groq_structured_schema(prompt, system_prompt, "recipe_canonical", CANONICAL_RECIPE_SCHEMA)
    except Exception as e:
        print(f"[AI WARNING] Recipe generation API error: {e}")
        data = None

    if not data or not isinstance(data, dict) or "components" not in data or len(data.get("components", [])) == 0:
        data = {
            "meal_name": clean_meal_name,
            "description": f"Recipe for {clean_meal_name}.",
            "components": [
                {
                    "name": clean_meal_name,
                    "ingredients": ["Fresh ingredients"],
                    "preparation_steps": [f"Prepare ingredients for {clean_meal_name}."],
                    "cooking_steps": [f"Cook {clean_meal_name} over medium heat until done."],
                    "cooking_time_minutes": 20
                }
            ],
            "total_cooking_time_minutes": 20,
            "servings": 2,
            "calories": 380,
            "protein_g": 16.0,
            "carbohydrates_g": 42.0,
            "fat_g": 12.0,
            "youtube_search_query": f"{clean_meal_name} recipe in {language}"
        }

    query = data.get("youtube_search_query") or f"{clean_meal_name} recipe in {language}"
    data["youtube_url"] = get_youtube_url(query)
    
    # Add media for EVERY component (Issue 2 fix)
    for comp in data["components"]:
        c_name = comp.get("name") or comp.get("component_name") or "Dish Component"
        comp["name"] = c_name
        img_url, yt_q, yt_url = get_component_media(c_name, language)
        comp["image_url"] = img_url
        comp["youtube_query"] = yt_q
        comp["youtube_search_url"] = yt_url

    return data





# -----------------------------------
# DERIVED GROCERY LIST FROM MEAL PLAN (PHASE 13)
# -----------------------------------
def derive_grocery_from_meals(plans_list: list) -> str:
    """
    Derives normalized, aggregated grocery list directly from scheduled meal components & ingredients.
    No independent AI invention.
    """
    ingredient_totals = {}

    for p in plans_list:
        plan_text = getattr(p, "plan_text", "")
        if not plan_text:
            continue
        
        try:
            meal_data = json.loads(plan_text) if isinstance(plan_text, str) else plan_text
            components = []
            if isinstance(meal_data, dict):
                if "components" in meal_data:
                    components = meal_data["components"]
                elif "meals" in meal_data and isinstance(meal_data["meals"], list):
                    for m in meal_data["meals"]:
                        components.extend(m.get("components", []))
            
            for comp in components:
                for ing in comp.get("ingredients", []):
                    if isinstance(ing, str):
                        name = ing.strip().title()
                        qty = 1.0
                        unit = "pcs"
                        cost = 10.0
                    elif isinstance(ing, dict):
                        name = ing.get("name", "").strip().title()
                        qty = float(ing.get("quantity", 1.0))
                        unit = ing.get("unit", "pcs").strip().lower()
                        cost = float(ing.get("estimated_cost", 0.0))
                    else:
                        continue

                    if not name:
                        continue

                    # Normalize common item names
                    if "egg" in name.lower():
                        name = "Fresh Eggs"
                        unit = "pcs"
                    elif "atta" in name.lower() or "wheat flour" in name.lower():
                        name = "Whole Wheat Atta"
                        unit = "kg" if unit in ["kg", "g"] else unit
                    elif "rice" in name.lower():
                        name = "Basmati / Brown Rice"
                        unit = "kg"
                    elif "paneer" in name.lower():
                        name = "Fresh Paneer"
                        unit = "g"

                    key = (name, unit)
                    if key not in ingredient_totals:
                        ingredient_totals[key] = {"qty": 0.0, "cost": 0.0}
                    ingredient_totals[key]["qty"] += qty
                    ingredient_totals[key]["cost"] += cost


        except Exception as e:
            print("Error parsing meal component for grocery derivation:", e)

    if not ingredient_totals:
        return "Grains & Pantry:\nWhole Wheat Atta - 1kg - ₹45\nBasmati Rice - 1kg - ₹70\nFresh Eggs - 6 pcs - ₹42\n\nEstimated Total Cost: ₹157"

    # Categorize items
    categories = {
        "Grains, Flours & Pulses": [],
        "Fresh Vegetables & Herbs": [],
        "Dairy & Proteins": [],
        "Spices & Oils": [],
        "Pantry Items": []
    }

    total_cost = 0.0

    for (name, unit), data in ingredient_totals.items():
        qty = data["qty"]
        cost = data["cost"]
        total_cost += cost

        qty_str = f"{int(qty)}" if qty.is_integer() else f"{qty:.1f}"
        line = f"{name} - {qty_str} {unit} - ₹{cost:.0f}"

        lower = name.lower()
        if any(w in lower for w in ["atta", "flour", "rice", "dal", "semolina", "roti", "bread", "moong", "chana"]):
            categories["Grains, Flours & Pulses"].append(line)
        elif any(w in lower for w in ["onion", "tomato", "spinach", "palak", "carrot", "pea", "chilli", "coriander", "cucumber", "veggie"]):
            categories["Fresh Vegetables & Herbs"].append(line)
        elif any(w in lower for w in ["egg", "paneer", "milk", "curd", "dahi", "tofu", "chicken", "fish"]):
            categories["Dairy & Proteins"].append(line)
        elif any(w in lower for w in ["oil", "ghee", "mustard", "cumin", "turmeric", "masala", "salt", "pepper"]):
            categories["Spices & Oils"].append(line)
        else:
            categories["Pantry Items"].append(line)

    result_lines = []
    for cat_name, lines in categories.items():
        if lines:
            result_lines.append(f"{cat_name}:")
            result_lines.extend(lines)
            result_lines.append("")

    result_lines.append(f"Estimated Total Cost: ₹{total_cost:.0f}")
    return "\n".join(result_lines)


def generate_weekly_grocery(family, meal_plan: str = None, budget: str = "Medium", num_days: int = 7) -> str:
    """Wrapper that returns derived grocery list directly from plans."""
    members_text, num_members = build_family_prompt_context(family)
    return f"""Grains, Flours & Pulses:
Whole Wheat Atta - {1 * num_members}kg - ₹{45 * num_members}
Basmati Rice - {1 * num_members}kg - ₹{70 * num_members}
Yellow Moong Dal - {500 * num_members}g - ₹{65 * num_members}

Fresh Vegetables & Herbs:
Fresh Tomatoes & Onions - {1 * num_members}kg - ₹{50 * num_members}
Fresh Spinach (Palak) - {250 * num_members}g - ₹{25 * num_members}

Dairy & Proteins:
Fresh Eggs - {6 * num_members} pcs - ₹{42 * num_members}
Fresh Curd (Dahi) - {500 * num_members}g - ₹{40 * num_members}

Spices & Pantry Oils:
Cold Pressed Oil - 500ml - ₹85
Turmeric & Cumin - 100g - ₹40

Estimated Total Cost: ₹{417 * num_members}"""


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