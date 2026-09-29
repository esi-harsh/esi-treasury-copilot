import json
import uuid
import httpx
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.config import OPENROUTER_API_KEY, LLM_MODEL, MAX_TOKENS
from app.models import Deal, Counterparty, Cashflow, CopilotConversation, Currency
from app.services.deal_service import create_deal_with_cashflows
from app.services.position_service import recalculate_positions
from app.services.risk_service import get_counterparty_exposure, check_limit
from app.services.valuation_service import compute_mtm

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are a Treasury AI Copilot for CIBC Finance. You help treasurers:
- Book FX and Money Market deals
- Monitor positions and cashflows
- Check credit limits and exposure
- Run mark-to-market valuations
- Generate reports
Always use the available tools to fetch real data. Be concise and professional."""

TOOLS = [
    {"type": "function", "function": {"name": "book_fx_deal", "description": "Book a new FX spot or forward deal", "parameters": {"type": "object", "properties": {
        "deal_type": {"type": "string", "description": "fx_spot or fx_forward"},
        "counterparty_name": {"type": "string"},
        "buy_currency": {"type": "string", "description": "ISO code e.g. USD"},
        "buy_amount": {"type": "number"},
        "sell_currency": {"type": "string"},
        "sell_amount": {"type": "number"},
        "rate": {"type": "number"},
        "direction": {"type": "string", "description": "buy or sell"},
    }, "required": ["deal_type", "counterparty_name", "buy_currency", "buy_amount", "sell_currency", "sell_amount", "rate", "direction"]}}},
    {"type": "function", "function": {"name": "get_positions", "description": "Get current net positions per currency", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_cashflow_forecast", "description": "Get projected cashflows for next N days", "parameters": {"type": "object", "properties": {"days": {"type": "integer", "default": 30}}}}},
    {"type": "function", "function": {"name": "check_counterparty_limit", "description": "Check credit limit utilization for a counterparty", "parameters": {"type": "object", "properties": {"counterparty_name": {"type": "string"}, "currency": {"type": "string"}, "amount": {"type": "number"}}, "required": ["counterparty_name"]}}},
    {"type": "function", "function": {"name": "get_exposure", "description": "Get total exposure for a counterparty", "parameters": {"type": "object", "properties": {"counterparty_name": {"type": "string"}}, "required": ["counterparty_name"]}}},
    {"type": "function", "function": {"name": "list_deals", "description": "List deals optionally filtered by type or status", "parameters": {"type": "object", "properties": {"deal_type": {"type": "string"}, "status": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "get_mtm_valuation", "description": "Run mark-to-market on open FX positions", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "get_market_rate", "description": "Get latest rate for a currency pair", "parameters": {"type": "object", "properties": {"pair_code": {"type": "string", "description": "e.g. USD/CAD"}}, "required": ["pair_code"]}}},
]

_sessions: dict[str, list] = {}


def _resolve_cp(db: Session, name: str):
    return db.query(Counterparty).filter(Counterparty.short_name.ilike(f"%{name}%")).first() or db.query(Counterparty).filter(Counterparty.legal_name.ilike(f"%{name}%")).first()


def _resolve_ccy(db: Session, code: str):
    return db.query(Currency).filter(Currency.iso_code == code.upper()).first()


def _execute_tool(db: Session, name: str, args: dict) -> str:
    if name == "book_fx_deal":
        cp = _resolve_cp(db, args["counterparty_name"])
        if not cp:
            return json.dumps({"error": f"Counterparty '{args['counterparty_name']}' not found"})
        buy_ccy = _resolve_ccy(db, args["buy_currency"])
        sell_ccy = _resolve_ccy(db, args["sell_currency"])
        if not buy_ccy or not sell_ccy:
            return json.dumps({"error": "Currency not found"})
        deal = Deal(
            deal_type=args["deal_type"], counterparty_id=cp.id, trade_date=date.today(),
            value_date=date.today() + timedelta(days=2), buy_currency_id=buy_ccy.id,
            buy_amount=args["buy_amount"], sell_currency_id=sell_ccy.id,
            sell_amount=args["sell_amount"], rate=args["rate"], direction=args["direction"],
        )
        deal = create_deal_with_cashflows(db, deal)
        return json.dumps({"success": True, "deal_number": deal.deal_number, "status": deal.status})
    elif name == "get_positions":
        return json.dumps(recalculate_positions(db))
    elif name == "get_cashflow_forecast":
        days = args.get("days", 30)
        end = date.today() + timedelta(days=days)
        cfs = db.query(Cashflow).join(Deal).filter(Deal.status.in_(("pending", "confirmed")), Cashflow.status == "projected", Cashflow.value_date <= end).all()
        return json.dumps([{"date": str(cf.value_date), "currency_id": cf.currency_id, "amount": cf.amount, "pay_receive": cf.pay_receive} for cf in cfs])
    elif name == "check_counterparty_limit":
        cp = _resolve_cp(db, args["counterparty_name"])
        if not cp:
            return json.dumps({"error": "Counterparty not found"})
        ccy = _resolve_ccy(db, args.get("currency", "USD"))
        return json.dumps(check_limit(db, cp.id, ccy.id if ccy else 1, args.get("amount", 0)))
    elif name == "get_exposure":
        cp = _resolve_cp(db, args["counterparty_name"])
        if not cp:
            return json.dumps({"error": "Counterparty not found"})
        return json.dumps(get_counterparty_exposure(db, cp.id))
    elif name == "list_deals":
        q = db.query(Deal)
        if args.get("deal_type"):
            q = q.filter(Deal.deal_type == args["deal_type"])
        if args.get("status"):
            q = q.filter(Deal.status == args["status"])
        deals = q.order_by(Deal.created_at.desc()).limit(10).all()
        return json.dumps([{"deal_number": d.deal_number, "type": d.deal_type, "status": d.status, "buy_amount": d.buy_amount, "sell_amount": d.sell_amount, "rate": d.rate} for d in deals])
    elif name == "get_mtm_valuation":
        return json.dumps(compute_mtm(db))
    elif name == "get_market_rate":
        from app.models import MarketRate, CurrencyPair
        pair = db.query(CurrencyPair).filter(CurrencyPair.pair_code == args["pair_code"].upper()).first()
        if not pair:
            return json.dumps({"error": f"Pair {args['pair_code']} not found"})
        rate = db.query(MarketRate).filter(MarketRate.currency_pair_id == pair.id).order_by(MarketRate.rate_date.desc()).first()
        if not rate:
            return json.dumps({"error": "No rate available"})
        return json.dumps({"pair": pair.pair_code, "mid": rate.mid_rate, "bid": rate.bid_rate, "ask": rate.ask_rate, "date": str(rate.rate_date)})
    return json.dumps({"error": "Unknown tool"})


def _call_llm(messages: list, tools=None) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "ESI Treasury Copilot",
    }
    body = {
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
    }
    if tools:
        body["tools"] = tools
    resp = httpx.post(OPENROUTER_URL, json=body, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]


def chat(db: Session, message: str, session_id: str | None = None) -> tuple[str, str]:
    if not session_id:
        session_id = uuid.uuid4().hex
    if session_id not in _sessions:
        _sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    _sessions[session_id].append({"role": "user", "content": message})
    db.add(CopilotConversation(session_id=session_id, role="user", content=message))

    # Call LLM with tools
    response_msg = _call_llm(_sessions[session_id], tools=TOOLS)
    _sessions[session_id].append(response_msg)

    # Handle tool calls (loop until no more tool calls)
    while response_msg.get("tool_calls"):
        for tc in response_msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            result = _execute_tool(db, fn_name, fn_args)
            _sessions[session_id].append({"role": "tool", "tool_call_id": tc["id"], "content": result})
        response_msg = _call_llm(_sessions[session_id], tools=TOOLS)
        _sessions[session_id].append(response_msg)

    reply = response_msg.get("content", "") or ""
    db.add(CopilotConversation(session_id=session_id, role="assistant", content=reply))
    db.commit()
    return reply, session_id

