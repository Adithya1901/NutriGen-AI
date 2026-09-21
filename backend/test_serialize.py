import traceback
from app.database import SessionLocal
from app.routes.mealplan import create_multi_daily_plan
from app.schemas import MultiDailyPlanRequest, MultiDailyPlanResponse

try:
    req = MultiDailyPlanRequest(
        dates=["2026-08-04"],
        meals=["Breakfast"],
        budget="Medium"
    )
    result = create_multi_daily_plan(id=1, req=req)
    print("Function called successfully.")
    
    # Try parsing / serializing using the response model
    serialized = MultiDailyPlanResponse.model_validate(result)
    print("Serialized successfully:")
    print(serialized.model_dump_json(indent=2).encode('utf-8'))
except Exception as e:
    print("SERIALIZATION/EXECUTION FAILED:")
    traceback.print_exc()
