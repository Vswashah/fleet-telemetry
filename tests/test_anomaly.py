# tests/test_anomaly.py
"""Tests for anomaly detector — 15 tests."""
import pytest
from anomaly.detector import is_anomaly, get_anomaly_reason, classify_event

BASE = {
    "vehicle_id": "VH-0001",
    "speed_mph": 60.0,
    "battery_pct": 75.0,
    "temperature_f": 85.0,
}


class TestIsAnomaly:
    def test_normal_event_returns_false(self):
        assert is_anomaly(BASE) is False

    def test_critical_speed_returns_true(self):
        assert is_anomaly({**BASE, "speed_mph": 115.0}) is True

    def test_critical_low_battery_returns_true(self):
        assert is_anomaly({**BASE, "battery_pct": 8.0}) is True

    def test_critical_high_temp_returns_true(self):
        assert is_anomaly({**BASE, "temperature_f": 115.0}) is True

    def test_speed_just_below_critical_not_anomaly(self):
        assert is_anomaly({**BASE, "speed_mph": 114.9}) is False

    def test_battery_just_above_critical_not_anomaly(self):
        assert is_anomaly({**BASE, "battery_pct": 8.1}) is False

    def test_returns_bool(self):
        assert isinstance(is_anomaly(BASE), bool)


class TestGetAnomalyReason:
    def test_normal_returns_none(self):
        assert get_anomaly_reason(BASE) is None

    def test_speed_reason_mentions_speed(self):
        r = get_anomaly_reason({**BASE, "speed_mph": 115.0})
        assert "speed" in r.lower()

    def test_battery_reason_mentions_battery(self):
        r = get_anomaly_reason({**BASE, "battery_pct": 8.0})
        assert "battery" in r.lower()

    def test_temp_reason_mentions_temperature(self):
        r = get_anomaly_reason({**BASE, "temperature_f": 115.0})
        assert "temperature" in r.lower()

    def test_reason_is_string_when_anomaly(self):
        r = get_anomaly_reason({**BASE, "speed_mph": 115.0})
        assert isinstance(r, str)


class TestClassifyEvent:
    def test_normal_classification(self):
        assert classify_event(BASE) == "normal"

    def test_critical_classification_speed(self):
        assert classify_event({**BASE, "speed_mph": 115.0}) == "critical"

    def test_warn_classification_speed(self):
        assert classify_event({**BASE, "speed_mph": 102.0}) == "warn"