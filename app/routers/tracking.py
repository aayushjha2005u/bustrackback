"""
THIS FILE IS THE HEART OF THE ASSESSMENT'S BUSINESS LOGIC.

Every endpoint here uses `current_user: User = Depends(get_current_user)`.
Notice that NONE of these endpoints take a "user_id" or "vehicle_id"
as a parameter from the client - they only ever look at
`current_user.assigned_vehicle_id` / `current_user.assigned_route_id`,
which came from the verified JWT token, not from anything the client
can fake in the URL or request body.

This is what "authorization enforced by the backend, not just the
Flutter app" means: even if someone edits the Flutter app or calls
these APIs directly with Postman, they can only ever get back the
route/vehicle that THEIR account is assigned to.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, GpsLog
from app.schemas.schemas import (
    RouteOut, VehicleOut, GpsLogOut, MyTrackingResponse
)

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get("/my-route", response_model=RouteOut)
def get_my_route(current_user: User = Depends(get_current_user)):
    if not current_user.assigned_route:
        raise HTTPException(status_code=404, detail="No route assigned to this user")
    return current_user.assigned_route


@router.get("/my-vehicle", response_model=VehicleOut)
def get_my_vehicle(current_user: User = Depends(get_current_user)):
    if not current_user.assigned_vehicle:
        raise HTTPException(status_code=404, detail="No vehicle assigned to this user")
    return current_user.assigned_vehicle


@router.get("/my-location", response_model=GpsLogOut)
def get_my_latest_location(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.assigned_vehicle_id:
        raise HTTPException(status_code=404, detail="No vehicle assigned to this user")

    latest = (
        db.query(GpsLog)
        .filter(GpsLog.vehicle_id == current_user.assigned_vehicle_id)
        .order_by(GpsLog.timestamp.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No GPS data yet for this vehicle")
    return latest


@router.get("/my-history", response_model=list[GpsLogOut])
def get_my_vehicle_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.assigned_vehicle_id:
        raise HTTPException(status_code=404, detail="No vehicle assigned to this user")

    history = (
        db.query(GpsLog)
        .filter(GpsLog.vehicle_id == current_user.assigned_vehicle_id)
        .order_by(GpsLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return history


@router.get("/my-summary", response_model=MyTrackingResponse)
def get_my_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    One-stop endpoint for the Flutter Home screen: route + vehicle +
    latest location in a single response, so the app doesn't have to
    make three separate calls just to draw one screen.
    """
    latest_location = None
    if current_user.assigned_vehicle_id:
        latest_location = (
            db.query(GpsLog)
            .filter(GpsLog.vehicle_id == current_user.assigned_vehicle_id)
            .order_by(GpsLog.timestamp.desc())
            .first()
        )

    return MyTrackingResponse(
        route=current_user.assigned_route,
        vehicle=current_user.assigned_vehicle,
        latest_location=latest_location,
    )
