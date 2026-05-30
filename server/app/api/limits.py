from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import CreditLimit, AuditLog
from app.schemas import CreditLimitCreate, CreditLimitOut, ExposureOut
from app.services.risk_service import get_counterparty_exposure, check_limit

router = APIRouter()


@router.post("/limits", response_model=CreditLimitOut)
def create_limit(data: CreditLimitCreate, db: Session = Depends(get_db)):
    lim = CreditLimit(**data.model_dump(), utilized_amount=0.0, available_amount=data.limit_amount)
    db.add(lim)
    db.add(AuditLog(entity_type="limit", entity_id=0, action="create", new_value=f"{data.limit_type} {data.limit_amount}"))
    db.commit()
    db.refresh(lim)
    return lim


@router.get("/limits", response_model=list[CreditLimitOut])
def list_limits(counterparty_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(CreditLimit).filter(CreditLimit.is_active == True)
    if counterparty_id:
        q = q.filter(CreditLimit.counterparty_id == counterparty_id)
    return q.all()


@router.get("/risk/exposure")
def exposure(counterparty_id: int, db: Session = Depends(get_db)):
    return get_counterparty_exposure(db, counterparty_id)


@router.get("/risk/check-limit")
def check_limit_endpoint(counterparty_id: int, currency_id: int, amount: float, db: Session = Depends(get_db)):
    return check_limit(db, counterparty_id, currency_id, amount)
