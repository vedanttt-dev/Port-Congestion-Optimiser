# Container Congestion Predictor & Port Operations Optimiser

> A full-stack AI-powered dashboard that predicts port congestion, optimises berth/crane assignments via CP-SAT, and generates 72-hour shift plans — with live WebSocket simulation streaming.

---

## Team

| Field | Value |
|---|---|
| **Team Name** | Infinite Loop |
| **Track** | AI |
| **Team Lead** | Prajapati Vedant — 26msit122@charusat.edu.in |
| **Members** | Rana Harsh (26msit127@charusat.edu.in), Savaliya Harshit (26msit134@charusat.edu.in), Patel Manav (26msit099@charusat.edu.in) |

---

## Problem Statement

> Container ports worldwide face increasing congestion, costing the shipping industry $10B+ annually in demurrage fees. Port operations teams rely on manual spreadsheets and first-come-first-served scheduling, failing to optimise berth allocation, crane deployment, or predict congestion before it cascades into costly delays.

---

## Solution

> A full-stack web application combining discrete event simulation, CP-SAT constraint optimization, Monte Carlo forward prediction, and 72-hour shift planning into a single tablet-friendly dashboard. Port managers can run what-if scenarios, compare infrastructure investments, and download professional PDF reports — all in real-time via WebSocket streaming.

---

## Key Features

- **CP-SAT Optimization:** Berth & crane assignment reducing wait times by 20-40% vs FCFS baseline
- **Congestion Prediction:** Monte Carlo forward simulation with vessel-level forecasts and hotspot detection
- **Scenario Builder:** 5 presets (Light Traffic, Heavy Surge, Crane Shortage, etc.) + custom parameters
- **What-If Comparison:** Side-by-side scenario comparison with KPI deltas and grouped bar charts
- **Live Simulation:** Real-time WebSocket streaming with satellite vessel map and transport controls
- **72-Hour Shift Plan:** Automated work order generation with contingency notes
- **Mobile-Friendly:** Responsive layout with hamburger navigation for tablet demos

---

## Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.12, TypeScript |
| **Frameworks** | FastAPI, React 18, Vite, Tailwind CSS |
| **AI / Optimization** | Google OR-Tools (CP-SAT), SimPy (DES), Monte Carlo Simulation |
| **Visualization** | Recharts, MapLibre GL, Lucide React |
| **Other** | WebSocket, ReportLab (PDF), GitHub Actions |

---

## Repository Structure

```
├── backend/                # Python FastAPI backend
│   ├── app/                # Application source code
│   │   ├── routers/        # 12 API endpoints + WebSocket
│   │   ├── services/       # Scenario management
│   │   ├── simulation/     # SimPy DES engine + KPI
│   │   ├── optimization/   # CP-SAT solver + rerouting
│   │   ├── prediction/     # Forward simulator + hotspots
│   │   └── planning/       # 72-hour shift builder
│   ├── tests/              # 154 pytest tests
│   └── requirements.txt
├── frontend/               # React + Vite + TypeScript
│   ├── src/
│   │   ├── pages/          # 8 page components
│   │   ├── components/     # Layout, Sidebar, PortMap, etc.
│   │   └── api.ts          # Typed API client
│   ├── public/             # Static assets
│   └── package.json
├── docs/                   # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                   # Demo artifacts
│   ├── screenshots/        # App screenshots
│   └── demo-video-link.txt
├── presentation/           # Slide deck
└── submission.yaml         # Structured submission metadata
```

---

## How to Run

> **See [`docs/setup-guide.md`](docs/setup-guide.md) for detailed instructions.**

```bash
# 1. Clone the repo
git clone https://github.com/vedanttt-dev/bob-ai-hackathon-Infinite-loop.git
cd bob-ai-hackathon-Infinite-loop

# 2. Install backend dependencies
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Install frontend dependencies
cd ../frontend
npm install

# 4. Start the backend (Terminal 1)
cd backend
uvicorn app.main:app --reload --port 8000

# 5. Start the frontend (Terminal 2)
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Demo

| Artifact | Link |
|---|---|
| Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| Live Demo | [port-optimizer.vercel.app](https://port-optimizer.vercel.app) |
| Screenshots | [See demo/screenshots/](demo/screenshots/) |
| Presentation | [See presentation/](presentation/) |

---

## Known Limitations

- All data is synthetic/simulated — no real port data
- Vessel map uses simplified lat/lon coordinates

---

## What We're Most Proud Of

The integrated optimization pipeline — from scenario generation through DES simulation, CP-SAT solving, reroute recommendations, and shift planning — all computed in under 2 seconds and presented in a polished dashboard with live WebSocket streaming. The what-if comparison engine lets managers evaluate infrastructure investments interactively.

---

## Tests

```bash
cd backend
python -m pytest tests/ -v
# 154 tests passing
```
