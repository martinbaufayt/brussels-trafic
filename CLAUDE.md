# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Pedagogical open-source GIS project: automated pipeline collecting live Brussels road traffic data (88 sensors, updated every minute) and displaying it on an interactive map.

## Stack

| Role | Tool |
|------|------|
| Scheduler | APScheduler 3.x (AsyncIOScheduler, embedded in FastAPI) |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Backend API | FastAPI + psycopg2 |
| HTTP client | httpx |
| Frontend | Leaflet.js (vanilla JS, no framework) |
| Infrastructure | Docker Compose |

## Architecture

```
Brussels Mobility API  →  APScheduler (every 1min)  →  PostGIS
                                                           ↓
                                                     FastAPI endpoints
                                                           ↓
                                                     Leaflet.js map
```

## Development

```bash
docker compose down && docker compose build --no-cache api && docker compose up
# full rebuild required after any change to api/*.py

docker compose up
# frontend changes (frontend/*.html, frontend/*.js) apply without rebuild

docker compose logs -f api      # scheduler logs + HTTP requests
docker compose logs -f db       # PostgreSQL logs
```

## Key files

- [api/scheduler.py](api/scheduler.py) — 3 APScheduler jobs: `init_devices` (once at startup), `collect_live` (every 1min), `purge_old` (every 24h)
- [api/db.py](api/db.py) — all PostGIS queries: upsert devices, insert readings, purge, GeoJSON query
- [api/fetcher.py](api/fetcher.py) — thin wrapper around the Brussels Mobility API
- [api/main.py](api/main.py) — FastAPI app, lifespan (scheduler start/stop), 2 endpoints
- [sql/init.sql](sql/init.sql) — schema run once at DB container creation (re-run requires `docker compose down -v`)

## Data source

`https://data.mobility.brussels/traffic/api/counts/`
- `?request=devices` → GeoJSON, sensor locations (static)
- `?request=live&interval=1&singleValue=true` → live readings (count, speed km/h, occupancy %)

## Environment variables

Copy `.env.example` to `.env` (not committed):

```
DATABASE_URL=postgresql://postgres:postgres@db:5432/traffic
RETENTION_DAYS=30
```

## Mac / Docker notes

- Port `5432` may conflict with a local PostgreSQL instance — the db service exposes `5433:5432`
- The PostGIS image (`postgis/postgis:16-3.4`) is amd64-only; Docker Desktop runs it via Rosetta 2 on Apple Silicon — the platform warning is benign, do not add `platform: linux/arm64`
- Frontend files are volume-mounted (`./frontend:/app/frontend`) — no rebuild needed for JS/HTML changes
- Python changes in `api/` always require `docker compose build --no-cache api`
