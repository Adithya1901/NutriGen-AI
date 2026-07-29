from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models import Family, WeeklyPlan
from app.ai import generate_weekly_meal_plan, generate_weekly_grocery
from app.utils.helpers import get_current_ist_week

router = APIRouter()

@router.get("/families/{id}/weekly-grocery")
def grocery(id: int):
    db = SessionLocal()

    try:
        family = db.query(Family).filter(Family.id == id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        start_date, end_date = get_current_ist_week()

        weekly_plan = db.query(WeeklyPlan).filter(
            WeeklyPlan.family_id == id,
            WeeklyPlan.start_date == start_date
        ).first()

        if not weekly_plan:
            meal_plan_text = generate_weekly_meal_plan(family)
            grocery_list_text = generate_weekly_grocery(family, meal_plan_text)

            weekly_plan = WeeklyPlan(
                family_id=family.id,
                start_date=start_date,
                end_date=end_date,
                meal_plan_text=meal_plan_text,
                grocery_list_text=grocery_list_text
            )
            db.add(weekly_plan)
            db.commit()
            db.refresh(weekly_plan)

        return {
            "items": weekly_plan.grocery_list_text
        }
    finally:
        db.close()