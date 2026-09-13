#!/usr/bin/env python
"""Run the baseline FCFS simulation and print a KPI report.

Usage (from ``backend/``)::

    python ../scripts/run_baseline.py --seed 42 --weeks 4
    python ../scripts/run_baseline.py --seed 42 --weeks 4 --output ../data/raw
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.data.generator import generate_scenario
from app.simulation.engine import SimulationEngine
from app.simulation.kpi import (
    compute_kpis,
    format_kpi_report,
    kpis_to_dict,
    save_kpi_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the baseline FCFS simulation and print a KPI report.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    parser.add_argument("--weeks", type=int, default=4, help="Weeks of arrivals (default: 4).")
    parser.add_argument(
        "--horizon", type=float, default=672.0,
        help="Simulation horizon in hours (default: 672 = 4 weeks).",
    )
    parser.add_argument("--output", type=str, default="data/raw", help="CSV output directory.")
    args = parser.parse_args()

    print(f"Generating scenario: seed={args.seed}, weeks={args.weeks} ...")
    scenario = generate_scenario(seed=args.seed, weeks=args.weeks)

    print(f"Running baseline simulation (horizon={args.horizon}h) ...")
    t0 = time.perf_counter()
    engine = SimulationEngine(scenario, seed=args.seed, horizon_h=args.horizon)
    result = engine.run()
    elapsed = time.perf_counter() - t0
    print(f"  Completed in {elapsed:.2f}s  ({len(result.events)} events)")

    kpis = compute_kpis(result, scenario)
    print()
    print(format_kpi_report(kpis, scenario))

    # Save CSVs
    kpi_path = save_kpi_csv(result, kpis, args.output)
    print(f"\nCSV files saved to {args.output}/")
    print(f"  KPI summary  -> {kpi_path}")
    print(f"  Vessel data  -> {Path(args.output) / 'vessel_results.csv'}")

    # Quick congestion check
    if kpis.avg_wait_h > 12:
        print("\n>> Congested port behaviour detected (avg wait > 12h)")
    else:
        print("\n>> Wait times within normal range")


if __name__ == "__main__":
    main()
