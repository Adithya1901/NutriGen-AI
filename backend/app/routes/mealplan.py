from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models import Family, WeeklyPlan, DailyPlan, CustomGroceryList
from app.ai import generate_weekly_meal_plan, generate_weekly_grocery, generate_daily_meal_plan
from app.utils.helpers import get_current_ist_week
from datetime import datetime, timezone, timedelta
from typing import List
from app import schemas
import json
import re
router = APIRouter()

@router.get("/families/{id}/weekly-plan")
def meal(id: int):
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
            "plan": weekly_plan.meal_plan_text
        }
    finally:
        db.close()

from typing import List
from app import schemas
from app.models import DailyPlan
from app.ai import generate_daily_meal_plan
import re

from app.models import DailyPlan, CustomGroceryList
import json

def parse_daily_plan_response(daily_plan_text: str, meals: list) -> dict:
    parsed = {}
    if not daily_plan_text or "GROQ ERROR" in daily_plan_text or "REQUEST ERROR" in daily_plan_text:
        for m in meals:
            parsed[m] = "Nutritious Indian Home Meal"
        return parsed

    clean_text = re.sub(r'[*#]', '', daily_plan_text).strip()
    meal_pattern = r'(' + '|'.join([re.escape(m) for m in meals]) + r'):'
    split_parts = re.split(meal_pattern, clean_text, flags=re.IGNORECASE)
    
    if len(split_parts) >= 3:
        for i in range(1, len(split_parts) - 1, 2):
            meal_name = split_parts[i].strip()
            meal_content = split_parts[i+1].strip()
            
            matched_meal = next((m for m in meals if m.lower() == meal_name.lower()), None)
            if matched_meal:
                lines = [l.strip() for l in meal_content.split('\n') if l.strip()]
                cleaned_lines = []
                for l in lines:
                    l_clean = re.sub(r'^[\-\*\•]\s*', '', l)
                    if ':' in l_clean:
                        parts = l_clean.split(':')
                        if 'for ' in parts[0].lower() or matched_meal.lower() in parts[0].lower():
                            l_clean = ':'.join(parts[1:]).strip()
                    if l_clean and not any(m.lower() + ':' in l_clean.lower() for m in meals):
                        cleaned_lines.append(l_clean)
                
                parsed[matched_meal] = "\n".join(cleaned_lines) if cleaned_lines else (lines[0] if lines else "Nutritious Indian Meal")

    for m in meals:
        if m not in parsed or not parsed[m]:
            match = re.search(rf"{re.escape(m)}[\s:-]+(.*)", clean_text, re.IGNORECASE)
            if match and match.group(1).strip():
                parsed[m] = match.group(1).strip()
            else:
                parsed[m] = "Nutritious Healthy Meal"

    return parsed


