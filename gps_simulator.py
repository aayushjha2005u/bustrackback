"""
Simple GPS simulator (bonus task).

This pretends to be a real vehicle: every few seconds it "moves" a
tiny bit and publishes its new coordinates to MQTT. Run it alongside
the backend + MQTT broker to see live data flowing in without needing
a real GPS device.

Run with:
    python gps_simulator.py
"""
import json
import random
import time
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Simulate two vehicles moving around, starting near New Delhi.
VEHICLES = {
    "BUS-001": {"lat": 28.6139, "lon": 77.2090},
    "BUS-002": {"lat": 28.7041, "lon": 77.1025},
}


def main():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print("Simulator started. Publishing fake GPS data every 3 seconds. Ctrl+C to stop.")

    try:
        while True:
            for vehicle_code, pos in VEHICLES.items():
                # small random movement to simulate driving
                pos["lat"] += random.uniform(-0.001, 0.001)
                pos["lon"] += random.uniform(-0.001, 0.001)
                speed = round(random.uniform(20, 60), 1)

                payload = {
                    "vehicle_code": vehicle_code,
                    "latitude": round(pos["lat"], 6),
                    "longitude": round(pos["lon"], 6),
                    "speed": speed,
                }
                topic = f"vehicles/{vehicle_code}/gps"
                client.publish(topic, json.dumps(payload))
                print(f"Published to {topic}: {payload}")

            time.sleep(3)
    except KeyboardInterrupt:
        print("Simulator stopped.")
        client.loop_stop()


if __name__ == "__main__":
    main()
