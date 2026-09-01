"""Test environment: isolated PostgreSQL database, never production credentials."""

from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

# Must be set before application imports.
os.environ["APP_NAME"] = "NyaySetu"
os.environ["APP_ENV"] = "test"
os.environ["APP_DEBUG"] = "false"
os.environ["JWT_SECRET"] = "pytest-only-jwt-secret-not-for-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://nyaysetu:nyaysetu_dev_only@127.0.0.1:5432/nyaysetu_test"
)
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_ALEMBIC_INI_PATH = _BACKEND_DIR / "alembic.ini"

from alembic import command
from alembic.config import Config

from app.core.config import get_settings
from app.db.database import get_db
from app.main import app
from app.models.user import UserRole
from app.services import auth_service


def _ensure_database(url_str: str) -> None:
    url = make_url(url_str)
    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    db_name = url.database
    if db_name is None:
        raise RuntimeError("DATABASE_URL must include a database name")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


def _postgres_unavailable_message(exc: BaseException) -> str:
    return (
        "PostgreSQL is not available. Phase 1 tests require a running Postgres instance. "
        "See docs/BACKEND_SETUP.md. "
        f"Underlying error: {exc}"
    )


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    url = get_settings().database_url
    try:
        _ensure_database(url)
    except Exception as exc:
        pytest.exit(_postgres_unavailable_message(exc), returncode=1)

    test_engine = create_engine(url, pool_pre_ping=True)
    try:
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        test_engine.dispose()
        pytest.exit(_postgres_unavailable_message(exc), returncode=1)

    alembic_cfg = Config(str(_ALEMBIC_INI_PATH))
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(alembic_cfg, "head")

    yield test_engine
    test_engine.dispose()


@pytest.fixture(autouse=True)
def _truncate_users(engine: Engine) -> Generator[None, None, None]:
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))


@pytest.fixture
def db(engine: Engine) -> Generator[Session, None, None]:
    SessionTesting = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_header(client: TestClient) -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={
            "name": "Test Client",
            "email": "client@example.com",
            "password": "securePass1",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "client@example.com", "password": "securePass1"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_expired_token(user_id: UUID, role: str = UserRole.CLIENT.value) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(UTC) - timedelta(minutes=5),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_role_user(db: Session, *, email: str, role: UserRole) -> None:
    auth_service.create_user(
        db,
        name=f"{role.value} User",
        email=email,
        password="securePass1",
        role=role,
    )
