CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS devices (
    traverse_name TEXT PRIMARY KEY,
    descr_fr      TEXT,
    orientation   FLOAT,
    num_lanes     INT,
    geom          GEOMETRY(Point, 4326)
);

CREATE INDEX IF NOT EXISTS devices_geom_idx ON devices USING GIST (geom);

CREATE TABLE IF NOT EXISTS traffic_readings (
    id            SERIAL PRIMARY KEY,
    traverse_name TEXT REFERENCES devices(traverse_name),
    recorded_at   TIMESTAMPTZ NOT NULL,
    interval_min  INT,
    count         INT,
    speed         FLOAT,
    occupancy     FLOAT
);

CREATE INDEX IF NOT EXISTS readings_sensor_time_idx
    ON traffic_readings (traverse_name, recorded_at DESC);
