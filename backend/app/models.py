from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Family(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    members = relationship(
        "Member",
        back_populates="family",
        cascade="all, delete"
    )

    weekly_plans = relationship(
        "WeeklyPlan",
        back_populates="family",
        cascade="all, delete"
    )


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"))

    name = Column(String)
    age = Column(Integer)
    goal = Column(String)
    health_condition = Column(String)
    diet = Column(String)

    family = relationship(
        "Family",
        back_populates="members"
    )

class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"))
    start_date = Column(String)
    end_date = Column(String)
    meal_plan_text = Column(String)
    grocery_list_text = Column(String)

    family = relationship("Family", back_populates="weekly_plans")


class DailyPlan(Base):
    __tablename__ = "daily_plans"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"))
    date = Column(String)
    meal_type = Column(String)  # Breakfast, Lunch, Dinner, etc.
    plan_text = Column(String)

    family = relationship("Family")

class CustomGroceryList(Base):
    __tablename__ = "custom_grocery_lists"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"))
    dates = Column(String)
    meals = Column(String)
    grocery_text = Column(String)
    budget = Column(String, default="Medium")