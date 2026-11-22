# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI SQL Detective** is an AI-powered PostgreSQL investigation assistant with deterministic AST security (SQLGlot), a LangGraph 7-agent workflow, 100% free-tier LLM architecture with 8-provider failover chain and circuit breaker, and a native FinOps observability module (EvalLaps).

### Core Architecture
- **Backend**: FastAPI modular monolith (Python 3.11+, Pydantic v2, SQLAlchemy 2, Psycopg 3)
- **AI Orchestration**: LangGraph with 7 specialized agents (Schema Analyst → SQL Generator → Query Reviewer → Independent Security Gate → SQL Executor → Result Explainer → Optimization Agent)
- **Security**: 100% deterministic SQLGlot AST validator — never trusts LLM for security
- **LLM Providers**: 8 free-tier providers (Groq, SambaNova, OpenRouter, Google, Cohere, Cloudflare, z.ai, Meta) with intelligent circuit breaker and quota-aware load balancing
- **Database**: PostgreSQL 16 with 3 dedicated roles (migrator, read-only executor, app telemetry)
- **Frontend**: Next.js 15, React 19, TypeScript strict, Tailwind CSS v4, Monaco Editor, Recharts
- **Observability**: EvalLaps — token ledger, savings calculator, quota renewal profiling, circuit breaker HUD

---

## Common Development Commands

### Backend (Python/FastAPI)

```bash
cd backend

# Install dependencies (including dev)
uv sync --extra dev

# Run linting (Ruff)
uv run ruff check .
uv run ruff format --check .

# Run tests
uv run pytest -v                    # All tests
uv run pytest -m "not integration" -v   # Unit tests only (no PG required)
uv run pytest -m integration -v       # Integration tests (requires PG)
uv run pytest tests/path/to/test_file.py::test_name -v  # Single test

# Database operations
uv run alembic upgrade head          # Apply migrations
uv run alembic downgrade base        # Rollback all
uv run alembic revision --autogenerate -m "description"  # New migration
uv run python -m app.modules.database.seed  # Deterministic seed (57,427 rows)

# Run backend server
uv run uvicorn app.main:create_app --factory --reload --port 8000
```

### Frontend (Next.js/React)

```bash
cd frontend

# Install dependencies
npm ci

# Development
npm run dev

# Linting & Type checking
npm run lint
npm run typecheck

# Build
npm run build
npm run start        # Production server

# E2E Tests (Playwright)
npm run test:e2e
```

### Full Stack with Docker

```bash
# Start PostgreSQL only
docker compose up -d --wait postgres

# Full stack (backend + frontend + postgres)
docker compose --profile full up --build

# Stop all
docker compose down -v
```

### CI Pipeline (GitHub Actions)

The CI runs 4 parallel jobs defined in `.github/workflows/ci.yml`:
1. **Backend Lint & Unit Tests** — Ruff + Pytest (unit, security, secrets hygiene)
2. **Backend PostgreSQL 16 Integration** — Ephemeral PG16, migrations up/down/up, seeding, integration tests
3. **Frontend Typecheck, Lint & Build** — `tsc --noEmit`, ESLint, Next.js production build
4. **Playwright E2E** — Full stack startup, critical user journeys

---

## High-Level Architecture

