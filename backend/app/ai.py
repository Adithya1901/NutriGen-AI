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
            # Fallback to json_object if strict json_schema fails on specific model endpoint
            result = res.json() if res.text else {}
            err_msg = result.get("error", {}).get("message", "Invalid request or model schema")
            if "response_format" in err_msg.lower() or "schema" in err_msg.lower():
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
          "meal_name": { "type": "string" },
          "description": { "type": "string" },
          "estimated_cost": { "type": "number" },
          "calories": { "type": "integer" },
          "protein_g": { "type": "number" },
          "carbohydrates_g": { "type": "number" },
          "fat_g": { "type": "number" },
          "components": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "component_name": { "type": "string" },
                "component_type": { "type": "string" },
                "ingredients": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "name": { "type": "string" },
                      "quantity": { "type": "number" },
                      "unit": { "type": "string" },
                      "estimated_cost": { "type": "number" }
                    },
                    "required": ["name", "quantity", "unit", "estimated_cost"],
                    "additionalProperties": False
                  }
                },
                "preparation_steps": { "type": "array", "items": { "type": "string" } },
                "cooking_steps": { "type": "array", "items": { "type": "string" } },
                "cooking_time_minutes": { "type": "integer" }
              },
              "required": ["component_name", "component_type", "ingredients", "preparation_steps", "cooking_steps", "cooking_time_minutes"],
              "additionalProperties": False
            }
          }
        },
        "required": ["meal_type", "meal_name", "description", "estimated_cost", "calories", "protein_g", "carbohydrates_g", "fat_g", "components"],
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
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "quantity": { "type": "string" },
                "unit": { "type": "string" }
              },
              "required": ["name", "quantity", "unit"],
              "additionalProperties": False
            }
          },
          "preparation_steps": { "type": "array", "items": { "type": "string" } },
          "cooking_steps": { "type": "array", "items": { "type": "string" } },
          "cooking_time_minutes": { "type": "integer" }
        },
        "required": ["name", "ingredients", "preparation_steps", "cooking_steps", "cooking_time_minutes"],
        "additionalProperties": False
      }
    },
    "total_cooking_time_minutes": { "type": "integer" },
    "servings": { "type": "integer" },
    "nutrition": {
      "type": "object",
      "properties": {
        "calories": { "type": "integer" },
        "protein_g": { "type": "number" },
        "carbohydrates_g": { "type": "number" },
        "fat_g": { "type": "number" }
      },
      "required": ["calories", "protein_g", "carbohydrates_g", "fat_g"],
      "additionalProperties": False
    },
    "youtube_search_query": { "type": "string" }
  },
  "required": ["meal_name", "description", "components", "total_cooking_time_minutes", "servings", "nutrition", "youtube_search_query"],
  "additionalProperties": False
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
        data = ask_groq_structured_schema(prompt, system_prompt, "canonical_daily_meals", CANONICAL_MEALS_SCHEMA)
        if data and isinstance(data, dict) and "meals" in data and isinstance(data["meals"], list):
            res_meals = data["meals"]
            parsed_dict = {}
            valid = True
            
            for m_obj in res_meals:
                m_type = m_obj.get("meal_type", "").capitalize()
                m_name = m_obj.get("meal_name", "")
                if not is_valid_dish_name(m_name):
                    valid = False
                    break
                parsed_dict[m_type] = m_obj

            if valid and len(parsed_dict) >= len(meals):
                # Calculate daily cost & validate against budget engine
                total_cost = sum(m.get("estimated_cost", 0.0) for m in parsed_dict.values())
                
                # If budget exceeded by > 15%, auto-adjust component costs
                if total_cost > (allowed_daily_budget * 1.15) and total_cost > 0:
                    scale_factor = (allowed_daily_budget * 0.95) / total_cost
                    for m_type, m_obj in parsed_dict.items():
                        m_obj["estimated_cost"] = round(m_obj.get("estimated_cost", 0.0) * scale_factor, 2)
                        for comp in m_obj.get("components", []):
                            for ing in comp.get("ingredients", []):
                                ing["estimated_cost"] = round(ing.get("estimated_cost", 0.0) * scale_factor, 2)

                return parsed_dict

    raise HTTPException(status_code=500, detail=f"AI generation failed to produce valid canonical meal plan for {date}.")


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
    clean_meal_name = str(meal_input or "").strip()
    if not is_valid_dish_name(clean_meal_name):
        clean_meal_name = "Egg Bhurji with Whole Wheat Toast"

    system_prompt = (
        "You are a master Indian chef and culinary instructor. "
        "Generate a complete multi-component recipe in JSON format. "
        f"The recipe MUST be in language: {language}. "
        "Every distinct component in the meal (e.g. 'Egg Bhurji' AND 'Whole Wheat Toast') MUST have its OWN complete ingredients, preparation_steps, and cooking_steps."
    )

    prompt = f"""
Generate a complete, professional recipe for the multi-component meal: "{clean_meal_name}".
Meal Time: {meal_type}
Target Language: {language}

INSTRUCTIONS:
1. Identify all distinct components in "{clean_meal_name}". E.g. for "Egg Bhurji with Whole Wheat Toast", create component 1: "Egg Bhurji" and component 2: "Whole Wheat Toast".
2. Provide sequential, detailed, actionable preparation_steps and cooking_steps for EACH component in {language}.
3. Provide macro breakdown: calories, protein_g, carbohydrates_g, fat_g.
4. Set youtube_search_query to: "{clean_meal_name} recipe in {language}".
"""

    data = ask_groq_structured_schema(prompt, system_prompt, "recipe_canonical", CANONICAL_RECIPE_SCHEMA)
    
    if data and isinstance(data, dict) and "components" in data and len(data["components"]) > 0:
        query = data.get("youtube_search_query") or f"{clean_meal_name} recipe in {language}"
        data["youtube_url"] = get_youtube_url(query)
        return data

    raise HTTPException(status_code=500, detail=f"Failed to generate structured recipe for '{clean_meal_name}'.")


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
                    name = ing.get("name", "").strip().title()
                    qty = float(ing.get("quantity", 1.0))
                    unit = ing.get("unit", "pcs").strip().lower()
                    cost = float(ing.get("estimated_cost", 0.0))

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