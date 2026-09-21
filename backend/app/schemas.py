from pydantic import BaseModel
from typing import List, Optional

class MemberCreate(BaseModel):
    name: str
    age: int
    weight: Optional[str] = None
    height: Optional[str] = None
    goal: str
    health_condition: str
    diet: str
    meal_preferences: Optional[str] = None


class MemberOut(BaseModel):
    id: int
    name: str
    age: int
    weight: Optional[str] = None
    height: Optional[str] = None
    goal: str
    health_condition: str
    diet: str
    meal_preferences: Optional[str] = None

    class Config:
        from_attributes = True


class FamilyCreate(BaseModel):
    name: str


class FamilyOut(BaseModel):
    id: int
    name: str
    members: List[MemberOut] = []

    class Config:
        from_attributes = True


# --- CANONICAL DATA CONTRACT SCHEMAS ---

class MealSchema(BaseModel):
    meal_type: str # Breakfast | Lunch | Dinner | Snacks
    name: str
    description: str = ""
    ingredients: List[str] = []
    steps: List[str] = []
    prep_time: str = "10 mins"
    cook_time: str = "15 mins"
    servings: int = 4
    calories: int = 0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    estimated_price_inr: float = 0.0
    image_url: str = ""
    youtube_url: str = ""

class MealDaySchema(BaseModel):
    date: str
    day_name: str = "Monday"
    budget_level: str = "Medium"
    daily_budget: float = 250.0
    total_estimated_cost: float = 0.0
    meals: List[MealSchema] = []



class DailyPlanResponse(BaseModel):
    id: int
    date: str
    meal_type: str
    plan_text: str

    class Config:
        from_attributes = True

class MultiDailyPlanRequest(BaseModel):
    dates: List[str]
    meals: List[str]
    budget: Optional[str] = "Medium"
    overwrite: Optional[bool] = False

class MultiDailyPlanResponse(BaseModel):
    plans: List[DailyPlanResponse]
    grocery_list: str