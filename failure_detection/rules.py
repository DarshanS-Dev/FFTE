"""
Rule-based failure classifier for HTTP responses.

Flags crashes, server errors, timeouts, and invalid JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from execution.http_executor import HttpExecutionResult


class FailureType(str, Enum):
    """Categories of HTTP failures."""
    NONE = "none"
    CRASH = "crash"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    INVALID_JSON = "invalid_json"
    CLIENT_ERROR = "client_error"  # 4xx errors


@dataclass
class FailureClassification:
    """Result of failure classification."""
    failure_type: FailureType
    message: str = ""
    flags: dict[str, bool] = field(default_factory=dict)
    
    @property
    def is_failure(self) -> bool:
        """True if any failure was detected."""
        return self.failure_type != FailureType.NONE


def classify(result: "HttpExecutionResult") -> FailureClassification:
    """
    Classify an HTTP execution result using rule-based checks.
    
    Args:
        result: HttpExecutionResult from http_executor.execute_request.
    
    Returns:
        FailureClassification with failure_type, message, and per-rule flags.
    """
    flags: dict[str, bool] = {
        "crash": False,
        "server_error": False,
        "client_error": False,
        "timeout": False,
        "invalid_json": False,
    }
    
    # 1. Timeout: exception indicates request timed out
    if result.exception and _is_timeout_exception(result.exception):
        flags["timeout"] = True
        return FailureClassification(
            failure_type=FailureType.TIMEOUT,
            message=result.exception or "Request timed out",
            flags=flags,
        )
    
    # 2. Crash: any exception (connection refused, DNS, SSL, etc.)
    if result.exception:
        flags["crash"] = True
        return FailureClassification(
            failure_type=FailureType.CRASH,
            message=result.exception,
            flags=flags,
        )
    
    # 3. Server error: 5xx status codes
    if result.status_code is not None and 500 <= result.status_code < 600:
        flags["server_error"] = True
        return FailureClassification(
            failure_type=FailureType.SERVER_ERROR,
            message=f"HTTP {result.status_code}",
            flags=flags,
        )
    
    # 4. Client error: 4xx status codes (optional to flag as failure)
    if result.status_code is not None and 400 <= result.status_code < 500:
        flags["client_error"] = True
        return FailureClassification(
            failure_type=FailureType.CLIENT_ERROR,
            message=f"HTTP {result.status_code}",
            flags=flags,
        )
    
    # 5. Invalid JSON: Content-Type says JSON but body is not parseable
    if _expects_json(result) and not _is_valid_json_response(result):
        flags["invalid_json"] = True
        return FailureClassification(
            failure_type=FailureType.INVALID_JSON,
            message="Response claimed JSON but body is not valid JSON",
            flags=flags,
        )
    
    return FailureClassification(
        failure_type=FailureType.NONE,
        message="",
        flags=flags,
    )


def _is_timeout_exception(exception: str) -> bool:
    """Check if exception message indicates a timeout."""
    lower = exception.lower()
    return "timeout" in lower or "timed out" in lower


def _expects_json(result: "HttpExecutionResult") -> bool:
    """True if response Content-Type indicates JSON."""
    ct = result.headers.get("Content-Type", "")
    return "application/json" in ct


def _is_valid_json_response(result: "HttpExecutionResult") -> bool:
    """
    True if response body is valid JSON.
    """
    body = result.response_body
    if body is None:
        return False
    if isinstance(body, (dict, list)):
        return True  # Already parsed successfully
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8", errors="replace")
        except Exception:
            return False
    if isinstance(body, str):
        try:
            json.loads(body)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    return False