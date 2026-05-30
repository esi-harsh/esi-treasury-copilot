from datetime import date
from sqlalchemy.orm import Session
from app.models import Deal, MarketRate, Valuation, CurrencyPair


def compute_mtm(db: Session) -> list[dict]:
    """Mark-to-market open FX deals and store results."""
    fx_deals = (
        db.query(Deal)
        .filter(Deal.deal_type.in_(("fx_spot", "fx_forward")), Deal.status.in_(("pending", "confirmed")))
        .all()
    )
    results = []
    today = date.today()
    for deal in fx_deals:
        # Find currency pair
        pair = (
            db.query(CurrencyPair)
            .filter(CurrencyPair.base_currency_id == deal.buy_currency_id, CurrencyPair.quote_currency_id == deal.sell_currency_id)
            .first()
        )
        if not pair:
            continue
        # Get latest market rate
        rate_row = (
            db.query(MarketRate)
            .filter(MarketRate.currency_pair_id == pair.id, MarketRate.rate_type == "fx_spot")
            .order_by(MarketRate.rate_date.desc())
            .first()
        )
        if not rate_row:
            continue

        current_rate = rate_row.mid_rate
        pnl = deal.buy_amount * (current_rate - deal.rate) if deal.direction == "buy" else deal.buy_amount * (deal.rate - current_rate)
        pnl = round(pnl, 2)

        # Store valuation
        val = Valuation(
            deal_id=deal.id, valuation_date=today, market_rate=current_rate,
            mtm_value=pnl, mtm_currency_id=deal.sell_currency_id, deal_rate=deal.rate,
        )
        db.add(val)

        results.append({
            "deal_id": deal.id, "deal_number": deal.deal_number, "deal_type": deal.deal_type,
            "currency_pair": pair.pair_code, "deal_rate": deal.rate, "market_rate": current_rate,
            "notional": deal.buy_amount, "unrealized_pnl": pnl,
        })
    db.commit()
    return results
