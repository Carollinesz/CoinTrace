"""Brings the database up to `head` on startup, so any way of booting the app
(uvicorn, docker, the test client) ends up with the same schema."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.core.database import engine_migrations

ROOT_DIR = Path(__file__).resolve().parents[2]
MIGRATION_LOCK_KEY = 918273645  # arbitrary, shared by every process running these migrations


def handle_run_migrations() -> None:
    """The advisory lock keeps concurrent workers from applying the same revision twice."""
    with engine_migrations.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK_KEY})
        conn.commit()
        try:
            command.upgrade(_build_alembic_config(), "head")
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK_KEY})
            conn.commit()


def _build_alembic_config() -> Config:
    """Paths are absolute because the app is not always started from the repo root."""
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    config.attributes["configure_logger"] = False  # keeps alembic.ini from replacing the uvicorn loggers
    return config
