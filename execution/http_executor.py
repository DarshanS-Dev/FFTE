"""
HTTP execution module for sending requests with timeout handling.

Records status code, response body, latency, and exceptions for each request.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class HttpExecutionResult:
    """Result of an HTTP request execution."""

    status_code: int | None = None
    response_body: str | bytes | None = None
    latency_seconds: float | None = None
    exception: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    success: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a dictionary for serialization."""
        body = self.response_body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        return {
            "status_code": self.status_code,
            "response_body": body,
            "latency_seconds": self.latency_seconds,
            "exception": self.exception,
            "headers": dict(self.headers),
            "success": self.success,
        }


def execute_request(
    method: str,
    url: str,
    *,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: Any = None,
    data: Any = None,
) -> HttpExecutionResult:
    """
    Execute an HTTP request and record the result.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        url: Request URL.
        timeout: Request timeout in seconds. Defaults to 10.0.
        headers: Optional request headers.
        params: Optional query parameters.
        json: Optional JSON body (sets Content-Type automatically).
        data: Optional form/data body.

    Returns:
        HttpExecutionResult with status_code, response_body, latency, and any exception.
    """
    result = HttpExecutionResult()
    start = time.perf_counter()

    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            timeout=timeout,
            headers=headers or {},
            params=params,
            json=json,
            data=data,
        )

        elapsed = time.perf_counter() - start

        result.status_code = resp.status_code
        result.latency_seconds = elapsed
        result.headers = dict(resp.headers)
        result.success = True

        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                result.response_body = resp.json()
            except ValueError:
                result.response_body = resp.text
        else:
            result.response_body = resp.content if resp.content else resp.text

    except requests.Timeout as e:
        result.latency_seconds = time.perf_counter() - start
        result.exception = f"Timeout ({timeout}s): {e!s}"
    except requests.RequestException as e:
        result.latency_seconds = time.perf_counter() - start
        result.exception = f"{type(e).__name__}: {e!s}"
    except Exception as e:
        result.latency_seconds = time.perf_counter() - start
        result.exception = f"{type(e).__name__}: {e!s}"

    return result
