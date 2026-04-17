import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def upsert_devices(features: list[dict]) -> None:
    rows = []
    for f in features:
        props = f["properties"]
        coords = f["geometry"]["coordinates"] if f.get("geometry") else None
        if coords is None:
            continue
        rows.append((
            props["traverse_name"],
            props.get("descr_fr"),
            props.get("orientation"),
            props.get("number_of_lanes"),
            coords[0],
            coords[1],
        ))

    sql = """
        INSERT INTO devices (traverse_name, descr_fr, orientation, num_lanes, geom)
        VALUES %s
        ON CONFLICT (traverse_name) DO UPDATE
            SET descr_fr    = EXCLUDED.descr_fr,
                orientation = EXCLUDED.orientation,
                num_lanes   = EXCLUDED.num_lanes,
                geom        = EXCLUDED.geom
    """
    template = "(%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))"
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, rows, template=template)


def insert_readings(data: dict, recorded_at: str) -> None:
    rows = []
    for traverse_name, sensor in data.items():
        result = sensor.get("results", {}).get("1m")
        if result is None:
            continue
        rows.append((
            traverse_name,
            recorded_at,
            1,
            result.get("count"),
            result.get("speed"),
            result.get("occupancy"),
        ))

    sql = """
        INSERT INTO traffic_readings (traverse_name, recorded_at, interval_min, count, speed, occupancy)
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)


def purge_old_readings(retention_days: int) -> None:
    sql = "DELETE FROM traffic_readings WHERE recorded_at < NOW() - INTERVAL '%s days'"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (retention_days,))


def get_latest_readings() -> list[dict]:
    sql = """
        SELECT
            d.traverse_name,
            d.descr_fr,
            d.num_lanes,
            ST_X(d.geom) AS lon,
            ST_Y(d.geom) AS lat,
            r.count,
            r.speed,
            r.occupancy,
            r.recorded_at
        FROM devices d
        LEFT JOIN LATERAL (
            SELECT count, speed, occupancy, recorded_at
            FROM traffic_readings
            WHERE traverse_name = d.traverse_name
            ORDER BY recorded_at DESC
            LIMIT 1
        ) r ON true
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_sensor_history(traverse_name: str, hours: int = 1) -> list[dict]:
    sql = """
        SELECT recorded_at, count, speed, occupancy
        FROM traffic_readings
        WHERE traverse_name = %s
          AND recorded_at >= NOW() - INTERVAL '%s hours'
        ORDER BY recorded_at ASC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (traverse_name, hours))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