### Backend Module Structure
```
backend/app/
├── main.py                    # FastAPI factory with dependency wiring
├── core/
│   ├── config.py              # Pydantic Settings (all env config, SecretStr, multi-provider keys)
│   ├── logging.py             # Structured logging with SecretRedactingFilter
│   └── exceptions.py          # HTTP error handling
├── api/v1/                    # REST endpoints
│   ├── router.py              # API router aggregation
│   ├── health.py              # /health
│   ├── connections.py         # /connections
│   ├── schema.py              # /schema (PG catalog introspection)
│   ├── queries.py             # /queries (validate, execute, ask, ask/stream)
│   ├── history.py             # /history (audit log)
│   ├── analytics.py           # /analytics (Recharts data)
│   ├── evals.py               # /evals (golden benchmarks)
│   └── evallaps.py            # /evallaps (FinOps observability)
├── modules/
│   ├── ai/
│   │   ├── service.py         # DetectiveWorkflowService (LangGraph orchestration)
│   │   ├── llm.py             # Circuit breaker, quota-aware load balancing, 8-provider chain
│   │   ├── graph.py           # LangGraph state graph definition
│   │   ├── nodes/             # 7 agent node implementations
│   │   │   ├── schema_analyst.py
│   │   │   ├── sql_generator.py
│ │   │   ├── query_reviewer.py
│ │   │   ├── security_gate.py  # Non-LLM, deterministic
│ │   │   ├── sql_executor.py   # Non-LLM, Psycopg 3
│ │   │   ├── result_explainer.py
│ │   │   └── optimization_agent.py
│   │   └── state.py           # Typed LangGraph state
│   ├── security/
│   │   ├── gate.py            # SQLGlot AST validator (THE security boundary)
│   │   ├── policies.py        # Allowlist/denylist constants
│   │   └── types.py           # ValidatedSQL sealed artifact
│   ├── execution/
│   │   └── executor.py        # SQLExecutor (read-only, timeout, LIMIT+1 probe)
│   ├── connections/
│   │   └── registry.py        # Connection pool management
│   ├── database/
│   │   ├── seed.py            # Deterministic synthetic data (57,427 rows)
│   │   └── base.py            # SQLAlchemy engine/session
│   ├── evallaps/              # FinOps observability module
│   │   ├── repository.py      # Token ledger CRUD
│   │   ├── service.py         # Savings calc, renewal profiling, CB HUD
│   │   └── models.py          # Pydantic response models
│   ├── evals/
│   │   └── service.py         # Golden benchmark evaluation
│   ├── history/
│   │   └── repository.py      # Query run audit log
│   └── schema/
│       └── introspection.py   # PG catalog queries
```

### Key Architectural Principles

1. **Modular Monolith** — Clear domain boundaries, explicit internal interfaces, no distributed services
2. **Defense-in-Depth Security** — 5 layers: AST Gate → ValidatedSQL token → PG read-only roles → Timeouts/LIMIT+1 probe → SecretStr + log redaction
3. **100% Deterministic Security** — SQLGlot AST parsing, never LLM judgment
4. **LLM Never Bypasses Security Gate** — Both AI-generated and manual Monaco SQL must pass through `SecurityGate.validate()`
5. **Free-Tier LLM Sovereignty** — Zero OpenAI paid models; OpenAI-compatible HTTP protocol drives all 8 free providers
5. **Circuit Breaker with Quarantine** — Per-key isolation on HTTP 429/401/402, TTL-based auto-recovery
6. **Obsidian Dark Workbench UI** — Strict design tokens (4-tier elevation, WCAG AAA, tabular-nums, Lucide React only)

---

## Security Architecture (Critical)

### Independent Security Gate (`backend/app/modules/security/gate.py`)
The **single source of truth** for SQL safety. Every query passes through `SecurityGate.validate()`:

1. **Parse** — SQLGlot PostgreSQL dialect, rejects unparseable
2. **Single Statement** — Exactly one statement (blocks stacked queries)
3. **Root Allowlist** — Only `SELECT` / read-only `UNION/INTERSECT/EXCEPT`
4. **Forbidden Constructs** — Blocks all DDL/DML/DCL, writable CTEs, locking, admin ops
5. **Function Blocklist** — Blocks `pg_*`, `inet_*`, `txid_*`, `lo_*`, `dblink_*` functions
6. **Schema Isolation** — Tables must be in allowed schemas; blocks cross-catalog refs
7. **LIMIT Enforcement** — Injects or clamps `LIMIT` to ceiling (default 200, hard 1000)
8. **LIMIT+1 Probe** — Executes `LIMIT n+1` to detect exact truncation without false positives

### ValidatedSQL Sealed Artifact (`backend/app/modules/security/types.py`)
`SQLExecutor` **structurally requires** a `ValidatedSQL` instance (minted only by Security Gate). Raw string execution is impossible.

