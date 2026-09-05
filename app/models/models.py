"""
These classes define our database tables.

Relationship logic (the "important business logic" from the task):
- Each User has ONE assigned_route_id and ONE assigned_vehicle_id.
- Each Vehicle sends many GpsLog entries over time (its location history).
- A Route can have many vehicles/users over time, but each user only
  ever sees the ONE route + ONE vehicle assigned to THEM.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Each user is assigned exactly one route and one vehicle.
    assigned_route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)

    assigned_route = relationship("Route", back_populates="users")
    assigned_vehicle = relationship("Vehicle", back_populates="users")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)   # e.g. "Route A"
    description = Column(String, nullable=True)                     # e.g. "Downtown -> Airport"

    users = relationship("User", back_populates="assigned_route")
    vehicles = relationship("Vehicle", back_populates="route")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_code = Column(String, unique=True, index=True, nullable=False)  # e.g. "BUS-001"
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)

    route = relationship("Route", back_populates="vehicles")
    users = relationship("User", back_populates="assigned_vehicle")
    gps_logs = relationship("GpsLog", back_populates="vehicle", order_by="GpsLog.timestamp.desc()")


class GpsLog(Base):
    """
    Every GPS ping received from a vehicle (via MQTT or REST) becomes
    one row here. We never overwrite old data - the "latest location"
    is just the most recent row for that vehicle, and "historical data"
    is every row. This is simple and works fine for an assessment-scale system.
    """
    __tablename__ = "gps_logs"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    vehicle = relationship("Vehicle", back_populates="gps_logs")
