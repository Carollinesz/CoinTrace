import os
import pytest
from fastapi.testclient import TestClient

_TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://postgres:1234@localhost:3308/financial_api_test",
)
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["MIGRATION_DATABASE_URL"] = _TEST_DB_URL
os.environ["DEMO"] = "False"  # keeps the demo dataset and the mutation block out of the tests

from app.main import app  # noqa: E402 — must come after env override
from app.core.database import get_db  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)
