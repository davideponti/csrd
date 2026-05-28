"""
CSRD Comply — Application Monitoring Integration.

Provides Sentry integration for error tracking and performance monitoring.
To enable, set SENTRY_DSN in your environment variables.
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_monitoring() -> None:
    """
    Initialize Sentry SDK for error tracking and performance monitoring.

    Skips initialization if SENTRY_DSN is not set (e.g., in development).
    Sentry is configured to:
    - Capture unhandled exceptions with full stack traces
    - Track performance traces (sampled at configurable rate)
    - Include environment name for environment-aware grouping
    - Attach request body for debugging (PII-safe)
    """
    sentry_dsn = getattr(settings, "SENTRY_DSN", None)

    if not sentry_dsn:
        logger.info(
            "Sentry monitoring not configured — set SENTRY_DSN to enable error tracking."
        )
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        traces_sample_rate = getattr(settings, "SENTRY_TRACES_SAMPLE_RATE", 0.1)

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=traces_sample_rate,
            enable_tracing=True,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            send_default_pii=False,        # Do NOT send user PII
            attach_request_body=False,      # Avoid leaking sensitive data
            max_request_body_size="never",
            release=getattr(settings, "APP_VERSION", "1.0.0"),
        )

        logger.info(
            "Sentry monitoring initialized",
            extra={
                "environment": settings.ENVIRONMENT,
                "traces_sample_rate": traces_sample_rate,
            },
        )

    except ImportError:
        logger.warning(
            "sentry-sdk not installed — run 'pip install sentry-sdk' to enable Sentry monitoring."
        )
    except Exception as e:
        logger.error("Failed to initialize Sentry: %s", e)
