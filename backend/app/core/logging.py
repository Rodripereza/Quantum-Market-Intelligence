import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.settings import settings


def setup_logging() -> None:
    logs_path = Path(settings.logs_dir)
    logs_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    system_handler = RotatingFileHandler(
        logs_path / "system.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    system_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(
        logs_path / "errors.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        handlers=[system_handler, error_handler],
    )