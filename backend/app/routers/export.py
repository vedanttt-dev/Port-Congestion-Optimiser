"""GET /api/export/* — CSV + PDF export endpoints (P12)."""

from __future__ import annotations

import csv
import io
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.optimization.rerouting import ReroutingRecommender
from app.optimization.solver import BerthCraneOptimiser
from app.planning.shift_plan import ShiftPlanBuilder, shift_plan_to_csv
from app.prediction.forecaster import ForwardSimulator
from app.prediction.hotspots import detect_hotspots
from app.services.scenario import svc

router = APIRouter(tags=["export"])


def _to_csv(rows: list[dict], headers: list[str]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    return output.getvalue()


def _make_csv_response(csv_str: str, filename: str) -> StreamingResponse:
    buf = io.BytesIO(csv_str.encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Data export
# ---------------------------------------------------------------------------

@router.get("/export/data")
def export_data(format: Literal["csv"] = "csv") -> StreamingResponse:
    """Export scenario vessels as CSV."""
    sc = svc.scenario
    rows = [
        {
            "id": v.id, "name": v.name, "type": v.type,
            "teu_capacity": v.teu_capacity, "loa_m": v.loa_m,
            "eta_h": v.eta_h, "priority_class": v.priority_class,
            "moves": v.import_moves + v.export_moves,
            "demurrage_per_day": v.demurrage_usd_per_day,
        }
        for v in sc["vessels"]
    ]
    headers = ["id", "name", "type", "teu_capacity", "loa_m", "eta_h", "priority_class", "moves", "demurrage_per_day"]
    return _make_csv_response(_to_csv(rows, headers), "vessels.csv")


# ---------------------------------------------------------------------------
# Prediction export
# ---------------------------------------------------------------------------

@router.get("/export/predict")
def export_predict(format: Literal["csv"] = "csv") -> StreamingResponse:
    """Export prediction forecasts as CSV."""
    sc = svc.scenario
    sim = ForwardSimulator(sc)
    pred = sim.run()
    hotspots = detect_hotspots(pred, sc)

    vessel_rows = [
        {
            "vessel_id": f.vessel_id, "name": f.name, "type": f.vessel_type,
            "predicted_wait_h": round(f.predicted_wait_h, 2),
            "predicted_berth_h": round(f.predicted_berth_h, 2),
            "status": f.status, "eta_h": round(f.eta_h, 1),
        }
        for f in pred.vessel_predictions
    ]
    headers = ["vessel_id", "name", "type", "predicted_wait_h", "predicted_berth_h", "status", "eta_h"]
    return _make_csv_response(_to_csv(vessel_rows, headers), "predictions.csv")


# ---------------------------------------------------------------------------
# Optimiser export
# ---------------------------------------------------------------------------

@router.get("/export/optimize")
def export_optimize(format: Literal["csv"] = "csv") -> StreamingResponse:
    """Export optimiser assignments + reroutes as CSV."""
    sc = svc.scenario
    opt = BerthCraneOptimiser(sc, horizon_h=168.0, time_limit_s=2.0)
    result = opt.solve()

    vessel_waits = {a.vessel_id: a.wait_h for a in result.assignments}
    rec = ReroutingRecommender(sc, vessel_waits=vessel_waits, max_diversions=5)
    reroute_recs = rec.recommend()

    rows = []
    for a in result.assignments:
        rows.append({
            "vessel_id": a.vessel_id, "berth_id": a.berth_id,
            "start_h": round(a.start_h, 1), "end_h": round(a.end_h, 1),
            "crane_count": a.crane_count, "moves_planned": a.moves_planned,
            "wait_h": round(a.wait_h, 2),
            "reroute_alt_port": "", "reroute_saving": "",
        })
    for r in reroute_recs:
        rows.append({
            "vessel_id": r.vessel_id, "berth_id": "",
            "start_h": "", "end_h": "",
            "crane_count": "", "moves_planned": "",
            "wait_h": "",
            "reroute_alt_port": r.alt_port_id,
            "reroute_saving": round(r.saving_usd, 2),
        })

    headers = ["vessel_id", "berth_id", "start_h", "end_h", "crane_count", "moves_planned", "wait_h", "reroute_alt_port", "reroute_saving"]
    return _make_csv_response(_to_csv(rows, headers), "optimiser.csv")


# ---------------------------------------------------------------------------
# Plan export (already exists in plan.py, but adding consistent wrapper)
# ---------------------------------------------------------------------------

@router.get("/export/plan")
def export_plan(horizon_h: float = 72.0, shift_h: float = 8.0) -> StreamingResponse:
    """Export shift plan as CSV."""
    sc = svc.scenario
    opt = BerthCraneOptimiser(sc, horizon_h=horizon_h, time_limit_s=2.0)
    opt_result = opt.solve()
    builder = ShiftPlanBuilder(list(opt_result.assignments), sc, horizon_h=horizon_h, shift_h=shift_h)
    shifts = builder.build()
    csv_str = shift_plan_to_csv(shifts)
    return _make_csv_response(csv_str, "shift_plan.csv")


# ---------------------------------------------------------------------------
# Full report PDF (text-based)
# ---------------------------------------------------------------------------

@router.get("/export/report")
def export_report() -> StreamingResponse:
    """Generate a full text-based PDF report."""
    sc = svc.scenario
    result = svc.get_result()

    from app.simulation.kpi import compute_kpis
    kpis = compute_kpis(result, sc)

    opt = BerthCraneOptimiser(sc, horizon_h=168.0, time_limit_s=2.0)
    opt_result = opt.solve()

    vessel_waits = {a.vessel_id: a.wait_h for a in opt_result.assignments}
    rec = ReroutingRecommender(sc, vessel_waits=vessel_waits, max_diversions=5)
    reroute_recs = rec.recommend()

    lines = []
    lines.append("=" * 60)
    lines.append("PORT CONGESTION REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append("BASELINE KPIs (FCFS)")
    lines.append(f"  Avg Wait:          {kpis.avg_wait_h:.1f}h")
    lines.append(f"  P95 Wait:          {kpis.p95_wait_h:.1f}h")
    lines.append(f"  Berth Util:        {kpis.berth_util_pct:.0f}%")
    lines.append(f"  Crane Util:        {kpis.crane_util_pct:.0f}%")
    lines.append(f"  Yard Util:         {kpis.yard_util_pct:.0f}%")
    lines.append(f"  Demurrage Cost:    ${kpis.demurrage_cost_usd:,.0f}")
    lines.append("")
    lines.append("OPTIMISED KPIs (CP-SAT)")
    lines.append(f"  Avg Wait:          {opt_result.avg_wait_h:.1f}h")
    lines.append(f"  Assignments:       {len(opt_result.assignments)}")
    lines.append("")
    lines.append("REROUTE RECOMMENDATIONS")
    for r in reroute_recs:
        lines.append(f"  {r.vessel_id} -> {r.alt_port_id}  saving ${r.saving_usd:,.0f}  ({r.reason})")
    lines.append("")
    lines.append("SCENARIO DATA")
    lines.append(f"  Vessels: {len(sc['vessels'])}")
    lines.append(f"  Berths:  {len(sc['berths'])}")
    lines.append(f"  Cranes:  {len(sc['cranes'])}")
    lines.append(f"  Yard:    {len(sc['yard_zones'])} zones")
    lines.append(f"  Alt Ports: {len(sc['alt_ports'])}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("Generated by Port Congestion Optimiser")

    report = "\n".join(lines)
    buf = io.BytesIO(report.encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=port_congestion_report.txt"},
    )
