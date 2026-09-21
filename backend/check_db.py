from app.database import SessionLocal
from app.models import DailyPlan, CustomGroceryList, Family

db = SessionLocal()
try:
    print("FAMILIES:")
    for f in db.query(Family).all():
        print(f"ID: {f.id}, Name: {f.name}")
        for m in f.members:
            print(f"  Member: {m.name}, Diet: {m.diet}, Goal: {m.goal}, Health: {m.health_condition}")
    
    print("\nDAILY PLANS:")
    for p in db.query(DailyPlan).all():
        print(f"ID: {p.id}, FamilyID: {p.family_id}, Date: {p.date}, Meal: {p.meal_type}")
        print("Plan Text:")
        print(repr(p.plan_text))
        print("-" * 20)

    print("\nGROCERY LISTS:")
    for g in db.query(CustomGroceryList).all():
        print(f"ID: {g.id}, FamilyID: {g.family_id}, Dates: {g.dates}, Meals: {g.meals}")
        print("Grocery Text:")
        print(repr(g.grocery_text))
        print("-" * 20)
finally:
    db.close()
