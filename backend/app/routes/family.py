from fastapi import APIRouter
from app.database import SessionLocal
from app import models, schemas

router = APIRouter()


from typing import List
from sqlalchemy.orm import joinedload

@router.get("/families/", response_model=List[schemas.FamilyOut])
def get_families():
    db = SessionLocal()
    try:
        families = db.query(models.Family).options(joinedload(models.Family.members)).all()
        return families
    finally:
        db.close()


@router.post("/families/")
def create_family(data: schemas.FamilyCreate):
    db = SessionLocal()

    try:
        family = models.Family(name=data.name)

        db.add(family)
        db.commit()
        db.refresh(family)

        return family
    finally:
        db.close()

@router.delete("/families/{family_id}")
def delete_family(family_id: int):
    db = SessionLocal()
    try:
        family = db.query(models.Family).filter(models.Family.id == family_id).first()
        if family:
            db.delete(family)
            db.commit()
        return {"msg": "Family Deleted"}
    finally:
        db.close()