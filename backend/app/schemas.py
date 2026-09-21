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

class IngredientSchema(BaseModel):
    name: str
    quantity: float = 1.0
    unit: str = "pieces"
    estimated_cost: float = 0.0

class MealComponentSchema(BaseModel):
    component_name: str
    component_type: str = "main" # main, side, beverage, dessert
    ingredients: List[IngredientSchema] = []
    preparation_steps: List[str] = []
    cooking_steps: List[str] = []
    cooking_time_minutes: int = 10

class MealSchema(BaseModel):
    meal_type: str # breakfast, lunch, dinner, snacks
    meal_name: str
    description: str = ""
    estimated_cost: float = 0.0
    calories: int = 0
    protein_g: float = 0.0
    carbohydrates_g: float = 0.0
    fat_g: float = 0.0
    components: List[MealComponentSchema] = []

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