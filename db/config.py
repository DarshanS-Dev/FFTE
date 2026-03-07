from __future__ import annotations

import logging
import os
from collections.abc import Generator
from typing import Optional

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine

from db import models  # ensure models are imported so metadata is populated

logger = logging.getLogger("ffte.db")


# Database URL from environment, with sensible local default
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://faulty:password@localhost:5432/ffte",
)


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """Create all database tables."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables ensured/created successfully.")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to create database tables: %s", exc)
        # Let callers decide how to handle startup failures.
        raise


def get_session() -> Generator[Optional[Session], None, None]:
    """
    FastAPI dependency that yields a database session.

    If the database is unavailable, yields None so callers can
    gracefully degrade instead of crashing the request.
    """
    try:
        with Session(engine) as session:
            logger.debug("Opened database session.")
            yield session
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to open database session: %s", exc)
        # Yield None so API handlers can continue without DB.
        yield None


def init_db() -> None:
    """
    Initialize database schema and create performance indexes.

    Calls :func:`create_db_and_tables` then idempotently adds indexes
    that speed up history queries on existing databases.
    """
    create_db_and_tables()

    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_scan_start_time ON scans (start_time);",
        "CREATE INDEX IF NOT EXISTS idx_test_scan_id ON test_executions (scan_id);",
        "CREATE INDEX IF NOT EXISTS idx_test_failure ON test_executions (caused_failure);",
    ]

    with Session(engine) as session:
        for query in index_queries:
            session.exec(text(query))
        session.commit()


