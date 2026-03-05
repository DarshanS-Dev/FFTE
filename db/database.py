from __future__ import annotations

import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

# Reuse the same env var already present in .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://faulty:password@localhost:5432/ffte",
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def init_db() -> None:
    """
    Initialize database schema.

    Import models so SQLModel is aware of them before creating tables.
    """
    from db import models  # noqa: F401
    from sqlalchemy import text

    SQLModel.metadata.create_all(bind=engine)
    
    # Add indexes to optimize history queries for existing databases
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_scan_start_time ON scans (start_time);",
        "CREATE INDEX IF NOT EXISTS idx_test_scan_id ON test_executions (scan_id);",
        "CREATE INDEX IF NOT EXISTS idx_test_failure ON test_executions (caused_failure);"
    ]
    
    with Session(engine) as session:
        for query in index_queries:
            session.exec(text(query))
        session.commit()


def get_session() -> Generator[Session, None, None]:
    """
    Yield a database session.

    Suitable for using as a dependency in FastAPI endpoints:

        def endpoint(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session

