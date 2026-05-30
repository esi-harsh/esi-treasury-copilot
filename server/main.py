from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import *  # noqa: F401,F403
from app.api import counterparties, currencies, bank_accounts, deals, positions, limits, market_rates, valuation, copilot

app = FastAPI(title="Treasury Management System", version="2.0.0", description="AI-powered Treasury Management System inspired by Kondor/Acumen Plus — 14 table schema")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "Treasury Management System", "version": "2.0", "tables": 14}


app.include_router(counterparties.router, prefix="/api/v1", tags=["Counterparties"])
app.include_router(currencies.router, prefix="/api/v1", tags=["Currencies"])
app.include_router(bank_accounts.router, prefix="/api/v1", tags=["Bank Accounts"])
app.include_router(deals.router, prefix="/api/v1", tags=["Deals"])
app.include_router(positions.router, prefix="/api/v1", tags=["Positions"])
app.include_router(limits.router, prefix="/api/v1", tags=["Limits & Risk"])
app.include_router(market_rates.router, prefix="/api/v1", tags=["Market Data"])
app.include_router(valuation.router, prefix="/api/v1", tags=["Valuation"])
app.include_router(copilot.router, prefix="/api/v1", tags=["AI Copilot"])
