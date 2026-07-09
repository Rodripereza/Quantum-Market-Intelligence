from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Quantum Market Intelligence"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    host: str = "127.0.0.1"
    port: int = 8000

    log_level: str = "INFO"
    logs_dir: str = "backend/logs"

    default_timezone: str = "Europe/Madrid"
    default_currency: str = "USD"
    default_market: str = "US"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()