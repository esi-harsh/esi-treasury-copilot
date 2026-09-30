# Treasury Digital Twin & Harness Engine MCP Server

An enterprise AI-native Treasury Digital Twin and Model Context Protocol (MCP) server implementing **Pre-Trade Deal Compliance Checking**, **Counterparty Contagion & Credit Limit Breach Forecasting**, **Intraday Liquidity Shock & Basel III LCR Stress Testing**, and **Synthetic Deal Book Backtesting**.

Inspired by Kondor / Acumen Plus architectures, built with a 14-table relational treasury schema, and conforming to **Basel III Liquidity Framework**, **BCBS 239 Risk Data Aggregation**, and institutional AI/ML governance standards.

---

## Architecture Overview

```text
                          ┌─────────────────────────────────────────┐
                          │    Treasury AI Agent Orchestrator /     │
                          │   Claude Desktop / Antigravity Client   │
                          └───────────────────┬─────────────────────┘
                                              │ (SSE / Stdio / HTTP JSON-RPC)
                          ┌───────────────────▼─────────────────────┐
                          │     Treasury MCP Server (Port 8000)     │
                          │  twin.* | risk.* | trade.* | market.*   │
                          │      /api/v1/mcp  |  /api/v1/mcp/sse    │
                          └───────────────────┬─────────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       ┌──────────────────────────┐                        ┌──────────────────────────┐
       │  Treasury Engine Core    │                        │  AI Copilot Function     │
       │ (Deal / Risk / Valuation │                        │  Calling & Reasoning     │
       │  / Position Services)    │                        │ (OpenRouter / Gemini)    │
       └────────────┬─────────────┘                        └────────────┬─────────────┘
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                                 ┌──────────────────────────┐
                                 │   SQLite Database Store  │
                                 │    (14 Table Schema:     │
                                 │  Deals, Accounts, Limits │
                                 │   Cashflows, Valuations) │
                                 └──────────────────────────┘
```

---

## 1. Database Setup

### Step 1.1: 14-Table Treasury Schema
The database models 14 core treasury entities:
- `counterparties`, `currencies`, `currency_pairs`, `bank_accounts` (Nostro/Vostro)
- `deals` (FX Spot, Forward, Swaps, Deposits, Loans), `deal_legs`, `cashflows`
- `positions` (Spot, Forward, Net), `credit_limits`, `exposures`
- `market_rates` (Bid, Ask, Mid), `valuations` (Mark-to-Market PnL), `audit_logs`, `copilot_conversations`

### Step 1.2: Load Seed Data
Seed synthetic banking counterparties (JPM, RBC, BMO, Barclays, Deutsche Bank), active Nostro accounts, market yield curves, and live deals:

```bash
cd server
python -m app.seed
```

This seeds:
- **Major Banking Counterparties**: Credit ratings (AAA to BBB-), LEI codes, SWIFT BIC codes, and netting flags.
- **Nostro Accounts**: Multi-currency nostro accounts across USD, CAD, EUR, and GBP with initial cash reserves.
- **Credit Limits**: Real-time counterparty exposure ceilings and pre-settlement limits.
- **Market Rates**: FX Spot, forward points, and interest rate curves.
- **Active Deal Book**: Existing FX spot/forward trades and cashflow schedules.

---

## 2. Environment Configuration

Copy `.env.example` to `.env` in the `server` directory:

```bash
cd server
cp .env.example .env
```

Update your `.env` file with your credentials:

