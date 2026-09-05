"""
MQTT is the preferred GPS ingestion method per the task. Here's how
it works:

1. Each vehicle (or our simulator) publishes a JSON message to a
   topic like "vehicles/BUS-001/gps" containing lat/long/speed.
2. This listener subscribes to "vehicles/+/gps" (the + is a wildcard
   meaning "any vehicle code") using the MQTT broker.
3. Whenever a message arrives, we parse it and save it to the
   gps_logs table - the exact same table the REST /gps/ingest
   endpoint writes to.

This runs as a background thread started from main.py on app startup,
so the FastAPI server and the MQTT listener run side by side in the
same process.
"""
import json
import threading
import paho.mqtt.client as mqtt

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Vehicle, GpsLog


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe(settings.MQTT_TOPIC)
    print(f"[MQTT] Subscribed to {settings.MQTT_TOPIC}")


def on_message(client, userdata, msg):
    """
    Expected payload (JSON):
    {
        "vehicle_code": "BUS-001",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "speed": 42.5
    }
    """
    try:
        data = json.loads(msg.payload.decode())
        vehicle_code = data["vehicle_code"]
        latitude = data["latitude"]
        longitude = data["longitude"]
        speed = data.get("speed")

        db = SessionLocal()
        try:
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_code == vehicle_code).first()
            if not vehicle:
                print(f"[MQTT] Unknown vehicle_code: {vehicle_code}, ignoring message")
                return

            log = GpsLog(
                vehicle_id=vehicle.id,
                latitude=latitude,
                longitude=longitude,
                speed=speed,
            )
            db.add(log)
            db.commit()
            print(f"[MQTT] Saved GPS for {vehicle_code}: ({latitude}, {longitude})")
        finally:
            db.close()

    except Exception as e:
        print(f"[MQTT] Failed to process message: {e}")


def start_mqtt_listener():
    """Called once at FastAPI startup. Runs in a background thread
    so it doesn't block the API server."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    def _run():
        try:
            client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Could not connect to broker: {e}")
            print("[MQTT] GPS ingestion will still work via the REST /gps/ingest endpoint.")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
