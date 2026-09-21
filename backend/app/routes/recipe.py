from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models import Family, DailyPlan
from app.ai import generate_recipe

from typing import Optional

router = APIRouter()

@router.get("/families/{id}/recipe")
def get_recipe(id: int, date: Optional[str] = None, meal_type: str = "Breakfast", language: str = "English", recipe_name: Optional[str] = None):
    db = SessionLocal()

    try:
        family = db.query(Family).filter(Family.id == id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        meal_description = ""
        clean_search = str(recipe_name or "").strip()

        if clean_search:
            meal_description = clean_search
        elif date:
            daily_plan = db.query(DailyPlan).filter(
                DailyPlan.family_id == id,
                DailyPlan.date == date,
                DailyPlan.meal_type == meal_type
            ).first()

            if daily_plan and daily_plan.plan_text:
                meal_description = daily_plan.plan_text.strip()

        if not meal_description:
            if not date:
                raise HTTPException(status_code=400, detail="Please provide a date or enter a recipe name to search.")
            raise HTTPException(status_code=404, detail="Meal plan not generated for this date and meal time. Try using Recipe Search above!")

        # Using AI to generate recipe based on search name or generated meal plan text
        recipe_data = generate_recipe(meal_description, meal_type, language)

        return {
            "recipe": recipe_data,
            "meal_description": meal_description
        }
    finally:
        db.close()
