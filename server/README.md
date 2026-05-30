# Treasury Management System + AI Copilot

AI-powered Treasury Management System inspired by Kondor/Acumen Plus, built for CIBC Finance team demo.

## Tech Stack
- **Backend**: Python/FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **AI Copilot**: Google Gemini 2.0 Flash with function-calling

## Quick Start

```bash
pip install -r requirements.txt

# Set your Gemini API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Seed demo data
python -m app.seed

# Run server
uvicorn main:app --reload
```

API docs at: http://localhost:8000/docs

## Modules

| Module | Endpoints | Description |
|--------|-----------|-------------|
| Counterparties | `/api/v1/counterparties` | CRUD for trading counterparties |
| Currencies | `/api/v1/currencies` | Currency master data |
| Bank Accounts | `/api/v1/bank-accounts` | Nostro/Vostro accounts |
| Deals | `/api/v1/deals` | FX Spot, Forward, Deposit, Loan booking & lifecycle |
| Positions | `/api/v1/positions` | Net position per currency |
| Cashflows | `/api/v1/cashflows/projected` | Cashflow projections |
| Limits & Risk | `/api/v1/limits`, `/api/v1/risk/*` | Credit limits, exposure, pre-deal checks |
| Market Data | `/api/v1/market-rates` | FX and interest rates |
| Valuation | `/api/v1/valuation/mtm` | Mark-to-market P&L |
| AI Copilot | `/api/v1/copilot/chat` | Natural language treasury operations |

## AI Copilot Usage

```bash
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my current USD position?"}'
```

Example prompts:
- "Book a 5M USD/CAD FX spot at 1.37 with Goldman Sachs"
- "Show my limit utilization for JP Morgan"
- "What are my cashflows for the next 7 days?"
- "Run mark-to-market on my open positions"
- "List all confirmed deals"
- "What is my exposure to Deutsche Bank?"
