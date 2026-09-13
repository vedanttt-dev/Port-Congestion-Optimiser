# Container Congestion Predictor & Port Operations Optimiser

> **Project plan — `plan.md`**
> Repository: `d:\ship-managment`
> Stack: Python 3.12 (FastAPI) backend · React 18 + Vite + TypeScript frontend
> Status: v1.0 — project kickoff
> Horizon: hackathon build (see §6 for phase estimates)

---

## 1. Problem Overview

**Context.** In 2021 the LA/Long Beach port complex had 100+ container ships waiting
offshore for weeks, disrupting global supply chains at an estimated **$10B+ cost**.
Port operators allocate **berths, cranes, and yard space** across hundreds of vessels
**manually in spreadsheets**. Congestion hotspots are identified **reactively** — after
vessels are already queuing — and alternate routing decisions come **too late** to help.

**Pain points in today's workflow**

1. Spreadsheet-driven berth/crane/yard allocation — no optimization, first-come-first-served (FCFS) behaviour.
2. Congestion detected only after queues form (reactive, zero lead time).
3. Rerouting decisions arrive after the queue is already built up.

**Challenge deliverables (verbatim from the problem statement)**

| # | Deliverable | Our module |
|---|---|---|
| 1 | **Predict congestion hotspots** using vessel schedules + berth capacity data | Prediction engine (§3.3) |
| 2 | **Recommend alternate routing strategies** | Rerouting recommender (§3.5) |
| 3 | **Optimise berth and crane assignments** | CP-SAT optimizer (§3.4) |
| 4 | **Generate a 72-hour port operations plan** for shift supervisors | Shift planner (§3.6) |

**Goal.** A working web product: `data → prediction → optimization → 72h plan`,
with a measurable before/after improvement over the spreadsheet (FCFS) baseline,
demoable end-to-end in a browser.

---

## 2. Domain Analysis — where this sits in ship management

This problem is the **port-side (container terminal operations) slice of ship
management / maritime logistics**:

| Problem-statement term | Maritime / Operations-Research domain |
|---|---|
| Vessel schedules | Ship arrival planning; ETA/ETD, voyage data |
| Berth capacity | **Berth Allocation Problem (BAP)** |
| Crane assignments | **Quay Crane Assignment/Scheduling (QCAP/QCSP)** |
| Yard space | Container yard / storage planning |
| Ships waiting offshore | Anchorage queueing (queueing theory, discrete-event simulation) |
| Alternate routing | Vessel diversion to alternate ports; slow steaming / virtual arrival |
| 72-hour operations plan | Shift scheduling / terminal operating system (TOS) output |

**Scope decisions**

- We model **one primary container terminal + its anchorage**, with **alternate ports** available for diversion.
- **In scope:** vessel arrival, anchorage queueing, berthing, crane work, yard constraints, departure, diversion.
- **Out of scope:** fleet management (cargo holds, engine ops), customs, trucking/drayage, gate ops, billing.

---

## 3. Solution Architecture

```
                ┌────────────────────────────────────────────────────────────┐
                │                     BACKEND (FastAPI)                      │
                │                                                            │
 synthetic ───► │  [3.1 Data generator] ──► [3.2 DES simulator (simpy)]      │
 data (vessels, │        vessels/berths/       │  baseline FCFS policy       │
 berths, cranes,│        cranes/ports          ▼  → KPIs                     │
 alt ports)     │                            [3.3 Prediction engine]         │
                │                              forward sim → forecasts       │
                │                              → hotspot alerts (lead time)  │
                │                                │                           │
                │                                ▼                           │
                │  [3.4 Optimizer: CP-SAT berth + crane assignment]          │
                │  [3.5 Rerouting recommender: wait-cost vs divert-cost]     │
                │                                │                           │
                │                                ▼                           │
                │  [3.6 72h shift planner → 9 shift blocks + work orders]    │
                └──────────────────────┬─────────────────────────────────────┘
                                       │ REST /api/* · WS /api/ws/live
                ┌──────────────────────▼─────────────────────────────────────┐
                │                  FRONTEND (React + Vite + TS)              │
                │  Overview KPIs · congestion heatmap · berth Gantt          │
                │  vessel queue + reroute badges · 72h shift plan            │
                │  before/after compare · what-if sliders                    │
                │  LIVE vessel map · SVG ships · speed 1×–100× · ticker      │
                └────────────────────────────────────────────────────────────┘
```

