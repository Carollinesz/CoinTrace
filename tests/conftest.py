import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parents[1]

_TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:1234@localhost:3308/cointrace_api_test",
)
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["MIGRATION_DATABASE_URL"] = _TEST_DB_URL
os.environ["DEMO"] = "False"  # keeps the demo dataset and the mutation block out of the tests

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app.main import app  # noqa: E402 — must come after env override
from app.core.database import get_db  # noqa: E402


def _build_alembic_config() -> Config:
    config = Config(str(_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_ROOT / "alembic"))
    # sqlalchemy.url is left empty on purpose: env.py then reuses the app engine,
    # which the env overrides above already pointed at the test database.
    config.attributes["configure_logger"] = False  # keeps pytest's own logging alive
    return config


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    command.upgrade(_build_alembic_config(), "head")


@pytest.fixture
def client():
    return TestClient(app)
