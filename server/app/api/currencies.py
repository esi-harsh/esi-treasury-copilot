from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Currency, CurrencyPair
from app.schemas import CurrencyCreate, CurrencyOut, CurrencyPairCreate, CurrencyPairOut

router = APIRouter()


@router.post("/currencies", response_model=CurrencyOut)
def create_currency(data: CurrencyCreate, db: Session = Depends(get_db)):
    ccy = Currency(**data.model_dump())
    db.add(ccy)
    db.commit()
    db.refresh(ccy)
    return ccy


@router.get("/currencies", response_model=list[CurrencyOut])
def list_currencies(db: Session = Depends(get_db)):
    return db.query(Currency).filter(Currency.is_active == True).all()


@router.post("/currency-pairs", response_model=CurrencyPairOut)
def create_currency_pair(data: CurrencyPairCreate, db: Session = Depends(get_db)):
    cp = CurrencyPair(**data.model_dump())
    db.add(cp)
    db.commit()
    db.refresh(cp)
    return cp


@router.get("/currency-pairs", response_model=list[CurrencyPairOut])
def list_currency_pairs(db: Session = Depends(get_db)):
    return db.query(CurrencyPair).all()
