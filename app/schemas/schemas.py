"""
Pydantic schemas control what data comes IN to an endpoint and what
goes OUT. This is separate from the SQLAlchemy models on purpose:
e.g. we never want to accidentally send hashed_password back in a
response, so the "out" schema for User simply doesn't include it.
"""
from pydantic import BaseModel
from datetime import datetime


# ---------- Auth ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Route ----------

class RouteOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


# ---------- Vehicle ----------

class VehicleOut(BaseModel):
    id: int
    vehicle_code: str
    route_id: int | None = None

    class Config:
        from_attributes = True


# ---------- GPS ----------

class GpsIngestRequest(BaseModel):
    """What a vehicle/simulator sends us to report its location."""
    vehicle_code: str
    latitude: float
    longitude: float
    speed: float | None = None


class GpsLogOut(BaseModel):
    id: int
    vehicle_id: int
    latitude: float
    longitude: float
    speed: float | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ---------- Combined "my tracking info" response ----------

class MyTrackingResponse(BaseModel):
    """
    This is the single endpoint the Flutter Home screen will call.
    It bundles the user's route, vehicle, and latest location together
    so the app doesn't need 3 separate calls.
    """
    route: RouteOut | None
    vehicle: VehicleOut | None
    latest_location: GpsLogOut | None
