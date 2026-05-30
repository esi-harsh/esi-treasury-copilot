# Treasury Management System — Complete API Documentation

> AI-powered Treasury Management System inspired by Kondor/Acumen Plus  
> Built for CIBC Finance Team Demo

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Database Schema (14 Tables)](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Deal Lifecycle Workflow](#deal-lifecycle-workflow)
6. [AI Copilot Workflow](#ai-copilot-workflow)
7. [User Flows](#user-flows)
8. [Setup & Deployment](#setup--deployment)

---

## System Overview

### What is this?

A full-stack Treasury Management System that allows bank treasurers to:
- Book and manage FX and Money Market deals
- Monitor real-time currency positions
- Track cashflow projections
- Manage counterparty credit limits with pre-deal checks
- Run mark-to-market valuations
- Interact with all of the above via an AI Copilot (natural language)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 + FastAPI |
| Database | SQLite (SQLAlchemy ORM) |
| AI/LLM | OpenRouter API (Gemini 2.0 Flash) |
| Frontend | React + Vite + Tailwind CSS |
| Deployment | Docker Compose |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│              Treasury AI Copilot Chat UI                  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (POST /api/v1/copilot/chat)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                          │
├─────────────────────────────────────────────────────────┤
│  API Layer                                               │
│  ├── /api/v1/counterparties    (CRUD)                   │
│  ├── /api/v1/currencies        (CRUD)                   │
│  ├── /api/v1/currency-pairs    (CRUD)                   │
│  ├── /api/v1/bank-accounts     (CRUD)                   │
│  ├── /api/v1/deals             (Book + Lifecycle)       │
│  ├── /api/v1/positions         (Aggregation)            │
│  ├── /api/v1/cashflows         (Projections)            │
│  ├── /api/v1/limits            (Credit Limits)          │
│  ├── /api/v1/risk              (Exposure + Checks)      │
│  ├── /api/v1/market-rates      (FX + IR Rates)         │
│  ├── /api/v1/valuation         (MTM P&L)               │
│  └── /api/v1/copilot/chat      (AI Copilot)            │
├─────────────────────────────────────────────────────────┤
│  Service Layer                                           │
│  ├── deal_service      (deal booking + cashflows)       │
│  ├── position_service  (net position calculation)       │
│  ├── risk_service      (exposure + limit checks)        │
│  ├── valuation_service (MTM computation)                │
│  └── copilot_service   (LLM + tool execution)          │
├─────────────────────────────────────────────────────────┤
│  Data Layer (SQLite - 14 Tables)                         │
│  counterparties, currencies, currency_pairs,             │
│  bank_accounts, deals, deal_legs, cashflows,             │
│  positions, credit_limits, exposures, market_rates,      │
│  valuations, audit_log, copilot_conversations            │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              OpenRouter API (LLM)                         │
│         google/gemini-2.0-flash-001                       │
│         Function Calling (8 tools)                        │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table 1: `currencies`

Master currency reference data.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| iso_code | VARCHAR(3) UNIQUE | ISO 4217 code (USD, CAD, EUR) |
| name | VARCHAR(50) | Full name |
| decimal_places | INTEGER | 2 for most, 0 for JPY |
| is_active | BOOLEAN | Soft delete |
| settlement_days | INTEGER | T+1, T+2 convention |

### Table 2: `currency_pairs`

Defines tradeable FX pairs with market conventions.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| base_currency_id | FK → currencies | Base currency |
| quote_currency_id | FK → currencies | Quote currency |
| pair_code | VARCHAR(7) UNIQUE | "USD/CAD", "EUR/USD" |
| spot_days | INTEGER | Settlement days (usually 2) |
| pip_size | FLOAT | 0.0001 or 0.01 for JPY |

### Table 3: `counterparties`

All trading counterparties (banks, corporates, brokers).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| short_name | VARCHAR(20) UNIQUE | Trading shortcode ("GS", "JPM") |
| legal_name | VARCHAR(200) | Full legal entity name |
| counterparty_type | VARCHAR(20) | bank, corporate, broker, central_bank |
| lei_code | VARCHAR(20) | Legal Entity Identifier |
| swift_code | VARCHAR(11) | SWIFT/BIC code |
| country | VARCHAR(3) | ISO country code |
| credit_rating | VARCHAR(5) | "AA+", "BBB-" |
| rating_agency | VARCHAR(20) | S&P, Moody's, Fitch |
| is_active | BOOLEAN | |
| settlement_netting | BOOLEAN | Whether netting applies |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### Table 4: `bank_accounts`

Nostro/Vostro accounts for settlement.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| account_number | VARCHAR(34) | IBAN or account number |
| account_name | VARCHAR(100) | Descriptive name |
| account_type | VARCHAR(10) | nostro, vostro, internal |
| currency_id | FK → currencies | Account currency |
| counterparty_id | FK → counterparties | Correspondent bank |
| swift_code | VARCHAR(11) | |
| current_balance | FLOAT | Running balance |
| is_active | BOOLEAN | |

### Table 5: `deals`

The heart of the system — all treasury instruments.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| deal_number | VARCHAR(20) UNIQUE | System-generated (e.g. "FX-2025-A3B2C") |
| deal_type | VARCHAR(30) | fx_spot, fx_forward, fx_swap, deposit, loan |
| deal_subtype | VARCHAR(30) | Optional refinement |
| trade_date | DATE | When deal was struck |
| value_date | DATE | Settlement/start date |
| maturity_date | DATE | End date (forwards, deposits) |
| counterparty_id | FK → counterparties | |
| status | VARCHAR(20) | pending, confirmed, settled, cancelled, matured |
| direction | VARCHAR(4) | buy, sell |
| buy_currency_id | FK → currencies | Currency we receive |
| buy_amount | FLOAT | |
| sell_currency_id | FK → currencies | Currency we pay |
| sell_amount | FLOAT | |
| rate | FLOAT | Agreed FX rate |
| forward_points | FLOAT | For forwards |
| principal_currency_id | FK → currencies | For deposits/loans |
| principal_amount | FLOAT | |
| interest_rate | FLOAT | Annual rate |
| day_count_convention | VARCHAR(10) | ACT/360, ACT/365, 30/360 |
| interest_amount | FLOAT | Calculated interest |
| buy_account_id | FK → bank_accounts | Settlement account |
| sell_account_id | FK → bank_accounts | Settlement account |
| trader | VARCHAR(50) | Who booked it |
| notes | TEXT | |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### Table 6: `deal_legs`

For FX swaps (near/far legs).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| deal_id | FK → deals | Parent deal |
| leg_number | INTEGER | 1=near, 2=far |
| value_date | DATE | |
| buy_currency_id | FK → currencies | |
| buy_amount | FLOAT | |
| sell_currency_id | FK → currencies | |
| sell_amount | FLOAT | |
| rate | FLOAT | |

### Table 7: `cashflows`

Every deal generates projected/actual cash movements.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| deal_id | FK → deals | Source deal |
| cashflow_type | VARCHAR(20) | principal, interest, fee, settlement |
| currency_id | FK → currencies | |
| amount | FLOAT | |
| pay_receive | VARCHAR(7) | pay, receive |
| value_date | DATE | When cash moves |
| account_id | FK → bank_accounts | Settlement account |
| status | VARCHAR(20) | projected, confirmed, settled, failed |
| settled_date | DATE | Actual settlement date |

### Table 8: `positions`

Aggregated net position per currency (materialized cache).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| currency_id | FK → currencies | |
| position_date | DATE | As-of date |
| spot_position | FLOAT | Net spot exposure |
| forward_position | FLOAT | Net forward exposure |
| total_position | FLOAT | Combined |
| avg_rate | FLOAT | Weighted average rate |

### Table 9: `credit_limits`

Per-counterparty credit limits for pre-deal checks.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| counterparty_id | FK → counterparties | |
| limit_type | VARCHAR(20) | settlement, pre_settlement, total |
| limit_currency_id | FK → currencies | |
| limit_amount | FLOAT | Maximum allowed |
| utilized_amount | FLOAT | Current usage |
| available_amount | FLOAT | Remaining |
| tenor_months | INTEGER | Limit tenor bucket |
| approved_by | VARCHAR(50) | |
| expiry_date | DATE | |
| is_active | BOOLEAN | |

### Table 10: `exposures`

Point-in-time counterparty exposure snapshots.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| counterparty_id | FK → counterparties | |
| exposure_date | DATE | |
| settlement_exposure | FLOAT | |
| pre_settlement_exposure | FLOAT | |
| total_exposure | FLOAT | |
| currency_id | FK → currencies | |
| calculated_at | DATETIME | |

### Table 11: `market_rates`

FX rates and interest rates for valuation.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| rate_type | VARCHAR(20) | fx_spot, fx_forward, interest_rate |
| currency_pair_id | FK → currency_pairs | For FX rates |
| currency_id | FK → currencies | For interest rates |
| tenor | VARCHAR(10) | SPOT, 1W, 1M, 3M, 1Y |
| bid_rate | FLOAT | |
| ask_rate | FLOAT | |
| mid_rate | FLOAT | |
| rate_date | DATE | |
| source | VARCHAR(50) | Reuters, Bloomberg |

### Table 12: `valuations`

Stored Mark-to-Market results per deal.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| deal_id | FK → deals | |
| valuation_date | DATE | |
| market_rate | FLOAT | Rate used for MTM |
| mtm_value | FLOAT | Unrealized P&L |
| mtm_currency_id | FK → currencies | Reporting currency |
| deal_rate | FLOAT | Original deal rate |

### Table 13: `audit_log`

Full audit trail for compliance.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| entity_type | VARCHAR(50) | deal, limit, counterparty |
| entity_id | INTEGER | |
| action | VARCHAR(20) | create, update, status_change |
| field_changed | VARCHAR(50) | |
| old_value | TEXT | |
| new_value | TEXT | |
| user | VARCHAR(50) | |
| timestamp | DATETIME | |
| ip_address | VARCHAR(45) | |

### Table 14: `copilot_conversations`

AI chat history for context continuity.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| session_id | VARCHAR(36) | UUID grouping a conversation |
| role | VARCHAR(10) | user, assistant, function |
| content | TEXT | Message text |
| function_call | TEXT | JSON of tool call details |
| tokens_used | INTEGER | For cost tracking |
| created_at | DATETIME | |

---


## API Endpoints

Base URL: `http://localhost:8000`  
Swagger Docs: `http://localhost:8000/docs`

---

### Health Check

```
GET /health
```

**Response:**
```json
{"status": "healthy", "service": "Treasury Management System", "version": "2.0", "tables": 14}
```

---

### Counterparties

#### Create Counterparty
```
POST /api/v1/counterparties
```
**Body:**
```json
{
  "short_name": "GS",
  "legal_name": "Goldman Sachs International",
  "counterparty_type": "bank",
  "credit_rating": "A+",
  "rating_agency": "S&P",
  "country": "US",
  "swift_code": "GOLDUS33",
  "settlement_netting": false
}
```

#### List Counterparties
```
GET /api/v1/counterparties
```

#### Get Single Counterparty
```
GET /api/v1/counterparties/{id}
```

#### Update Counterparty
```
PUT /api/v1/counterparties/{id}
```

---

### Currencies

#### Create Currency
```
POST /api/v1/currencies
```
**Body:**
```json
{"iso_code": "USD", "name": "US Dollar", "decimal_places": 2, "settlement_days": 2}
```

#### List Currencies
```
GET /api/v1/currencies
```

#### Create Currency Pair
```
POST /api/v1/currency-pairs
```
**Body:**
```json
{"base_currency_id": 1, "quote_currency_id": 2, "pair_code": "USD/CAD", "spot_days": 2, "pip_size": 0.0001}
```

#### List Currency Pairs
```
GET /api/v1/currency-pairs
```

---

### Bank Accounts

#### Create Bank Account
```
POST /api/v1/bank-accounts
```
**Body:**
```json
{
  "account_number": "CA001-USD-001",
  "account_name": "CIBC USD Nostro",
  "account_type": "nostro",
  "currency_id": 1,
  "swift_code": "CIBCUS33",
  "current_balance": 50000000
}
```

#### List Bank Accounts
```
GET /api/v1/bank-accounts
```

---

### Deals (Core Trading)

#### Book a Deal
```
POST /api/v1/deals
```

**FX Spot Example:**
```json
{
  "deal_type": "fx_spot",
  "counterparty_id": 1,
  "trade_date": "2025-05-29",
  "value_date": "2025-05-31",
  "direction": "buy",
  "buy_currency_id": 1,
  "buy_amount": 10000000,
  "sell_currency_id": 2,
  "sell_amount": 13720000,
  "rate": 1.372,
  "trader": "T.Shah"
}
```

**Deposit Example:**
```json
{
  "deal_type": "deposit",
  "counterparty_id": 5,
  "trade_date": "2025-05-29",
  "value_date": "2025-05-29",
  "maturity_date": "2025-08-27",
  "direction": "buy",
  "principal_currency_id": 2,
  "principal_amount": 25000000,
  "interest_rate": 0.045,
  "day_count_convention": "ACT/365",
  "buy_currency_id": 2,
  "buy_amount": 25000000,
  "sell_currency_id": 2,
  "sell_amount": 25000000,
  "rate": 4.50,
  "trader": "S.Kumar"
}
```

**Response:**
```json
{
  "id": 1,
  "deal_number": "FX-2025-A3B2C",
  "deal_type": "fx_spot",
  "status": "pending",
  "counterparty_id": 1,
  "buy_amount": 10000000,
  "sell_amount": 13720000,
  "rate": 1.372,
  ...
}
```

#### List Deals (with filters)
```
GET /api/v1/deals
GET /api/v1/deals?deal_type=fx_spot
GET /api/v1/deals?status=pending
GET /api/v1/deals?counterparty_id=1
```

#### Get Single Deal
```
GET /api/v1/deals/{id}
```

#### Confirm Deal
```
PUT /api/v1/deals/{id}/confirm
```
Changes status: `pending` → `confirmed`

#### Settle Deal
```
PUT /api/v1/deals/{id}/settle
```
Changes status: `confirmed` → `settled`  
Also marks all cashflows as `settled`.

#### Cancel Deal
```
PUT /api/v1/deals/{id}/cancel
```
Changes status: `pending|confirmed` → `cancelled`

#### Get Deal Cashflows
```
GET /api/v1/deals/{id}/cashflows
```

---

### Positions

#### Get Net Positions
```
GET /api/v1/positions
```
**Response:**
```json
[
  {
    "currency_id": 1,
    "currency": "USD",
    "position_date": "2025-05-29",
    "spot_position": 4575000.0,
    "forward_position": 5000000.0,
    "total_position": 9575000.0,
    "avg_rate": null
  }
]
```

#### Get Projected Cashflows
```
GET /api/v1/cashflows/projected?days=30
GET /api/v1/cashflows/projected?days=90
```
**Response:**
```json
[
  {
    "id": 1,
    "deal_id": 1,
    "cashflow_type": "settlement",
    "currency_id": 1,
    "amount": 10000000,
    "pay_receive": "receive",
    "value_date": "2025-05-31",
    "status": "projected"
  }
]
```

---

### Limits & Risk

#### Create Credit Limit
```
POST /api/v1/limits
```
**Body:**
```json
{
  "counterparty_id": 1,
  "limit_type": "total",
  "limit_currency_id": 1,
  "limit_amount": 50000000,
  "approved_by": "Risk Committee",
  "expiry_date": "2026-05-29"
}
```

#### List Limits
```
GET /api/v1/limits
GET /api/v1/limits?counterparty_id=1
```

#### Get Counterparty Exposure
```
GET /api/v1/risk/exposure?counterparty_id=1
```
**Response:**
```json
{
  "counterparty_id": 1,
  "settlement_exposure": 0,
  "pre_settlement_exposure": 10000000,
  "total_exposure": 10000000
}
```

#### Pre-Deal Limit Check
```
GET /api/v1/risk/check-limit?counterparty_id=1&currency_id=1&amount=5000000
```
**Response (within limit):**
```json
{
  "allowed": true,
  "message": "Within limit: 15,000,000 / 50,000,000",
  "current_exposure": 10000000,
  "limit_amount": 50000000,
  "utilization_pct": 30.0
}
```
**Response (breach):**
```json
{
  "allowed": false,
  "message": "LIMIT BREACH: exposure would be 55,000,000 vs limit 50,000,000",
  "current_exposure": 10000000,
  "limit_amount": 50000000,
  "available": 40000000
}
```

---

### Market Data

#### Upsert Market Rate
```
POST /api/v1/market-rates
```
**Body:**
```json
{
  "rate_type": "fx_spot",
  "currency_pair_id": 1,
  "tenor": "SPOT",
  "bid_rate": 1.3718,
  "ask_rate": 1.3722,
  "mid_rate": 1.3720,
  "rate_date": "2025-05-29",
  "source": "Reuters"
}
```

#### List Market Rates
```
GET /api/v1/market-rates
GET /api/v1/market-rates?currency_pair_id=1
```

---

### Valuation

#### Run Mark-to-Market
```
GET /api/v1/valuation/mtm
```
**Response:**
```json
[
  {
    "deal_id": 1,
    "deal_number": "FX-2025-A3B2C",
    "deal_type": "fx_spot",
    "currency_pair": "USD/CAD",
    "deal_rate": 1.372,
    "market_rate": 1.375,
    "notional": 10000000,
    "unrealized_pnl": 30000.00
  }
]
```

#### Valuation History
```
GET /api/v1/valuation/history
GET /api/v1/valuation/history?deal_id=1
```

---

### AI Copilot

#### Chat
```
POST /api/v1/copilot/chat
```
**Body:**
```json
{"message": "What is my current USD position?", "session_id": null}
```
**Response:**
```json
{
  "response": "Your current USD net position is **+$9,575,000**:\n- Spot: +$4,575,000\n- Forward: +$5,000,000",
  "session_id": "a1b2c3d4e5f6"
}
```

---


## Deal Lifecycle Workflow

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│  BOOK    │────▶│  PENDING  │────▶│ CONFIRMED│────▶│ SETTLED  │
│  (POST)  │     │           │     │          │     │          │
└──────────┘     └─────┬─────┘     └────┬─────┘     └──────────┘
                       │                 │
                       ▼                 ▼
                 ┌───────────┐     ┌───────────┐
                 │ CANCELLED │     │ CANCELLED │
                 └───────────┘     └───────────┘
```

### Step-by-step:

1. **Trader books deal** → `POST /api/v1/deals`
   - System generates unique deal_number
   - Status set to `pending`
   - Cashflows auto-generated based on deal type
   - Audit log entry created

2. **Middle office confirms** → `PUT /api/v1/deals/{id}/confirm`
   - Status changes to `confirmed`
   - Audit log records status change

3. **Back office settles** → `PUT /api/v1/deals/{id}/settle`
   - Status changes to `settled`
   - All cashflows marked as `settled`
   - Audit log records settlement

4. **Cancel (at any pre-settled stage)** → `PUT /api/v1/deals/{id}/cancel`
   - Status changes to `cancelled`

### Cashflow Generation Rules:

| Deal Type | Cashflows Generated |
|-----------|-------------------|
| FX Spot | 2 cashflows: receive buy_ccy on value_date, pay sell_ccy on value_date |
| FX Forward | Same as spot but value_date is in the future |
| FX Swap | 4 cashflows: near leg (2) + far leg (2) |
| Deposit | 2-3 cashflows: pay principal at start, receive principal+interest at maturity |
| Loan | 2-3 cashflows: receive principal at start, pay principal+interest at maturity |

### Interest Calculation (Money Market):

```
interest = principal × rate × (days / day_count_basis)

Where day_count_basis:
  ACT/365 → 365
  ACT/360 → 360
  30/360  → 360
```

---

## AI Copilot Workflow

### How it works:

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User    │────▶│  FastAPI      │────▶│  OpenRouter   │────▶│  Gemini LLM  │
│  Message │     │  /copilot/chat│     │  API          │     │  (Function   │
│          │     │               │     │               │     │   Calling)   │
└──────────┘     └──────┬───────┘     └──────────────┘     └──────┬───────┘
                        │                                          │
                        │◀─────────── tool_calls ─────────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │  Execute Tool    │
               │  (query DB,      │
               │   book deal,     │
               │   check limit)   │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │  Send result     │────▶ LLM formats response
               │  back to LLM     │
               └──────────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │  Return natural  │────▶ User sees formatted answer
               │  language reply  │
               └──────────────────┘
```

### Available AI Tools (8):

| Tool | What it does | Tables accessed |
|------|-------------|----------------|
| `book_fx_deal` | Books a new FX deal | deals, cashflows, counterparties, currencies, audit_log |
| `get_positions` | Returns net positions per currency | cashflows, deals, positions |
| `get_cashflow_forecast` | Projected cashflows for N days | cashflows, deals |
| `check_counterparty_limit` | Pre-deal limit check | credit_limits, deals |
| `get_exposure` | Total exposure for counterparty | deals |
| `list_deals` | List/filter deals | deals |
| `get_mtm_valuation` | Mark-to-market all open FX | deals, market_rates, valuations, currency_pairs |
| `get_market_rate` | Latest rate for a pair | market_rates, currency_pairs |

### Conversation Flow:

1. User sends message
2. Message saved to `copilot_conversations` table
3. Full conversation history sent to LLM with tool definitions
4. LLM decides whether to call a tool or respond directly
5. If tool_call → execute function → send result back to LLM → LLM formats answer
6. Multiple tool calls can chain (e.g., check limit then book deal)
7. Final response saved to `copilot_conversations`
8. Session ID maintains context across messages

---

## User Flows

### Flow 1: Treasurer Books an FX Deal via Copilot

```
User: "Book a 5M USD/CAD FX spot at 1.37 with Goldman Sachs"

Copilot internally:
  1. Calls tool: book_fx_deal({
       deal_type: "fx_spot",
       counterparty_name: "Goldman Sachs",
       buy_currency: "USD",
       buy_amount: 5000000,
       sell_currency: "CAD",
       sell_amount: 6850000,
       rate: 1.37,
       direction: "buy"
     })
  2. System resolves "Goldman Sachs" → counterparty_id=1
  3. System resolves "USD" → currency_id=1, "CAD" → currency_id=2
  4. Creates Deal record (status=pending)
  5. Generates 2 cashflows (receive 5M USD, pay 6.85M CAD)
  6. Creates audit_log entry
  7. Returns: {deal_number: "FX-2025-A3B2C", status: "pending"}

Copilot responds:
  "✅ Deal booked successfully!
   - Deal Number: FX-2025-A3B2C
   - Type: FX Spot
   - Buy: 5,000,000 USD
   - Sell: 6,850,000 CAD
   - Rate: 1.3700
   - Counterparty: Goldman Sachs
   - Status: Pending confirmation"
```

### Flow 2: Check Position Before Trading

```
User: "What is my current USD position?"

Copilot internally:
  1. Calls tool: get_positions()
  2. System aggregates all projected cashflows from open deals
  3. Groups by currency, splits spot vs forward

Copilot responds:
  "Your current USD position:
   | Type    | Amount        |
   |---------|---------------|
   | Spot    | +$4,575,000   |
   | Forward | +$5,000,000   |
   | **Total** | **+$9,575,000** |

   You are net long USD."
```

### Flow 3: Pre-Deal Limit Check

```
User: "Can I do a 40M USD deal with Goldman Sachs?"

Copilot internally:
  1. Calls tool: check_counterparty_limit({
       counterparty_name: "Goldman Sachs",
       currency: "USD",
       amount: 40000000
     })
  2. System finds GS limit = 50M USD
  3. Current exposure = 10M
  4. New total would be 50M = exactly at limit

Copilot responds:
  "⚠️ Caution — this would fully utilize your limit:
   - Current exposure: $10,000,000
   - Proposed deal: $40,000,000
   - New total: $50,000,000 / $50,000,000 (100% utilized)

   The deal is technically allowed but leaves zero headroom.
   Consider reducing the amount or requesting a limit increase."
```

### Flow 4: End-of-Day MTM Valuation

```
User: "Run mark-to-market on my open positions"

Copilot internally:
  1. Calls tool: get_mtm_valuation()
  2. System finds all open FX deals
  3. For each deal, fetches latest market rate from market_rates table
  4. Calculates PnL = notional × (market_rate - deal_rate)
  5. Stores results in valuations table

Copilot responds:
  "Mark-to-Market Results (as of 2025-05-29):

   | Deal | Pair | Notional | Deal Rate | Mkt Rate | P&L |
   |------|------|----------|-----------|----------|-----|
   | FX-2025-A3B2C | USD/CAD | 10M | 1.3720 | 1.3750 | +$30,000 |
   | FX-2025-D4E5F | EUR/USD | 5M | 1.0850 | 1.0870 | +$10,000 |

   **Total Unrealized P&L: +$40,000**"
```

### Flow 5: Cashflow Forecast

```
User: "What are my cashflows for the next 7 days?"

Copilot internally:
  1. Calls tool: get_cashflow_forecast({days: 7})
  2. System queries projected cashflows with value_date ≤ today+7

Copilot responds:
  "Upcoming cashflows (next 7 days):

   | Date | Currency | Amount | Direction | Deal |
   |------|----------|--------|-----------|------|
   | May 31 | USD | +10,000,000 | Receive | FX-2025-A3B2C |
   | May 31 | CAD | -13,720,000 | Pay | FX-2025-A3B2C |
   | May 31 | GBP | +3,000,000 | Receive | FX-2025-G6H7I |
   | May 31 | USD | -3,813,000 | Pay | FX-2025-G6H7I |

   Net: +10M USD, -13.7M CAD, +3M GBP, -3.8M USD"
```

---

## Setup & Deployment

### Local Development

```bash
# Backend
cd server
pip install -r requirements.txt
cp .env.example .env          # Add OPENROUTER_API_KEY
python -m app.seed            # Seed demo data
uvicorn main:app --reload --port 8000

# Frontend
cd client
npm install
npm run dev                   # Runs on port 5173
```

### Docker

```bash
# From project root
echo "OPENROUTER_API_KEY=sk-or-v1-your-key" > .env
docker compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000/docs
```

### AWS Lightsail ($5/month)

```bash
ssh ubuntu@<lightsail-ip>
sudo apt update && sudo apt install docker.io docker-compose-plugin -y
git clone <repo> && cd gl-treasury
echo "OPENROUTER_API_KEY=sk-or-..." > .env
sudo docker compose up -d
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| OPENROUTER_API_KEY | Yes | — | API key from openrouter.ai |
| LLM_MODEL | No | google/gemini-2.0-flash-001 | Any OpenRouter model |
| DATABASE_URL | No | sqlite:///./treasury.db | SQLite path |

---

## Seeded Demo Data

| Entity | Count | Examples |
|--------|-------|---------|
| Currencies | 6 | USD, CAD, EUR, GBP, JPY, CHF |
| Currency Pairs | 5 | USD/CAD, EUR/USD, GBP/USD, USD/JPY, EUR/CAD |
| Counterparties | 8 | GS, JPM, DB, BARC, RBC, BMO, BOC, ENB |
| Bank Accounts | 5 | USD/CAD/EUR/GBP/JPY Nostro accounts |
| Credit Limits | 16 | 50M USD total + 25M USD settlement per counterparty |
| Market Rates | 9 | FX spot + forward + interest rates |
| Sample Deals | 4 | 2 FX Spot + 1 FX Forward + 1 Deposit |
