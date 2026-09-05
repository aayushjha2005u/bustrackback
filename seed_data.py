"""
Run this once after starting the backend to populate sample data:
    python seed_data.py

Creates:
- 2 routes (Route A, Route B)
- 2 vehicles (BUS-001 on Route A, BUS-002 on Route B)
- 2 users:
    username: usera  password: pass123  -> assigned Route A + BUS-001
    username: userb  password: pass123  -> assigned Route B + BUS-002

This lets you immediately test the core business rule: log in as
usera, you should ONLY ever see Route A / BUS-001, never userb's data.
"""
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.models import User, Route, Vehicle

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    route_a = Route(name="Route A", description="Downtown -> Airport")
    route_b = Route(name="Route B", description="Suburb -> City Center")
    db.add_all([route_a, route_b])
    db.commit()
    db.refresh(route_a)
    db.refresh(route_b)

    bus_001 = Vehicle(vehicle_code="BUS-001", route_id=route_a.id)
    bus_002 = Vehicle(vehicle_code="BUS-002", route_id=route_b.id)
    db.add_all([bus_001, bus_002])
    db.commit()
    db.refresh(bus_001)
    db.refresh(bus_002)

    user_a = User(
        username="usera",
        hashed_password=hash_password("pass123"),
        assigned_route_id=route_a.id,
        assigned_vehicle_id=bus_001.id,
    )
    user_b = User(
        username="userb",
        hashed_password=hash_password("pass123"),
        assigned_route_id=route_b.id,
        assigned_vehicle_id=bus_002.id,
    )
    db.add_all([user_a, user_b])
    db.commit()

    print("Seed data created successfully:")
    print("  usera / pass123  -> Route A / BUS-001")
    print("  userb / pass123  -> Route B / BUS-002")

except Exception as e:
    print(f"Seeding failed (maybe data already exists?): {e}")
finally:
    db.close()
