# Setup Guide

> **This file is read by the automated evaluation pipeline. Be precise and complete.**

## Prerequisites

Before you begin, ensure you have the following installed:

- [x] Python 3.12+
- [x] Node.js 18+
- [x] npm or yarn

## Project Structure

```
ship-management/
├── backend/           # Python FastAPI backend
│   ├── app/           # Application source code
│   ├── tests/         # 154 pytest tests
│   ├── requirements.txt
│   └── .venv/         # Virtual environment
├── frontend/          # React + Vite + TypeScript
│   ├── src/           # Source code (pages, components, api)
│   ├── public/        # Static assets
│   ├── package.json
│   └── vite.config.ts
├── docs/              # Documentation
├── demo/              # Demo artifacts
├── presentation/      # Slide deck
└── submission.yaml    # Submission metadata
```

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/vedanttt-dev/ship-management.git
cd ship-management

# 2. Install backend dependencies
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt

# 3. Install frontend dependencies
cd ../frontend
npm install
```

## Running the Application

```bash
# Terminal 1 — Start the backend (from backend/)
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Start the frontend (from frontend/)
cd frontend
npm run dev
```

The application will be available at: **http://localhost:5173**

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

## Running Tests

```bash
# Backend tests (154 tests)
cd backend
python -m pytest tests/ -v
```

## Key Features to Demo

1. **Overview Dashboard** — KPI cards (avg wait, P95, berth util, demurrage)
2. **Scenario Builder** — Generate custom scenarios with presets (Light Traffic, Heavy Surge, etc.)
3. **Prediction** — Queue forecast charts + vessel-level congestion predictions
4. **Optimizer** — Before/after KPI comparison, berth assignment Gantt chart, reroute recommendations
5. **Live Map** — WebSocket-driven vessel position tracking with satellite imagery
6. **What-If Compare** — Side-by-side scenario comparison with delta summary
7. **PDF Report** — One-click executive summary download
8. **Mobile-Friendly** — Responsive layout with hamburger navigation

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Port 8000 in use | Change port: `uvicorn app.main:app --port 8001` |
| WebSocket disconnected | Backend must be running; check `ws://127.0.0.1:8000/api/ws/live` |
| Build fails | Run `npm install` in frontend/ directory |