### PostgreSQL Role Isolation
| Role | Purpose | Privileges |
|------|---------|------------|
| `sql_detective_migrator` | Alembic/seed only | Owner of `ecommerce`, `app_meta` schemas |
| `sql_detective_ro` | Query execution | `SELECT` on `ecommerce` only, `default_transaction_read_only = on` |
| `sql_detective_app` | Telemetry | `INSERT/SELECT` on `app_meta.query_runs`, `app_meta.llm_token_ledger` |

---

## LLM Provider Architecture

### Configuration (`.env` / `backend/app/core/config.py`)
```bash
# Primary + Fallback Chain (8 providers)
LLM_PROVIDER=groq
LLM_FALLBACK_CHAIN="groq,sambanova,openrouter,google,cohere,cloudflare,zai,meta"

# Per-provider keys (supports comma-separated pools: GROQ_API_KEYS="k1,k2,k3")
GROQ_API_KEYS="gsk_..."
SAMBANOVA_API_KEYS="..."
OPENROUTER_API_KEYS="sk-or-v1-..."
GOOGLE_API_KEYS="AIzaSy..."
COHERE_API_KEYS="..."
CLOUDFLARE_API_KEYS="..."
ZAI_API_KEYS="..."
META_API_KEYS="..."
```

### Verified Free Models (HTTP 200 Guaranteed)
| Provider | Model | Advantage |
|----------|-------|-----------|
| Groq | `qwen/qwen3.8-27b` | <20ms LPU latency |
| SambaNova | `gemma-4-31B-it` | >440 tok/s |
| OpenRouter | `cognitivecomputations/dolphin3.0-r1-mistral-24b:free` | Distributed free network |
| Google | `gemini-2.5-flash` | Reasoning, large context |
| Cohere | `command-r-plus` | Semantic analysis |
| Cloudflare | `@cf/meta/llama-3.3-70b-instruct` | Edge inference |
| z.ai | `glm-4-flash` | Fast cognitive |
| Meta | `llama-3.3-70b-instruct` | Open-source reference |

### Circuit Breaker (`backend/app/modules/ai/llm.py`)
- **LLMCircuitBreaker**: Per-key quarantine on 429/401/402 (TTL 300s default)
- **QuotaAwareLoadBalancer**: Tracks RPM/TPM/RPD, prefers healthy keys
- **ProviderChainResolver**: Routes through fallback chain transparently
- **Anonymized Fingerprints**: Only last 4 chars stored (e.g., `...y3HA`)

---

## EvalLaps FinOps Module

Located at `backend/app/modules/evallaps/` — native LLMOps/FinOps observability:

### Token Ledger (`app_meta.llm_token_ledger`)
Every cognitive call (5 agents) logs async:
- `run_id`, `stage_id`, `provider_name`, `key_fingerprint`
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `estimated_savings_usd` (vs GPT-4o baseline: $2.50/1M input + $10/1M output)
- `latency_ms`, `http_status`

### Quota Renewal Profiles (4 Types)
1. **Sliding Window 1m** — Groq, SambaNova, Meta (continuous 60s reset)
2. **Rolling Daily 24h** — Google, Cloudflare, OpenRouter (UTC 00:00 reset)
3. **Monthly Credits** — Cohere (1st of month)
4. **Static Tier** — z.ai (fixed volume, no auto-recharge)

### Dashboard (`/evallaps` UI)
- KPI cards: Total tokens, queries, savings USD
- Stacked token breakdown by agent (Recharts)
- Provider catalog with renewal profiles
- Circuit Breaker HUD: Live quarantines, TTL countdowns, active fallback chain

---

## Frontend Architecture

### Stack
- Next.js 15 App Router, React 19, TypeScript strict
- Tailwind CSS v4 with CSS variables for design tokens
- TanStack Query v5 for server state
- Monaco Editor with custom `ai-sql-detective-dark` theme
- Recharts for all 5 dashboard visualizations
- Lucide React icons only (16px standard, 1.5px stroke)

