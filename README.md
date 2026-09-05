# Bus Tracking System — Backend (FastAPI)

A GPS-based vehicle tracking backend built with FastAPI, PostgreSQL, and MQTT.
Each user is assigned exactly one route and one vehicle, and can only ever
access data for their own assignment — enforced at the backend/JWT level,
not just hidden in the UI.

## Architecture
Client (Flutter app)
│ POST /auth/login
▼
FastAPI (JWT auth) ──► PostgreSQL (users, routes, vehicles, gps_logs)
▲
│ reads
Vehicle GPS data ──► MQTT broker ──► MQTT listener ──┐
├──► gps_logs table
Vehicle GPS data ──► REST /gps/ingest ────────────────┘


- **FastAPI** serves REST APIs and auto-generates docs at `/docs`.
- **PostgreSQL** stores all persistent data via SQLAlchemy ORM.
- **MQTT** is the preferred GPS ingestion path (`app/core/mqtt_listener.py`
  subscribes to `vehicles/+/gps` and writes to the same `gps_logs` table).
- **REST `/gps/ingest`** is kept as the fallback ingestion method the task
  explicitly allows, and is what a simple GPS simulator script would use.

## Database Design

| Table    | Purpose                                                                 |
|----------|--------------------------------------------------------------------------|
| `users`      | Login credentials + `assigned_route_id` + `assigned_vehicle_id` (each user maps to exactly one route and one vehicle) |
| `routes`     | Named routes (e.g. "Route A", "Downtown -> Airport")                 |
| `vehicles`   | Vehicles (e.g. "BUS-001"), each linked to one route                  |
| `gps_logs`   | Every GPS ping ever received for a vehicle — never overwritten, so this table doubles as both live location and full history |

"Latest location" = most recent row in `gps_logs` for a vehicle.
"Historical data" = all rows in `gps_logs` for a vehicle.

## Authentication & Authorization

- Login (`POST /auth/login`) verifies a hashed password and issues a JWT.
- Every protected endpoint uses `Depends(get_current_user)`, which decodes
  the JWT and loads the user from the DB.
- **Critically: no endpoint accepts a `user_id` or `vehicle_id` from the
  client.** Every "my-*" endpoint only ever looks at
  `current_user.assigned_route_id` / `assigned_vehicle_id` — values that
  came from the verified token, not from anything a client could fake in
  a URL or request body. This means User A can never retrieve User B's
  route or vehicle, even by calling the API directly (e.g. via Postman).

## API Endpoints

| Method | Endpoint                  | Auth required | Description |
|--------|----------------------------|:---:|-------------|
| POST   | `/auth/login`               | ❌ | Returns a JWT access token |
| GET    | `/tracking/my-route`        | ✅ | Logged-in user's assigned route |
| GET    | `/tracking/my-vehicle`      | ✅ | Logged-in user's assigned vehicle |
| GET    | `/tracking/my-location`     | ✅ | Latest GPS ping for the user's vehicle |
| GET    | `/tracking/my-history?limit=50` | ✅ | Historical GPS pings for the user's vehicle |
| GET    | `/tracking/my-summary`      | ✅ | Route + vehicle + latest location in one call (used by the Flutter home screen) |
| POST   | `/gps/ingest`                | ❌ | Vehicle reports a GPS ping (REST fallback to MQTT) |
| POST   | `/admin/routes`              | ❌ | Create a route (setup/testing helper) |
| POST   | `/admin/vehicles`            | ❌ | Create a vehicle (setup/testing helper) |
| POST   | `/admin/users`               | ❌ | Create a user with route/vehicle assignment (setup/testing helper) |

> The `/gps/ingest` and `/admin/*` endpoints are intentionally not behind
> user login — a vehicle device or an admin setting up test data isn't a
> logged-in "user" in this system. In production these would sit behind
> a per-vehicle API key and an admin role check respectively; that's a
> known simplification for this assessment's scope.

Full interactive docs (try every endpoint from the browser) at:
`http://localhost:8000/docs`

## GPS Data Flow

1. A vehicle publishes `{latitude, longitude, speed}` either to the MQTT
   topic `vehicles/<vehicle_code>/gps` or to `POST /gps/ingest`.
2. The backend resolves the vehicle by `vehicle_code` and inserts a new
   row into `gps_logs` — old rows are never deleted or overwritten.
3. When a user requests `/tracking/my-location` or `/tracking/my-summary`,
   the backend queries the most recent `gps_logs` row for that user's
   `assigned_vehicle_id`.
4. `/tracking/my-history` returns the full (or `limit`-ed) list of past
   pings for the same vehicle, ordered newest-first.

## Route / Vehicle Assignment Logic

- Each `User` row has one `assigned_route_id` and one `assigned_vehicle_id`.
- Assignment happens once, either via `seed_data.py` (for the two demo
  users) or via `POST /admin/users`.
- Example: User A → Route A → BUS-001. If User A logs in, every
  `/tracking/*` call resolves data through their own `assigned_vehicle_id`
  only — they cannot see BUS-002's data no matter what they send in the
  request.

## Setup

**Prerequisites:** Python 3.11+, PostgreSQL running locally, (optional) an
MQTT broker such as Mosquitto for the MQTT ingestion path.

```bash
# 1. Clone and enter the project
git clone https://github.com/aayushjha2005u/bustrackback.git
cd bustrackback

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# edit .env with your own DATABASE_URL, SECRET_KEY, MQTT_BROKER, etc.

# 5. Seed demo users (Route A/BUS-001 and Route B/BUS-002)
python seed_data.py

# 6. Run the server
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

**Demo credentials** (from `seed_data.py`):

| Username | Password | Route | Vehicle |
|----------|----------|-------|---------|
| usera    | pass123  | Route A | BUS-001 |
| userb    | pass123  | Route B | BUS-002 |

## Tech Stack

FastAPI · SQLAlchemy · PostgreSQL · Pydantic · JWT (python-jose) · paho-mqtt · Uvicorn
Eof
