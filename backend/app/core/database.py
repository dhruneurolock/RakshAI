"""Database module"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Try PostgreSQL first, fall back to SQLite
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={} if not settings.DATABASE_URL.startswith("sqlite") else {"check_same_thread": False}
    )
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info("Connected to PostgreSQL database")
except Exception as e:
    logger.warning(f"PostgreSQL unavailable ({e}), falling back to SQLite")
    engine = create_engine(
        "sqlite:///./rakshaidb_dev.db",
        connect_args={"check_same_thread": False}
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def ensure_sqlite_schema() -> None:
    """Repair the local SQLite fallback schema when it lags behind the ORM model."""
    if not engine.url.drivername.startswith("sqlite"):
        return

    inspector = inspect(engine)

    # --- Fix missing columns on existing tables ---
    if inspector.has_table("vulnerabilities"):
        existing_columns = {column["name"] for column in inspector.get_columns("vulnerabilities")}
        missing_columns = {
            "llm_evidence": "TEXT",
            "llm_poc": "TEXT",
        }
        with engine.begin() as connection:
            for column_name, column_type in missing_columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE vulnerabilities ADD COLUMN {column_name} {column_type}")
                    )
                    logger.info("Added missing SQLite column: %s", column_name)

    # --- Create any missing tables from the ORM model ---
    # This handles evidence_records, lineage_events, correlation_groups,
    # audit_logs, scan_policies, and any future models automatically.
    Base.metadata.create_all(bind=engine)
    logger.info("Ensured all SQLite tables exist")


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