@router.post("/families/{id}/multi-daily-plan", response_model=schemas.MultiDailyPlanResponse)
def create_multi_daily_plan(id: int, req: schemas.MultiDailyPlanRequest):
    db = SessionLocal()

    try:
        family = db.query(Family).filter(Family.id == id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        all_final_plans = []
        combined_meal_text = ""

        for target_date in req.dates:
            if req.overwrite:
                db.query(DailyPlan).filter(
                    DailyPlan.family_id == id,
                    DailyPlan.date == target_date,
                    DailyPlan.meal_type.in_(req.meals)
                ).delete(synchronize_session=False)
                db.commit()

            existing_plans = db.query(DailyPlan).filter(
                DailyPlan.family_id == id,
                DailyPlan.date == target_date,
                DailyPlan.meal_type.in_(req.meals)
            ).all()
            
            existing_meal_types = {ep.meal_type for ep in existing_plans}
            missing_meals = [m for m in req.meals if m not in existing_meal_types]

            if missing_meals:
                try:
                    daily_plan_text = generate_daily_meal_plan(family, target_date, missing_meals, req.budget)
                except Exception as e:
                    print("Error calling generate_daily_meal_plan:", e)
                    daily_plan_text = ""

                parsed_meals = parse_daily_plan_response(daily_plan_text, missing_meals)

                for meal in missing_meals:
                    plan_content = parsed_meals.get(meal, "Nutritious Indian Meal")
                    plan = DailyPlan(
                        family_id=family.id,
                        date=target_date,
                        meal_type=meal,
                        plan_text=plan_content
                    )
                    db.add(plan)
                
                db.commit()
            
            final_plans_for_date = db.query(DailyPlan).filter(
                DailyPlan.family_id == id,
                DailyPlan.date == target_date,
                DailyPlan.meal_type.in_(req.meals)
            ).all()

            all_final_plans.extend(final_plans_for_date)
            
            combined_meal_text += f"\n--- {target_date} ---\n"
            for p in final_plans_for_date:
                combined_meal_text += f"{p.meal_type}: {p.plan_text}\n"

        # Consolidate grocery generation to ONE active list for all upcoming plans!
        ist = timezone(timedelta(hours=5, minutes=30))
        today_str = datetime.now(ist).strftime("%Y-%m-%d")
        
        all_upcoming_for_grocery = db.query(DailyPlan).filter(
            DailyPlan.family_id == id,
            DailyPlan.date >= today_str
        ).order_by(DailyPlan.date.asc()).all()

        full_grocery_text = ""
        for p in all_upcoming_for_grocery:
            full_grocery_text += f"\n--- {p.date} ---\n{p.meal_type}: {p.plan_text}\n"

        db.query(CustomGroceryList).filter(CustomGroceryList.family_id == id).delete(synchronize_session=False)
        
        final_grocery_string = ""
        if full_grocery_text.strip():
            try:
                final_grocery_string = generate_weekly_grocery(family, full_grocery_text)
                if "GROQ ERROR" in final_grocery_string or "REQUEST ERROR" in final_grocery_string:
                    final_grocery_string = "Grocery list generated based on scheduled meals."
            except Exception as e:
                print("Error generating grocery list:", e)
                final_grocery_string = "Grocery list generated based on scheduled meals."

            new_list = CustomGroceryList(
                family_id=id,
                dates='["all_upcoming"]',
                meals='["all_upcoming"]',
                grocery_text=final_grocery_string
            )
            db.add(new_list)
            db.commit()

        serialized_plans = [
            {
                "id": p.id,
                "date": p.date,
                "meal_type": p.meal_type,
                "plan_text": p.plan_text
            }
            for p in all_final_plans
        ]

        return {
            "plans": serialized_plans,
            "grocery_list": final_grocery_string
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print("Error in create_multi_daily_plan:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")
    finally:
        db.close()

from datetime import datetime, timezone, timedelta

@router.get("/families/{id}/upcoming-plans")
def get_upcoming_plans(id: int):
    db = SessionLocal()

    try:
        ist = timezone(timedelta(hours=5, minutes=30))
        today_str = datetime.now(ist).strftime("%Y-%m-%d")

        old_plans = db.query(DailyPlan).filter(
            DailyPlan.family_id == id,
            DailyPlan.date < today_str
        ).delete(synchronize_session=False)
        db.commit()

        plans = db.query(DailyPlan).filter(
            DailyPlan.family_id == id,
            DailyPlan.date >= today_str
        ).order_by(DailyPlan.date.asc()).all()

        serialized_plans = [
            {
                "id": p.id,
                "date": p.date,
                "meal_type": p.meal_type,
                "plan_text": p.plan_text
            }
            for p in plans
        ]

        all_groceries = db.query(CustomGroceryList).filter(CustomGroceryList.family_id == id).all()
        upcoming_groceries = []
        
        for g in all_groceries:
            try:
                dates_arr = json.loads(g.dates)
                if g.grocery_text and g.grocery_text.strip():
                    upcoming_groceries.append({
                        "dates": dates_arr,
                        "grocery_list": g.grocery_text
                    })
            except:
                pass

        # If plans exist but no valid non-empty grocery list exists, generate one automatically!
        if plans and not upcoming_groceries:
            family = db.query(Family).filter(Family.id == id).first()
            if family:
                combined_meal_text = ""
                for p in plans:
                    combined_meal_text += f"\n--- {p.date} ---\n{p.meal_type}: {p.plan_text}\n"

                db.query(CustomGroceryList).filter(CustomGroceryList.family_id == id).delete(synchronize_session=False)

                try:
                    new_grocery_text = generate_weekly_grocery(family, combined_meal_text)
                    if "GROQ ERROR" in new_grocery_text or "REQUEST ERROR" in new_grocery_text or not new_grocery_text.strip():
                        new_grocery_text = "Grocery list generated based on scheduled meals."
                except Exception as e:
                    print("Error auto-generating grocery list:", e)
                    new_grocery_text = "Grocery list generated based on scheduled meals."

                new_list = CustomGroceryList(
                    family_id=id,
                    dates='["all_upcoming"]',
                    meals='["all_upcoming"]',
                    grocery_text=new_grocery_text
                )
                db.add(new_list)
                db.commit()

                upcoming_groceries = [{
                    "dates": ["all_upcoming"],
                    "grocery_list": new_grocery_text
                }]

        return {
            "plans": serialized_plans,
            "groceries": upcoming_groceries
        }
    finally:
        db.close()


@router.delete("/families/{family_id}/daily-plan/{plan_id}")
def delete_daily_plan(family_id: int, plan_id: int):
    db = SessionLocal()
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")
        
        plan = db.query(DailyPlan).filter(DailyPlan.id == plan_id, DailyPlan.family_id == family_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Delete the specific meal item
        db.delete(plan)
        db.commit()

        # Gather all upcoming plans to regenerate ONE unified grocery list
        ist = timezone(timedelta(hours=5, minutes=30))
        today_str = datetime.now(ist).strftime("%Y-%m-%d")
        
        upcoming_plans = db.query(DailyPlan).filter(
            DailyPlan.family_id == family_id,
            DailyPlan.date >= today_str
        ).order_by(DailyPlan.date.asc()).all()

        combined_meal_text = ""
        for p in upcoming_plans:
            combined_meal_text += f"\n--- {p.date} ---\n{p.meal_type}: {p.plan_text}\n"

        # Delete all old custom grocery lists to ensure only ONE stays active
        db.query(CustomGroceryList).filter(CustomGroceryList.family_id == family_id).delete(synchronize_session=False)
        
        # Generate new one if there are still plans
        if combined_meal_text.strip():
            new_grocery_text = generate_weekly_grocery(family, combined_meal_text)
            new_list = CustomGroceryList(
                family_id=family.id,
                dates='["all_upcoming"]',
                meals='["all_upcoming"]',
                grocery_text=new_grocery_text
            )
            db.add(new_list)
        
        db.commit()
        return {"status": "success", "message": "Meal deleted and grocery list regenerated"}
    finally:
        db.close()

@router.delete("/families/{family_id}/daily-plan/date/{date_str}")
def delete_daily_plan_by_date(family_id: int, date_str: str):
    db = SessionLocal()
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")
        
        # Delete all plans for that day
        db.query(DailyPlan).filter(
            DailyPlan.family_id == family_id,
            DailyPlan.date == date_str
        ).delete(synchronize_session=False)
        db.commit()

        # Gather all upcoming plans to regenerate ONE unified grocery list
        ist = timezone(timedelta(hours=5, minutes=30))
        today_str = datetime.now(ist).strftime("%Y-%m-%d")
        
        upcoming_plans = db.query(DailyPlan).filter(
            DailyPlan.family_id == family_id,
            DailyPlan.date >= today_str
        ).order_by(DailyPlan.date.asc()).all()

        combined_meal_text = ""
        for p in upcoming_plans:
            combined_meal_text += f"\n--- {p.date} ---\n{p.meal_type}: {p.plan_text}\n"

        # Delete old grocery list
        db.query(CustomGroceryList).filter(CustomGroceryList.family_id == family_id).delete(synchronize_session=False)
        
        # Generate new one if there are still plans
        if combined_meal_text.strip():
            new_grocery_text = generate_weekly_grocery(family, combined_meal_text)
            new_list = CustomGroceryList(
                family_id=family.id,
                dates='["all_upcoming"]',
                meals='["all_upcoming"]',
                grocery_text=new_grocery_text
            )
            db.add(new_list)
        
        db.commit()
        return {"status": "success", "message": f"All meals for {date_str} deleted and grocery list regenerated"}
    finally:
        db.close()