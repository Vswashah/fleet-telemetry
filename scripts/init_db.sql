-- Fleet Telemetry — PostgreSQL schema
CREATE TABLE IF NOT EXISTS telemetry_events (
    id              BIGSERIAL PRIMARY KEY,
    vehicle_id      VARCHAR(64)     NOT NULL,
    ts              TIMESTAMPTZ     NOT NULL,
    speed_mph       NUMERIC(6, 2)   NOT NULL,
    battery_pct     NUMERIC(5, 2)   NOT NULL,
    temperature_f   NUMERIC(6, 2)   NOT NULL,
    latitude        NUMERIC(10, 6)  NOT NULL,
    longitude       NUMERIC(10, 6)  NOT NULL,
    odometer_miles  NUMERIC(10, 1)  NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tel_vehicle ON telemetry_events (vehicle_id);
CREATE INDEX IF NOT EXISTS idx_tel_ts      ON telemetry_events (ts DESC);

CREATE TABLE IF NOT EXISTS anomaly_events (
    id          BIGSERIAL PRIMARY KEY,
    vehicle_id  VARCHAR(64)  NOT NULL,
    ts          TIMESTAMPTZ  NOT NULL,
    reason      TEXT         NOT NULL,
    raw_event   JSONB        NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anom_vehicle ON anomaly_events (vehicle_id);
CREATE INDEX IF NOT EXISTS idx_anom_ts      ON anomaly_events (ts DESC);