| # | Component | Responsibility |
|---|---|---|
| 3.1 | **Data layer** | Synthetic generator producing realistic vessel schedules, berth/crane capacities, yard, alternate ports (challenge provides no dataset) |
| 3.2 | **Simulation engine** | simpy discrete-event simulation; **FCFS baseline policy** reproduces the "spreadsheet" status quo and produces KPIs |
| 3.3 | **Prediction engine** | Forward simulation from "now" using schedule + current queue → per-vessel predicted wait, berth/yard utilization forecast, **hotspot alerts with lead time** |
| 3.4 | **Optimizer** | OR-Tools **CP-SAT** model for berth allocation + crane assignment, minimizing weighted waiting/turnaround |
| 3.5 | **Rerouting recommender** | Cost model comparing *waiting at current port* vs *diverting to alternate port*; outputs diversion set + $ saved |
| 3.6 | **Shift planner** | Converts optimized schedule into **9 shift blocks** (3 shifts × 3 days) with per-shift work orders, alerts, contingency notes |
| 3.7 | **API + UI** | FastAPI REST endpoints + WebSocket live feed; React dashboard, 6 screens + what-if controls |
| 3.8 | **Live map feed** | Derives vessel trajectories from the sim timeline (inbound → anchorage → berth → outbound); serves position snapshots for map animation at 1×–100× speed; renders top-down SVG ships with wake trails + 3D-lite depth |

---

## 4. Data Model

All times are **simulation hours**; clocks start at `as_of_h = 0` (now).
Prediction horizon = 168 h (7 days); planning window = 72 h; shift length = 8 h.

| Entity | Fields |
|---|---|
| **Vessel** | `id, name, type(feeder/medium/mega), teu_capacity, import_moves, export_moves, loa_m, draft_m, eta_h, planned_etd_h, origin, destination, priority_class(1=high), demurrage_usd_per_day` |
| **Berth** | `id, length_m, max_draft_m, crane_ids[], base_moves_per_hr, yard_zone_id, status(idle/occupied/maintenance)` |
| **Crane** | `id, max_moves_per_hr, compatible_berths[], maintenance_window(optional)` |
| **YardZone** | `id, teu_capacity, current_teu, avg_dwell_days` |
| **AltPort** | `id, name, transit_hours, berth_capacity, handling_premium_usd, congestion_index` |
| **ScheduleEntry** | `vessel_id, berth_id, start_h, end_h, crane_count, moves_planned` |
| **ShiftBlock** | `day(1–3), shift_no(1–3), start_h, end_h` (9 blocks over 72 h) |
| **WorkOrder** | `shift_id, vessel_id, berth_id, crane_ids[], target_moves, priority, alert, contingency_note` |
| **HotspotAlert** | `id, kind(berth_util/queue/wait/yard), horizon_h, severity(low/med/high), affected_berths[], affected_vessels[], lead_time_h, message` |
| **KpiSnapshot** | `avg_wait_h, p95_wait_h, max_queue, berth_util_pct, crane_util_pct, yard_util_pct, demurrage_cost_usd, hotspot_count, cost_saved_usd` |

### Synthetic data design (P2)

- **Vessels:** Poisson-ish arrivals (~25–40 arrivals/week), 3 classes: feeder (≈1.5k TEU), medium (≈8k TEU), mega (≈18–24k TEU); moves = import+export container moves; priority 1 for reefer/urgent cargo.
- **Terminal:** 8 berths (lengths 250–400 m), 22–28 quay cranes (30–35 moves/hr), 2 yard zones.
- **Alternate ports:** 2 ports (transit 12 h / 24 h), limited berth capacity → diversion is a scarce resource.
- **Validation:** ranges sanity-checked against public terminal benchmarks.

---

