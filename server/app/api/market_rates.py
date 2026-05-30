from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import MarketRate
from app.schemas import MarketRateCreate, MarketRateOut

router = APIRouter()


@router.post("/market-rates", response_model=MarketRateOut)
def upsert_rate(data: MarketRateCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(MarketRate)
        .filter(MarketRate.currency_pair_id == data.currency_pair_id, MarketRate.rate_date == data.rate_date, MarketRate.tenor == data.tenor)
        .first()
    )
    if existing:
        existing.mid_rate = data.mid_rate
        existing.bid_rate = data.bid_rate
        existing.ask_rate = data.ask_rate
        existing.source = data.source
        db.commit()
        db.refresh(existing)
        return existing
    mr = MarketRate(**data.model_dump())
    db.add(mr)
    db.commit()
    db.refresh(mr)
    return mr


@router.get("/market-rates", response_model=list[MarketRateOut])
def list_rates(currency_pair_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(MarketRate)
    if currency_pair_id:
        q = q.filter(MarketRate.currency_pair_id == currency_pair_id)
    return q.order_by(MarketRate.rate_date.desc()).limit(50).all()
