# tests/test_consumer.py
"""Tests for Kafka consumer pipeline — 16 tests."""
import json
import pytest
from unittest.mock import MagicMock, patch

# Stub out heavy deps before import
import sys
for mod in ("kafka", "psycopg2", "redis", "prometheus_client"):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from consumer.kafka_consumer import parse_message, write_to_postgres, cache_event, process_event

SAMPLE = {
    "vehicle_id": "VH-0001",
    "timestamp": "2026-06-20T12:00:00+00:00",
    "speed_mph": 65.50,
    "battery_pct": 78.32,
    "temperature_f": 95.10,
    "latitude": 33.748992,
    "longitude": -117.453049,
    "odometer_miles": 12350.5,
}


class TestParseMessage:
    def test_valid_json_returns_dict(self):
        result = parse_message(json.dumps(SAMPLE).encode())
        assert isinstance(result, dict)

    def test_vehicle_id_preserved(self):
        result = parse_message(json.dumps(SAMPLE).encode())
        assert result["vehicle_id"] == "VH-0001"

    def test_all_fields_preserved(self):
        result = parse_message(json.dumps(SAMPLE).encode())
        assert set(result.keys()) == set(SAMPLE.keys())

    def test_invalid_json_returns_none(self):
        assert parse_message(b"{bad json{{") is None

    def test_empty_bytes_returns_none(self):
        assert parse_message(b"") is None

    def test_numeric_types_preserved(self):
        result = parse_message(json.dumps(SAMPLE).encode())
        assert isinstance(result["speed_mph"], float)
        assert isinstance(result["battery_pct"], float)


class TestWriteToPostgres:
    def _make_conn(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return conn, cursor

    def test_calls_execute(self):
        conn, cursor = self._make_conn()
        write_to_postgres(conn, SAMPLE)
        cursor.execute.assert_called_once()

    def test_commits_on_success(self):
        conn, _ = self._make_conn()
        write_to_postgres(conn, SAMPLE)
        conn.commit.assert_called_once()

    def test_returns_true_on_success(self):
        conn, _ = self._make_conn()
        assert write_to_postgres(conn, SAMPLE) is True

    def test_returns_false_on_db_error(self):
        conn, cursor = self._make_conn()
        cursor.execute.side_effect = Exception("DB error")
        assert write_to_postgres(conn, SAMPLE) is False

    def test_rolls_back_on_error(self):
        conn, cursor = self._make_conn()
        cursor.execute.side_effect = Exception("DB error")
        write_to_postgres(conn, SAMPLE)
        conn.rollback.assert_called_once()


class TestCacheEvent:
    def test_calls_redis_set(self):
        r = MagicMock()
        cache_event(r, SAMPLE)
        r.set.assert_called_once()

    def test_key_contains_vehicle_id(self):
        r = MagicMock()
        cache_event(r, SAMPLE)
        key = r.set.call_args[0][0]
        assert "VH-0001" in key

    def test_sets_ttl(self):
        r = MagicMock()
        cache_event(r, SAMPLE)
        _, kwargs = r.set.call_args
        assert kwargs.get("ex") is not None

    def test_value_is_valid_json(self):
        r = MagicMock()
        cache_event(r, SAMPLE)
        value = r.set.call_args[0][1]
        assert json.loads(value)["vehicle_id"] == "VH-0001"

    def test_returns_false_on_redis_error(self):
        r = MagicMock()
        r.set.side_effect = Exception("Redis down")
        assert cache_event(r, SAMPLE) is False


class TestProcessEvent:
    def _make_pg(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return conn

    def test_full_pipeline_returns_true(self):
        conn = self._make_pg()
        r = MagicMock()
        result = process_event(json.dumps(SAMPLE).encode(), conn, r)
        assert result is True

    def test_invalid_message_returns_false(self):
        conn = self._make_pg()
        r = MagicMock()
        assert process_event(b"bad json", conn, r) is False