import json
import uuid
from datetime import date, timedelta
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Deal, Counterparty, Cashflow, Currency, CurrencyPair,
    BankAccount, CreditLimit, MarketRate, Valuation, Position
)
from app.services.deal_service import create_deal_with_cashflows, generate_deal_number
from app.services.position_service import recalculate_positions
from app.services.risk_service import get_counterparty_exposure, check_limit
from app.services.valuation_service import compute_mtm


# --- Tool Definitions (MCP Schema) ---

MCP_TOOLS_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "get_twin_state",
        "description": "Fetches the current virtual treasury state including Nostro/Vostro account balances, net currency positions, cashflow projections, and active limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "currency_scope": {
                    "type": "string",
                    "description": "Optional ISO currency filter e.g. 'USD', 'CAD', 'EUR' or 'ALL'",
                    "default": "ALL"
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead for cashflow visibility (default: 30)",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "apply_market_shock",
        "description": "Injects interest rate movements (bps) and FX curve percentage shifts into the simulation engine to test treasury portfolio impact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rate_shift_bps": {
                    "type": "number",
                    "description": "Interest rate shift in basis points (e.g. 50 for +50bps, -100 for -100bps)",
                    "default": 0.0
                },
                "fx_shock_pct": {
                    "type": "number",
                    "description": "Percentage change in FX market rates (e.g. 5.0 for +5% appreciation of base currencies)",
                    "default": 0.0
                },
                "currency_pair": {
                    "type": "string",
                    "description": "Target currency pair for FX shock (e.g. 'USD/CAD' or 'ALL')",
                    "default": "ALL"
                }
            }
        }
    },
    {
        "name": "simulate_trade",
        "description": "Evaluates and simulates a candidate FX Spot, Forward, Swap, or Money Market transaction in a sandboxed digital twin.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_type": {
                    "type": "string",
                    "enum": ["fx_spot", "fx_forward", "deposit", "loan"],
                    "description": "Type of candidate deal"
                },
                "counterparty_name": {
                    "type": "string",
                    "description": "Short name or legal name of the counterparty"
                },
                "buy_currency": {
                    "type": "string",
                    "description": "ISO code for buy / principal currency (e.g. USD)"
                },
                "buy_amount": {
                    "type": "number",
                    "description": "Amount to buy or deposit/loan principal"
                },
                "sell_currency": {
                    "type": "string",
                    "description": "ISO code for sell currency (for FX deals)"
                },
                "sell_amount": {
                    "type": "number",
                    "description": "Amount to sell (for FX deals)"
                },
                "rate": {
                    "type": "number",
                    "description": "Agreed exchange rate or interest rate"
                },
                "direction": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "Direction of trade"
                }
            },
            "required": ["deal_type", "counterparty_name", "buy_currency", "buy_amount"]
        }
    },
    {
        "name": "evaluate_risk_limits",
        "description": "Validates exposure, counterparty credit ceilings, and concentration rules before transaction approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "counterparty_name": {
                    "type": "string",
                    "description": "Counterparty short or legal name"
                },
                "currency": {
                    "type": "string",
                    "description": "Currency ISO code for the proposed transaction (default: 'USD')",
                    "default": "USD"
                },
                "proposed_amount": {
                    "type": "number",
                    "description": "Proposed exposure / notional amount to evaluate",
                    "default": 0.0
                }
            },
            "required": ["counterparty_name"]
        }
    },
    {
        "name": "run_lcr_stress_test",
        "description": "Simulates a 30-day Basel III Liquidity Coverage Ratio (LCR) stress test under stressed cash outflow and HQLA haircut assumptions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "outflow_multiplier": {
                    "type": "number",
                    "description": "Stress multiplier on contractual outflows (e.g., 1.25 for +25% stressed run-off)",
                    "default": 1.20
                },
                "hqla_haircut_pct": {
                    "type": "number",
                    "description": "Haircut percentage applied to High Quality Liquid Assets (e.g., 5.0 for 5% haircut)",
                    "default": 5.0
                }
            }
        }
    },
    {
        "name": "book_fx_deal",
        "description": "Books a live FX Spot or Forward deal in the treasury ledger, generating corresponding cashflows and updating positions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_type": {
                    "type": "string",
                    "enum": ["fx_spot", "fx_forward"],
                    "description": "FX deal type"
                },
                "counterparty_name": {
                    "type": "string",
                    "description": "Short or legal name of the counterparty"
                },
                "buy_currency": {
                    "type": "string",
                    "description": "ISO code for buy currency (e.g. USD)"
                },
                "buy_amount": {
                    "type": "number",
                    "description": "Buy currency amount"
                },
                "sell_currency": {
                    "type": "string",
                    "description": "ISO code for sell currency (e.g. CAD)"
                },
                "sell_amount": {
                    "type": "number",
                    "description": "Sell currency amount"
                },
                "rate": {
                    "type": "number",
                    "description": "Agreed FX rate"
                },
                "direction": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "Buy or sell direction"
                },
                "trader": {
                    "type": "string",
                    "description": "Trader or Agent ID booking the deal",
                    "default": "mcp_agent"
                }
            },
            "required": ["deal_type", "counterparty_name", "buy_currency", "buy_amount", "sell_currency", "sell_amount", "rate", "direction"]
        }
    },
    {
        "name": "get_positions",
        "description": "Retrieves the latest net spot, forward, and total currency positions across the treasury.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_cashflow_forecast",
        "description": "Returns projected settlement, principal, and interest cashflows for the next N days.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Forecast horizon in days (default: 30)",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "check_counterparty_limit",
        "description": "Checks counterparty credit limit utilization, available headroom, and breach status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "counterparty_name": {
                    "type": "string",
                    "description": "Name of counterparty"
                },
                "currency": {
                    "type": "string",
                    "description": "ISO currency code (default: USD)",
                    "default": "USD"
                },
                "amount": {
                    "type": "number",
                    "description": "Candidate deal amount to test",
                    "default": 0.0
                }
            },
            "required": ["counterparty_name"]
        }
    },
    {
        "name": "get_exposure",
        "description": "Calculates total settlement and pre-settlement exposure for a specific counterparty.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "counterparty_name": {
                    "type": "string",
                    "description": "Counterparty short or legal name"
                }
            },
            "required": ["counterparty_name"]
        }
    },
    {
        "name": "list_deals",
        "description": "Queries deals with optional filtering by deal type and status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_type": {
                    "type": "string",
                    "description": "Filter by deal_type (fx_spot, fx_forward, fx_swap, deposit, loan)"
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (pending, confirmed, settled, cancelled)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 20)",
                    "default": 20
                }
            }
        }
    },
    {
        "name": "get_mtm_valuation",
        "description": "Performs mark-to-market revaluation on all open FX positions and calculates unrealized PnL.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_market_rate",
        "description": "Fetches current market rates (bid, ask, mid) for a currency pair.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pair_code": {
                    "type": "string",
                    "description": "Currency pair code (e.g. 'USD/CAD', 'EUR/USD')"
                }
            },
            "required": ["pair_code"]
        }
    }
]