## 5. Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | best ecosystem for sim + OR; verified installed |
| API | **FastAPI + Pydantic + Uvicorn** | typed REST, auto OpenAPI docs, fast dev |
| Simulation | **simpy** | clean discrete-event simulation for queues/berthing |
| Optimization | **Google OR-Tools CP-SAT** | industrial solver; BAP+QCAP for 100s of vessels in seconds |
| Data | pandas, numpy | tables, aggregation, KPI math |
| Frontend | **React 18 + Vite + TypeScript** (node v22 verified) | custom product look, typed API client |
| Styling | Tailwind CSS | fast, consistent UI |
| Charts | Recharts + custom SVG Gantt | heatmap / bar / gantt |
| Live map | **MapLibre GL JS** + react-map-gl (free OSM tiles) | animated real-map vessel tracking, no API key |
| 3D layer (optional) | three.js custom layer + CC0 glTF ship models (poly.pizza / Sketchfab) | toggleable 3D hero ships (stretch) |
| Testing/QA | pytest, ruff | unit tests, linting |

**Explicitly not on the critical path:** ML surrogate predictor (XGBoost) on simulation
outputs — optional stretch goal; simulation + rules already give interpretable,
explainable predictions (better for judges).

---

## 6. Roadmap — Step-by-Step

> Single-dev total ≈ **31–33 h**; parallelizable to **~15–17 h wall-clock** for a team of 4.
> Every phase ends with a **verifiable exit criterion**.

### P0 — Frame the problem & acceptance criteria — `0.5 h`
- Tasks: freeze scope (§2), define KPI definitions (§9), define "done".
- **Exit:** this `plan.md` approved; KPI table signed off.

### P1 — Repo scaffold — `0.75 h`
- Tasks: `git init`; `backend/` (venv, `requirements.txt`: fastapi, uvicorn, simpy, ortools, pandas, numpy, pydantic, pytest); FastAPI hello + CORS; `frontend/` (Vite react-ts template, Tailwind init); `.gitignore`; README stub.
- **Exit:** `uvicorn app.main:app` serves `GET /api/health`; `npm run dev` shows app shell.

### P2 — Data generator + domain entities — `2 h`
- Tasks: `domain/entities.py` (dataclasses); `data/generator.py` (vessels/berths/cranes/yard/ports per §4); validation ranges; save JSON/CSV under `data/`.
- **Exit:** `python scripts/generate_data.py` writes dataset; unit tests on ranges pass.

### P3 — Baseline DES simulator (FCFS) — `2.5 h`
- Tasks: simpy engine: `arrival → anchorage queue → berth assign (FCFS) → crane work → yard check → departure`; event logging; KPI computation; CSV outputs; seed control.
- **Exit:** baseline KPI report for default scenario reproduces "congested port" behaviour.

### P4 — FastAPI core (schemas + routers) — `2 h`
- Tasks: pydantic schemas (§7); routers `/api/data/summary`, `/api/predict`, `/api/optimize`, `/api/plan`, `/api/kpis`, `/api/live` (stub → real); CORS + Vite dev proxy; error handling.
- **Exit:** Swagger UI lists endpoints; frontend calls `/api/data/summary` successfully.

### P5 — Prediction engine + hotspot rules — `2.5 h`
- Tasks: forward sim from `as_of_h` using planned arrivals + current queue; per-vessel predicted wait; berth/yard utilization forecast in 4 h buckets; hotspot rules: `berth_util > 90%`, `queue > N`, `predicted_wait > X h`, `yard > 85%`; severity + `lead_time_h`.
- **Exit:** `/api/predict` returns forecasts + hotspot list with lead times ≥ 12 h.

### P6 — Berth + crane optimizer (CP-SAT) — `4 h`
- Tasks: decision vars `berth[v,b,t]` (1 h buckets) + `cranes[v,t]`; constraints: berth eligibility (LOA/draft), one berth per vessel, crane capacity per berth, yard limits, ETA release, priority weighting; objective: minimize Σ wait·priority + changeover penalty; rolling horizon; solve < 2 s.
- **Exit:** `/api/optimize` returns assignments; **avg wait reduction vs FCFS ≥ 30%** (target) on default scenario.

