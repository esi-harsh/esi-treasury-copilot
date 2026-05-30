import uuid
from datetime import date
from sqlalchemy.orm import Session
from app.models import Deal, Cashflow, DealLeg, AuditLog


def generate_deal_number(deal_type: str) -> str:
    prefix = deal_type.split("_")[0].upper()[:2]
    return f"{prefix}-{date.today().year}-{uuid.uuid4().hex[:5].upper()}"


def create_deal_with_cashflows(db: Session, deal: Deal) -> Deal:
    deal.deal_number = generate_deal_number(deal.deal_type)
    deal.status = "pending"
    db.add(deal)
    db.flush()

    if deal.deal_type in ("fx_spot", "fx_forward"):
        # Receive buy currency
        db.add(Cashflow(
            deal_id=deal.id, cashflow_type="settlement", currency_id=deal.buy_currency_id,
            amount=deal.buy_amount, pay_receive="receive", value_date=deal.value_date, status="projected",
        ))
        # Pay sell currency
        db.add(Cashflow(
            deal_id=deal.id, cashflow_type="settlement", currency_id=deal.sell_currency_id,
            amount=deal.sell_amount, pay_receive="pay", value_date=deal.value_date, status="projected",
        ))
    elif deal.deal_type in ("deposit", "loan"):
        is_deposit = deal.deal_type == "deposit"
        # Principal at start
        db.add(Cashflow(
            deal_id=deal.id, cashflow_type="principal", currency_id=deal.principal_currency_id,
            amount=deal.principal_amount, pay_receive="pay" if is_deposit else "receive",
            value_date=deal.value_date, status="projected",
        ))
        # Calculate interest
        days = (deal.maturity_date - deal.value_date).days if deal.maturity_date else 0
        dcc = deal.day_count_convention or "ACT/365"
        divisor = 360 if "360" in dcc else 365
        interest = deal.principal_amount * (deal.interest_rate or 0) * days / divisor
        deal.interest_amount = round(interest, 2)
        # Principal + interest at maturity
        db.add(Cashflow(
            deal_id=deal.id, cashflow_type="principal", currency_id=deal.principal_currency_id,
            amount=deal.principal_amount, pay_receive="receive" if is_deposit else "pay",
            value_date=deal.maturity_date or deal.value_date, status="projected",
        ))
        if interest > 0:
            db.add(Cashflow(
                deal_id=deal.id, cashflow_type="interest", currency_id=deal.principal_currency_id,
                amount=round(interest, 2), pay_receive="receive" if is_deposit else "pay",
                value_date=deal.maturity_date or deal.value_date, status="projected",
            ))

    # Audit
    db.add(AuditLog(entity_type="deal", entity_id=deal.id, action="create", user=deal.trader, new_value=deal.deal_number))
    db.commit()
    db.refresh(deal)
    return deal


def create_fx_swap(db: Session, deal: Deal, near_data: dict, far_data: dict) -> Deal:
    """Book an FX swap with near and far legs."""
    deal.deal_number = generate_deal_number("fx_swap")
    deal.deal_type = "fx_swap"
    deal.status = "pending"
    db.add(deal)
    db.flush()

    for leg_num, data in [(1, near_data), (2, far_data)]:
        leg = DealLeg(deal_id=deal.id, leg_number=leg_num, **data)
        db.add(leg)
        db.add(Cashflow(
            deal_id=deal.id, cashflow_type="settlement", currency_id=data["buy_currency_id"],
            amount=data["buy_amount"], pay_receive="receive", value_date=data["value_date"], status="projected",
        ))
        db.add(Cashflow(
            deal_id=deal.id, cashflow_type="settlement", currency_id=data["sell_currency_id"],
            amount=data["sell_amount"], pay_receive="pay", value_date=data["value_date"], status="projected",
        ))

    db.add(AuditLog(entity_type="deal", entity_id=deal.id, action="create", user=deal.trader, new_value=deal.deal_number))
    db.commit()
    db.refresh(deal)
    return deal
