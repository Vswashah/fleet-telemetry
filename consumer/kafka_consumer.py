# consumer/kafka_consumer.py
import json
import logging
import os
import time

import psycopg2
import redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC", "vehicle-telemetry")
KAFKA_GROUP     = os.getenv("KAFKA_GROUP", "fleet-consumer-group")
POSTGRES_DSN    = os.getenv("POSTGRES_DSN", "postgresql://fleet:fleet@localhost:5432/fleet_telemetry")
REDIS_HOST      = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT      = int(os.getenv("REDIS_PORT", "6379"))
REDIS_TTL       = int(os.getenv("REDIS_TTL", "300"))
METRICS_PORT    = int(os.getenv("METRICS_PORT", "8000"))

def _counter(name, doc, labels=None):
    try:
        return Counter(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

def _histogram(name, doc, buckets):
    try:
        return Histogram(name, doc, buckets=buckets)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

def _gauge(name, doc):
    try:
        return Gauge(name, doc)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

events_processed_total  = _counter("fleet_events_processed_total", "Total events processed")
events_written_postgres = _counter("fleet_events_written_postgres_total", "Total events written to PostgreSQL")
events_cached_redis     = _counter("fleet_events_cached_redis_total", "Total events cached in Redis")
parse_errors_total      = _counter("fleet_parse_errors_total", "Total message parse failures")
db_errors_total         = _counter("fleet_db_errors_total", "Total PostgreSQL write errors")
processing_latency      = _histogram("fleet_event_processing_latency_seconds", "Processing latency",
                                     [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0])
active_vehicles_gauge   = _gauge("fleet_active_vehicles", "Distinct vehicles seen")
avg_speed_gauge         = _gauge("fleet_average_speed_mph", "Rolling avg speed")
avg_batt_gauge          = _gauge("fleet_average_battery_pct", "Rolling avg battery")


def parse_message(raw: bytes) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("parse_message failed: %s", exc)
        parse_errors_total.inc()
        return None


def write_to_postgres(conn, event: dict) -> bool:
    sql = """
        INSERT INTO telemetry_events
            (vehicle_id, ts, speed_mph, battery_pct, temperature_f,
             latitude, longitude, odometer_miles)
        VALUES
            (%(vehicle_id)s, %(timestamp)s, %(speed_mph)s, %(battery_pct)s,
             %(temperature_f)s, %(latitude)s, %(longitude)s, %(odometer_miles)s)
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, event)
        conn.commit()
        events_written_postgres.inc()
        return True
    except Exception as exc:
        logger.exception("write_to_postgres error: %s", exc)
        db_errors_total.inc()
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def cache_event(redis_client, event: dict) -> bool:
    key = f"fleet:latest:{event['vehicle_id']}"
    try:
        redis_client.set(key, json.dumps(event), ex=REDIS_TTL)
        events_cached_redis.inc()
        return True
    except Exception as exc:
        logger.exception("cache_event error: %s", exc)
        return False


def process_event(raw: bytes, pg_conn, redis_client) -> bool:
    start = time.perf_counter()
    event = parse_message(raw)
    if event is None:
        return False
    ok_pg    = write_to_postgres(pg_conn, event)
    ok_redis = cache_event(redis_client, event)
    processing_latency.observe(time.perf_counter() - start)
    events_processed_total.inc()
    return ok_pg and ok_redis


def run():
    start_http_server(METRICS_PORT)
    pg_conn      = psycopg2.connect(POSTGRES_DSN)
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    from kafka import KafkaConsumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    logger.info("Consumer ready → topic '%s'", KAFKA_TOPIC)
    for msg in consumer:
        process_event(msg.value, pg_conn, redis_client)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
