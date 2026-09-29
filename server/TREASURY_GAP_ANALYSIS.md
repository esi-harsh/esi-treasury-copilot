# Treasury Repo — Feature Gap Analysis Report

**Repo:** `C:\ESI Treasury\server` | **Generated:** 2026-09-29 | **Tables:** 14 | **Routers:** 9 | **Services:** 5

---

## Current Repo Overview

| Item | Detail |
|---|---|
| **Framework** | FastAPI + SQLAlchemy ORM |
| **Database** | SQLite (14 tables) |
| **AI Copilot** | OpenRouter → Gemini 2.0 Flash (function-calling) |
| **Routers** | 9 API routers registered |
| **Services** | 5 service modules |
| **Models** | 14 ORM models |
| **Auth / Security** | ❌ None |
| **Tests** | ❌ None |

---

## Overall Scorecard

| Module | Implementation % | Status |
|---|---|---|
| Deal Management | 70% | ⚠️ Mostly Done |
| FX & Derivatives | 50% | ⚠️ Partial |
| Risk Management | 30% | ⚠️ Partial |
| Liquidity Management | 25% | ⚠️ Partial |
| Reporting & Analytics | 20% | ⚠️ Basic |
| Integration | 15% | ⚠️ Basic |
| Investment Portfolio | 0% | ❌ Missing |
| ALM | 0% | ❌ Missing |
| Regulatory Reporting | 0% | ❌ Missing |
| Accounting / GL | 0% | ❌ Missing |
| **Security & Controls** | **0%** | **🚨 Critical** |

---

## Module 1 — Deal / Transaction Management

**Status: ⚠️ 70% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| Deal Capture (POST) | `app/api/deals.py` | Book deal via API |
| FX Spot / Forward | `app/services/deal_service.py` | Full cashflow generation |
| FX Swap (2-leg) | `app/services/deal_service.py` | `create_fx_swap()` — not exposed via route |
| Deposit / Loan | `app/services/deal_service.py` | With interest calculation |
| Deal Lifecycle | `app/api/deals.py` | pending → confirmed → settled → cancelled |
| Audit on deal events | `app/services/deal_service.py` | AuditLog entries |
| Deal Number Generation | `app/services/deal_service.py` | UUID-based |
| List / Filter Deals | `app/api/deals.py` | By type, status, counterparty |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Maker-Checker / 4-eyes approval** | 🔴 Required | Deals go directly to `pending`; no second approver |
| **Deal Amendment endpoint** | 🔴 Required | No `PUT /deals/{id}` update route |
| **Deal date-range filters** | 🔴 Required | No `trade_date_from` / `trade_date_to` filters |
| **FX Swap API route** | 🔴 Required | Service exists but not wired to router |
| **Interest Rate Swap (IRS)** cashflow logic | 🟡 Nice-to-Have | Model field exists, no cashflow schedule |
| **Bond / Fixed Income** instrument | 🟡 Nice-to-Have | No coupon schedule, no amortization |
| **Repo / Reverse-Repo** instrument | 🟡 Nice-to-Have | Not implemented |
| **Maturity auto-processing** | 🟡 Nice-to-Have | No background scheduler |
| **STP flags** (straight-through-processing) | 🟡 Nice-to-Have | No auto-confirm rule engine |

---

## Module 2 — Liquidity Management

**Status: ⚠️ 25% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| Projected Cashflow (N-day) | `app/api/positions.py` | `GET /cashflows/projected` |
| Net FX Positions | `app/services/position_service.py` | Spot + Forward breakdown |
| Bank Account Balances | `app/api/bank_accounts.py` | Static balance; not updated on settlement |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Real-time cash position** (aggregated across accounts) | 🔴 Required | No `GET /liquidity/cash-position` |
| **Bank balance update on settlement** | 🔴 Required | Deal settlement doesn't update `BankAccount.current_balance` |
| **Cashflow time-bucketing** (O/N, 1W, 1M, 3M, 1Y) | 🔴 Required | Cashflows not bucketed by tenor |
| **Maturity Ladder / Funding Gap Report** | 🔴 Required | No time-bucketed gap report |
| **LCR Calculation** (HQLA / Net outflows) | 🟡 Nice-to-Have | No HQLA classification |
| **NSFR Calculation** | 🟡 Nice-to-Have | Needs stable funding categorization |
| **CRR / SLR tracking** | 🟡 Nice-to-Have | Regulatory ratios |
| **Liquidity threshold alerts** | 🟡 Nice-to-Have | No alerting mechanism |

---

## Module 3 — Risk Management

