from pydantic import BaseModel
from typing import List, Optional


class MemberCreate(BaseModel):
    name: str
    age: int
    goal: str
    health_condition: str
    diet: str


class MemberOut(MemberCreate):
    id: int

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
    date: str
    meal_type: str
    plan_text: str

    class Config:
        from_attributes = True

class MultiDailyPlanRequest(BaseModel):
    dates: List[str]
    meals: List[str]
    budget: Optional[str] = "Medium"

class MultiDailyPlanResponse(BaseModel):
    plans: List[DailyPlanResponse]
    grocery_list: str