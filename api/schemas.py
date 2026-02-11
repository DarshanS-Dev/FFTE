from __future__ import annotations

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    spec_url: str
    base_url: str | None = None
    timeout: float = Field(default=10.0, ge=0)
    limit_endpoints: int | None = Field(default=None, ge=1)


class ScanResponse(BaseModel):
    report: dict[str, list[str]]
