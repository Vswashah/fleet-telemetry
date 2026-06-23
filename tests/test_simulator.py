# tests/test_simulator.py
"""Tests for vehicle_simulator.py — 40 tests."""
import json
import pytest
from datetime import datetime
from simulator.vehicle_simulator import generate_telemetry, simulate_fleet

REQUIRED_FIELDS = [
    "vehicle_id", "timestamp", "speed_mph", "battery_pct",
    "temperature_f", "latitude", "longitude", "odometer_miles",
]


# ── Schema ───────────────────────────────────────────────────────────────────
class TestTelemetrySchema:
    def test_all_required_fields_present(self):
        e = generate_telemetry("VH-0001")
        for f in REQUIRED_FIELDS:
            assert f in e

    def test_no_unexpected_fields(self):
        e = generate_telemetry("VH-0001")
        assert set(e.keys()) == set(REQUIRED_FIELDS)

    def test_vehicle_id_is_string(self):
        assert isinstance(generate_telemetry("VH-0001")["vehicle_id"], str)

    def test_timestamp_is_string(self):
        assert isinstance(generate_telemetry("VH-0001")["timestamp"], str)

    def test_timestamp_parseable_as_iso8601(self):
        ts = generate_telemetry("VH-0001")["timestamp"]
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert dt.tzinfo is not None

    def test_speed_is_float(self):
        assert isinstance(generate_telemetry("VH-0001")["speed_mph"], float)

    def test_battery_is_float(self):
        assert isinstance(generate_telemetry("VH-0001")["battery_pct"], float)

    def test_temperature_is_float(self):
        assert isinstance(generate_telemetry("VH-0001")["temperature_f"], float)

    def test_latitude_is_float(self):
        assert isinstance(generate_telemetry("VH-0001")["latitude"], float)

    def test_longitude_is_float(self):
        assert isinstance(generate_telemetry("VH-0001")["longitude"], float)

    def test_odometer_is_float(self):
        assert isinstance(generate_telemetry("VH-0001")["odometer_miles"], float)

    def test_returns_dict(self):
        assert isinstance(generate_telemetry("VH-0001"), dict)


# ── Ranges ───────────────────────────────────────────────────────────────────
class TestTelemetryRanges:
    N = 50

    @pytest.fixture(scope="class")
    def samples(self):
        return [generate_telemetry(f"VH-{i:04d}") for i in range(self.N)]

    def test_speed_within_0_120(self, samples):
        for e in samples:
            assert 0.0 <= e["speed_mph"] <= 120.0

    def test_battery_within_5_100(self, samples):
        for e in samples:
            assert 5.0 <= e["battery_pct"] <= 100.0

    def test_temperature_within_32_120(self, samples):
        for e in samples:
            assert 32.0 <= e["temperature_f"] <= 120.0

    def test_latitude_within_33_34(self, samples):
        for e in samples:
            assert 33.0 <= e["latitude"] <= 34.0

    def test_longitude_within_neg118_neg117(self, samples):
        for e in samples:
            assert -118.0 <= e["longitude"] <= -117.0

    def test_odometer_within_0_50000(self, samples):
        for e in samples:
            assert 0.0 <= e["odometer_miles"] <= 50000.0

    def test_speed_two_decimal_places(self, samples):
        for e in samples:
            assert round(e["speed_mph"], 2) == e["speed_mph"]

    def test_battery_two_decimal_places(self, samples):
        for e in samples:
            assert round(e["battery_pct"], 2) == e["battery_pct"]

    def test_lat_six_decimal_places(self, samples):
        for e in samples:
            assert round(e["latitude"], 6) == e["latitude"]

    def test_lon_six_decimal_places(self, samples):
        for e in samples:
            assert round(e["longitude"], 6) == e["longitude"]

    def test_odometer_one_decimal_place(self, samples):
        for e in samples:
            assert round(e["odometer_miles"], 1) == e["odometer_miles"]


# ── Vehicle ID propagation ────────────────────────────────────────────────────
class TestVehicleIdPropagation:
    def test_id_matches_input(self):
        for vid in ["VH-0001", "VH-9999", "TRUCK-01", "EV-X"]:
            assert generate_telemetry(vid)["vehicle_id"] == vid

    def test_empty_string_id(self):
        assert generate_telemetry("")["vehicle_id"] == ""

    def test_numeric_string_id(self):
        assert generate_telemetry("12345")["vehicle_id"] == "12345"

    def test_different_vehicles_get_same_schema(self):
        e1 = generate_telemetry("VH-0001")
        e2 = generate_telemetry("VH-0002")
        assert set(e1.keys()) == set(e2.keys())

    def test_same_vehicle_produces_random_events(self):
        speeds = [generate_telemetry("VH-0001")["speed_mph"] for _ in range(20)]
        assert len(set(speeds)) > 1


# ── simulate_fleet generator ─────────────────────────────────────────────────
class TestSimulateFleet:
    def test_yields_dicts(self):
        gen = simulate_fleet(vehicle_count=3)
        assert isinstance(next(gen), dict)

    def test_vehicle_ids_use_zfill_format(self):
        gen = simulate_fleet(vehicle_count=3)
        ids = {next(gen)["vehicle_id"] for _ in range(9)}
        assert any("VH-" in v for v in ids)

    def test_cycles_through_all_vehicles(self):
        gen = simulate_fleet(vehicle_count=4)
        ids = {next(gen)["vehicle_id"] for _ in range(12)}
        assert len(ids) == 4

    def test_default_count_is_10(self):
        gen = simulate_fleet()
        ids = {next(gen)["vehicle_id"] for _ in range(50)}
        assert len(ids) == 10

    def test_single_vehicle(self):
        gen = simulate_fleet(vehicle_count=1)
        for _ in range(5):
            assert next(gen)["vehicle_id"] == "VH-0000"

    def test_is_infinite(self):
        gen = simulate_fleet(vehicle_count=2)
        events = [next(gen) for _ in range(100)]
        assert len(events) == 100

    def test_json_serialisable(self):
        gen = simulate_fleet(vehicle_count=1)
        e = next(gen)
        assert json.loads(json.dumps(e))["vehicle_id"] == e["vehicle_id"]