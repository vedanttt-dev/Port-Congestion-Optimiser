# Solution Overview

## What We Built

The **Container Congestion Predictor & Port Operations Optimiser** is a full-stack web application that provides port operations teams with AI-powered congestion prediction, berth/crane optimization, and 72-hour shift planning — all accessible through a modern, tablet-friendly dashboard.

## How It Works

1. **Scenario Generation** — The system generates realistic port scenarios with configurable parameters (number of vessels, berths, cranes, simulation duration)
2. **Discrete Event Simulation (DES)** — A SimPy-based simulation engine models vessel arrivals, queueing, berthing, crane operations, and departures to compute baseline FCFS KPIs
3. **Forward Prediction** — A Monte Carlo forward simulator predicts future congestion by running multiple simulation trajectories and identifying emerging hotspots
4. **CP-SAT Optimization** — Google OR-Tools' CP-SAT solver optimizes berth assignments and crane allocations to minimize wait times and demurrage costs
5. **Reroute Recommendations** — An intelligent rerouting recommender identifies vessels that should divert to alternative ports, with estimated cost savings
6. **72-Hour Shift Planning** — Generates detailed 8-hour shift plans with work orders, crane assignments, and contingency notes
7. **What-If Comparison** — Compare multiple scenarios side-by-side to evaluate infrastructure investments or operational changes
8. **Live WebSocket Feed** — Real-time simulation streaming with vessel positions, events, and KPI updates

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite + TypeScript)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Overview  │ │ Predict  │ │ Optimize │ │  Scenario/Compare│   │
│  │ Dashboard │ │ Charts   │ │ + Reroute│ │  Builder + WS    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                          │ REST API + WebSocket                  │
├──────────────────────────┼──────────────────────────────────────┤
│                     Backend (FastAPI + Python 3.12)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ SimPy    │ │ Forward  │ │ CP-SAT   │ │  Shift Plan +    │   │
│  │ Engine   │ │ Simulator│ │ Optimiser│ │  Rerouting       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                          │                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Scenario │ │ WebSocket│ │ KPI      │ │  Reroute Engine  │   │
│  │ Manager  │ │ Live Feed│ │ Compute  │ │  & Recommender   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| SimPy for DES | Lightweight, Python-native simulation; ideal for port/logistics modeling |
| CP-SAT for optimization | State-of-the-art constraint solver; handles integer variables, priorities, and time windows natively |
| FastAPI backend | Async-ready, auto-generates OpenAPI docs, high performance |
| React + Vite frontend | Fast HMR, modern tooling, excellent TypeScript support |
| Recharts for visualization | Declarative, responsive charts that integrate cleanly with React |
| MapLibre for vessel map | Open-source satellite imagery with WebGL rendering for smooth vessel tracking |
| ReportLab for PDF | Professional PDF generation with tables and formatted sections |

## IBM Technologies Used

This project is built as a standalone solution using open-source technologies. While no IBM-specific services are currently integrated, the architecture is designed for easy integration with:
- **IBM watsonx.ai** — Could enhance prediction accuracy with ML-based congestion forecasting
- **IBM Cloud Functions** — Serverless deployment for the optimization solver
- **IBM Db2** — Persistent storage for historical scenario data and KPIs
