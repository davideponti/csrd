"""
CSRD Comply — Shared test fixtures.
Patches postgresql.UUID for SQLite BEFORE any model imports.
"""
import os
# Override DATABASE_URL to SQLite BEFORE any app/model imports
os.environ["DATABASE_URL"] = "sqlite://"

# Add ai_engine to path so tests can import from ai_engine.*
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ai_engine"))

import uuid
import pytest
from datetime import date
from typing import Any, Dict

# ── Patch postgresql.UUID for SQLite ──
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.dialects import postgresql

class _UUID(TypeDecorator):
    impl = String(36)
    cache_ok = True
    python_type = uuid.UUID

    def get_col_spec(self, **kw):
        return "VARCHAR(36)"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            elif isinstance(value, uuid.UUID):
                return str(value)
            elif isinstance(value, str):
                return str(uuid.UUID(value))
            return str(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            elif isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)
        return process

postgresql.UUID = _UUID

# Now safe to import
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from app.main import app
from app.core.database import get_db

# Use hashlib to avoid bcrypt/passlib issues on Python 3.14+
import hashlib
import secrets
from datetime import timedelta, datetime, timezone
from jose import jwt
from app.core.config import settings

def hash_password(password: str) -> str:
    """Simple hash for testing - avoids bcrypt/passlib issues."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"$sha256${salt}${h}"

def create_access_token(data: dict) -> str:
    """Create a JWT for testing purposes."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

from app.models import Base, Company, User, MaterialityAssessment, Report, EmissionsData

# Use file-based SQLite to avoid connection-sharing issues with in-memory DB
engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db() -> Session:
    """Provide a session for test use. The autouse setup_db fixture handles cleanup."""
    _db = TestingSessionLocal()
    try:
        yield _db
    finally:
        try:
            _db.close()
        except Exception:
            pass

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture
def sample_company(db: Session) -> Company:
    c = Company(
        company_id=uuid.uuid4(),
        company_name="Test Srl",
        vat_number="IT12345678901",
        country="IT", sector="C10",
        employee_count=50, turnover=5_000_000, reporting_year=2026,
    )
    db.add(c); db.commit(); db.refresh(c)
    return c

@pytest.fixture
def sample_user(db: Session, sample_company: Company) -> User:
    u = User(
        user_id=uuid.uuid4(),
        company_id=sample_company.company_id,
        email="admin@test.com",
        hashed_password=hash_password("testpass123"),
        role="admin", is_active=True,
    )
    db.add(u); db.commit(); db.refresh(u)
    return u

@pytest.fixture
def user_token(sample_user: User) -> str:
    return create_access_token(data={"sub": str(sample_user.user_id)})

@pytest.fixture
def auth_header(user_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def sample_assessment(db: Session, sample_company: Company) -> MaterialityAssessment:
    a = MaterialityAssessment(
        id=uuid.uuid4(), company_id=sample_company.company_id,
        assessment_date=date.today(), status="in_progress",
    )
    db.add(a); db.commit(); db.refresh(a)
    return a

@pytest.fixture
def sample_report(db: Session, sample_company: Company) -> Report:
    r = Report(
        id=uuid.uuid4(), company_id=sample_company.company_id,
        reporting_year=2026, title="CSRD Report 2026 - Test Srl", status="draft",
    )
    db.add(r); db.commit(); db.refresh(r)
    return r
