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

from app.ai import generate_weekly_meal_plan, generate_weekly_grocery, derive_grocery_from_meals

@router.post("/families/{id}/generate-grocery")
def regenerate_grocery(id: int):
    db = SessionLocal()
    try:
        family = db.query(Family).filter(Family.id == id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        ist = timezone(timedelta(hours=5, minutes=30))
        today_str = datetime.now(ist).strftime("%Y-%m-%d")

        upcoming_plans = db.query(DailyPlan).filter(
            DailyPlan.family_id == id,
            DailyPlan.date >= today_str
        ).order_by(DailyPlan.date.asc()).all()

        if not upcoming_plans:
            raise HTTPException(status_code=400, detail="No upcoming meal plans found to generate groceries for.")

        db.query(CustomGroceryList).filter(CustomGroceryList.family_id == id).delete(synchronize_session=False)

        new_grocery_text = derive_grocery_from_meals(upcoming_plans)

        new_list = CustomGroceryList(
            family_id=id,
            dates='["all_upcoming"]',
            meals='["all_upcoming"]',
            grocery_text=new_grocery_text
        )
        db.add(new_list)
        db.commit()

        return {
            "status": "success",
            "grocery_list": new_grocery_text
        }
    finally:
        db.close()