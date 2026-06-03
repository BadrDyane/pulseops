# PulseOps — LLM Observability & Monitoring Platform

> Drop-in observability for production LLM applications. Log every call, track every dollar, catch every regression — before your users do.

---

## What It Does

PulseOps gives engineering teams full visibility into their LLM stack:

- **5-line SDK integration** — wrap your OpenAI client, everything is captured automatically
- **Real-time dashboard** — live token spend, latency percentiles, error rates per feature and tenant
- **Cost attribution** — break down spending by feature, model, and customer
- **Eval framework** — define assertions on outputs, get automatic regression alerts when quality drops
- **Replay engine** — re-run any historical prompt against any model, compare cost and quality side by side
- **Drift detection** — automatic alerts when output distribution shifts
- **Cost forecasting** — projected monthly spend based on current trajectory

---

## Tech Stack

**Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 15, Alembic, APScheduler  
**Frontend:** React 18, Vite, Recharts, pure CSS variables  
**SDK:** Python 3.11, httpx (zero hard dependencies beyond httpx + pydantic)  
**Infrastructure:** Docker, Railway (backend), Vercel (frontend)

---

## Project Structure
pulseops/
├── sdk/          # Installable Python SDK (pip install)
├── backend/      # FastAPI platform (ingestion, analytics, evals, replay)
└── frontend/     # React dashboard

---

## Quick Start (Local)

**Prerequisites:** Python 3.11, Node.js 18+, Docker Desktop

```powershell
# 1. Start Postgres
cd backend
docker compose up -d postgres

# 2. Install backend dependencies
py -3.11 -m pip install -r requirements.txt

# 3. Run migrations (Phase 1+)
py -3.11 -m alembic upgrade head

# 4. Start backend
py -3.11 -m uvicorn app.main:app --reload --port 8000

# 5. Start frontend (new terminal)
cd ..\frontend
npm install
npm run dev
```

Backend runs on `http://localhost:8000`  
Frontend runs on `http://localhost:5173`  
API docs at `http://localhost:8000/docs`

---

## SDK Usage

```python
from pulseops import PulseOps
import openai

po = PulseOps(api_key="po_proj_...")
client = po.wrap(openai.OpenAI())

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    pulseops_tags={
        "feature": "ticket_classifier",
        "tenant_id": "acme-corp"
    }
)
```

Every call is automatically logged — latency, tokens, cost, prompt, response.

---

## Build Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Scaffolding + Infrastructure + Hello World | ✅ Complete |
| 1 | Database Schema + Migrations + Project/API Key Management | 🔄 In Progress |
| 2 | SDK Core: Wrapping, Interception, Batching, Flush | ⏳ Pending |
| 3 | Ingestion API: Receive, Validate, Enrich, Persist | ⏳ Pending |
| 4 | Event Explorer: Query API + Frontend Table | ⏳ Pending |
| 5 | Real-Time Dashboard: WebSocket + Charts | ⏳ Pending |
| 6 | Eval Framework: Definitions + Runner + Results | ⏳ Pending |
| 7 | LLM-Judge Evals + Prompt Version Tracking | ⏳ Pending |
| 8 | Replay Engine: Side-by-Side Comparison | ⏳ Pending |
| 9 | Drift Detection + Cost Forecasting + Alerts | ⏳ Pending |
| 10 | Deployment + SDK GitHub Release + Demo Polish | ⏳ Pending |

---

## Portfolio Context

Built as a production-grade portfolio project demonstrating:
SDK design, time-series data engineering, real-time systems, multi-tenant architecture, LLM operations vocabulary, and production engineering depth.