from datetime import date, datetime
from sqlalchemy import String, Float, Integer, Boolean, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# --- 1. Counterparties ---
class Counterparty(Base):
    __tablename__ = "counterparties"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_name: Mapped[str] = mapped_column(String(20), unique=True)
    legal_name: Mapped[str] = mapped_column(String(200))
    counterparty_type: Mapped[str] = mapped_column(String(20))  # bank, corporate, broker, central_bank
    lei_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    swift_code: Mapped[str | None] = mapped_column(String(11), nullable=True)
    country: Mapped[str | None] = mapped_column(String(3), nullable=True)
    credit_rating: Mapped[str | None] = mapped_column(String(5), nullable=True)
    rating_agency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settlement_netting: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# --- 2. Currencies ---
class Currency(Base):
    __tablename__ = "currencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iso_code: Mapped[str] = mapped_column(String(3), unique=True)
    name: Mapped[str] = mapped_column(String(50))
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settlement_days: Mapped[int] = mapped_column(Integer, default=2)


# --- 3. Currency Pairs ---
class CurrencyPair(Base):
    __tablename__ = "currency_pairs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    base_currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    quote_currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    pair_code: Mapped[str] = mapped_column(String(7), unique=True)  # "USD/CAD"
    spot_days: Mapped[int] = mapped_column(Integer, default=2)
    pip_size: Mapped[float] = mapped_column(Float, default=0.0001)
    base_currency: Mapped["Currency"] = relationship(foreign_keys=[base_currency_id])
    quote_currency: Mapped["Currency"] = relationship(foreign_keys=[quote_currency_id])


# --- 4. Bank Accounts ---
class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(String(34))
    account_name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(10))  # nostro, vostro, internal
    currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    counterparty_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("counterparties.id"), nullable=True)
    swift_code: Mapped[str | None] = mapped_column(String(11), nullable=True)
    current_balance: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    currency: Mapped["Currency"] = relationship()


# --- 5. Deals ---
class Deal(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_number: Mapped[str] = mapped_column(String(20), unique=True)
    deal_type: Mapped[str] = mapped_column(String(30))  # fx_spot, fx_forward, fx_swap, deposit, loan, fra, interest_rate_swap
    deal_subtype: Mapped[str | None] = mapped_column(String(30), nullable=True)
    trade_date: Mapped[date] = mapped_column(Date)
    value_date: Mapped[date] = mapped_column(Date)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparties.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, confirmed, settled, cancelled, matured
    direction: Mapped[str] = mapped_column(String(4))  # buy, sell
    # FX fields
    buy_currency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("currencies.id"), nullable=True)
    buy_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_currency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("currencies.id"), nullable=True)
    sell_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    forward_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Money Market fields
    principal_currency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("currencies.id"), nullable=True)
    principal_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    interest_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    day_count_convention: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ACT/360, ACT/365, 30/360
    interest_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Settlement
    buy_account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    sell_account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    # Audit
    trader: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationships
    counterparty: Mapped["Counterparty"] = relationship()
    buy_currency: Mapped["Currency"] = relationship(foreign_keys=[buy_currency_id])
    sell_currency: Mapped["Currency"] = relationship(foreign_keys=[sell_currency_id])
    cashflows: Mapped[list["Cashflow"]] = relationship(back_populates="deal")
    legs: Mapped[list["DealLeg"]] = relationship(back_populates="deal")


# --- 6. Deal Legs ---
class DealLeg(Base):
    __tablename__ = "deal_legs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id"))
    leg_number: Mapped[int] = mapped_column(Integer)  # 1=near, 2=far
    value_date: Mapped[date] = mapped_column(Date)
    buy_currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    buy_amount: Mapped[float] = mapped_column(Float)
    sell_currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    sell_amount: Mapped[float] = mapped_column(Float)
    rate: Mapped[float] = mapped_column(Float)
    deal: Mapped["Deal"] = relationship(back_populates="legs")


# --- 7. Cashflows ---
class Cashflow(Base):
    __tablename__ = "cashflows"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id"))
    cashflow_type: Mapped[str] = mapped_column(String(20))  # principal, interest, fee, settlement
    currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    amount: Mapped[float] = mapped_column(Float)  # positive=inflow, negative=outflow
    pay_receive: Mapped[str] = mapped_column(String(7))  # pay, receive
    value_date: Mapped[date] = mapped_column(Date)
    account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="projected")  # projected, confirmed, settled, failed
    settled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deal: Mapped["Deal"] = relationship(back_populates="cashflows")
    currency: Mapped["Currency"] = relationship()


# --- 8. Positions ---
class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    position_date: Mapped[date] = mapped_column(Date)
    spot_position: Mapped[float] = mapped_column(Float, default=0.0)
    forward_position: Mapped[float] = mapped_column(Float, default=0.0)
    total_position: Mapped[float] = mapped_column(Float, default=0.0)
    avg_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    currency: Mapped["Currency"] = relationship()


# --- 9. Credit Limits ---
class CreditLimit(Base):
    __tablename__ = "credit_limits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparties.id"))
    limit_type: Mapped[str] = mapped_column(String(20))  # settlement, pre_settlement, total
    limit_currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    limit_amount: Mapped[float] = mapped_column(Float)
    utilized_amount: Mapped[float] = mapped_column(Float, default=0.0)
    available_amount: Mapped[float] = mapped_column(Float)
    tenor_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    counterparty: Mapped["Counterparty"] = relationship()
    limit_currency: Mapped["Currency"] = relationship()


# --- 10. Exposures ---
class Exposure(Base):
    __tablename__ = "exposures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparties.id"))
    exposure_date: Mapped[date] = mapped_column(Date)
    settlement_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    pre_settlement_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    total_exposure: Mapped[float] = mapped_column(Float, default=0.0)
    currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    counterparty: Mapped["Counterparty"] = relationship()


# --- 11. Market Rates ---
class MarketRate(Base):
    __tablename__ = "market_rates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rate_type: Mapped[str] = mapped_column(String(20))  # fx_spot, fx_forward, interest_rate, discount_factor
    currency_pair_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("currency_pairs.id"), nullable=True)
    currency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("currencies.id"), nullable=True)
    tenor: Mapped[str | None] = mapped_column(String(10), nullable=True)  # SPOT, 1W, 1M, 3M, 1Y
    bid_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    mid_rate: Mapped[float] = mapped_column(Float)
    rate_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# --- 12. Valuations ---
class Valuation(Base):
    __tablename__ = "valuations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id"))
    valuation_date: Mapped[date] = mapped_column(Date)
    market_rate: Mapped[float] = mapped_column(Float)
    mtm_value: Mapped[float] = mapped_column(Float)
    mtm_currency_id: Mapped[int] = mapped_column(Integer, ForeignKey("currencies.id"))
    deal_rate: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deal: Mapped["Deal"] = relationship()


# --- 13. Audit Log ---
class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50))  # deal, limit, counterparty
    entity_id: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20))  # create, update, delete, status_change, approve
    field_changed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    user: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)


# --- 14. Copilot Conversations ---
class CopilotConversation(Base):
    __tablename__ = "copilot_conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(10))  # user, assistant, function
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    function_call: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