### P7 — Rerouting recommender — `2 h`
- Tasks: cost model `wait_cost(v) = demurrage·wait + schedule_slippage` vs `divert_cost(v) = fuel + transit + premium + alt_port_congestion`; choose diversion set under alt-port capacity limits; output `reroutes[]` with $ saved; re-run prediction to show queue relief.
- **Exit:** optimizer response includes reroutes; UI can render badges.

### P8 — 72 h shift planner — `2.5 h`
- Tasks: map optimized schedule → 9 shift blocks; per shift: work orders (vessel, berth, cranes, target moves), hotspot alerts, contingency notes (crane breakdown, weather, yard overflow); CSV/PDF export.
- **Exit:** `/api/plan` returns 9 blocks; CSV download works.

### P9 — React shell + Overview screen — `2 h`
- Tasks: Vite+TS+Tailwind shell, routing, typed API client, KPI cards, **day×berth congestion heatmap**, what-if sidebar (divert N vessels, add crane, yard cap +10%).
- **Exit:** live KPIs + heatmap rendered from API.

### P10 — Berth Gantt + Queue screens — `2.5 h`
- Tasks: `BerthGantt` (SVG: vessels vs 72–168 h, status colors, crane counts); `VesselTable` (sortable, predicted wait, reroute badge with $ saved).
- **Exit:** both screens live against API.

### P11 — Shift Plan + Compare screens — `2.5 h`
- Tasks: ShiftPlan (9 blocks, work orders, alerts, CSV/PDF download); Compare (baseline vs optimized bars: wait, utilization, cost).
- **Exit:** full 6-screen dashboard wired; what-if re-runs < 2 s.

### P12 — Live tracking map ("Mission Control") — `3 h`
- Tasks: trajectory builder (vessel position = f(sim_h) from state timeline: inbound → anchorage → berth → outbound); MapLibre GL map (free tiles, no API key); play/pause + speed 1×–100×; live event ticker + queue counter; REST snapshot polling (WebSocket upgrade if time).
- **Vessel visuals (style A — core):** hand-drawn top-down SVG hulls per class (feeder/medium/mega) with gradient shading + drop shadow; rotate to heading; status color-rings (inbound/queued/berthed/delayed/diverted); fading wake trails behind moving ships; berth crane-gantry animation + loading progress arc; pulsing hotspot halos; click → vessel detail card.
- **3D-lite touches (from style D):** terminal buildings via fill-extrusion, water shimmer, hover/zoom pop-out depth on ships; **toggleable three.js glTF hero-ship layer** (CC0 model from poly.pizza/Sketchfab) if time allows.
- Stretch: real-AIS context layer via **AISStream.io** (free WebSocket key) showing actual LA/Long Beach traffic next to the simulated plan.
- **Exit:** ships glide on the map with wake trails and working crane animations; 3D-lite depth visible; speed controls work; hotspots pulse as overlays.

### P13 — Evaluation, demo, polish — `2 h`
- Tasks: evaluation script (before/after table + charts); `docs/demo_script.md`; README; fixed seed for reproducibility; screenshots; final commit.
- **Exit:** submission package ready.

---

## 7. API Contract (v1)

Base URL: `http://localhost:8000` · Frontend dev proxy: Vite → `/api/*` to backend.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness check |
| GET | `/api/data/summary` | current scenario snapshot: vessels, berths, cranes, ports, `as_of_h` |
| POST | `/api/predict` | congestion forecast + hotspot alerts |
| POST | `/api/optimize` | berth/crane assignments + reroutes + KPIs (baseline vs optimized) |
| POST | `/api/plan` | 72 h shift plan (9 blocks + work orders) |
| GET | `/api/kpis` | aggregated metrics + deltas |
| GET | `/api/live` | live sim snapshot: vessel positions/states, queue, recent events (map animation) |
| WS | `/api/ws/live` | (upgrade) push live snapshots each sim tick |

**Request/response shapes (key fields)**

