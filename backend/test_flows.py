import os
import sys
from app.database import SessionLocal, Base, engine
from app import models, schemas

# Initialize database tables
Base.metadata.create_all(bind=engine)

from app.routes.family import create_family, get_families
from app.routes.member import add_member
from app.routes.mealplan import create_multi_daily_plan
from app.routes.recipe import get_recipe

def test_full_pipeline():
    print("--- 1. Testing Family Creation ---")
    fam_in = schemas.FamilyCreate(name="Test Family AI")
    fam = create_family(fam_in)
    fam_id = fam.id
    print("Family created:", fam.id, fam.name)

    print("--- 2. Testing Member Creation ---")
    mem_in = schemas.MemberCreate(
        name="Adithya",
        age=25,
        goal="Muscle Gain",
        health_condition="None",
        diet="Vegetarian"
    )
    res_mem = add_member(fam_id, mem_in)
    print("Member added response:", res_mem)

    print("--- 3. Testing GET Families ---")
    fams = get_families()
    print(f"Retrieved {len(fams)} families. Latest family members count:", len(fams[-1].members))

    print("--- 4. Testing Multi-Daily Meal Plan Generation ---")
    req = schemas.MultiDailyPlanRequest(
        dates=["2026-09-22"],
        meals=["Breakfast", "Lunch"],
        budget="Medium",
        overwrite=True
    )
    plan_res = create_multi_daily_plan(fam_id, req)
    print("Multi-daily plan response plans count:", len(plan_res["plans"]))
    for p in plan_res["plans"]:
        print(f"  - [{p['meal_type']}] on {p['date']}: {p['plan_text']}")

    print("--- 5. Testing Recipe Generation ---")
    rec_res = get_recipe(fam_id, date="2026-09-22", meal_type="Breakfast", language="English")
    print("Recipe response received. Meal description:", rec_res["meal_description"])
    print("Recipe content snippet:", rec_res["recipe"][:150], "...")

    print("\nALL BACKEND FLOWS TESTED AND PASSED DIRECTLY!")

if __name__ == "__main__":
    test_full_pipeline()
