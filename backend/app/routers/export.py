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


# ---------------------------------------------------------------------------
# Executive PDF Report
# ---------------------------------------------------------------------------

@router.get("/export/report-pdf")
def export_report_pdf() -> StreamingResponse:
    """Generate a professional PDF report with charts and tables."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    )

    sc = svc.scenario
    result = svc.get_result()

    from app.simulation.kpi import compute_kpis
    kpis = compute_kpis(result, sc)

    opt = BerthCraneOptimiser(sc, horizon_h=168.0, time_limit_s=2.0)
    opt_result = opt.solve()

    vessel_waits = {a.vessel_id: a.wait_h for a in opt_result.assignments}
    rec = ReroutingRecommender(sc, vessel_waits=vessel_waits, max_diversions=5)
    reroute_recs = rec.recommend()

    sim = ForwardSimulator(sc)
    pred = sim.run()
    hotspots = detect_hotspots(pred, sc)

    from app.planning.shift_plan import ShiftPlanBuilder
    builder = ShiftPlanBuilder(list(opt_result.assignments), sc, horizon_h=72.0, shift_h=8.0)
    shifts = builder.build()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements: list = []

    blue = colors.HexColor("#2563eb")
    dark = colors.HexColor("#0f172a")
    muted = colors.HexColor("#64748b")
    green = colors.HexColor("#059669")
    red = colors.HexColor("#dc2626")

    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=22, textColor=blue, spaceAfter=6)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=muted, spaceAfter=16)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=dark, spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=10, textColor=dark, leading=14)

    def add_table(headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None):
        data = [headers] + rows
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), blue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

    # --- Cover ---
    elements.append(Paragraph("Port Congestion Optimiser", title_style))
    elements.append(Paragraph("Executive Summary Report", subtitle_style))
    elements.append(Paragraph(
        f"Scenario: {len(sc['vessels'])} vessels, {len(sc['berths'])} berths, "
        f"{len(sc['cranes'])} cranes &mdash; Generated by CP-SAT Optimiser",
        body_style,
    ))
    elements.append(Spacer(1, 24))

    # --- KPI Summary ---
    elements.append(Paragraph("Key Performance Indicators", h2_style))
    add_table(
        ["Metric", "Baseline (FCFS)", "Optimised (CP-SAT)", "Improvement"],
        [
            [
                "Avg Wait (h)",
                f"{kpis.avg_wait_h:.1f}",
                f"{opt_result.avg_wait_h:.1f}",
                f"{((opt_result.avg_wait_h - kpis.avg_wait_h) / max(kpis.avg_wait_h, 0.01) * 100):+.0f}%",
            ],
            [
                "P95 Wait (h)",
                f"{kpis.p95_wait_h:.1f}",
                "—",
                "",
            ],
            [
                "Berth Util (%)",
                f"{kpis.berth_util_pct:.0f}",
                f"{kpis.berth_util_pct:.0f}",
                "—",
            ],
            [
                "Demurrage ($)",
                f"${kpis.demurrage_cost_usd:,.0f}",
                "—",
                "",
            ],
        ],
        col_widths=[120, 110, 110, 100],
    )

    # --- Vessel Forecasts ---
    elements.append(Paragraph("Vessel Arrival Forecasts", h2_style))
    vessel_rows = sorted(pred.vessel_predictions, key=lambda f: -f.predicted_wait_h)
    add_table(
        ["Vessel", "Type", "ETA (h)", "Wait (h)", "Berth (h)", "Status"],
        [
            [
                f.name, f.vessel_type, f"{f.eta_h:.1f}",
                f"{f.predicted_wait_h:.1f}", f"{f.predicted_berth_h:.1f}", f.status,
            ]
            for f in vessel_rows[:20]
        ],
        col_widths=[100, 60, 60, 60, 60, 70],
    )

    # --- Hotspots ---
    if hotspots:
        elements.append(Paragraph("Congestion Hotspots Detected", h2_style))
        add_table(
            ["ID", "Severity", "Lead Time (h)", "Message"],
            [[h.id, h.severity, str(h.lead_time_h), h.message] for h in hotspots],
            col_widths=[50, 60, 70, 260],
        )

    # --- Reroutes ---
    if reroute_recs:
        elements.append(Paragraph("Reroute Recommendations", h2_style))
        add_table(
            ["Vessel", "Alt Port", "Saving ($)", "Reason"],
            [[r.vessel_id, r.alt_port_id, f"${r.saving_usd:,.0f}", r.reason] for r in reroute_recs],
            col_widths=[90, 80, 80, 190],
        )

    # --- Assignments ---
    elements.append(Paragraph("Berth Assignments (Optimised)", h2_style))
    add_table(
        ["Vessel", "Berth", "Start (h)", "End (h)", "Cranes", "Moves"],
        [
            [a.vessel_id, a.berth_id, f"{a.start_h:.1f}", f"{a.end_h:.1f}", str(a.crane_count), str(a.moves_planned)]
            for a in opt_result.assignments
        ],
        col_widths=[100, 60, 60, 60, 60, 60],
    )

    # --- Shift Plan ---
    elements.append(Paragraph("72-Hour Shift Plan", h2_style))
    add_table(
        ["Shift", "Window", "Orders", "Alerts"],
        [
            [s.id, s.window, str(len(s.work_orders)), str(len(s.alerts))]
            for s in shifts
        ],
        col_widths=[80, 160, 80, 80],
    )

    # --- Footer ---
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "<i>Generated by Port Congestion Optimiser &mdash; CP-SAT + Forward Simulation</i>",
        ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=muted, alignment=1),
    ))

    doc.build(elements)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=port_congestion_report.pdf"},
    )
