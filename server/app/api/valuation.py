from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Valuation
from app.schemas import ValuationOut
from app.services.valuation_service import compute_mtm

router = APIRouter()


@router.get("/valuation/mtm")
def mtm_valuation(db: Session = Depends(get_db)):
    return compute_mtm(db)


@router.get("/valuation/history", response_model=list[ValuationOut])
def valuation_history(deal_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Valuation)
    if deal_id:
        q = q.filter(Valuation.deal_id == deal_id)
    return q.order_by(Valuation.valuation_date.desc()).limit(50).all()
