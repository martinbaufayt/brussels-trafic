# Brussels Traffic Live

A pedagogical open-source GIS project that automates the collection of real-time road traffic data from Brussels and displays it on an interactive map.

The goal is to learn **open-source alternatives to Windows Task Scheduler** for data pipeline automation, using a live traffic feed as a concrete use case.

[![CI](https://github.com/martinbaufayt/brussels-trafic/actions/workflows/ci.yml/badge.svg)](https://github.com/martinbaufayt/brussels-trafic/actions/workflows/ci.yml)

![Screenshot](docs/screenshot.png)

## What it does

- Fetches live traffic data from the [Brussels Mobility API](https://data.mobility.brussels/traffic/api/counts/) every minute (88 sensors across the city)
- Stores historical readings (speed, vehicle count, occupancy) in a PostGIS database, with automatic purge after 30 days
- Exposes a GeoJSON API via FastAPI
- Displays a live map in Leaflet with color-coded sensors, refreshed automatically every minute

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
| Database | PostgreSQL 16 + PostGIS 3.4 | ArcGIS Geodatabase |
| API | FastAPI | ArcGIS REST Services |
| Frontend | Leaflet.js | ArcGIS Maps SDK |
| Infrastructure | Docker Compose | — |

## Data source

The [Brussels Mobility open API](https://data.mobility.brussels/traffic/api/counts/) provides:

- **`?request=devices`** — GeoJSON with sensor locations (static, loaded at startup)
- **`?request=live&interval=1`** — Live readings: vehicle count, average speed (km/h), occupancy (%), updated every minute

No authentication required.

> [!NOTE]
> Some sensors transmit timestamps with all-null measurements. These are excluded from the map automatically.

## Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/)

## Getting started

```bash
git clone https://github.com/martinbaufayt/brussels-trafic.git
cd brussels-trafic
cp .env.example .env
docker compose up
```

Open [http://localhost:8000](http://localhost:8000). The map loads immediately and refreshes every 60 seconds. Data starts appearing after the first scheduler tick (~1 minute).

## API endpoints

| Route | Description |
|-------|-------------|
| `GET /api/devices` | GeoJSON FeatureCollection — all sensors with their latest reading |
| `GET /api/history/{sensor_id}?hours=1` | Time series for one sensor (rolling window, default 1h) |

```bash
curl http://localhost:8000/api/devices
curl http://localhost:8000/api/history/ARL_103
```

## Map legend

Sensors are color-coded by the latest average speed:

- **Red** — below 20 km/h (congestion)
- **Orange** — 20–50 km/h (slow traffic)
- **Green** — above 50 km/h (free flow)

Only sensors with at least one valid measurement are displayed. Click a sensor to see its current count, speed and occupancy.

## Project structure

```
brussels-trafic/
├── docker-compose.yml
├── .env.example
├── sql/
│   └── init.sql          # PostGIS schema (auto-run at DB creation)
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py           # FastAPI app + lifespan
│   ├── scheduler.py      # APScheduler jobs (init, collect, purge)
│   ├── fetcher.py        # Brussels Mobility API client
│   └── db.py             # PostGIS connection + queries
└── frontend/
    ├── index.html
    └── map.js            # Leaflet map with auto-refresh
```

## Data retention

With 88 sensors and a 1-minute collection interval, the `traffic_readings` table grows at roughly **~450 MB/month**. A daily APScheduler job automatically purges readings older than `RETENTION_DAYS` (default: 30).

## Key concepts covered

- **Scheduled automation** with APScheduler (`AsyncIOScheduler`, interval jobs, one-shot startup job, daily maintenance job)
- **Spatial data in PostgreSQL** with PostGIS (`GEOMETRY(Point, 4326)`, spatial index, `ST_MakePoint`)
- **Serving GeoJSON** from a PostGIS query via FastAPI
- **Docker Compose** for multi-service local development with health checks and dependency ordering
- **GitHub Actions** CI that validates the Docker build on every push

> [!NOTE]
> This project uses APScheduler embedded in FastAPI rather than a dedicated orchestration tool (Prefect, Dagster, Airflow). A natural next step once the fundamentals are clear.
