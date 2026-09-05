"""
Entry point. Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Then open http://localhost:8000/docs for interactive API docs
(FastAPI generates this automatically - use it to test every
endpoint from the browser before wiring up Flutter).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.mqtt_listener import start_mqtt_listener
from app.routers import auth, tracking, gps, admin

# Creates all tables defined in app/models/models.py if they don't
# already exist. For a real production system you'd use Alembic
# migrations instead, but this is fine for an assessment.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bus Tracking System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Flutter app can call from anywhere during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tracking.router)
app.include_router(gps.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup():
    start_mqtt_listener()


@app.get("/")
def root():
    return {"status": "ok", "message": "Bus Tracking System API is running"}
