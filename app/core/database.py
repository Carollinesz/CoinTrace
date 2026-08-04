from urllib.parse import quote

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

def _build_safe_url(raw: str) -> str:
    url = make_url(raw)
    if url.password and not url.password.isascii():
        url = url.set(password=quote(url.password, safe=""))
    return url.render_as_string(hide_password=False)


def _ensure_user_exists(safe_url) -> None:
    url = make_url(safe_url)
    system_engine = create_engine( 
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with system_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :name"),
                {"name": settings.USERNAME_API},
            ).scalar()
            if not exists:
                conn.execute(
                    text(f'CREATE USER "{settings.USERNAME_API}" WITH PASSWORD :password'),
                    {"password": settings.USERNAME_PASSWORD},
                )
    finally:
        system_engine.dispose()


def _ensure_database_exists(safe_url: str) -> None:
    url = make_url(safe_url)
    system_engine = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with system_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        system_engine.dispose()


DB_Name = "/demo_db_v1" if settings.DEMO else "/financial_api_V1"


_ensure_user_exists( _build_safe_url(settings.MIGRATION_DATABASE_URL + DB_Name))
_ensure_database_exists(_build_safe_url(settings.MIGRATION_DATABASE_URL + DB_Name))

engine = create_engine( _build_safe_url(settings.MIGRATION_DATABASE_URL + DB_Name), pool_pre_ping=True)
engine_migrations = create_engine(_build_safe_url(settings.MIGRATION_DATABASE_URL + DB_Name), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
