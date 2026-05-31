"""CSRD Comply — Application Configuration."""
import os
import logging
from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import model_validator
import json

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "SECRET_KEY",
]

PRODUCTION_REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "SECRET_KEY",
]


def _read_file_secret(env_var: str, file_env_var: str, default: str = "") -> str:
    """Read a secret from a file path (Docker secret) or from an env var.
    
    Priority:
    1. Content of file pointed by <file_env_var> (e.g., SECRET_KEY_FILE)
    2. Value of <env_var> directly
    3. default
    """
    file_path = os.environ.get(file_env_var)
    if file_path and os.path.isfile(file_path):
        try:
            with open(file_path, "r") as f:
                return f.read().strip()
        except OSError as e:
            logger.warning(f"Could not read secret file {file_path}: {e}")
    
    return os.environ.get(env_var, default)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/csrd_comply"

    # Auth / JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI / LLM
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # CORS — only specific origins, no wildcards
    # Usiamo str per evitare errori di parsing con pydantic-settings su Render
    CORS_ORIGINS: str = "http://localhost:3000,https://csrdcomply.com,https://www.csrdcomply.com"
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "X-Tenant-ID"]

    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "1.0.0"

    # Multitenancy (Step 29)
    ENABLE_MULTITENANCY: bool = False
    DEFAULT_SCHEMA: str = "public"

    # Deployment (Step 29)
    DEPLOYMENT_DOMAIN: str = "csrdcomply.com"
    DEPLOYMENT_SSL_ENABLED: bool = True

    # Request limits (DoS protection)
    MAX_REQUEST_SIZE_MB: int = 10

    # Monitoring (Sentry) — optional, non bloccante in produzione
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # ── Email (SMTP / SendGrid / Mailgun) ──────────────────────
    EMAIL_FROM: str = "noreply@csrdcomply.com"
    EMAIL_FROM_NAME: str = "CSRD Comply"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SENDGRID_API_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    RESEND_API_KEY: str = ""

    # ── Stripe ─────────────────────────────────────────────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_FREE: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_TEAM: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""

    def _parse_origins(self) -> List[str]:
        """Parse CORS_ORIGINS into a list."""
        v = self.CORS_ORIGINS.strip()
        if not v:
            return ["http://localhost:3000"]
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @model_validator(mode="after")
    def resolve_file_secrets(self):
        """Resolve Docker secrets from files before validation."""
        # Read SECRET_KEY from file if SECRET_KEY_FILE is set
        file_key = _read_file_secret("SECRET_KEY", "SECRET_KEY_FILE")
        if file_key and file_key != "change-me-in-production":
            object.__setattr__(self, "SECRET_KEY", file_key)
        
        # Read DATABASE_URL components from file if DB_PASSWORD_FILE is set
        db_password_file = os.environ.get("DB_PASSWORD_FILE")
        if db_password_file and os.path.isfile(db_password_file):
            try:
                with open(db_password_file, "r") as f:
                    db_password = f.read().strip()
                # Rebuild DATABASE_URL with the password from file
                current_url = self.DATABASE_URL
                if db_password and ":" in current_url:
                    # Replace password in postgresql://user:password@host/db
                    parts = current_url.split("@")
                    if len(parts) == 2:
                        creds = parts[0].split(":")
                        if len(creds) == 3:
                            new_url = f"{creds[0]}:{creds[1]}:{db_password}@{parts[1]}"
                            object.__setattr__(self, "DATABASE_URL", new_url)
            except OSError as e:
                logger.warning(f"Could not read DB_PASSWORD_FILE {db_password_file}: {e}")
        
        return self

    @model_validator(mode="after")
    def validate_secret_key(self):
        """Block startup in production with default SECRET_KEY."""
        if self.SECRET_KEY in ("change-me-in-production", "") and self.ENVIRONMENT == "production":
            raise ValueError(
                "❌ CRITICAL: SECRET_KEY not changed in production! "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return self

    @model_validator(mode="after")
    def validate_required_env_vars(self):
        """Validate that all required environment variables are set on startup.

        In production, validates core requirements. Sentry is optional.
        """
        missing = []

        if self.ENVIRONMENT == "production":
            required = PRODUCTION_REQUIRED_ENV_VARS
        else:
            required = REQUIRED_ENV_VARS

        for var_name in required:
            value = getattr(self, var_name, None)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing.append(var_name)
            if var_name == "SECRET_KEY" and value in ("change-me-in-production", ""):
                missing.append(var_name)

        if missing:
            error_msg = (
                f"❌ Required environment variables not configured: {', '.join(missing)}. "
                f"Set them in the .env file or in the container environment variables."
            )
            if self.ENVIRONMENT == "production":
                raise ValueError(error_msg)
            else:
                logger.warning(error_msg)

        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
