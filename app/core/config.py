from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Cinema Ticket Booking API"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    database_url: str = "postgresql+asyncpg://cinema_user:cinema_pass@postgres:5432/cinema"
    redis_url: str = "redis://:redis_pass@redis:6379/0"
    mongo_url: str = "mongodb://mongo_user:mongo_pass@mongodb:27017/cinema_logs"
    mongo_db: str = "cinema_logs"
    rabbitmq_url: str = "amqp://rabbit_user:rabbit_pass@rabbitmq:5672/cinema"
    otel_exporter_otlp_endpoint: str = "http://otel-collector:4317"


settings = Settings()
