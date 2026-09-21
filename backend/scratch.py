import traceback
from app.database import SessionLocal
from app.routes.mealplan import create_multi_daily_plan
from app.schemas import MultiDailyPlanRequest

try:
    req = MultiDailyPlanRequest(
        dates=["2026-08-04"],
        meals=["Breakfast"],
        budget="Medium"
    )
    result = create_multi_daily_plan(id=1, req=req)
    # Print as utf-8 encoded bytes to avoid Windows terminal character set issues
    print("SUCCESS RESULT:", str(result).encode('utf-8'))
except Exception as e:
    print("FAILED:")
    traceback.print_exc()
