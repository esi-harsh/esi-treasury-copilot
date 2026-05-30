from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models import Deal, Cashflow, AuditLog
from app.schemas import DealCreate, DealOut, CashflowOut
from app.services.deal_service import create_deal_with_cashflows

router = APIRouter()


@router.post("/deals", response_model=DealOut)
def book_deal(data: DealCreate, db: Session = Depends(get_db)):
    deal = Deal(**data.model_dump())
    deal = create_deal_with_cashflows(db, deal)
    return deal


@router.get("/deals", response_model=list[DealOut])
def list_deals(
    deal_type: Optional[str] = None,
    status: Optional[str] = None,
    counterparty_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Deal)
    if deal_type:
        q = q.filter(Deal.deal_type == deal_type)
    if status:
        q = q.filter(Deal.status == status)
    if counterparty_id:
        q = q.filter(Deal.counterparty_id == counterparty_id)
    return q.order_by(Deal.created_at.desc()).all()


@router.get("/deals/{deal_id}", response_model=DealOut)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


@router.put("/deals/{deal_id}/confirm", response_model=DealOut)
def confirm_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    if deal.status != "pending":
        raise HTTPException(400, f"Cannot confirm deal in status {deal.status}")
    db.add(AuditLog(entity_type="deal", entity_id=deal.id, action="status_change", field_changed="status", old_value="pending", new_value="confirmed"))
    deal.status = "confirmed"
    db.commit()
    db.refresh(deal)
    return deal


@router.put("/deals/{deal_id}/settle", response_model=DealOut)
def settle_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    if deal.status != "confirmed":
        raise HTTPException(400, f"Cannot settle deal in status {deal.status}")
    deal.status = "settled"
    for cf in deal.cashflows:
        cf.status = "settled"
    db.add(AuditLog(entity_type="deal", entity_id=deal.id, action="status_change", field_changed="status", old_value="confirmed", new_value="settled"))
    db.commit()
    db.refresh(deal)
    return deal


@router.put("/deals/{deal_id}/cancel", response_model=DealOut)
def cancel_deal(deal_id: int, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    if deal.status in ("settled", "cancelled"):
        raise HTTPException(400, f"Cannot cancel deal in status {deal.status}")
    db.add(AuditLog(entity_type="deal", entity_id=deal.id, action="status_change", field_changed="status", old_value=deal.status, new_value="cancelled"))
    deal.status = "cancelled"
    db.commit()
    db.refresh(deal)
    return deal


@router.get("/deals/{deal_id}/cashflows", response_model=list[CashflowOut])
def get_deal_cashflows(deal_id: int, db: Session = Depends(get_db)):
    return db.query(Cashflow).filter(Cashflow.deal_id == deal_id).all()
