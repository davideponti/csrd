"""
CSRD Comply — Structured JSON Logging Configuration.

Provides:
- JSON-formatted log output for production (structured)
- Correlation ID injection via middleware for request tracing
- Configurable log levels
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON structured data."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Include extra fields passed to logger (e.g., correlation_id)
        for key in ("correlation_id", "user_id", "tenant_id", "request_path", "request_method", "status_code", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


class CorrelationIDFilter(logging.Filter):
    """Filter that adds correlation_id to log records from the current context."""

    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = get_current_correlation_id()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


# ── Context variable for correlation ID ──────────────────────────
from contextvars import ContextVar

_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current request context."""
    _correlation_id.set(cid)


def get_current_correlation_id() -> Optional[str]:
    """Get the correlation ID for the current request context."""
    return _correlation_id.get()


def generate_correlation_id() -> str:
    """Generate a new correlation ID (UUID)."""
    return str(uuid.uuid4())


def setup_logging() -> None:
    """
    Configure root logger with JSON structured output.

    In development, logs are human-readable. In production, they are JSON.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO")

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.ENVIRONMENT == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    handler.addFilter(CorrelationIDFilter())
    root_logger.addHandler(handler)

    # Set third-party loggers to WARNING to reduce noise
    for logger_name in ("uvicorn", "uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Ensure uvicorn.error uses our handler too
    uvicorn_error = logging.getLogger("uvicorn.error")
    if not uvicorn_error.handlers:
        uvicorn_error.addHandler(handler)

    root_logger.info("Logging configured", extra={"environment": settings.ENVIRONMENT, "log_level": root_logger.level})