```
POST /api/predict   { as_of_h: 0, horizon_h: 168, overrides?: {extra_cranes, divert_n, yard_boost_pct} }
                 →  { vessel_forecasts: [{vessel_id, predicted_wait_h, predicted_berth_h, status}],
                      berth_util_forecast: [{berth_id, buckets: [{h, util_pct}]}],
                      queue_forecast: [{h, queue_size}], yard_forecast: [{h, util_pct}],
                      hotspots: [{kind, severity, horizon_h, lead_time_h, affected[], message}] }

POST /api/optimize  { scenario: "default", overrides? }
                 →  { assignments: [{vessel_id, berth_id, start_h, end_h, crane_count}],
                      reroutes: [{vessel_id, alt_port_id, est_cost_usd, saving_usd, reason}],
                      kpis: { baseline: {...}, optimized: {...} }, solve_ms }

POST /api/plan      { assignments, horizon_h: 72, shift_h: 8 }
                 →  { shifts: [ { id: "D1S1", window: "h0-h8", alerts: [...],
                        work_orders: [{vessel_id, berth_id, crane_ids, target_moves, priority}],
                        contingency_notes: [...] } x 9 ] }

GET  /api/live      { sim_h, vessels: [{id, name, lat, lon,
                        state(inbound/anchorage/berthed/outbound/diverted),
                        speed_kn, berth_id?}],
                      queue_size, yard_util_pct,
                      recent_events: ["h14 MV X berthed at B3, 4 cranes"], kpis: {...} }
```

---

## 8. Frontend Spec — 6 screens

| # | Screen | Content | Data source |
|---|---|---|---|
| 1 | **Overview** | KPI cards (queue size, avg wait, berth util, cost), 7-day **day×berth congestion heatmap**, hotspot list with lead time | `/api/predict`, `/api/kpis` |
| 2 | **Berth Gantt** | vessels vs 72–168 h timeline, status colors (green berthed / yellow queued / red delayed), crane-count labels | `/api/optimize` |
| 3 | **Queue** | sortable vessel table (ETA, size, priority, predicted wait), **"Re-route ↗" badge** with $ saved | `/api/predict` + reroutes |
| 4 | **Shift Plan** | 9 shift blocks (D1S1…D3S3), work orders, per-shift alerts + contingency notes, **CSV/PDF download** | `/api/plan` |
| 5 | **Compare** | baseline vs optimized bars (wait, utilization, demurrage $) — the demo "wow" slide | `/api/kpis` |
| 6 | **Live Map** ("Mission Control") | animated top-down SVG ships per class (heading-rotated, status rings, wake trails), crane + loading animations at berths, 3D-lite depth (extruded terminal, shimmer), pulsing hotspot halos, alt-port routes, play/pause + speed 1×–100×, event ticker, click → vessel card | `/api/live`, `/api/data/summary` |

**Global controls (sidebar, all screens):** scenario picker, what-if sliders —
`divert up to N vessels`, `add crane to berth B`, `yard capacity +X%` → re-run predict/optimize;
on the Live Map: `play/pause`, `speed 1×/10×/100×`, hover tooltips per vessel.

**Live Map visual style (A + 3D-lite):** hand-drawn SVG hulls per vessel class with gradient
shading + drop shadow; status rings — 🔵 inbound · 🟡 queued · 🟢 berthed · 🔴 delayed · 🟣 diverted;
fading wake trail behind moving ships; crane-gantry slide + loading progress arc on berthed
vessels; pulsing red halos on hotspots; 3D-lite = extruded terminal buildings, water shimmer,
hover pop-out; stretch = toggleable three.js glTF hero-ship layer.

**UX conventions:** dark theme, 8 h shift gridlines on Gantt, color-blind-safe palette,
loading states < 2 s, empty/error states for API failures.

---

## 9. Evaluation Criteria & KPIs

Run the same scenario through (a) FCFS baseline and (b) optimized plan; report deltas.

| KPI | Definition | Target vs FCFS baseline |
|---|---|---|
| `avg_wait_h` | mean anchorage waiting time per vessel | **−30% or better** |
| `p95_wait_h` | 95th-percentile anchorage wait | −25% |
| `max_queue` | max vessels at anchorage in any hour | −20% |
| `berth_util_pct` | occupied berth-hours / available berth-hours | ≥ 75%, better balanced |
| `crane_util_pct` | working crane-hours / available crane-hours | ≥ 70% |
| `yard_util_pct` | yard TEU / yard capacity | ≤ 85% (no overflow) |
| `demurrage_cost_usd` | Σ (wait_h × demurrage rate) | −30% |
| `hotspot_lead_time_h` | hours of warning before a hotspot forms | **≥ 12 h** |
| `cost_saved_usd` | Σ (baseline cost − optimized cost) over horizon | headline demo number |

