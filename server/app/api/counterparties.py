from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Counterparty
from app.schemas import CounterpartyCreate, CounterpartyOut

router = APIRouter()


@router.post("/counterparties", response_model=CounterpartyOut)
def create_counterparty(data: CounterpartyCreate, db: Session = Depends(get_db)):
    cp = Counterparty(**data.model_dump())
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


@router.get("/counterparties", response_model=list[CounterpartyOut])
def list_counterparties(db: Session = Depends(get_db)):
    return db.query(Counterparty).filter(Counterparty.is_active == True).all()


@router.get("/counterparties/{cp_id}", response_model=CounterpartyOut)
def get_counterparty(cp_id: int, db: Session = Depends(get_db)):
    cp = db.get(Counterparty, cp_id)
    if not cp:
        raise HTTPException(404, "Counterparty not found")
    return cp


@router.put("/counterparties/{cp_id}", response_model=CounterpartyOut)
def update_counterparty(cp_id: int, data: CounterpartyCreate, db: Session = Depends(get_db)):
    cp = db.get(Counterparty, cp_id)
    if not cp:
        raise HTTPException(404, "Counterparty not found")
    for k, v in data.model_dump().items():
        setattr(cp, k, v)
    db.commit()
    db.refresh(cp)
    return cp
