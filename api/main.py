# api/main.py
import json
import os
import redis
from fastapi import FastAPI, HTTPException
from prometheus_client import make_asgi_app

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = FastAPI(title="Fleet Telemetry API", version="1.0.0")
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

_redis: redis.Redis = None

def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    return _redis


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(
    "/vehicles/{vehicle_id}/latest",
    responses={404: {"description": "No data for vehicle"}},
)
def get_latest(vehicle_id: str):
    r = get_redis()
    raw = r.get(f"fleet:latest:{vehicle_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail=f"No data for vehicle {vehicle_id}")
    return json.loads(raw)


@app.get("/vehicles")
def list_vehicles():
    r = get_redis()
    keys = r.keys("fleet:latest:*")
    return {"vehicles": [k.replace("fleet:latest:", "") for k in keys]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)