### Key Pages/Components
| Route | Purpose |
|-------|---------|
| `/` | Workbench: Schema Explorer, NL Composer, Monaco Editor, Results Grid, Security Panel, Optimization Panel |
| `/evallaps` | FinOps Dashboard: KPIs, token breakdown, renewal catalog, CB HUD |
| `/analytics` | Latency trends, status donut, activity area, comparisons, table stats |
| `/history` | Paginated audit log, reload via `?runId=` |
| `/evals` | Golden benchmark evaluation |

### Design Tokens (Obsidian Dark)
```css
/* Canvas → Surface → Card → Hover */
--bg-canvas: #070A12;
--bg-surface: #0D121F;
--bg-card: #131B2E;
--bg-card-hover: #1A243D;
--border-subtle: #1E2B45;
--border-interactive: #3B82F6;
--accent-primary: #6366F1;   /* Electric Indigo */
--accent-secondary: #06B6D4; /* Electric Cyan */
--status-success: #10B981;
--status-warning: #F59E0B;
--status-error: #F43F5E;
--text-primary: #F8FAFC;
--text-secondary: #94A3B8;
--text-muted: #64748B;
```

### Mandatory Rules
- `font-variant-numeric: tabular-nums` on ALL numeric metrics
- Zero emojis in chrome/navigation/badges
- Zero hardcoded hex — use Tailwind/CSS tokens only
- Border radius: `rounded-lg` (8px) cards, `rounded-md` (6px) buttons, `rounded-sm` (4px) micro
- Transitions: 150-200ms, `cubic-bezier(0.16, 1, 0.3, 1)`

---

## Database & Migrations

### Schemas
- **ecommerce** — 9 tables: `customers`, `orders`, `products`, `order_items`, `inventory`, `payments`, `reviews`, `categories`, `addresses` (57,427 deterministic rows)
- **app_meta** — `query_runs` (audit), `llm_token_ledger` (FinOps)

### Alembic Migrations
```
0001_initial_schema.py      # ecommerce + app_meta schemas, tables, indexes
0002_add_roles_rls.py       # PostgreSQL roles, RLS policies, grants
0003_add_llm_token_ledger.py # FinOps token ledger table
```

### Seeding
```bash
uv run python -m app.modules.database.seed
```
Deterministic synthetic data (fixed seed) — 57,427 rows reproducible across environments.

---

## Testing Strategy

### Backend (Pytest)
- **Unit** (`-m "not integration"`): Services, SQLGlot rules, circuit breaker, EvalLaps logic, secrets hygiene — no PG needed
- **Integration** (`-m integration`): Requires live PostgreSQL 16 — role isolation, executor, schema introspection, full workflow
- **Adversarial Security**: SQL injection, DDL/DML payloads, CTE modification, stacked queries, prompt injection attempts

### Frontend
- **TypeScript**: `npm run typecheck` (strict mode)
- **ESLint**: `npm run lint` (Next.js config)
- **Build**: `npm run build` (production verification)
- **E2E Playwright**: Critical journeys — schema browse, NL query, security rejection, SQL execution, results, optimization, SSE streaming

---

## Environment Configuration

### Root `.env` (Never Committed)
```ini
# PostgreSQL
POSTGRES_DB=ai_sql_detective
POSTGRES_USER=postgres
POSTGRES_PASSWORD=...
POSTGRES_PORT=5434  # Avoids conflict with local PG on 5432/5433

PG_MIGRATOR_USER=sql_detective_migrator
PG_MIGRATOR_PASSWORD=...
PG_RO_USER=sql_detective_ro
PG_RO_PASSWORD=...
PG_APP_USER=sql_detective_app
PG_APP_PASSWORD=...

# Backend DSNs (SQLAlchemy +psycopg format)
DATABASE_RO_URL=postgresql+psycopg://sql_detective_ro:...@localhost:5434/ai_sql_detective
DATABASE_APP_URL=postgresql+psycopg://sql_detective_app:...@localhost:5434/ai_sql_detective
DATABASE_MIGRATOR_URL=postgresql+psycopg://sql_detective_migrator:...@localhost:5434/ai_sql_detective

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# LLM (100% Free-Tier)
LLM_PROVIDER=groq
LLM_FALLBACK_CHAIN="groq,sambanova,openrouter,google,cohere,cloudflare,zai,meta"
GROQ_API_KEYS="gsk_..."
# ... other provider keys
```