Demo narrative: *"Avg anchorage wait cut 40%, $2.4M saved per 72 h, hotspots flagged 24 h early."*
(Numbers to be produced by P13 evaluation run — placeholders above.)

---

## 10. Risks & Assumptions

| Risk / Assumption | Mitigation |
|---|---|
| No real dataset provided | synthetic generator with documented, benchmark-validated assumptions (§4) |
| CP-SAT model blow-up at hundreds of vessels | 1 h time buckets, rolling horizon, cap horizon at 168 h, warm-start from FCFS |
| `/api/optimize` must respond < 2 s | memoize identical scenario requests; fall back to greedy heuristic if solver exceeds budget |
| Simulation realism | calibrate arrival rate/utilization so baseline reproduces congestion (queue forms ~48–72 h) |
| Frontend/backend integration friction | freeze API contract (§7) at P4; Vite dev proxy + CORS configured in P1/P4 |
| Environment | Python 3.12 + node v22 verified on this machine; use `venv` + pinned `requirements.txt` |
| Hackathon time pressure | phases have exit criteria; cut list (in order): PDF export → what-if sliders → ML stretch |

---

## 11. Team Split (3–4 developers)

| Person | Phases | Scope |
|---|---|---|
| **A** | P2, P3, P5 | data generator, DES simulator, prediction + hotspots |
| **B** | P6, P7, P8 | CP-SAT optimizer, rerouting, shift planner |
| **C** | P1, P4, P13 | scaffold, API wiring, integration, evaluation/demo |
| **D** | P9, P10, P11, P12 | React shell + 6 screens + what-if + live map |

Dependency rule: B starts P6 only after §4 entity schemas are agreed (P2 contract),
which is why the pydantic schemas (P4) are frozen early.

---

## 12. Repository Structure (target)

```
ship-managment/
├── plan.md                     ← this file
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, router mounting
│   │   ├── config.py
│   │   ├── schemas.py          # pydantic models (§7 contract)
│   │   ├── domain/entities.py  # Vessel, Berth, Crane, YardZone, AltPort
│   │   ├── data/generator.py   # synthetic scenario generator
│   │   ├── simulation/engine.py        # simpy DES + FCFS baseline
│   │   ├── prediction/forecaster.py    # forward sim
│   │   ├── prediction/hotspots.py      # hotspot rules
│   │   ├── optimization/solver.py      # CP-SAT berth+crane
│   │   ├── optimization/rerouting.py   # diversion recommender
│   │   ├── planning/shift_plan.py      # 72h plan builder
│   │   ├── services/           # orchestration for routers
│   │   └── routers/            # /predict /optimize /plan /kpis /data
│   └── tests/
├── frontend/
│   └── src/{api,types,components,pages,hooks}
├── scripts/
│   ├── generate_data.py
│   └── evaluate.py             # baseline vs optimized report
├── data/                       # generated JSON/CSV artifacts
└── docs/
    └── demo_script.md
```

---

## 13. Final Deliverables Checklist

- [x] `plan.md` (this document)
- [ ] `README.md` (run instructions, architecture summary)
- [ ] Backend: generator, DES simulator, prediction + hotspots, CP-SAT optimizer, rerouting, shift planner, FastAPI, tests
- [ ] Frontend: 6 screens (Overview, Gantt, Queue, Shift Plan, Compare, Live Map), what-if controls, CSV/PDF downloads
- [ ] Live tracking map: SVG ship visuals (wake trails, crane/loading animations), 3D-lite depth, play/pause/speed, hotspot overlays (stretch: glTF hero ships, real AIS via AISStream.io)
- [ ] Evaluation: baseline-vs-optimized table + charts, fixed seed
- [ ] `docs/demo_script.md` + screenshots
- [ ] Sample 72 h shift plan (CSV + PDF)





