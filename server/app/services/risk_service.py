from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import CreditLimit, Deal, Exposure


def get_counterparty_exposure(db: Session, counterparty_id: int) -> dict:
    """Calculate current exposure for a counterparty from open deals."""
    deals = (
        db.query(Deal)
        .filter(Deal.counterparty_id == counterparty_id, Deal.status.in_(("pending", "confirmed")))
        .all()
    )
    settlement_exp = 0.0
    pre_settlement_exp = 0.0
    for d in deals:
        notional = d.buy_amount or d.principal_amount or 0
        if d.status == "confirmed":
            settlement_exp += notional
        else:
            pre_settlement_exp += notional
    return {
        "counterparty_id": counterparty_id,
        "settlement_exposure": settlement_exp,
        "pre_settlement_exposure": pre_settlement_exp,
        "total_exposure": settlement_exp + pre_settlement_exp,
    }


def check_limit(db: Session, counterparty_id: int, currency_id: int, amount: float) -> dict:
    """Pre-deal limit check."""
    limit = (
        db.query(CreditLimit)
        .filter(CreditLimit.counterparty_id == counterparty_id, CreditLimit.limit_currency_id == currency_id, CreditLimit.is_active == True)
        .first()
    )
    if not limit:
        return {"allowed": True, "message": "No limit defined — deal allowed"}

    exposure = get_counterparty_exposure(db, counterparty_id)
    current = exposure["total_exposure"]
    new_total = current + amount

    if new_total > limit.limit_amount:
        return {
            "allowed": False,
            "message": f"LIMIT BREACH: exposure would be {new_total:,.0f} vs limit {limit.limit_amount:,.0f}",
            "current_exposure": current, "limit_amount": limit.limit_amount, "available": limit.limit_amount - current,
        }
    # Update utilized
    limit.utilized_amount = new_total
    limit.available_amount = limit.limit_amount - new_total
    db.commit()
    return {
        "allowed": True,
        "message": f"Within limit: {new_total:,.0f} / {limit.limit_amount:,.0f}",
        "current_exposure": current, "limit_amount": limit.limit_amount,
        "utilization_pct": round(new_total / limit.limit_amount * 100, 1),
    }


def snapshot_exposure(db: Session, counterparty_id: int, currency_id: int):
    """Store an exposure snapshot."""
    exp = get_counterparty_exposure(db, counterparty_id)
    record = Exposure(
        counterparty_id=counterparty_id, exposure_date=date.today(),
        settlement_exposure=exp["settlement_exposure"],
        pre_settlement_exposure=exp["pre_settlement_exposure"],
        total_exposure=exp["total_exposure"], currency_id=currency_id,
    )
    db.add(record)
    db.commit()
    return record
