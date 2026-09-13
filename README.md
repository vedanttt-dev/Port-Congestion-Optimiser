# Container Congestion Predictor & Port Operations Optimiser

Hackathon solution that predicts port congestion hotspots **before** queues form,
recommends alternate routing, optimises berth + crane assignments via CP-SAT, and
generates a **72-hour port operations plan** for shift supervisors — with a live
"Mission Control" dashboard.

> Full roadmap, architecture, data model and API contract: [`plan.md`](./plan.md)

## Results

| Metric | Baseline (FCFS) | Optimised (CP-SAT) | Change |
|---|---|---|---|
| Avg Wait | 18.3 h | 2.7 h | **-85%** |
| P95 Wait | 134.0 h | 4.9 h | **-96%** |
| Demurrage Cost | $1,411,833 | $210,503 | **-85%** |
| **Total Savings** | | | **$1,201,331** |

- 91 vessel assignments across 8 berths (CP-SAT, 26ms solve time)
- 3 hotspots detected with lead times for proactive response
- 9 shift blocks with 21 work orders for 72-hour operations plan

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React + Vite Frontend                  │
│  Overview │ Data │ Predict │ Optimise │ Plan │ Live Map  │
└──────────┬──────────────────────────────────────────────┘
           │ /api/* (Vite proxy)
┌──────────▼──────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  /data/summary  /predict  /optimize  /plan  /live  /kpis│
│  /export/data   /export/predict  /export/optimize        │
│  /export/plan   /export/report                          │
└──────────┬──────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────┐
│                   Engine Layer                           │
│  Synthetic Generator → DES Simulation (simpy)            │
│  → Forward Predictor → Hotspot Detector                  │
│  → CP-SAT Optimiser → Rerouting Recommender              │
│  → 72h Shift Plan Builder                                │
└─────────────────────────────────────────────────────────┘
```

## Quickstart

### Backend (Python 3.12 + FastAPI)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# health → http://127.0.0.1:8000/api/health
# docs   → http://127.0.0.1:8000/docs
```

### Frontend (React 18 + Vite + TypeScript + Tailwind)

```powershell
cd frontend
npm install
npm run dev
# app → http://localhost:5173 (proxies /api/* to backend on :8000)
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/data/summary` | Scenario data (vessels, berths, cranes, yard, alt ports) |
| POST | `/api/predict` | 7-day congestion prediction with hotspot detection |
| POST | `/api/optimize` | CP-SAT berth+crane optimiser + reroute recommendations |
| POST | `/api/plan` | 72-hour shift plan (9 blocks, work orders, contingencies) |
| GET | `/api/kpis` | Key performance indicators |
| GET | `/api/live` | Live port status (polling) |
| GET | `/api/export/data` | CSV export — vessels |
| GET | `/api/export/predict` | CSV export — predictions |
| GET | `/api/export/optimize` | CSV export — optimiser results |
| GET | `/api/export/plan` | CSV export — shift plan |
| GET | `/api/export/report` | Full text report |

## Stack

| Layer | Tech |
|---|---|
| Simulation | simpy (discrete-event simulation) |
| Optimisation | Google OR-Tools CP-SAT |
| Prediction | Forward simulation + hotspot rules |
| API | FastAPI + Pydantic |
| Frontend | React 18 + Vite + TypeScript + Tailwind |
| Charts | Recharts |

## Project Structure

```
ship-management/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Settings
│   │   ├── schemas.py              # Pydantic request/response models
│   │   ├── domain/entities.py      # 10 dataclasses (Vessel, Berth, Crane, etc.)
│   │   ├── data/generator.py       # Synthetic scenario generator
│   │   ├── simulation/
│   │   │   ├── engine.py           # simpy DES engine
│   │   │   └── kpi.py              # KPI computation + CSV export
│   │   ├── prediction/
│   │   │   ├── forecaster.py       # Forward simulation predictor
│   │   │   └── hotspots.py         # Hotspot detection rules
│   │   ├── optimization/
│   │   │   ├── solver.py           # CP-SAT berth+crane optimiser
│   │   │   └── rerouting.py        # Rerouting recommender
│   │   ├── planning/shift_plan.py  # 72h shift builder
│   │   ├── routers/                # 8 API routers (data, predict, optimize, etc.)
│   │   └── services/scenario.py    # Singleton scenario service
│   ├── tests/                      # 154 tests
│   └── scripts/
│       ├── generate_data.py        # CLI: generate synthetic data
│       ├── run_baseline.py         # CLI: run baseline FCFS sim
│       └── evaluate.py             # CLI: full evaluation report
├── frontend/
│   ├── src/
│   │   ├── api.ts                  # Typed API client
│   │   ├── components/             # Layout, Header, Sidebar, StatusBadge
│   │   └── pages/                  # 6 screens (Overview, Data, Predict, etc.)
│   └── vite.config.ts              # Vite proxy to backend
├── plan.md                         # Full 13-phase roadmap
└── README.md
```

## How It Works

1. **Generate** — Synthetic vessel arrivals, berths, cranes, yard zones, alt ports
2. **Simulate** — Baseline FCFS simulation computes anchor wait, berth util, demurrage
3. **Predict** — Forward 7-day simulation detects congestion hotspots with lead times
4. **Optimise** — CP-SAT solver assigns vessels to berths, minimising total wait
5. **Reroute** — Cost model recommends alt-port diversion when waiting > divert cost
6. **Plan** — 72h shift plan with 9 blocks, work orders, alerts, contingency notes
7. **Export** — CSV/text download from every screen
