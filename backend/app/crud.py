from sqlalchemy.orm import Session
from . import models

def create_family(db: Session, name: str):
    family = models.Family(name=name)
    db.add(family)
    db.commit()
    db.refresh(family)
    return family

def get_families(db: Session):
    return db.query(models.Family).all()

def add_member(db: Session, family_id: int, data):
    member = models.Member(
        family_id=family_id,
        name=data.name,
        age=data.age,
        goal=data.goal,
        diet=data.diet,
        allergies=data.allergies,
        health_condition=data.health_condition
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
    
def update_member(db: Session, member_id: int, data):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()

    member.name = data.name
    member.age = data.age
    member.goal = data.goal
    member.diet = data.diet
    member.allergies = data.allergies
    member.health_condition = data.health_condition

    db.commit()
    db.refresh(member)
    return member

def delete_member(db: Session, member_id: int):
    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    db.delete(member)
    db.commit()