**Status: ⚠️ 30% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| Credit Limit Check (pre-deal) | `app/services/risk_service.py` | `check_limit()` |
| Counterparty Exposure calc | `app/services/risk_service.py` | Settlement + pre-settlement |
| Exposure Snapshot | `app/services/risk_service.py` | `snapshot_exposure()` — not API-exposed |
| Limit Utilization List | `app/api/limits.py` | `GET /limits` |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Limit breach hard-block at deal booking** | 🔴 Required | `check_limit` is separate; not called during booking |
| **Limit expiry enforcement** | 🔴 Required | `expiry_date` stored but never checked |
| **Exposure snapshot API endpoint** | 🔴 Required | Service method exists; no route |
| **FX open position limits** | 🔴 Required | Positions calculated but no limit check |
| **Limit type differentiation** (settlement vs pre-settlement) | 🔴 Required | Only `total` limit type queried |
| **VaR Engine** (Value at Risk) | 🟡 Nice-to-Have | No statistical risk calculation |
| **Stress Testing / Scenario Analysis** | 🟡 Nice-to-Have | No rate shock scenarios |
| **DV01 / Duration Sensitivity** | 🟡 Nice-to-Have | Requires yield curve |
| **ALCO summary dashboard** | 🟡 Nice-to-Have | No aggregate risk summary endpoint |

---

## Module 4 — Investment Portfolio Management

**Status: ❌ 0% Implemented**

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **HTM / AFS / HFT portfolio classification** | 🟡 Nice-to-Have | Standard for banks holding securities |
| **Bond / Government Security deal type** | 🟡 Nice-to-Have | No coupon schedule |
| **Bond Valuation** (YTM, duration, modified duration) | 🟡 Nice-to-Have | Not in scope yet |
| **MTM for bond portfolio** | 🟡 Nice-to-Have | Current MTM is FX-only |
| **Accrued Interest (daily)** | 🟡 Nice-to-Have | Only computed at deal creation |
| **SLR investment tracking** | ⚪ Not Required | Central bank specific |
| **Coupon / Maturity event scheduler** | ⚪ Not Required | Advanced feature |

> **Note:** Investment Portfolio is recommended for Phase 2. Existing MTM and deal infrastructure provide a foundation.

---

## Module 5 — Foreign Exchange & Derivatives

**Status: ⚠️ 50% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| FX Spot deal | `app/services/deal_service.py` | Full lifecycle |
| FX Forward deal | `app/services/deal_service.py` | Full lifecycle |
| FX Swap (2-leg) | `app/services/deal_service.py` | Service only — no API route |
| Open Currency Position | `app/services/position_service.py` | Spot + Forward breakdown |
| MTM P&L (FX unrealized) | `app/services/valuation_service.py` | Via market rate lookup |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **FX Swap API route** (expose `create_fx_swap`) | 🔴 Required | `POST /deals/fx-swap` missing |
| **Realized P&L on settlement** | 🔴 Required | Settlement doesn't compute realized P&L |
| **Daily FX P&L report** | 🔴 Required | No aggregate realized + unrealized P&L endpoint |
| **FX open position limit enforcement** | 🔴 Required | Positions shown but no limit guard |
| **Hedge Management** (IFRS 9 effectiveness test) | 🟡 Nice-to-Have | No hedge designation |
| **Interest Rate Swap (IRS)** | 🟡 Nice-to-Have | Fixed/float leg cashflow schedules |
| **FX Options** | ⚪ Not Required | Advanced derivatives |
| **ISDA / CSA netting** | ⚪ Not Required | Legal/collateral management |

---

## Module 6 — Asset-Liability Management (ALM)

**Status: ❌ 0% Implemented**

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Maturity Ladder / Gap Report** | 🔴 Required | Achievable: `Cashflow` table already has dates + amounts |
| **Interest rate re-pricing gap** | 🟡 Nice-to-Have | Fixed vs floating rate buckets |
| **EVE (Economic Value of Equity)** | 🟡 Nice-to-Have | Needs full balance sheet model |
| **EaR (Earnings at Risk)** | 🟡 Nice-to-Have | Rate shock NII impact |
| **ALCO dashboard endpoint** | 🟡 Nice-to-Have | Summary for Assets-Liabilities Committee |
| **Behavioral modeling** (non-maturing deposits) | ⚪ Not Required | Advanced ALM |
| **Funds Transfer Pricing (FTP)** | ⚪ Not Required | Internal banking allocation |

---

## Module 7 — Regulatory Compliance & Reporting

