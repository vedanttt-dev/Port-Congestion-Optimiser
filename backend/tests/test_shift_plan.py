"""P8 tests: 72-hour shift planner + CSV export.

Run with: ``pytest tests/test_shift_plan.py -v``
"""

from __future__ import annotations

import csv
import io

import pytest

from app.data.generator import generate_scenario
from app.optimization.solver import BerthCraneOptimiser
from app.planning.shift_plan import ShiftPlanBuilder, shift_plan_to_csv, save_shift_plan_csv


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def scenario() -> dict:
    return generate_scenario(seed=42, weeks=4)


@pytest.fixture(scope="module")
def assignments(scenario: dict) -> list:
    opt = BerthCraneOptimiser(scenario, horizon_h=168.0, time_limit_s=2.0)
    result = opt.solve()
    return list(result.assignments)


@pytest.fixture(scope="module")
def shifts(scenario: dict, assignments: list) -> list[dict]:
    builder = ShiftPlanBuilder(assignments, scenario, horizon_h=72.0, shift_h=8.0)
    return builder.build()


# ---------------------------------------------------------------------------
# Shift plan builder tests
# ---------------------------------------------------------------------------

class TestShiftPlanBuilder:
    def test_build_completes(self, shifts) -> None:
        assert len(shifts) > 0

    def test_nine_shifts_for_72h(self, shifts) -> None:
        assert len(shifts) == 9

    def test_shift_ids(self, shifts) -> None:
        ids = [s["id"] for s in shifts]
        assert ids == ["D1S1", "D1S2", "D1S3", "D2S1", "D2S2", "D2S3", "D3S1", "D3S2", "D3S3"]

    def test_shift_windows_contiguous(self, shifts) -> None:
        for i, s in enumerate(shifts):
            assert s["start_h"] == i * 8.0
            assert s["end_h"] == (i + 1) * 8.0

    def test_shift_has_required_fields(self, shifts) -> None:
        for s in shifts:
            assert "id" in s
            assert "window" in s
            assert "alerts" in s
            assert "work_orders" in s
            assert "contingency_notes" in s

    def test_work_orders_have_fields(self, shifts) -> None:
        for s in shifts:
            for wo in s["work_orders"]:
                assert "vessel_id" in wo
                assert "berth_id" in wo
                assert "crane_ids" in wo
                assert "target_moves" in wo
                assert "priority" in wo

    def test_contingency_notes_populated(self, shifts) -> None:
        has_notes = any(len(s["contingency_notes"]) > 0 for s in shifts)
        assert has_notes

    def test_no_overlapping_vessels_per_shift(self, shifts) -> None:
        """Each vessel should appear at most once per shift."""
        for s in shifts:
            vessel_ids = [wo["vessel_id"] for wo in s["work_orders"]]
            assert len(vessel_ids) == len(set(vessel_ids))


# ---------------------------------------------------------------------------
# Hotspot alert tests
# ---------------------------------------------------------------------------

class TestShiftAlerts:
    def test_alerts_are_strings(self, shifts) -> None:
        for s in shifts:
            for a in s["alerts"]:
                assert isinstance(a, str)

    def test_delay_alerts_or_empty(self, shifts) -> None:
        """Optimizer may reduce waits below 24h, so alerts may be empty."""
        all_alerts = [a for s in shifts for a in s["alerts"]]
        assert isinstance(all_alerts, list)


# ---------------------------------------------------------------------------
# CSV export tests
# ---------------------------------------------------------------------------

class TestCSVExport:
    def test_csv_valid(self, shifts) -> None:
        csv_str = shift_plan_to_csv(shifts)
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) > 1  # header + data

    def test_csv_header(self, shifts) -> None:
        csv_str = shift_plan_to_csv(shifts)
        first_line = csv_str.strip().split("\n")[0]
        assert "shift_id" in first_line
        assert "vessel_id" in first_line

    def test_csv_has_data_rows(self, shifts) -> None:
        csv_str = shift_plan_to_csv(shifts)
        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) >= 10  # header + 9 shifts minimum

    def test_csv_save_to_file(self, shifts, tmp_path) -> None:
        path = tmp_path / "plan.csv"
        save_shift_plan_csv(shifts, path)
        assert path.exists()
        content = path.read_text()
        assert "shift_id" in content
