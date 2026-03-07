from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Generator

import psycopg2
from dotenv import load_dotenv
from sqlmodel import Session

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from db.config import DATABASE_URL, engine, init_db  # noqa: E402
from db.models import Scan, TestExecution  # noqa: E402


def _parse_database_url(url: str) -> dict[str, str]:
    """
    Parse a simple postgres DATABASE_URL into components psycopg2.connect understands.

    Expected format: postgresql://user:password@host:port/dbname
    """
    if not url.startswith("postgresql://"):
        raise ValueError("Only postgresql:// URLs are supported for init_db.")

    without_scheme = url[len("postgresql://") :]
    auth_part, rest = without_scheme.split("@", 1)
    user, password = auth_part.split(":", 1)
    host_port, dbname = rest.rsplit("/", 1)
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host, port = host_port, "5432"

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "dbname": dbname,
    }


def ensure_database_exists(url: str) -> None:
    """
    Create the PostgreSQL database if it does not already exist.
    """
    cfg = _parse_database_url(url)
    dbname = cfg.pop("dbname")

    # Connect to default "postgres" database to create the target database.
    admin_cfg = {**cfg, "dbname": "postgres"}

    try:
        with psycopg2.connect(**admin_cfg) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (dbname,),
                )
                exists = cur.fetchone() is not None
                if not exists:
                    print(f"Creating database '{dbname}'...")
                    cur.execute(f'CREATE DATABASE "{dbname}"')
                else:
                    print(f"Database '{dbname}' already exists.")
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"Error while ensuring database exists: {exc}")
        raise


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def seed_test_data() -> None:
    """
    Seed the database with minimal development data.
    """
    print("Seeding development data...")
    with session_scope() as session:
        scan = Scan(
            scan_name="Demo Scan",
            target_url="http://localhost:8000",
            status="completed",
        )
        session.add(scan)
        session.flush()  # ensure scan.id is available

        test_exec = TestExecution(
            scan_id=scan.id,
            endpoint="/health",
            http_method="GET",
            field_name=None,
            field_type=None,
            is_required=None,
            edge_case_type=None,
            edge_case_value=None,
            status_code=200,
            failure_type=None,
            caused_failure=False,
            response_time_ms=5.0,
        )
        session.add(test_exec)
    print("Seeding complete.")


def main() -> None:
    # Load environment variables from .env if present
    load_dotenv()

    db_url = os.getenv("DATABASE_URL", DATABASE_URL)
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set; cannot initialize database.")

    print(f"Using DATABASE_URL={db_url!r}")

    # 1. Ensure database exists
    ensure_database_exists(db_url)

    # 2. Create tables
    print("Creating tables (if not present)...")
    init_db()
    print("Database schema initialized.")

    # 3. Optionally seed
    if os.getenv("INIT_DB_SEED", "false").lower() in {"1", "true", "yes"}:
        seed_test_data()
    else:
        print("Skipping seeding; set INIT_DB_SEED=true to enable.")


if __name__ == "__main__":
    main()