**Status: ❌ ~5% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| AuditLog model + data capture | `app/models/__init__.py` | Populated throughout codebase |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Audit log query endpoint** (`GET /audit-log`) | 🔴 Required | Model exists; no API to read it |
| **Audit log filtering** (entity, action, user, date) | 🔴 Required | Must be searchable |
| **LCR Report** (Basel III) | 🟡 Nice-to-Have | Needs HQLA classification |
| **NSFR Report** | 🟡 Nice-to-Have | Needs stable funding tagging |
| **Central bank / regulatory returns** | ⚪ Not Required | Jurisdiction-specific |
| **Capital Adequacy / RWA** | ⚪ Not Required | Full Basel III scope |
| **EMIR / Dodd-Frank trade reporting** | ⚪ Not Required | Regulatory jurisdiction specific |

---

## Module 8 — Accounting & GL Integration

**Status: ❌ 0% Implemented**

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **GL Journal Entry generation** | 🟡 Nice-to-Have | Auto double-entry for each deal event |
| **Daily interest accrual engine** | 🟡 Nice-to-Have | Currently only computed at deal creation |
| **Realized P&L GL posting on settlement** | 🟡 Nice-to-Have | Realized P&L not posted anywhere |
| **Chart of Accounts / GL mapping** | 🟡 Nice-to-Have | Deal types → GL account codes |
| **IFRS 9 classification** | ⚪ Not Required | Investment portfolio feature |
| **Month-end revaluation process** | ⚪ Not Required | Enterprise feature |
| **External GL integration** (Finacle, SAP) | ⚪ Not Required | System integration project |

---

## Module 9 — Reporting & Analytics

**Status: ⚠️ 20% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| Deal list with basic filters | `app/api/deals.py` | Type, status, counterparty |
| Currency positions | `app/api/positions.py` | Net per currency |
| Cashflow projections (N-day) | `app/api/positions.py` | No bucketing |
| MTM valuation history | `app/api/valuation.py` | Per deal |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Maturity Ladder / Gap Report** | 🔴 Required | Time-bucketed cashflow summary |
| **Audit log query endpoint** | 🔴 Required | See Module 7 |
| **Deal blotter with pagination** | 🔴 Required | No `skip`/`limit` on deal list |
| **FX P&L report** (realized + unrealized) | 🔴 Required | No aggregate P&L endpoint |
| **Limit utilization summary** | 🔴 Required | All counterparties with % utilization |
| **Cash position dashboard** | 🔴 Required | Aggregated bank account balances |
| **Interest income / cost report** | 🟡 Nice-to-Have | For deposit / loan portfolio |
| **Executive KPI dashboard** endpoint | 🟡 Nice-to-Have | Single `/dashboard` with all KPIs |
| **CSV / Excel export** | 🟡 Nice-to-Have | No export functionality |
| **Counterparty P&L report** | 🟡 Nice-to-Have | Per counterparty trading P&L |

---

## Module 10 — Security & Controls

**Status: ❌ 0% Implemented — 🚨 CRITICAL**

> **CAUTION:** The application has **zero authentication, zero authorization, and zero access control**.
> Any caller can book deals, cancel limits, read all data, and access the AI copilot without any credentials.

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Authentication** (JWT / OAuth2 / API Key) | 🔴 Required | No login, no token validation |
| **User model** (users table) | 🔴 Required | No user entity in database |
| **Role-Based Access Control (RBAC)** | 🔴 Required | Trader, Risk, Ops, ReadOnly roles |
| **Maker-Checker enforcement** | 🔴 Required | 4-eyes principle for deal booking |
| **Password hashing** (bcrypt) | 🔴 Required | No user auth model |
| **Copilot session persistence** in DB | 🔴 Required | In-memory dict; lost on server restart |
| **HTTPS / TLS** | 🔴 Required | Default is HTTP only |
| **Rate limiting** | 🟡 Nice-to-Have | No API throttle |
| **MFA** | ⚪ Not Required | Advanced auth |
| **SSO integration** | ⚪ Not Required | Enterprise identity provider |

---

## Module 11 — Integration & Interoperability

**Status: ⚠️ 15% Implemented**

### ✅ What's Implemented

| Feature | File | Notes |
|---|---|---|
| OpenRouter / LLM API integration | `app/services/copilot_service.py` | Gemini 2.0 Flash via function-calling |
| Manual market rate input | `app/api/market_rates.py` | Upsert via API |

### ❌ What's Missing

| Gap | Priority | Notes |
|---|---|---|
| **Copilot session DB persistence** | 🔴 Required | `_sessions` dict in memory; lost on restart |
| **Live market data feed** (Bloomberg / Reuters) | 🟡 Nice-to-Have | Rates entered manually |
| **Webhook / event notifications** | 🟡 Nice-to-Have | On limit breach, deal settle |
| **Background job scheduler** | 🟡 Nice-to-Have | For MTM, maturity checks, accruals |
| **SWIFT message generation** | ⚪ Not Required | Production settlement |
| **Core banking integration** | ⚪ Not Required | External CBS vendor |

