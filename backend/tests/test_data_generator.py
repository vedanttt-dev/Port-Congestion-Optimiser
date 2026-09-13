"""P2 exit-criterion tests: data generator produces valid synthetic data.

Run with: ``pytest tests/test_data_generator.py -v``
"""

from __future__ import annotations

import pytest

from app.data.generator import generate_scenario
from app.domain.entities import (
    AltPort,
    Berth,
    Crane,
    Vessel,
    VesselType,
    YardZone,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def scenario() -> dict:
    """Generate a default scenario once per test module."""
    return generate_scenario(seed=42, weeks=4)


@pytest.fixture(scope="module")
def vessels(scenario: dict) -> list[Vessel]:
    return scenario["vessels"]


@pytest.fixture(scope="module")
def berths(scenario: dict) -> list[Berth]:
    return scenario["berths"]


@pytest.fixture(scope="module")
def cranes(scenario: dict) -> list[Crane]:
    return scenario["cranes"]


@pytest.fixture(scope="module")
def yard_zones(scenario: dict) -> list[YardZone]:
    return scenario["yard_zones"]


@pytest.fixture(scope="module")
def alt_ports(scenario: dict) -> list[AltPort]:
    return scenario["alt_ports"]


# ---------------------------------------------------------------------------
# Vessel tests
# ---------------------------------------------------------------------------

class TestVessels:
    def test_arrival_count_in_range(self, vessels: list[Vessel]) -> None:
        """25–40 arrivals/week × 4 weeks → 100–160 vessels."""
        assert 100 <= len(vessels) <= 160

    def test_all_vessel_ids_unique(self, vessels: list[Vessel]) -> None:
        ids = [v.id for v in vessels]
        assert len(ids) == len(set(ids))

    def test_vessel_type_distribution(self, vessels: list[Vessel]) -> None:
        """Feeder ~40%, Medium ~40%, Mega ~20% (±15% tolerance for finite samples)."""
        counts = {vt: 0 for vt in VesselType}
        for v in vessels:
            counts[v.type] += 1
        total = len(vessels)

        assert counts[VesselType.FEEDER] / total == pytest.approx(0.40, abs=0.15)
        assert counts[VesselType.MEDIUM] / total == pytest.approx(0.40, abs=0.15)
        assert counts[VesselType.MEGA] / total == pytest.approx(0.20, abs=0.15)

    def test_feeder_teu_range(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            if v.type == VesselType.FEEDER:
                assert 800 <= v.teu_capacity <= 2_000

    def test_medium_teu_range(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            if v.type == VesselType.MEDIUM:
                assert 4_000 <= v.teu_capacity <= 12_000

    def test_mega_teu_range(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            if v.type == VesselType.MEGA:
                assert 18_000 <= v.teu_capacity <= 24_000

    def test_feeder_loa_range(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            if v.type == VesselType.FEEDER:
                assert 140 <= v.loa_m <= 200

    def test_medium_loa_range(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            if v.type == VesselType.MEDIUM:
                assert 250 <= v.loa_m <= 320

    def test_mega_loa_range(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            if v.type == VesselType.MEGA:
                assert 360 <= v.loa_m <= 400

    def test_moves_non_negative(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            assert v.import_moves >= 0
            assert v.export_moves >= 0

    def test_eta_before_etd(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            assert v.eta_h < v.planned_etd_h

    def test_demurrage_positive(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            assert v.demurrage_usd_per_day > 0

    def test_priority_class_valid(self, vessels: list[Vessel]) -> None:
        for v in vessels:
            assert v.priority_class in (1, 2)


# ---------------------------------------------------------------------------
# Berth tests
# ---------------------------------------------------------------------------

class TestBerths:
    def test_berth_count(self, berths: list[Berth]) -> None:
        assert len(berths) == 8

    def test_berth_lengths(self, berths: list[Berth]) -> None:
        for b in berths:
            assert 250 <= b.length_m <= 400

    def test_berth_drafts(self, berths: list[Berth]) -> None:
        for b in berths:
            assert 13.0 <= b.max_draft_m <= 17.0

    def test_berth_ids_unique(self, berths: list[Berth]) -> None:
        ids = [b.id for b in berths]
        assert len(ids) == len(set(ids))

    def test_berths_have_yard_zone(self, berths: list[Berth]) -> None:
        for b in berths:
            assert b.yard_zone_id.startswith("YZ")


# ---------------------------------------------------------------------------
# Crane tests
# ---------------------------------------------------------------------------

class TestCranes:
    def test_crane_count_in_range(self, cranes: list[Crane]) -> None:
        """22–28 quay cranes."""
        assert 22 <= len(cranes) <= 28

    def test_crane_moves_per_hr(self, cranes: list[Crane]) -> None:
        for c in cranes:
            assert 30 <= c.max_moves_per_hr <= 35

    def test_crane_compatibility_non_empty(self, cranes: list[Crane]) -> None:
        for c in cranes:
            assert len(c.compatible_berths) > 0

    def test_crane_ids_unique(self, cranes: list[Crane]) -> None:
        ids = [c.id for c in cranes]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Yard zone tests
# ---------------------------------------------------------------------------

class TestYardZones:
    def test_yard_zone_count(self, yard_zones: list[YardZone]) -> None:
        assert len(yard_zones) == 2

    def test_yard_capacity(self, yard_zones: list[YardZone]) -> None:
        for z in yard_zones:
            assert 8_000 <= z.teu_capacity <= 15_000

    def test_yard_utilization(self, yard_zones: list[YardZone]) -> None:
        for z in yard_zones:
            util = z.current_teu / z.teu_capacity if z.teu_capacity else 0
            assert 0.55 <= util <= 0.75

    def test_yard_dwell(self, yard_zones: list[YardZone]) -> None:
        for z in yard_zones:
            assert 3.0 <= z.avg_dwell_days <= 7.0


# ---------------------------------------------------------------------------
# Alternate port tests
# ---------------------------------------------------------------------------

class TestAltPorts:
    def test_alt_port_count(self, alt_ports: list[AltPort]) -> None:
        assert len(alt_ports) == 2

    def test_transit_hours(self, alt_ports: list[AltPort]) -> None:
        hours = sorted(p.transit_hours for p in alt_ports)
        assert hours[0] == 12.0
        assert hours[1] == 24.0

    def test_berth_capacities(self, alt_ports: list[AltPort]) -> None:
        for p in alt_ports:
            assert p.berth_capacity >= 2

    def test_handling_premium_positive(self, alt_ports: list[AltPort]) -> None:
        for p in alt_ports:
            assert p.handling_premium_usd > 0

    def test_congestion_index_range(self, alt_ports: list[AltPort]) -> None:
        for p in alt_ports:
            assert 0.0 <= p.congestion_index <= 1.0


# ---------------------------------------------------------------------------
# Cross-entity consistency
# ---------------------------------------------------------------------------

class TestConsistency:
    def test_crane_berth_assignment(self, berths: list[Berth], cranes: list[Crane]) -> None:
        """Every crane assigned to a berth must list that berth as compatible."""
        crane_ids = {c.id: c for c in cranes}
        for berth in berths:
            for cid in berth.crane_ids:
                assert cid in crane_ids
                assert berth.id in crane_ids[cid].compatible_berths

    def test_yard_zone_ids_match(self, berths: list[Berth], yard_zones: list[YardZone]) -> None:
        zone_ids = {z.id for z in yard_zones}
        for b in berths:
            assert b.yard_zone_id in zone_ids

    def test_total_cranes_ge_22(self, berths: list[Berth]) -> None:
        total = sum(len(b.crane_ids) for b in berths)
        assert total >= 22

    def test_meta_summary(self, scenario: dict) -> None:
        meta = scenario["meta"]
        assert meta["num_berths"] == 8
        assert meta["num_cranes"] >= 22
        assert meta["num_yard_zones"] == 2
        assert meta["num_alt_ports"] == 2
        assert meta["total_arrivals"] >= 100
        assert meta["yard_util_pct"] >= 50


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestReproducibility:
    def test_same_seed_same_data(self) -> None:
        s1 = generate_scenario(seed=42, weeks=4)
        s2 = generate_scenario(seed=42, weeks=4)
        assert len(s1["vessels"]) == len(s2["vessels"])
        for v1, v2 in zip(s1["vessels"], s2["vessels"]):
            assert v1.id == v2.id
            assert v1.teu_capacity == v2.teu_capacity
            assert v1.eta_h == v2.eta_h

    def test_different_seed_different_data(self) -> None:
        s1 = generate_scenario(seed=42, weeks=4)
        s2 = generate_scenario(seed=99, weeks=4)
        # At least some vessel names should differ
        names1 = {v.name for v in s1["vessels"]}
        names2 = {v.name for v in s2["vessels"]}
        assert names1 != names2
