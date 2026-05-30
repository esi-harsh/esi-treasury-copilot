from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import BankAccount
from app.schemas import BankAccountCreate, BankAccountOut

router = APIRouter()


@router.post("/bank-accounts", response_model=BankAccountOut)
def create_bank_account(data: BankAccountCreate, db: Session = Depends(get_db)):
    ba = BankAccount(**data.model_dump())
    db.add(ba)
    db.commit()
    db.refresh(ba)
    return ba


@router.get("/bank-accounts", response_model=list[BankAccountOut])
def list_bank_accounts(db: Session = Depends(get_db)):
    return db.query(BankAccount).filter(BankAccount.is_active == True).all()
