"""
Central place for all app settings.
Reads values from a .env file (see .env.example) so we never
hardcode secrets or DB URLs in the code itself.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/bus_tracking"

    # JWT auth
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # MQTT
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "vehicles/+/gps"  # + is a wildcard for vehicle_id

    class Config:
        env_file = ".env"


settings = Settings()
