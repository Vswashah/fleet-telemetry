# simulator/vehicle_simulator.py
import random
import time
import json
from datetime import datetime, timezone

def generate_telemetry(vehicle_id: str) -> dict:
    """Generate a single telemetry event for a vehicle."""
    return {
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "speed_mph": round(random.uniform(0, 120), 2),
        "battery_pct": round(random.uniform(5, 100), 2),
        "temperature_f": round(random.uniform(32, 120), 2),
        "latitude": round(random.uniform(33.0, 34.0), 6),
        "longitude": round(random.uniform(-118.0, -117.0), 6),
        "odometer_miles": round(random.uniform(0, 50000), 1),
    }

def simulate_fleet(vehicle_count: int = 10):
    """Continuously generate telemetry for a fleet of vehicles."""
    vehicles = [f"VH-{str(i).zfill(4)}" for i in range(vehicle_count)]
    
    while True:
        for vehicle_id in vehicles:
            event = generate_telemetry(vehicle_id)
            yield event
        time.sleep(0.1)

if __name__ == "__main__":
    print("Simulating 3 vehicles...")
    count = 0
    for event in simulate_fleet(vehicle_count=3):
        print(json.dumps(event, indent=2))
        count += 1
        if count >= 5:
            break