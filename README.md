# Bus Tracking System - Backend (FastAPI)

A GPS-based vehicle tracking backend built with FastAPI, PostgreSQL,
and MQTT. Each user logs in and can only ever see the bus route and
vehicle assigned to them.

## Architecture

```
Vehicle / GPS Simulator
        |
        |  MQTT (preferred) or REST POST /gps/ingest
        v
   FastAPI Backend  ---->  PostgreSQL (users, routes, vehicles, gps_logs)
        ^
        |  REST API (JWT-authenticated)
        |
   Flutter Mobile App
```

- **FastAPI** exposes REST endpoints for login and for each user's
  assigned route / vehicle / location data.
- **MQTT (Mosquitto)** is the primary channel for vehicles to report
  GPS coordinates. A background listener (`app/core/mqtt_listener.py`)
  subscribes to `vehicles/+/gps` and writes every message straight
  into the database.
- **REST `/gps/ingest`** is kept as a fallback ingestion method (the
  task explicitly allows "MQTT, REST, or another suitable approach").
  The GPS simulator uses MQTT by default.
- **PostgreSQL** stores everything: users, routes, vehicles, and the
  full GPS history (every ping, not just the latest).

## Database design

| Table      | Purpose                                                   |
|------------|------------------------------------------------------------|
| `users`    | Login credentials + `assigned_route_id` + `assigned_vehicle_id` |
| `routes`   | Named bus routes (e.g. "Route A")                          |
| `vehicles` | Physical vehicles, each linked to one route                |
| `gps_logs` | Every GPS ping ever received, linked to a vehicle          |

Each user has exactly one assigned route and one assigned vehicle
(foreign keys on the `users` table). "Latest location" is simply the
most recent row in `gps_logs` for that vehicle; "historical data" is
every row, so nothing is ever overwritten.

## Authentication & authorization (the core business logic)

1. `POST /auth/login` checks username/password and returns a JWT.
2. Every other protected endpoint requires `Authorization: Bearer <token>`.
3. `app/core/deps.py` decodes the token and loads the **real** user
   record from the database on every request.
4. Every tracking endpoint (`/tracking/my-route`, `/tracking/my-vehicle`,
   `/tracking/my-location`, `/tracking/my-history`, `/tracking/my-summary`)
   reads `current_user.assigned_route_id` / `assigned_vehicle_id` -
   **never** an ID passed in by the client.

This means the restriction is enforced by the backend itself: even if
someone calls the API directly with a tool like Postman, they can
never fetch another user's route or vehicle, because the endpoints
never accept "which user" as an input - they only ever use whoever
the token says you are.

## API endpoints

| Method | Endpoint                  | Auth required | Description                              |
|--------|----------------------------|:--:|-------------------------------------------|
| POST   | `/auth/login`              | No | Returns a JWT access token                |
| GET    | `/tracking/my-route`       | Yes | The logged-in user's assigned route       |
| GET    | `/tracking/my-vehicle`     | Yes | The logged-in user's assigned vehicle     |
| GET    | `/tracking/my-location`    | Yes | Latest GPS position of the assigned vehicle |
| GET    | `/tracking/my-history`     | Yes | Historical GPS pings (default last 50)    |
| GET    | `/tracking/my-summary`     | Yes | Route + vehicle + latest location in one call (used by the Flutter Home screen) |
| POST   | `/gps/ingest`               | No* | Vehicle reports a new GPS position (REST fallback) |
| POST   | `/admin/routes`             | No* | Create a route (setup/testing)            |
| POST   | `/admin/vehicles`           | No* | Create a vehicle (setup/testing)          |
| POST   | `/admin/users`              | No* | Create a user with route/vehicle assignment (setup/testing) |

\* Not user-auth protected because these are called by devices/admins,
not by app users. In a production system these would use a separate
API key or admin role - noted here as a known simplification for the
scope of this assessment.

Interactive docs (Swagger UI) are auto-generated at `/docs` once the
server is running.

## GPS data flow

```
GPS Simulator --publishes--> MQTT topic "vehicles/BUS-001/gps"
                                      |
                     MQTT listener (background thread in FastAPI)
                                      |
                              gps_logs table (Postgres)
                                      |
                    Flutter app polls /tracking/my-summary
                                      |
                         Map screen shows current position
```

## Setup - local (without Docker)

1. Install PostgreSQL and create a database named `bus_tracking`.
2. Install an MQTT broker locally (e.g. Mosquitto) OR skip MQTT and
   just use the REST `/gps/ingest` endpoint for testing.
3. Copy `.env.example` to `.env` and adjust values if needed.
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the server:
   ```
   uvicorn app.main:app --reload
   ```
6. Populate sample data:
   ```
   python seed_data.py
   ```
   This creates two test users:
   - `usera` / `pass123` -> Route A / BUS-001
   - `userb` / `pass123` -> Route B / BUS-002
7. (Optional) Run the GPS simulator to see live data:
   ```
   python gps_simulator.py
   ```
8. Open `http://localhost:8000/docs` to try every endpoint.

## Setup - with Docker (bonus)

```
docker-compose up --build
```

This starts PostgreSQL, the Mosquitto MQTT broker, and the FastAPI
backend together. Then run `python seed_data.py` and
`python gps_simulator.py` from your host machine (pointed at
`localhost`) to populate and simulate data.

## Testing the core business rule manually

1. Log in as `usera`, call `/tracking/my-summary` -> see Route A / BUS-001.
2. Log in as `userb`, call `/tracking/my-summary` -> see Route B / BUS-002.
3. Confirm neither user can ever retrieve the other's data, regardless
   of what's sent in the request - because the endpoints only trust
   the identity embedded in the JWT token.
