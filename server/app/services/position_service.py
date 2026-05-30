from datetime import date
from sqlalchemy.orm import Session
from app.models import Deal, Cashflow, Position, Currency


def recalculate_positions(db: Session) -> list[dict]:
    """Recalculate and store net positions per currency from open deals."""
    active_statuses = ("pending", "confirmed")
    cashflows = (
        db.query(Cashflow).join(Deal)
        .filter(Deal.status.in_(active_statuses), Cashflow.status == "projected")
        .all()
    )
    pos_map: dict[int, dict] = {}
    for cf in cashflows:
        if cf.currency_id not in pos_map:
            pos_map[cf.currency_id] = {"spot": 0.0, "forward": 0.0}
        # Determine if spot or forward based on deal type
        deal = cf.deal
        amount = cf.amount if cf.pay_receive == "receive" else -cf.amount
        if deal.deal_type in ("fx_spot", "deposit", "loan"):
            pos_map[cf.currency_id]["spot"] += amount
        else:
            pos_map[cf.currency_id]["forward"] += amount

    # Upsert positions
    today = date.today()
    results = []
    for ccy_id, amounts in pos_map.items():
        pos = db.query(Position).filter(Position.currency_id == ccy_id, Position.position_date == today).first()
        if not pos:
            pos = Position(currency_id=ccy_id, position_date=today)
            db.add(pos)
        pos.spot_position = amounts["spot"]
        pos.forward_position = amounts["forward"]
        pos.total_position = amounts["spot"] + amounts["forward"]
        ccy = db.query(Currency).get(ccy_id)
        results.append({
            "currency_id": ccy_id, "currency": ccy.iso_code if ccy else str(ccy_id),
            "position_date": str(today), "spot_position": pos.spot_position,
            "forward_position": pos.forward_position, "total_position": pos.total_position,
            "avg_rate": pos.avg_rate,
        })
    db.commit()
    return results
