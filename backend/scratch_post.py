from app.database import SessionLocal
from app.models import CustomGroceryList, Family, DailyPlan
from app.ai import generate_weekly_grocery

db = SessionLocal()
try:
    groceries = db.query(CustomGroceryList).all()
    print("TOTAL GROCERY LISTS IN DB:", len(groceries))
    for g in groceries:
        print("--- GROCERY ITEM ---")
        print("ID:", g.id)
        print("FAMILY_ID:", g.family_id)
        print("DATES:", g.dates)
        print("TEXT LENGTH:", len(g.grocery_text))
        print("GROCERY TEXT CONTENT:")
        print(repr(g.grocery_text))
finally:
    db.close()
