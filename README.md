# 🚢 Container Congestion Predictor & Port Operations Optimiser

Hackathon solution that predicts port congestion hotspots **before** queues form,
recommends alternate routing, optimises berth + crane assignments, and generates a
**72-hour port operations plan** for shift supervisors — with a live "Mission Control"
map of every vessel in the port.

> 📋 Full roadmap, architecture, data model and API contract: [`plan.md`](./plan.md)

## Quickstart

### Backend (Python 3.12 + FastAPI)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# health → http://127.0.0.1:8000/api/health · interactive docs → /docs
```

### Frontend (React 18 + Vite + TypeScript + Tailwind)

```powershell
cd frontend
npm install
npm run dev
# app → http://localhost:5173  (proxies /api/* to the backend on :8000)
```

## Stack

| Layer | Tech |
|---|---|
| Simulation | simpy (discrete-event simulation) |
| Optimisation | Google OR-Tools CP-SAT |
| API | FastAPI + Pydantic |
| UI | React + Vite + TS + Tailwind · MapLibre GL (live map) |

## Roadmap status

- [x] P0/P1 — plan approved + repo scaffold
- [ ] P2–P13 — data generator → baseline sim → API → prediction → optimiser → rerouting → shift plan → dashboard → live map → evaluation (see `plan.md` §6)
