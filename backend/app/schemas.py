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