from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.core.database import get_db
from app.models import Cashflow, Deal
from app.schemas import CashflowOut
from app.services.position_service import recalculate_positions

router = APIRouter()


@router.get("/positions")
def positions(db: Session = Depends(get_db)):
    return recalculate_positions(db)


@router.get("/cashflows/projected", response_model=list[CashflowOut])
def projected_cashflows(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    end = date.today() + timedelta(days=days)
    return (
        db.query(Cashflow).join(Deal)
        .filter(Deal.status.in_(("pending", "confirmed")), Cashflow.status == "projected", Cashflow.value_date <= end)
        .order_by(Cashflow.value_date)
        .all()
    )
