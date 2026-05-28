"""CSRD Comply — Database engine & session."""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DatabaseError, IntegrityError
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,            # Maintain up to 20 connections in pool
    max_overflow=10,          # Allow up to 10 additional connections beyond pool_size
    pool_timeout=30,          # Wait max 30 seconds for a connection from pool
    pool_recycle=1800,        # Recycle connections every 30 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Deadlock / Retry Utility ─────────────────────────────────────

RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    OperationalError,    # Covers deadlocks, connection timeouts, serialization failures
    DatabaseError,       # Covers other transient DB errors
)


def db_retry(
    max_retries: int = 3,
    base_delay: float = 0.1,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> Callable:
    """Decorator that retries a DB operation on retryable exceptions.

    Implements exponential backoff with jitter to handle:
    - Deadlock detection (PostgreSQL serialization failures)
    - Transient connection errors
    - Pool timeout races

    Args:
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds before first retry (default 0.1)
        backoff_factor: Multiplier for delay after each retry (default 2.0)
        retryable_exceptions: Tuple of exception types that trigger retry

    Usage:
        @db_retry()
        def my_db_operation(db: Session):
            ...

        @db_retry(max_retries=5, base_delay=0.05)
        def critical_operation(db: Session):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Add jitter: randomize delay slightly to avoid thundering herd
                        import random
                        jitter = random.uniform(0, delay * 0.5)
                        sleep_time = delay + jitter
                        logger.warning(
                            "DB retry %d/%d after %.3fs on %s: %s",
                            attempt + 1, max_retries, sleep_time,
                            type(e).__name__, str(e),
                        )
                        time.sleep(sleep_time)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "DB operation failed after %d retries: %s",
                            max_retries, str(e),
                        )

            # All retries exhausted — re-raise the last exception
            raise last_exception  # type: ignore

        return wrapper
    return decorator


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    except RETRYABLE_EXCEPTIONS:
        # Roll back the session if a retryable error occurred
        # The caller should use @db_retry for full retry logic
        db.rollback()
        raise
    finally:
        db.close()

