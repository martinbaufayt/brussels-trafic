import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import db
import fetcher

logger = logging.getLogger(__name__)
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", 30))


def init_devices() -> None:
    logger.info("Fetching sensor locations from Brussels Mobility API...")
    geojson = fetcher.fetch_devices()
    features = geojson.get("features", [])
    db.upsert_devices(features)
    logger.info("Upserted %d devices.", len(features))


def collect_live() -> None:
    payload = fetcher.fetch_live()
    recorded_at = payload["requestDate"]
    db.insert_readings(payload["data"], recorded_at)
    logger.info("Inserted readings at %s.", recorded_at)


def purge_old() -> None:
    db.purge_old_readings(RETENTION_DAYS)
    logger.info("Purged readings older than %d days.", RETENTION_DAYS)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(init_devices, "date")
    scheduler.add_job(collect_live, "interval", minutes=1)
    scheduler.add_job(purge_old, "interval", hours=24)
    return scheduler
