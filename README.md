## Live Grafana Dashboard

Real-time telemetry monitoring — throughput, latency, anomaly detection, and fleet metrics.

![Fleet Telemetry Dashboard](assets/grafana_dashboard.png)

### Dashboard Panels
- **Events Received/sec** — Kafka ingestion rate (~70 ops/s)
- **p50/p95/p99 Latency** — End-to-end processing latency
- **Active Vehicles** — Distinct vehicles seen in real time
- **Avg Speed & Battery** — Rolling fleet health metrics
- **Anomalies Detected/min** — Threshold breach monitoring
- **Kafka Consumer Lag** — Pipeline keeping pace with producer
- **PostgreSQL Write Rate** — ~95 ops/s persistent storage
- **Pipeline Throughput** — 79.8 events/sec end to end