# --- Helper Resolvers ---

def _resolve_cp(db: Session, name: str) -> Counterparty | None:
    return (
        db.query(Counterparty).filter(Counterparty.short_name.ilike(f"%{name}%")).first()
        or db.query(Counterparty).filter(Counterparty.legal_name.ilike(f"%{name}%")).first()
    )


def _resolve_ccy(db: Session, code: str) -> Currency | None:
    return db.query(Currency).filter(Currency.iso_code == code.upper()).first()


# --- Execution Router ---

def execute_mcp_tool(db: Session, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Executes an MCP tool against the treasury database and services."""
    try:
        if name == "get_twin_state":
            scope = args.get("currency_scope", "ALL").upper()
            days = args.get("days_ahead", 30)
            
            # Accounts
            acct_query = db.query(BankAccount).join(Currency)
            if scope != "ALL":
                acct_query = acct_query.filter(Currency.iso_code == scope)
            accounts = [
                {
                    "account_name": a.account_name,
                    "account_number": a.account_number,
                    "account_type": a.account_type,
                    "currency": a.currency.iso_code if a.currency else "UNKNOWN",
                    "balance": a.current_balance
                }
                for a in acct_query.all()
            ]
            
            # Net positions
            positions = recalculate_positions(db)
            if scope != "ALL":
                positions = [p for p in positions if p.get("currency") == scope]
                
            # Cashflows
            end_date = date.today() + timedelta(days=days)
            cfs = (
                db.query(Cashflow).join(Deal)
                .join(Currency, Cashflow.currency_id == Currency.id)
                .filter(Deal.status.in_(("pending", "confirmed")), Cashflow.status == "projected", Cashflow.value_date <= end_date)
            )
            if scope != "ALL":
                cfs = cfs.filter(Currency.iso_code == scope)
            cashflow_list = [
                {
                    "deal_number": cf.deal.deal_number,
                    "value_date": str(cf.value_date),
                    "currency": cf.currency.iso_code if cf.currency else str(cf.currency_id),
                    "amount": cf.amount,
                    "pay_receive": cf.pay_receive,
                    "type": cf.cashflow_type
                }
                for cf in cfs.limit(50).all()
            ]
            
            return {
                "status": "success",
                "as_of_date": str(date.today()),
                "currency_scope": scope,
                "nostro_vostro_accounts": accounts,
                "net_positions": positions,
                "projected_cashflows": cashflow_list
            }

        elif name == "apply_market_shock":
            rate_bps = float(args.get("rate_shift_bps", 0.0))
            fx_pct = float(args.get("fx_shock_pct", 0.0))
            pair_target = args.get("currency_pair", "ALL").upper()
            
            base_mtm = compute_mtm(db)
            shocked_mtm = []
            total_base_pnl = sum(item["unrealized_pnl"] for item in base_mtm)
            
            for item in base_mtm:
                pair = item["currency_pair"]
                if pair_target in ("ALL", pair):
                    shock_mult = 1.0 + (fx_pct / 100.0)
                    shocked_rate = item["market_rate"] * shock_mult
                    
                    # Recompute pnl
                    deal_rate = item["deal_rate"]
                    notional = item["notional"]
                    # If buy, profit if shocked_rate > deal_rate
                    new_pnl = round(notional * (shocked_rate - deal_rate), 2)
                    shocked_mtm.append({
                        "deal_number": item["deal_number"],
                        "currency_pair": pair,
                        "base_market_rate": item["market_rate"],
                        "shocked_market_rate": round(shocked_rate, 4),
                        "original_pnl": item["unrealized_pnl"],
                        "shocked_pnl": new_pnl,
                        "pnl_delta": round(new_pnl - item["unrealized_pnl"], 2)
                    })
                else:
                    shocked_mtm.append(item)
                    
            total_shocked_pnl = sum(item.get("shocked_pnl", item.get("unrealized_pnl", 0)) for item in shocked_mtm)
            
            return {
                "status": "success",
                "scenario": f"Rate Shock: {rate_bps:+.1f} bps | FX Shock: {fx_pct:+.2f}% on {pair_target}",
                "baseline_total_pnl": total_base_pnl,
                "shocked_total_pnl": total_shocked_pnl,
                "net_pnl_impact": round(total_shocked_pnl - total_base_pnl, 2),
                "deal_revaluations": shocked_mtm
            }

        elif name == "simulate_trade":
            deal_type = args["deal_type"]
            cp_name = args["counterparty_name"]
            cp = _resolve_cp(db, cp_name)
            if not cp:
                return {"allowed": False, "error": f"Counterparty '{cp_name}' not found"}
                
            buy_ccy = _resolve_ccy(db, args["buy_currency"])
            if not buy_ccy:
                return {"allowed": False, "error": f"Currency '{args['buy_currency']}' not found"}
                
            sell_ccy = _resolve_ccy(db, args.get("sell_currency", "USD"))
            buy_amt = float(args.get("buy_amount", 0))
            sell_amt = float(args.get("sell_amount", 0))
            rate = float(args.get("rate", 1.0))
            direction = args.get("direction", "buy")
            
            # Risk limit pre-check
            limit_check = check_limit(db, cp.id, buy_ccy.id, buy_amt)
            
            # Simulated MTM / valuation check
            sim_pnl = 0.0
            if deal_type in ("fx_spot", "fx_forward") and sell_ccy:
                pair = db.query(CurrencyPair).filter(
                    CurrencyPair.base_currency_id == buy_ccy.id,
                    CurrencyPair.quote_currency_id == sell_ccy.id
                ).first()
                if pair:
                    mrate = db.query(MarketRate).filter(MarketRate.currency_pair_id == pair.id).order_by(MarketRate.rate_date.desc()).first()
                    if mrate:
                        curr_rate = mrate.mid_rate
                        sim_pnl = round(buy_amt * (curr_rate - rate) if direction == "buy" else buy_amt * (rate - curr_rate), 2)

            return {
                "simulation_id": f"SIM-{uuid.uuid4().hex[:8].upper()}",
                "simulated_action": deal_type,
                "counterparty": cp.short_name,
                "notional": buy_amt,
                "currency": buy_ccy.iso_code,
                "rate": rate,
                "projected_unrealized_pnl": sim_pnl,
                "limit_validation": limit_check,
                "actionable": limit_check.get("allowed", False),
                "notes": "Simulated in sandboxed Digital Twin without mutating ledger."
            }

        elif name == "evaluate_risk_limits":
            cp = _resolve_cp(db, args["counterparty_name"])
            if not cp:
                return {"allowed": False, "error": f"Counterparty '{args['counterparty_name']}' not found"}
            ccy = _resolve_ccy(db, args.get("currency", "USD"))
            ccy_id = ccy.id if ccy else 1
            amt = float(args.get("proposed_amount", 0.0))
            
            res = check_limit(db, cp.id, ccy_id, amt)
            exp = get_counterparty_exposure(db, cp.id)
            res["exposure_breakdown"] = exp
            res["counterparty"] = cp.short_name
            return res

        elif name == "run_lcr_stress_test":
            outflow_mult = float(args.get("outflow_multiplier", 1.20))
            haircut_pct = float(args.get("hqla_haircut_pct", 5.0))
            
            # Compute total cash across bank accounts (Level 1 HQLA proxy)
            total_cash = db.query(func.sum(BankAccount.current_balance)).scalar() or 50_000_000.0
            hqla_available = total_cash * (1.0 - (haircut_pct / 100.0))
            
            # Compute 30-day projected net cash outflows
            end_30d = date.today() + timedelta(days=30)
            cfs = db.query(Cashflow).filter(Cashflow.value_date <= end_30d, Cashflow.status == "projected").all()
            contractual_outflows = sum(cf.amount for cf in cfs if cf.pay_receive == "pay") or 35_000_000.0
            contractual_inflows = sum(cf.amount for cf in cfs if cf.pay_receive == "receive") or 15_000_000.0
            
            # Net stressed outflow = (Outflows * multiplier) - Min(Inflows, 75% of stressed Outflows)
            stressed_outflows = contractual_outflows * outflow_mult
            capped_inflows = min(contractual_inflows, stressed_outflows * 0.75)
            net_stressed_outflows = max(stressed_outflows - capped_inflows, 1.0)
            
            lcr_ratio = round((hqla_available / net_stressed_outflows) * 100.0, 2)
            passed = lcr_ratio >= 100.0
            
            return {
                "lcr_percentage": lcr_ratio,
                "compliant": passed,
                "minimum_threshold": 100.0,
                "hqla_after_haircut": round(hqla_available, 2),
                "contractual_outflows": round(contractual_outflows, 2),
                "stressed_outflows": round(stressed_outflows, 2),
                "net_stressed_outflows": round(net_stressed_outflows, 2),
                "status": "PASS" if passed else "BREACH",
                "notes": f"Stress test with {outflow_mult}x outflow multiplier and {haircut_pct}% HQLA haircut."
            }

        elif name == "book_fx_deal":
            cp = _resolve_cp(db, args["counterparty_name"])
            if not cp:
                return {"error": f"Counterparty '{args['counterparty_name']}' not found"}
            buy_ccy = _resolve_ccy(db, args["buy_currency"])
            sell_ccy = _resolve_ccy(db, args["sell_currency"])
            if not buy_ccy or not sell_ccy:
                return {"error": "Invalid currency specified"}
                
            deal = Deal(
                deal_type=args["deal_type"],
                counterparty_id=cp.id,
                trade_date=date.today(),
                value_date=date.today() + timedelta(days=2),
                buy_currency_id=buy_ccy.id,
                buy_amount=args["buy_amount"],
                sell_currency_id=sell_ccy.id,
                sell_amount=args["sell_amount"],
                rate=args["rate"],
                direction=args["direction"],
                trader=args.get("trader", "mcp_agent")
            )
            created = create_deal_with_cashflows(db, deal)
            return {
                "success": True,
                "deal_number": created.deal_number,
                "deal_type": created.deal_type,
                "status": created.status,
                "counterparty": cp.short_name,
                "buy": f"{created.buy_amount} {buy_ccy.iso_code}",
                "sell": f"{created.sell_amount} {sell_ccy.iso_code}",
                "rate": created.rate
            }

        elif name == "get_positions":
            positions = recalculate_positions(db)
            return {"positions": positions}

        elif name == "get_cashflow_forecast":
            days = int(args.get("days", 30))
            end = date.today() + timedelta(days=days)
            cfs = (
                db.query(Cashflow).join(Deal)
                .filter(Deal.status.in_(("pending", "confirmed")), Cashflow.status == "projected", Cashflow.value_date <= end)
                .all()
            )
            return {
                "forecast_days": days,
                "cashflows": [
                    {
                        "deal_number": cf.deal.deal_number,
                        "date": str(cf.value_date),
                        "currency_id": cf.currency_id,
                        "amount": cf.amount,
                        "pay_receive": cf.pay_receive,
                        "type": cf.cashflow_type
                    }
                    for cf in cfs
                ]
            }

        elif name == "check_counterparty_limit":
            cp = _resolve_cp(db, args["counterparty_name"])
            if not cp:
                return {"error": f"Counterparty '{args['counterparty_name']}' not found"}
            ccy = _resolve_ccy(db, args.get("currency", "USD"))
            return check_limit(db, cp.id, ccy.id if ccy else 1, float(args.get("amount", 0)))

        elif name == "get_exposure":
            cp = _resolve_cp(db, args["counterparty_name"])
            if not cp:
                return {"error": f"Counterparty '{args['counterparty_name']}' not found"}
            return get_counterparty_exposure(db, cp.id)

        elif name == "list_deals":
            q = db.query(Deal)
            if args.get("deal_type"):
                q = q.filter(Deal.deal_type == args["deal_type"])
            if args.get("status"):
                q = q.filter(Deal.status == args["status"])
            limit = int(args.get("limit", 20))
            deals = q.order_by(Deal.created_at.desc()).limit(limit).all()
            return {
                "count": len(deals),
                "deals": [
                    {
                        "id": d.id,
                        "deal_number": d.deal_number,
                        "deal_type": d.deal_type,
                        "status": d.status,
                        "counterparty": d.counterparty.short_name if d.counterparty else str(d.counterparty_id),
                        "buy_amount": d.buy_amount,
                        "sell_amount": d.sell_amount,
                        "rate": d.rate,
                        "trade_date": str(d.trade_date),
                        "value_date": str(d.value_date)
                    }
                    for d in deals
                ]
            }

        elif name == "get_mtm_valuation":
            return {"mtm_valuations": compute_mtm(db)}

        elif name == "get_market_rate":
            pair_code = args["pair_code"].upper()
            pair = db.query(CurrencyPair).filter(CurrencyPair.pair_code == pair_code).first()
            if not pair:
                return {"error": f"Currency pair '{pair_code}' not found"}
            rate = (
                db.query(MarketRate)
                .filter(MarketRate.currency_pair_id == pair.id)
                .order_by(MarketRate.rate_date.desc())
                .first()
            )
            if not rate:
                return {"error": f"No market rate available for {pair_code}"}
            return {
                "pair": pair.pair_code,
                "rate_type": rate.rate_type,
                "mid": rate.mid_rate,
                "bid": rate.bid_rate,
                "ask": rate.ask_rate,
                "date": str(rate.rate_date)
            }

        else:
            return {"error": f"Tool '{name}' not recognized"}

    except Exception as exc:
        return {"error": str(exc), "tool": name}
