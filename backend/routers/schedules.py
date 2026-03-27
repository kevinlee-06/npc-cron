from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api", tags=["Scheduling"])

@router.get("/schedules", response_model=list[schemas.ScheduleOut])
def list_schedules(db: Session = Depends(get_db)):
    return db.query(models.Schedule).all()

@router.post("/schedules", response_model=schemas.ScheduleOut)
def create_schedule(request: schemas.ScheduleIn, db: Session = Depends(get_db)):
    db_sched = models.Schedule(**request.model_dump())
    db.add(db_sched)
    db.commit()
    db.refresh(db_sched)
    return db_sched

@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    sched = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(sched)
    db.commit()
    return {"status": "success"}

@router.get("/exclusions", response_model=list[schemas.ExclusionOut])
def list_exclusions(db: Session = Depends(get_db)):
    return db.query(models.Exclusion).all()

@router.post("/exclusions", response_model=schemas.ExclusionOut)
def add_exclusion(request: schemas.ExclusionIn, db: Session = Depends(get_db)):
    db_ex = models.Exclusion(**request.model_dump())
    db.add(db_ex)
    db.commit()
    db.refresh(db_ex)
    return db_ex

@router.delete("/exclusions/{exclusion_id}")
def delete_exclusion(exclusion_id: int, db: Session = Depends(get_db)):
    ex = db.query(models.Exclusion).filter(models.Exclusion.id == exclusion_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(ex)
    db.commit()
    return {"status": "success"}
