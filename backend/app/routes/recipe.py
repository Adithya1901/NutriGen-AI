from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models import Family, DailyPlan
from app.ai import generate_recipe

router = APIRouter()

@router.get("/families/{id}/recipe")
def get_recipe(id: int, date: str, meal_type: str, language: str = "English"):
    db = SessionLocal()

    try:
        family = db.query(Family).filter(Family.id == id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        # The AI just needs the meal description from the generated plan.
        daily_plan = db.query(DailyPlan).filter(
            DailyPlan.family_id == id,
            DailyPlan.date == date,
            DailyPlan.meal_type == meal_type
        ).first()

        if not daily_plan:
            raise HTTPException(status_code=404, detail="Meal plan not generated for this date and meal time.")

        # Using AI to generate recipe based on the generated meal plan text
        meal_description = daily_plan.plan_text

        prompt_meal = f"{meal_type} ({meal_description})"
        
        recipe_text = generate_recipe(date, prompt_meal, language)

        return {
            "recipe": recipe_text,
            "meal_description": meal_description
        }
    finally:
        db.close()
