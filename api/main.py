import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

import db
import scheduler as sched

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = sched.create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Brussels Traffic API", lifespan=lifespan)


@app.get("/api/devices")
def devices():
    rows = db.get_latest_readings()
    features = []
    for r in rows:
        if r["lon"] is None or r["lat"] is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "traverse_name": r["traverse_name"],
                "descr_fr": r["descr_fr"],
                "num_lanes": r["num_lanes"],
                "count": r["count"],
                "speed": r["speed"],
                "occupancy": r["occupancy"],
                "recorded_at": r["recorded_at"].isoformat() if r["recorded_at"] else None,
            },
        })
    return {"type": "FeatureCollection", "features": features}


@app.get("/api/history/{traverse_name}")
def history(traverse_name: str, hours: int = 1):
    rows = db.get_sensor_history(traverse_name, hours)
    if not rows:
        raise HTTPException(status_code=404, detail="No data found for this sensor.")
    return [
        {
            "recorded_at": r["recorded_at"].isoformat(),
            "count": r["count"],
            "speed": r["speed"],
            "occupancy": r["occupancy"],
        }
        for r in rows
    ]


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