```env
# Database Configuration (Defaults to server/treasury.db)
DATABASE_URL=sqlite:///./treasury.db

# LLM Configuration (OpenRouter or Gemini for AI Copilot reasoning)
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=google/gemini-2.5-flash
MAX_TOKENS=2048

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

---

## 3. Installation

Install backend dependencies:

```bash
cd server
pip install -r requirements.txt
```

---

## 4. MCP Tools Reference

### A. Digital Twin & Scenario Simulation Tools (`twin.*`)
Sandboxed execution tools for balance sheet stress testing and Basel III compliance.

| Tool Name | Description | Key Inputs | Output |
| :--- | :--- | :--- | :--- |
| `get_twin_state` | Reads virtual treasury state (Nostro balances, net positions, cashflows) | `currency_scope`, `days_ahead` | Account balances, positions, projected cashflow array |
| `apply_market_shock` | Injects rate shifts (bps) and FX curve % shocks to revalue portfolio | `rate_shift_bps`, `fx_shock_pct`, `currency_pair` | Base PnL, shocked PnL, delta, and deal-level revaluations |
| `run_lcr_stress_test` | Runs 30-day Basel III Liquidity Coverage Ratio stress simulation | `outflow_multiplier`, `hqla_haircut_pct` | LCR ratio %, HQLA available, stressed outflows, compliance status |

### B. Pre-Trade Risk & Limit Governance Tools (`risk.*`)
Enforces hard exposure ceilings, pre-deal headroom validation, and concentration limits.

| Tool Name | Description | Key Inputs | Output |
| :--- | :--- | :--- | :--- |
| `evaluate_risk_limits` | Validates candidate trade against active counterparty credit limit | `counterparty_name`, `currency`, `proposed_amount` | Allowed/breached status, utilization %, available headroom, exposure breakdown |
| `check_counterparty_limit` | Queries credit limit headroom for a candidate transaction amount | `counterparty_name`, `currency`, `amount` | Utilization %, breach alert, current exposure |
| `get_exposure` | Calculates total settlement and pre-settlement counterparty exposure | `counterparty_name` | Settlement exposure, pre-settlement exposure, total exposure |

### C. Trade Execution & Simulation Tools (`trade.*`)
Simulates and executes FX and money market transactions with cashflow scheduling.

| Tool Name | Description | Key Inputs | Output |
| :--- | :--- | :--- | :--- |
| `simulate_trade` | Evaluates candidate trade inside sandbox without mutating live book | `deal_type`, `counterparty_name`, `buy_currency`, `buy_amount`, `sell_currency`, `sell_amount`, `rate`, `direction` | Simulation ID, projected MTM PnL, limit validation, actionability flag |
| `book_fx_deal` | Books live FX Spot or Forward deal, generating settlement cashflows | `deal_type`, `counterparty_name`, `buy_currency`, `buy_amount`, `sell_currency`, `sell_amount`, `rate`, `direction` | Deal number, status (`pending`), generated cashflow IDs, audit record |
| `list_deals` | Queries and filters deals by deal type and settlement status | `deal_type`, `status`, `limit` | Deal list with amounts, counterparty names, rates, and value dates |

### D. Valuation & Market Data Tools (`market.*`, `pos.*`)
Provides mark-to-market revaluation, position aggregation, and rate queries.

| Tool Name | Description | Key Inputs | Output |
| :--- | :--- | :--- | :--- |
| `get_positions` | Retrieves aggregated net spot, forward, and total currency positions | *(None)* | Net positions by ISO currency code |
| `get_cashflow_forecast` | Returns projected contractual cashflows for the next $N$ days | `days` (default: 30) | Chronological cashflows with amounts and pay/receive directions |
| `get_mtm_valuation` | Calculates mark-to-market valuations on open FX positions | *(None)* | Deal-by-deal MTM PnL and total unrealized portfolio PnL |
| `get_market_rate` | Fetches latest bid, ask, and mid rates for a currency pair | `pair_code` (e.g. `USD/CAD`) | Spot rate, bid/ask spread, quote timestamp |

---

## 5. Running the MCP Server

### Option A: FastAPI HTTP / SSE Server (Recommended)
Starts the FastAPI application with both REST and MCP endpoints over HTTP/SSE:

```bash
cd server
python -m uvicorn main:app --reload --port 8000
```

* **HTTP JSON-RPC Endpoint**: `http://localhost:8000/api/v1/mcp`
* **Server-Sent Events (SSE) Stream**: `http://localhost:8000/api/v1/mcp/sse`
* **Swagger API Documentation**: `http://localhost:8000/docs`

### Option B: Standard I/O (stdio) Runner
Direct stdio execution for local desktop agent orchestrators (e.g. Claude Desktop, Cursor, Antigravity CLI):

```bash
python server/mcp_stdio.py
```

---

## 6. Testing & Verification

Run the automated MCP test suite:

```bash
cd server
python test_mcp.py
```

Expected output:
```text
--- 1. Testing GET /api/v1/mcp ---
Status: 200
Body: {'status': 'online', 'service': 'Treasury Harness Engine MCP Server', 'tool_count': 13, ...}

--- 2. Testing MCP initialize ---
Status: 200
Result: {
  "protocolVersion": "2024-11-05",
  "serverInfo": { "name": "esi-treasury-harness", "version": "2.0.0" }
}

--- 3. Testing tools/list ---
Found 13 tools:
  - get_twin_state
  - apply_market_shock
  - simulate_trade
  - evaluate_risk_limits
  - run_lcr_stress_test
  - book_fx_deal
  - get_positions
  - get_cashflow_forecast
  - check_counterparty_limit
  - get_exposure
  - list_deals
  - get_mtm_valuation
  - get_market_rate

--- 4. Testing tools/call: get_twin_state ---
Status: success (Nostro balances & positions retrieved)

--- 5. Testing tools/call: evaluate_risk_limits ---
Status: success (Limit: 30,000,000 / 50,000,000 | 60.0% utilization)

--- 6. Testing tools/call: run_lcr_stress_test ---
Status: PASS (LCR: 14843.35% vs 100.0% minimum threshold)

--- 7. Testing tools/call: apply_market_shock ---
Status: success (Rate Shock: +50.0 bps | FX Shock: +2.50% | Net PnL Impact: +$573,950.00)

ALL MCP TESTS PASSED SUCCESSFULLY!
```

You can also run the quick data fetch script:
```bash
python fetch_data_example.py
```

---

## 7. Connecting to Agent Clients

### A. Official MCP Inspector
Test the server visually using the MCP Inspector:

```bash
# Option 1: SSE Web UI Mode (when uvicorn is running)
npx @modelcontextprotocol/inspector
# Open browser, select SSE transport, and connect to: http://localhost:8000/api/v1/mcp/sse

# Option 2: Direct Stdio CLI Mode
npx @modelcontextprotocol/inspector python "C:/ESI Treasury/server/mcp_stdio.py"
```

### B. Claude Desktop Configuration
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "esi-treasury": {
      "command": "python",
      "args": [
        "C:/ESI Treasury/server/mcp_stdio.py"
      ],
      "env": {
        "DATABASE_URL": "sqlite:///C:/ESI Treasury/server/treasury.db"
      }
    }
  }
}
```

### C. HTTP Remote Client Configuration (e.g. Antigravity / Web UI)
```json
{
  "mcpServers": {
    "esi-treasury-http": {
      "url": "http://localhost:8000/api/v1/mcp",
      "transport": "http-jsonrpc"
    },
    "esi-treasury-sse": {
      "url": "http://localhost:8000/api/v1/mcp/sse",
      "transport": "sse"
    }
  }
}
```
