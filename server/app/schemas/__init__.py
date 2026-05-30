from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


# --- Currency ---
class CurrencyCreate(BaseModel):
    iso_code: str
    name: str
    decimal_places: int = 2
    settlement_days: int = 2

class CurrencyOut(CurrencyCreate):
    id: int
    is_active: bool
    class Config:
        from_attributes = True


# --- Currency Pair ---
class CurrencyPairCreate(BaseModel):
    base_currency_id: int
    quote_currency_id: int
    pair_code: str
    spot_days: int = 2
    pip_size: float = 0.0001

class CurrencyPairOut(CurrencyPairCreate):
    id: int
    class Config:
        from_attributes = True


# --- Counterparty ---
class CounterpartyCreate(BaseModel):
    short_name: str
    legal_name: str
    counterparty_type: str
    lei_code: Optional[str] = None
    swift_code: Optional[str] = None
    country: Optional[str] = None
    credit_rating: Optional[str] = None
    rating_agency: Optional[str] = None
    settlement_netting: bool = False

class CounterpartyOut(CounterpartyCreate):
    id: int
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# --- Bank Account ---
class BankAccountCreate(BaseModel):
    account_number: str
    account_name: str
    account_type: str  # nostro, vostro, internal
    currency_id: int
    counterparty_id: Optional[int] = None
    swift_code: Optional[str] = None
    current_balance: float = 0.0

class BankAccountOut(BankAccountCreate):
    id: int
    is_active: bool
    class Config:
        from_attributes = True


# --- Deal ---
class DealCreate(BaseModel):
    deal_type: str
    deal_subtype: Optional[str] = None
    trade_date: date
    value_date: date
    maturity_date: Optional[date] = None
    counterparty_id: int
    direction: str
    # FX
    buy_currency_id: Optional[int] = None
    buy_amount: Optional[float] = None
    sell_currency_id: Optional[int] = None
    sell_amount: Optional[float] = None
    rate: Optional[float] = None
    forward_points: Optional[float] = None
    # MM
    principal_currency_id: Optional[int] = None
    principal_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    day_count_convention: Optional[str] = None
    # Settlement
    buy_account_id: Optional[int] = None
    sell_account_id: Optional[int] = None
    trader: Optional[str] = None
    notes: Optional[str] = None

class DealOut(BaseModel):
    id: int
    deal_number: str
    deal_type: str
    deal_subtype: Optional[str]
    trade_date: date
    value_date: date
    maturity_date: Optional[date]
    counterparty_id: int
    status: str
    direction: str
    buy_currency_id: Optional[int]
    buy_amount: Optional[float]
    sell_currency_id: Optional[int]
    sell_amount: Optional[float]
    rate: Optional[float]
    forward_points: Optional[float]
    principal_currency_id: Optional[int]
    principal_amount: Optional[float]
    interest_rate: Optional[float]
    day_count_convention: Optional[str]
    interest_amount: Optional[float]
    trader: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# --- Deal Leg ---
class DealLegCreate(BaseModel):
    deal_id: int
    leg_number: int
    value_date: date
    buy_currency_id: int
    buy_amount: float
    sell_currency_id: int
    sell_amount: float
    rate: float

class DealLegOut(DealLegCreate):
    id: int
    class Config:
        from_attributes = True


# --- Cashflow ---
class CashflowOut(BaseModel):
    id: int
    deal_id: int
    cashflow_type: str
    currency_id: int
    amount: float
    pay_receive: str
    value_date: date
    status: str
    settled_date: Optional[date]
    class Config:
        from_attributes = True


# --- Position ---
class PositionOut(BaseModel):
    currency_id: int
    position_date: date
    spot_position: float
    forward_position: float
    total_position: float
    avg_rate: Optional[float]
    class Config:
        from_attributes = True


# --- Credit Limit ---
class CreditLimitCreate(BaseModel):
    counterparty_id: int
    limit_type: str
    limit_currency_id: int
    limit_amount: float
    tenor_months: Optional[int] = None
    approved_by: Optional[str] = None
    expiry_date: Optional[date] = None

class CreditLimitOut(BaseModel):
    id: int
    counterparty_id: int
    limit_type: str
    limit_currency_id: int
    limit_amount: float
    utilized_amount: float
    available_amount: float
    tenor_months: Optional[int]
    approved_by: Optional[str]
    expiry_date: Optional[date]
    is_active: bool
    class Config:
        from_attributes = True


# --- Exposure ---
class ExposureOut(BaseModel):
    id: int
    counterparty_id: int
    exposure_date: date
    settlement_exposure: float
    pre_settlement_exposure: float
    total_exposure: float
    currency_id: int
    class Config:
        from_attributes = True


# --- Market Rate ---
class MarketRateCreate(BaseModel):
    rate_type: str
    currency_pair_id: Optional[int] = None
    currency_id: Optional[int] = None
    tenor: Optional[str] = None
    bid_rate: Optional[float] = None
    ask_rate: Optional[float] = None
    mid_rate: float
    rate_date: date
    source: Optional[str] = None

class MarketRateOut(MarketRateCreate):
    id: int
    class Config:
        from_attributes = True


# --- Valuation ---
class ValuationOut(BaseModel):
    id: int
    deal_id: int
    valuation_date: date
    market_rate: float
    mtm_value: float
    mtm_currency_id: int
    deal_rate: float
    class Config:
        from_attributes = True


# --- Audit ---
class AuditLogOut(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    field_changed: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    user: Optional[str]
    timestamp: datetime
    class Config:
        from_attributes = True


# --- Copilot ---
class CopilotRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class CopilotResponse(BaseModel):
    response: str
    session_id: str
