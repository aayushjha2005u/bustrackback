"""
Simple setup endpoints so you can create routes, vehicles, and users
(with assignments) without touching the database directly.

Note: in a real production app these would be locked behind an
"admin" role check. For this assessment, keeping them open (or you
can remove this router entirely and use the seed_data.py script
instead) is acceptable - just mention it as a known simplification
in your README.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import User, Route, Vehicle

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateRouteRequest(BaseModel):
    name: str
    description: str | None = None


class CreateVehicleRequest(BaseModel):
    vehicle_code: str
    route_id: int | None = None


class CreateUserRequest(BaseModel):
    username: str
    password: str
    assigned_route_id: int | None = None
    assigned_vehicle_id: int | None = None


@router.post("/routes")
def create_route(payload: CreateRouteRequest, db: Session = Depends(get_db)):
    route = Route(name=payload.name, description=payload.description)
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


@router.post("/vehicles")
def create_vehicle(payload: CreateVehicleRequest, db: Session = Depends(get_db)):
    vehicle = Vehicle(vehicle_code=payload.vehicle_code, route_id=payload.route_id)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.post("/users")
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        assigned_route_id=payload.assigned_route_id,
        assigned_vehicle_id=payload.assigned_vehicle_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}
