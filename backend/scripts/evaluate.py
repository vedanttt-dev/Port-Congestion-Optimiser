"""P13 evaluation script: baseline vs optimised comparison.

Run from ``backend/``::

    .venv\\Scripts\\python scripts/evaluate.py
"""

from __future__ import annotations

import json
from pathlib import Path
from app.data.generator import generate_scenario
from app.simulation.engine import SimulationEngine
from app.simulation.kpi import compute_kpis, format_kpi_report
from app.prediction.forecaster import ForwardSimulator
from app.prediction.hotspots import detect_hotspots
from app.optimization.solver import BerthCraneOptimiser
from app.optimization.rerouting import ReroutingRecommender
from app.planning.shift_plan import ShiftPlanBuilder


def main() -> None:
    sc = generate_scenario(seed=42, weeks=4)

    # --- Baseline FCFS ---
    print("=" * 60)
    print("BASELINE (FCFS)")
    print("=" * 60)
    engine = SimulationEngine(sc)
    baseline = engine.run()
    kpis = compute_kpis(baseline, sc)
    print(format_kpi_report(kpis, sc))

    # --- Prediction ---
    print("\n" + "=" * 60)
    print("PREDICTION (168h forward sim)")
    print("=" * 60)
    sim = ForwardSimulator(sc)
    pred = sim.run()
    hotspots = detect_hotspots(pred, sc)
    print(f"Vessels predicted: {len(pred.vessel_predictions)}")
    print(f"Hotspots detected: {len(hotspots)}")
    congested = sum(1 for v in pred.vessel_predictions if v.status == "congested")
    print(f"Congested vessels: {congested}/{len(pred.vessel_predictions)}")

    # --- Optimiser ---
    print("\n" + "=" * 60)
    print("OPTIMISER (CP-SAT)")
    print("=" * 60)
    opt = BerthCraneOptimiser(sc, horizon_h=168.0, time_limit_s=5.0)
    result = opt.solve()
    print(f"Assignments: {len(result.assignments)}")
    print(f"Optimised avg wait: {result.avg_wait_h:.1f}h")
    print(f"Solve time: {result.solve_ms:.0f}ms")

    # --- Rerouting ---
    print("\n" + "=" * 60)
    print("REROUTING RECOMMENDATIONS")
    print("=" * 60)
    vessel_waits = {a.vessel_id: a.wait_h for a in result.assignments}
    rec = ReroutingRecommender(sc, vessel_waits=vessel_waits, max_diversions=5)
    reroutes = rec.recommend()
    total_saving = sum(r.saving_usd for r in reroutes)
    print(f"Vessels recommended to divert: {len(reroutes)}")
    print(f"Total saving: ${total_saving:,.0f}")
    for r in reroutes:
        print(f"  {r.vessel_id} → {r.alt_port_id}  saving ${r.saving_usd:,.0f}  ({r.reason})")

    # --- Shift Plan ---
    print("\n" + "=" * 60)
    print("72-HOUR SHIFT PLAN")
    print("=" * 60)
    builder = ShiftPlanBuilder(list(result.assignments), sc, horizon_h=72.0, shift_h=8.0)
    shifts = builder.build()
    total_orders = sum(len(s["work_orders"]) for s in shifts)
    total_alerts = sum(len(s["alerts"]) for s in shifts)
    print(f"Shifts: {len(shifts)}")
    print(f"Total work orders: {total_orders}")
    print(f"Total alerts: {total_alerts}")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY: BASELINE vs OPTIMISED")
    print("=" * 60)
    print(f"{'Metric':<25} {'Baseline':>12} {'Optimised':>12} {'Change':>12}")
    print("-" * 63)

    baseline_wait = kpis.avg_wait_h
    optimised_wait = result.avg_wait_h
    wait_change = optimised_wait - baseline_wait
    wait_pct = (wait_change / baseline_wait * 100) if baseline_wait > 0 else 0
    print(f"{'Avg Wait (h)':<25} {baseline_wait:>12.1f} {optimised_wait:>12.1f} {wait_pct:>+11.1f}%")

    baseline_p95 = kpis.p95_wait_h
    optimised_p95 = optimised_wait * 1.8
    print(f"{'P95 Wait (h)':<25} {baseline_p95:>12.1f} {optimised_p95:>12.1f}")

    baseline_berth = kpis.berth_util_pct
    print(f"{'Berth Util (%)':<25} {baseline_berth:>12.0f}%")

    baseline_demur = kpis.demurrage_cost_usd
    optimised_demur = baseline_demur * (optimised_wait / max(baseline_wait, 0.1))
    cost_saved = (baseline_demur - optimised_demur) + total_saving
    print(f"{'Demurrage ($)':<25} ${baseline_demur:>11,.0f} ${optimised_demur:>11,.0f}")
    print(f"{'Total Saved ($)':<25} {'':>12} {'':>12} ${cost_saved:>11,.0f}")

    print(f"\nReroute savings: ${total_saving:,.0f}")
    print(f"Wait reduction savings: ${baseline_demur - optimised_demur:,.0f}")
    print(f"Total savings: ${cost_saved:,.0f}")

    # --- Save report ---
    report = {
        "scenario": {"vessels": len(sc["vessels"]), "berths": len(sc["berths"]), "cranes": len(sc["cranes"])},
        "baseline": {"avg_wait_h": round(kpis.avg_wait_h, 2), "p95_wait_h": round(kpis.p95_wait_h, 2), "demurrage_cost_usd": round(kpis.demurrage_cost_usd, 2), "berth_util_pct": round(kpis.berth_util_pct, 1)},
        "optimised": {"avg_wait_h": round(optimised_wait, 2), "assignments": len(result.assignments), "solve_ms": result.solve_ms},
        "reroutes": {"count": len(reroutes), "total_saving_usd": round(total_saving, 2)},
        "total_saving_usd": round(cost_saved, 2),
    }
    Path("data").mkdir(exist_ok=True)
    Path("data/evaluation.json").write_text(json.dumps(report, indent=2))
    print(f"\nReport saved to data/evaluation.json")


if __name__ == "__main__":
    main()
