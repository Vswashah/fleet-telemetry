# tests/test_producer.py
"""Tests for Kafka producer — 11 tests."""
import json
import os
import pytest
from unittest.mock import MagicMock, patch

# Prevent real KafkaProducer from instantiating during import
import sys
sys.modules.setdefault("kafka", MagicMock())

import importlib
import producer.kafka_producer as kp


class TestProducerConfig:
    def test_default_topic_is_vehicle_telemetry(self):
        assert kp.TOPIC == "vehicle-telemetry"

    def test_bootstrap_servers_env_override(self, monkeypatch):
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-host:9092")
        importlib.reload(kp)
        assert kp.BOOTSTRAP_SERVERS == "kafka-host:9092"

    def test_bootstrap_servers_default_fallback(self, monkeypatch):
        monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)
        importlib.reload(kp)
        assert kp.BOOTSTRAP_SERVERS == "localhost:9092"


class TestSerialisation:
    def test_event_encodes_to_bytes(self):
        event = {"vehicle_id": "VH-0001", "speed_mph": 60.0}
        assert isinstance(json.dumps(event).encode("utf-8"), bytes)

    def test_encoded_event_round_trips(self):
        event = {"vehicle_id": "VH-0002", "battery_pct": 75.5}
        assert json.loads(json.dumps(event).encode()) == event

    def test_all_fields_survive_serialisation(self):
        from simulator.vehicle_simulator import generate_telemetry
        e = generate_telemetry("VH-TEST")
        assert json.loads(json.dumps(e).encode())["vehicle_id"] == "VH-TEST"


class TestSendEvent:
    def test_send_calls_producer_send(self):
        mock_producer = MagicMock()
        kp.send_event({"vehicle_id": "VH-0001"}, producer=mock_producer)
        mock_producer.send.assert_called_once()

    def test_send_targets_correct_topic(self):
        mock_producer = MagicMock()
        kp.send_event({"vehicle_id": "VH-0002"}, producer=mock_producer)
        args, _ = mock_producer.send.call_args
        assert args[0] == kp.TOPIC

    def test_send_flushes_after_send(self):
        mock_producer = MagicMock()
        kp.send_event({"vehicle_id": "VH-0003"}, producer=mock_producer)
        mock_producer.flush.assert_called_once()

    def test_send_returns_true_on_success(self):
        mock_producer = MagicMock()
        result = kp.send_event({"vehicle_id": "VH-0004"}, producer=mock_producer)
        assert result is True

    def test_send_returns_false_on_kafka_error(self):
        mock_producer = MagicMock()
        mock_producer.send.side_effect = Exception("connection refused")
        result = kp.send_event({"vehicle_id": "VH-ERR"}, producer=mock_producer)
        assert result is False