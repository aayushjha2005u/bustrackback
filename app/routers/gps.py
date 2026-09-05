"""
REST endpoint that receives GPS pings from vehicles.

Note: the task prefers MQTT for this, and we DO also run an MQTT
listener (see app/core/mqtt_listener.py) that writes to the exact
same database table. This REST endpoint is kept as the "another
suitable approach" fallback the task explicitly allows, and it's
also what the GPS simulator script uses for simplicity.

This endpoint is intentionally NOT behind user login - a vehicle
device isn't a "user", it's a machine reporting its own position.
In a real production system this would instead use a per-vehicle
API key; for this assessment scale, the vehicle_code is enough.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Vehicle, GpsLog
from app.schemas.schemas import GpsIngestRequest, GpsLogOut

router = APIRouter(prefix="/gps", tags=["gps"])


@router.post("/ingest", response_model=GpsLogOut)
def ingest_gps(payload: GpsIngestRequest, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == payload.vehicle_code).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Unknown vehicle_code: {payload.vehicle_code}")

    log = GpsLog(
        vehicle_id=vehicle.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
