# Brussels Traffic Live Map

A pedagogical open-source GIS project that automates the collection of real-time road traffic data from Brussels and displays it on an interactive map.

The goal is to learn **open-source alternatives to Windows Task Scheduler** for data pipeline automation, using a live traffic feed as a concrete use case.

## What it does

- Fetches live traffic data from the [Brussels Mobility API](https://data.mobility.brussels/traffic/api/counts/) every minute (88 sensors across the city)
- Stores historical readings (speed, vehicle count, occupancy) in a PostGIS database
- Exposes a GeoJSON API via FastAPI
- Displays a live map in Leaflet with color-coded sensors updated automatically

## Architecture

```
[Brussels Mobility API]  →  [APScheduler]  →  [PostGIS]
         (every 60s)                               ↓
                                           [FastAPI endpoints]
                                                   ↓
                                           [Leaflet.js map]
```

| Component | Tool | Esri equivalent |
|-----------|------|----------------|
| Scheduler | APScheduler (Python) | Windows Task Scheduler |
| Database | PostgreSQL + PostGIS | ArcGIS Geodatabase |
| API | FastAPI | ArcGIS REST Services |
| Frontend | Leaflet.js | ArcGIS Maps SDK |
| Infrastructure | Docker Compose | — |

## Data source

The [Brussels Mobility open API](https://data.mobility.brussels/traffic/api/counts/) provides:

- **`?request=devices`** — GeoJSON with sensor locations (static)
- **`?request=live&interval=1`** — Live readings: vehicle count, average speed (km/h), occupancy (%), updated every minute

No authentication required.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [gh](https://cli.github.com/) (optional, for GitHub operations)

## Getting started

```bash
git clone https://github.com/martinbaufayt/brussels-trafic.git
cd brussels-trafic
docker compose up
```

Open [http://localhost:8000](http://localhost:8000) — the map loads immediately and refreshes every 60 seconds.

## API endpoints

| Route | Description |
|-------|-------------|
| `GET /api/devices` | GeoJSON FeatureCollection — all sensors with their latest reading |
| `GET /api/history/{sensor_id}` | Time series for one sensor (rolling 1-hour window) |

```bash
# Latest readings for all sensors
curl http://localhost:8000/api/devices

# History for a specific sensor
curl http://localhost:8000/api/history/ARL_103
```

## Map legend

Sensors are color-coded by the latest average speed:

- **Red** — below 20 km/h (congestion)
- **Orange** — 20–50 km/h (slow traffic)
- **Green** — above 50 km/h (free flow)

Click a sensor to see its current count, speed, occupancy, and a link to its 1-hour history.

## Project structure

```
brussels-trafic/
├── docker-compose.yml
├── sql/
│   └── init.sql          # PostGIS schema
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py           # FastAPI app + lifespan
│   ├── scheduler.py      # APScheduler jobs
│   ├── fetcher.py        # Brussels Mobility API client
│   └── db.py             # PostGIS connection + helpers
└── frontend/
    ├── index.html
    └── map.js            # Leaflet map with auto-refresh
```

## Key concepts covered

- **Scheduled automation** with APScheduler (`AsyncIOScheduler`, interval jobs, startup jobs)
- **Spatial data in PostgreSQL** with PostGIS (`GEOMETRY(Point, 4326)`, spatial indexes)
- **Serving GeoJSON** from a database via FastAPI
- **Docker Compose** for multi-service local development (database + API as separate containers)

> [!NOTE]
> This project is intentionally kept simple. It uses APScheduler embedded in FastAPI rather than a dedicated orchestration tool (Prefect, Dagster, Airflow) — a good next step once the fundamentals are clear.

## Data retention

With 88 sensors and a 1-minute collection interval, the `traffic_readings` table grows at roughly **~450 MB/month** (~3.8M rows). Without cleanup, the database becomes unmanageable within weeks.

A daily APScheduler job purges readings older than 30 days:

```python
scheduler.add_job(purge_old_readings, "interval", hours=24)
```

```sql
DELETE FROM traffic_readings WHERE recorded_at < NOW() - INTERVAL '30 days';
```

Adjust the retention window by changing the `RETENTION_DAYS` environment variable (default: `30`).
