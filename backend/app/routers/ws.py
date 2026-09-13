"""WebSocket /api/ws/live — real-time vessel movement streaming."""

from __future__ import annotations

import asyncio
import json
import math
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.scenario import get_active_scenario, get_active_result, get_active_kpis

router = APIRouter(tags=["live"])

_BASE_LAT = 33.75
_BASE_LON = -118.25
_BERTH_SPACING = 0.005


def _compute_positions(scenario: dict, result: Any, sim_h: float) -> list[dict]:
    """Compute vessel positions for a given sim hour."""
    berths_map = {b.id: b for b in scenario["berths"]}
    positions = []

    for vs in result.vessel_states.values():
        vessel = vs.vessel
        status = vessel.status.value

        # Only include vessels that have arrived by sim_h
        if vs.arrived_h > sim_h and vs.arrived_h < 0:
            continue

        if status == "berthed" and vs.assigned_berth:
            berth_idx = 0
            for i, b in enumerate(berths_map.values()):
                if b.id == vs.assigned_berth:
                    berth_idx = i
                    break
            lat = _BASE_LAT + berth_idx * _BERTH_SPACING
            lon = _BASE_LON + berth_idx * _BERTH_SPACING * 0.5
            heading = 0.0
        elif status == "anchorage":
            lat = _BASE_LAT - 0.02
            lon = _BASE_LON + 0.01 + (hash(vessel.id) % 100) * 0.0002
            heading = 0.0
        elif status == "outbound":
            lat = _BASE_LAT + 0.05
            lon = _BASE_LON - 0.05
            heading = 225.0
        elif status == "diverted":
            lat = _BASE_LAT - 0.1
            lon = _BASE_LON + 0.1
            heading = 315.0
        else:
            lat = _BASE_LAT - 0.04
            lon = _BASE_LON + 0.03
            heading = 45.0

        speed = 0.0 if status in ("berthed", "anchorage") else 12.0

        positions.append({
            "id": vessel.id,
            "name": vessel.name,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "state": status,
            "speed_kn": speed,
            "heading": heading,
            "berth_id": vs.assigned_berth or None,
            "vessel_type": vessel.type.value,
            "teu_capacity": vessel.teu_capacity,
        })

    return positions


def _compute_events(result: Any, limit: int = 20) -> list[dict]:
    """Get recent events."""
    events = []
    for e in result.events[-limit:]:
        events.append({
            "time_h": round(e.time_h, 2),
            "vessel_id": e.vessel_id,
            "event_type": e.event_type.value,
            "detail": e.detail,
        })
    return events


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time live simulation updates.

    Client sends JSON commands:
      {"action": "start", "speed": 1} — start streaming (speed = multiplier)
      {"action": "stop"} — stop streaming
      {"action": "seek", "sim_h": 48.0} — jump to specific time
      {"action": "status"} — get current status

    Server pushes JSON updates:
      {"type": "update", "sim_h": ..., "vessels": [...], "events": [...], "kpis": {...}}
      {"type": "status", "running": ..., "sim_h": ..., "horizon_h": ...}
    """
    await websocket.accept()

    sc = get_active_scenario()
    result = get_active_result()
    kpis = get_active_kpis()

    # State
    running = False
    speed = 1.0
    current_h = 0.0
    horizon_h = 672.0
    update_interval = 0.5  # seconds between pushes

    try:
        while True:
            # Check for client messages (non-blocking)
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                msg = json.loads(raw)
                action = msg.get("action", "")

                if action == "start":
                    running = True
                    speed = msg.get("speed", 1.0)
                    await websocket.send_json({
                        "type": "status",
                        "running": running,
                        "sim_h": current_h,
                        "horizon_h": horizon_h,
                        "speed": speed,
                    })

                elif action == "stop":
                    running = False
                    await websocket.send_json({
                        "type": "status",
                        "running": running,
                        "sim_h": current_h,
                        "horizon_h": horizon_h,
                    })

                elif action == "seek":
                    current_h = min(max(0.0, msg.get("sim_h", 0.0)), horizon_h)
                    positions = _compute_positions(sc, result, current_h)
                    events = _compute_events(result)
                    yard_cap = sum(z.teu_capacity for z in sc["yard_zones"])
                    yard_teu = sum(
                        result.yard_teu.get(z.id, z.current_teu) for z in sc["yard_zones"]
                    )
                    await websocket.send_json({
                        "type": "update",
                        "sim_h": round(current_h, 2),
                        "vessels": positions,
                        "events": events[-10:],
                        "queue_size": max(
                            (qs[1] for qs in result.queue_samples if qs[0] <= current_h),
                            default=0,
                        ),
                        "yard_util_pct": round(yard_teu / yard_cap * 100, 1) if yard_cap else 0.0,
                        "kpis": {
                            "avg_wait_h": kpis.avg_wait_h,
                            "demurrage_cost_usd": kpis.demurrage_cost_usd,
                        },
                    })

                elif action == "status":
                    await websocket.send_json({
                        "type": "status",
                        "running": running,
                        "sim_h": round(current_h, 2),
                        "horizon_h": horizon_h,
                        "speed": speed,
                        "num_vessels": len(sc["vessels"]),
                        "num_berths": len(sc["berths"]),
                        "num_cranes": len(sc["cranes"]),
                    })

            except asyncio.TimeoutError:
                pass

            # If running, advance sim_h and push update
            if running and current_h < horizon_h:
                current_h = min(current_h + speed, horizon_h)

                positions = _compute_positions(sc, result, current_h)
                events = _compute_events(result)

                # Count vessels by status
                status_counts: dict[str, int] = {}
                for p in positions:
                    s = p["state"]
                    status_counts[s] = status_counts.get(s, 0) + 1

                yard_cap = sum(z.teu_capacity for z in sc["yard_zones"])
                yard_teu = sum(
                    result.yard_teu.get(z.id, z.current_teu) for z in sc["yard_zones"]
                )

                await websocket.send_json({
                    "type": "update",
                    "sim_h": round(current_h, 2),
                    "vessels": positions,
                    "events": events[-10:],
                    "queue_size": max(
                        (qs[1] for qs in result.queue_samples if qs[0] <= current_h),
                        default=0,
                    ),
                    "yard_util_pct": round(yard_teu / yard_cap * 100, 1) if yard_cap else 0.0,
                    "status_counts": status_counts,
                    "kpis": {
                        "avg_wait_h": kpis.avg_wait_h,
                        "demurrage_cost_usd": kpis.demurrage_cost_usd,
                    },
                })

                if current_h >= horizon_h:
                    running = False
                    await websocket.send_json({
                        "type": "status",
                        "running": False,
                        "sim_h": round(current_h, 2),
                        "horizon_h": horizon_h,
                        "message": "Simulation complete",
                    })

            await asyncio.sleep(update_interval)

    except WebSocketDisconnect:
        pass
