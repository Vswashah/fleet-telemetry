# anomaly/detector.py
import logging

logger = logging.getLogger(__name__)

THRESHOLDS = {
    "speed_mph":     {"warn": 100.0, "critical": 115.0},
    "battery_pct":   {"warn": 15.0,  "critical": 8.0},
    "temperature_f": {"warn": 105.0, "critical": 115.0},
}

def is_anomaly(event: dict) -> bool:
    if event.get("speed_mph", 0) >= THRESHOLDS["speed_mph"]["critical"]:
        return True
    if event.get("battery_pct", 100) <= THRESHOLDS["battery_pct"]["critical"]:
        return True
    if event.get("temperature_f", 70) >= THRESHOLDS["temperature_f"]["critical"]:
        return True
    return False

def get_anomaly_reason(event: dict) -> str | None:
    speed = event.get("speed_mph", 0)
    if speed >= THRESHOLDS["speed_mph"]["critical"]:
        return f"speed anomaly: {speed} mph >= critical {THRESHOLDS['speed_mph']['critical']}"
    batt = event.get("battery_pct", 100)
    if batt <= THRESHOLDS["battery_pct"]["critical"]:
        return f"battery anomaly: {batt}% <= critical {THRESHOLDS['battery_pct']['critical']}"
    temp = event.get("temperature_f", 70)
    if temp >= THRESHOLDS["temperature_f"]["critical"]:
        return f"temperature anomaly: {temp}°F >= critical {THRESHOLDS['temperature_f']['critical']}"
    return None

def classify_event(event: dict) -> str:
    speed = event.get("speed_mph", 0)
    batt  = event.get("battery_pct", 100)
    temp  = event.get("temperature_f", 70)
    if (speed >= THRESHOLDS["speed_mph"]["critical"] or
            batt <= THRESHOLDS["battery_pct"]["critical"] or
            temp >= THRESHOLDS["temperature_f"]["critical"]):
        return "critical"
    if (speed >= THRESHOLDS["speed_mph"]["warn"] or
            batt <= THRESHOLDS["battery_pct"]["warn"] or
            temp >= THRESHOLDS["temperature_f"]["warn"]):
        return "warn"
    return "normal"
