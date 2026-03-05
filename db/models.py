from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Scan(SQLModel, table=True):
    __tablename__ = "scans"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        index=True,
    )
    scan_name: str = Field(nullable=False, index=True)
    target_url: str = Field(nullable=False, index=True)
    status: str = Field(nullable=False, index=True)
    start_time: datetime = Field(index=True)
    end_time: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )


class TestExecution(SQLModel, table=True):
    __tablename__ = "test_executions"

    id: Optional[int] = Field(default=None, primary_key=True)
    scan_id: UUID = Field(
        nullable=False,
        foreign_key="scans.id",
        index=True,
    )

    endpoint: str = Field(nullable=False, index=True)
    http_method: str = Field(nullable=False, index=True)
    field_name: Optional[str] = Field(default=None, index=True)
    field_type: Optional[str] = Field(default=None)
    is_required: Optional[bool] = Field(default=None, index=True)
    edge_case_type: Optional[str] = Field(default=None, index=True)
    edge_case_value: Optional[str] = Field(default=None)
    status_code: Optional[int] = Field(default=None, index=True)
    failure_type: Optional[str] = Field(default=None, index=True)
    caused_failure: Optional[bool] = Field(default=None, index=True)
    response_time_ms: Optional[float] = Field(default=None, index=True)
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )
