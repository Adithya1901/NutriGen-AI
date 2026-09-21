from fastapi import APIRouter
from app.database import SessionLocal
from app import models, schemas

router = APIRouter()

@router.post("/families/{family_id}/members")
def add_member(family_id: int, data: schemas.MemberCreate):
    db = SessionLocal()

    try:
        member = models.Member(
            name=data.name,
            age=data.age,
            weight=data.weight,
            height=data.height,
            goal=data.goal,
            health_condition=data.health_condition,
            diet=data.diet,
            meal_preferences=data.meal_preferences,
            family_id=family_id
        )

        db.add(member)
        db.commit()

        return {"msg": "Member Added"}
    finally:
        db.close()

@router.delete("/members/{member_id}")
def delete_member(member_id: int):
    db = SessionLocal()
    try:
        member = db.query(models.Member).filter(models.Member.id == member_id).first()
        if member:
            db.delete(member)
            db.commit()
        return {"msg": "Member Deleted"}
    finally:
        db.close()