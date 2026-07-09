from app.core.settings import settings


def get_app_config() -> dict:
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "host": settings.host,
        "port": settings.port,
        "default_timezone": settings.default_timezone,
        "default_currency": settings.default_currency,
        "default_market": settings.default_market,
    }