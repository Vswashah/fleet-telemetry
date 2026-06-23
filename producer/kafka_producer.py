# producer/kafka_producer.py
import json
import logging
import os
import time
from kafka import KafkaProducer
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

TOPIC = "vehicle-telemetry"
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Metrics
events_produced_total = Counter(
    "fleet_events_produced_total",
    "Total telemetry events sent to Kafka",
)
produce_latency = Histogram(
    "fleet_produce_latency_seconds",
    "Time to send a single event to Kafka",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5],
)
produce_errors_total = Counter(
    "fleet_produce_errors_total",
    "Total Kafka send failures",
)

_producer_instance = None


def get_producer() -> KafkaProducer:
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=3,
            linger_ms=5,
        )
    return _producer_instance


def send_event(event: dict, producer: KafkaProducer = None) -> bool:
    """Send a single telemetry event to Kafka. Returns True on success."""
    _p = producer or get_producer()
    start = time.perf_counter()
    try:
        _p.send(TOPIC, value=event)
        _p.flush()
        produce_latency.observe(time.perf_counter() - start)
        events_produced_total.inc()
        logger.debug("Sent event for vehicle %s", event.get("vehicle_id"))
        return True
    except Exception as exc:
        produce_errors_total.inc()
        logger.exception("Failed to send event to Kafka: %s", exc)
        return False


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from simulator.vehicle_simulator import simulate_fleet
    from prometheus_client import start_http_server

    logging.basicConfig(level=logging.INFO)
    start_http_server(int(os.getenv("METRICS_PORT", "8001")))
    logger.info("Producer started → topic '%s' on %s", TOPIC, BOOTSTRAP_SERVERS)

    for event in simulate_fleet(vehicle_count=int(os.getenv("VEHICLE_COUNT", "10"))):
        send_event(event)
        time.sleep(float(os.getenv("PRODUCE_INTERVAL_S", "0.1")))