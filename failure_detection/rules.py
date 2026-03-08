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

    # 1. Timeout
    if result.exception and _is_timeout_exception(result.exception):
        flags["timeout"] = True
        return FailureClassification(
            failure_type=FailureType.TIMEOUT,
            message=result.exception or "Request timed out",
            flags=flags,
        )

    # 2. Exception handling — THE CRITICAL FIX
    #
    # http_executor.py formats exceptions as: "ClassName: message"
    # e.g. "InvalidHeader: Invalid header value..."
    #      "ConnectionError: HTTPSConnectionPool...Max retries exceeded..."
    #      "RemoteDisconnected: Remote end closed connection"
    #
    # THREE categories:
    #
    # A) OUR FAULT — bad input we generated caused invalid HTTP request
    #    Server never received it. NOT a server failure → NONE
    #    Examples: null byte \x00 in URL, \r\n in header, invalid URL
    #
    # B) REAL CRASH — server is down or completely unreachable → CRASH
    #    Examples: ConnectionRefused, DNS failure
    #
    # C) SERVER REJECTION — server alive but dropped our garbage request → NONE
    #    Examples: RemoteDisconnected, SSLError, ConnectionReset
    #    Public APIs like PetStore do this on extreme inputs — it's expected

    if result.exception:
        # Extract exception class name (first word before ":")
        exc_class = result.exception.split(":")[0].strip().lower()
        exc_msg = result.exception.lower()

        # ── A) OUR FAULT ──────────────────────────────────────────────
        our_fault_classes = {
            "invalidheader",       # null byte or \r\n in header/query param
            "invalidurl",          # malformed URL we built
            "missingschema",       # URL missing http://
            "invalidschema",       # wrong URL scheme
            "unicodeencodeerror",  # non-encodable chars
            "locationparsedfailed",
        }
        our_fault_msg_keywords = [
            "invalid header value",
            "nul byte",
            "null byte",
            "invalid url",
            "no schema supplied",
            "codec can't encode",
            "codec can\u2019t encode",
        ]
        if exc_class in our_fault_classes:
            return FailureClassification(
                failure_type=FailureType.NONE,
                message=f"Bad test input (not a server crash): {result.exception}",
                flags=flags,
            )
        for kw in our_fault_msg_keywords:
            if kw in exc_msg:
                return FailureClassification(
                    failure_type=FailureType.NONE,
                    message=f"Bad test input (not a server crash): {result.exception}",
                    flags=flags,
                )

        # ── B) REAL CRASH — server is down ────────────────────────────
        real_crash_msg_keywords = [
            "connection refused",
            "failed to establish a new connection",
            "name or service not known",
            "nodename nor servname provided",
            "no address associated with hostname",
            "network is unreachable",
            "errno 111",   # ECONNREFUSED on linux
            "errno 61",    # ECONNREFUSED on mac
        ]
        real_crash_classes = {
            "connectionrefusederror",
            "newconnectionerror",
            "nameresolutionerror",
            "gaierror",
        }
        if exc_class in real_crash_classes:
            flags["crash"] = True
            return FailureClassification(
                failure_type=FailureType.CRASH,
                message=result.exception,
                flags=flags,
            )
        for kw in real_crash_msg_keywords:
            if kw in exc_msg:
                flags["crash"] = True
                return FailureClassification(
                    failure_type=FailureType.CRASH,
                    message=result.exception,
                    flags=flags,
                )

        # ── C) SERVER REJECTION — server alive, dropped bad request ───
        rejection_classes = {
            "remotedisconnected",
            "connectionreseterror",
            "connectionabortederror",
            "sslerror",
            "chunkedencodingerror",
            "protocolerror",
        }
        rejection_msg_keywords = [
            "remote end closed connection",
            "connection reset by peer",
            "broken pipe",
            "ssl",
            "max retries exceeded",   # public API rate-limiting on bad input
        ]
        if exc_class in rejection_classes:
            return FailureClassification(
                failure_type=FailureType.NONE,
                message=f"Server rejected request (not a crash): {result.exception}",
                flags=flags,
            )
        for kw in rejection_msg_keywords:
            if kw in exc_msg:
                return FailureClassification(
                    failure_type=FailureType.NONE,
                    message=f"Server rejected request (not a crash): {result.exception}",
                    flags=flags,
                )

        # ── D) Unknown — default to crash to not miss real failures ───
        flags["crash"] = True
        return FailureClassification(
            failure_type=FailureType.CRASH,
            message=result.exception,
            flags=flags,
        )

    # 3. Server error: 5xx — genuine server bug
    if result.status_code is not None and 500 <= result.status_code < 600:
        flags["server_error"] = True
        return FailureClassification(
            failure_type=FailureType.SERVER_ERROR,
            message=f"HTTP {result.status_code}",
            flags=flags,
        )

    # 4. Smart 4xx handling
    if result.status_code is not None and 400 <= result.status_code < 500:
        flags["client_error"] = True
        response_text = ""
        if result.response_body:
            if isinstance(result.response_body, bytes):
                response_text = result.response_body.decode("utf-8", errors="replace").lower()
            elif isinstance(result.response_body, str):
                response_text = result.response_body.lower()
            elif isinstance(result.response_body, (dict, list)):
                response_text = json.dumps(result.response_body).lower()

        # Rate limit or server-side timeout
        problematic_4xx = [408, 429, 499]
        if result.status_code in problematic_4xx:
            return FailureClassification(
                failure_type=FailureType.CLIENT_ERROR,
                message=f"Problematic 4xx: {result.status_code}",
                flags=flags,
            )

        # 400 with server-side error trace = real bug
        error_indicators = ["exception", "traceback", "stack trace", "internal error", "unhandled"]
        if result.status_code == 400 and any(ind in response_text for ind in error_indicators):
            return FailureClassification(
                failure_type=FailureType.CLIENT_ERROR,
                message="400 with server error trace",
                flags=flags,
            )

        # All other 4xx = validation working correctly — NOT a failure
        return FailureClassification(
            failure_type=FailureType.NONE,
            message=f"Expected validation rejection: {result.status_code}",
            flags=flags,
        )

    # 5. Invalid JSON response
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
    """True if response body is valid JSON."""
    body = result.response_body
    if body is None:
        return False
    if isinstance(body, (dict, list)):
        return True
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