### Configuration Loading
- `backend/app/core/config.py` — `Settings` class with `pydantic-settings`
- `ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"` — always loads from repo root
- `SecretStr` for all credentials — never leaked in logs/errors
- Startup validation via `load_settings()` — clear errors without exposing values
- Frontend receives **only** `NEXT_PUBLIC_API_BASE_URL` — zero secrets in browser

---

## Key Files to Reference

| File | Purpose |
|------|---------|
| `.agent/roles.md` | Authoritative engineering config: 10 roles, security policy, UI design system, AI agent definitions, implementation approval rules |
| `README.md` | Complete project docs: architecture, API spec, deployment, stack |
| `backend/app/main.py` | FastAPI factory, dependency wiring |
| `backend/app/core/config.py` | All configuration, multi-provider key management, SecretStr |
| `backend/app/modules/security/gate.py` | **The security boundary** — SQLGlot AST validator |
| `backend/app/modules/ai/llm.py` | Circuit breaker, quota-aware load balancing, provider chain |
| `backend/app/modules/ai/graph.py` | LangGraph 7-agent workflow topology |
| `backend/app/modules/evallaps/service.py` | FinOps calculations, renewal profiling, CB HUD |
| `docker-compose.yml` | PG16, backend, frontend with health checks |
| `.github/workflows/ci.yml` | 4-job CI pipeline |
| `frontend/package.json` | Next.js 15, React 19, Tailwind v4, Recharts, Monaco, Playwright |

---

## Implementation Approval Rule (from `.agent/roles.md`)

**Before ANY implementation, you MUST:**
1. Inspect the repository (structure, config, current state)
2. Analyze architecture fit (modular monolith, LangGraph, security boundaries, UI system)
3. Identify ambiguities (missing requirements, edge cases, schema assumptions)
4. Propose implementation plan (exact files, modules, migrations, tests, verification)
5. Explain technical decisions and trade-offs
6. **Wait for explicit user approval** ("OK", "Go", "Proceed")

**Hard Constraint:** Do NOT install dependencies, create database infrastructure, scaffold code, or implement features before approval.

---

## Common Pitfalls to Avoid

1. **Never bypass Security Gate** — All SQL (AI or manual) must pass `SecurityGate.validate()`
2. **Never use `EXPLAIN ANALYZE`** — Only `EXPLAIN (FORMAT JSON)` for plan inspection
3. **Never hardcode secrets** — All credentials via `SecretStr` in `.env`
4. **Never put DB credentials in frontend** — Only `NEXT_PUBLIC_API_BASE_URL`
5. **Never use `if/else` for intent/classification** — Delegate to LLM agents (per Architecture Policy §10)
6. **Never skip `tabular-nums`** on numeric displays
7. **Never use non-Lucide icons** or non-Recharts visualizations
8. **Never commit `.env`** — Only `.env.example` with placeholders

---

## Quick Reference: Running Locally

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your keys (at minimum GROQ_API_KEYS)

# 2. Start PostgreSQL
docker compose up -d --wait postgres

# 3. Backend setup
cd backend
uv sync --extra dev
uv run alembic upgrade head
uv run python -m app.modules.database.seed

# 4. Run backend (Terminal 1)
uv run uvicorn app.main:create_app --factory --reload --port 8000

# 5. Run frontend (Terminal 2)
cd ../frontend
npm ci
npm run dev

# 6. Access
# Workbench: http://localhost:3000
# EvalLaps: http://localhost:3000/evallaps
# API Docs: http://localhost:8000/docs
```