---

## Full Prioritized Gap List

### 🔴 Required — Must Build (19 items)

| # | Gap | Module | Effort |
|---|---|---|---|
| 1 | **Authentication (JWT)** + User model | Security | Medium |
| 2 | **RBAC** (Trader / Risk / Ops / ReadOnly) | Security | Medium |
| 3 | **Maker-Checker** on deal booking | Security + Deal | Medium |
| 4 | **Limit breach hard-block** at deal booking | Risk | Small |
| 5 | **Limit expiry enforcement** | Risk | Small |
| 6 | **FX open position limits** | Risk | Small |
| 7 | **Exposure snapshot API endpoint** | Risk | Small |
| 8 | **Deal Amendment endpoint** | Deal | Small |
| 9 | **Deal date-range filters** | Deal | Small |
| 10 | **FX Swap API route** | FX | Small |
| 11 | **Realized P&L on deal settlement** | FX | Small |
| 12 | **Daily FX P&L report** endpoint | FX + Reporting | Small |
| 13 | **Audit log query endpoint** | Reporting | Small |
| 14 | **Maturity Ladder / Gap Report** | Liquidity + ALM | Medium |
| 15 | **Cash position endpoint** (aggregated) | Liquidity | Small |
| 16 | **Bank balance update on settlement** | Liquidity | Small |
| 17 | **Cashflow time-bucketing** | Liquidity | Small |
| 18 | **Deal blotter with pagination** | Reporting | Small |
| 19 | **Copilot session persistence** in DB | Integration | Small |

---

### 🟡 Nice-to-Have — Build After Core (15 items)

| # | Gap | Module | Effort |
|---|---|---|---|
| 20 | IRS / FRA instrument cashflow logic | Deal | Large |
| 21 | Bond / Fixed Income deal type | Deal | Large |
| 22 | VaR Engine (parametric) | Risk | Large |
| 23 | Stress Testing scenarios | Risk | Large |
| 24 | LCR / NSFR calculation | Liquidity | Large |
| 25 | HTM / AFS / HFT portfolio | Investment | Large |
| 26 | ALCO dashboard endpoint | Risk + ALM | Medium |
| 27 | Hedge management (IFRS 9) | FX | Large |
| 28 | Executive KPI dashboard endpoint | Reporting | Medium |
| 29 | CSV / Excel export | Reporting | Medium |
| 30 | GL journal entry generation | Accounting | Large |
| 31 | Live market data feed integration | Integration | Large |
| 32 | Background job scheduler | Integration | Medium |
| 33 | Webhook notifications | Integration | Medium |
| 34 | Rate limiting on APIs | Security | Small |

---

### ⚪ Not Required — Out of Scope (10 items)

| # | Gap | Reason |
|---|---|---|
| 35 | SWIFT message generation | Needs SWIFT connectivity |
| 36 | Core banking system integration | External CBS vendor |
| 37 | ISDA/CSA collateral management | Advanced legal/collateral |
| 38 | ILAAP / ICAAP regulatory reports | Regulator-specific |
| 39 | Behavioral modeling (deposits) | Advanced ALM |
| 40 | FTP (Funds Transfer Pricing) | Internal banking allocation |
| 41 | SSO / MFA | Enterprise identity mgmt |
| 42 | Capital Adequacy / RWA calculation | Full Basel III scope |
| 43 | EMIR / Dodd-Frank trade reporting | Jurisdiction-specific |
| 44 | External GL integration (SAP, Finacle) | System integration project |

---

## Recommended Implementation Phases

### Phase 1 — Security & Core Fixes (🔴 Required)
Build items #1–19 above:
- JWT authentication + user model
- RBAC roles (Trader, Risk, Ops, ReadOnly)
- Maker-Checker workflow on deals
- Limit enforcement at deal booking
- FX Swap route, deal amendments, date filters
- Audit log endpoint
- Cash position, bank balance on settlement
- Cashflow bucketing, maturity ladder
- Pagination on deal blotter
- Copilot session DB persistence

### Phase 2 — Analytics & Advanced Risk (🟡 Nice-to-Have)
Build items #20–34:
- LCR / NSFR calculation
- VaR engine (parametric)
- ALCO & executive dashboards
- Bond / IRS instruments
- GL journal entries
- Background job scheduler

### Phase 3 — Enterprise Features (⚪ Optional)
Build items #35–44 based on go-live requirements.

---

*Document: `TREASURY_GAP_ANALYSIS.md` | Repo: `C:\ESI Treasury\server`*
