"""
Report module: group execution failures by type and generate reproducible curl commands.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from failure_detection.rules import FailureType, classify
from execution.http_executor import HttpExecutionResult


@dataclass
class ExecutionLogEntry:
    """
    A single execution log entry: request details + result.

    Used to classify failures and generate reproducible curl commands.
    """

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] | None = None
    json_body: Any = None
    data: Any = None
    result: HttpExecutionResult | dict[str, Any] | None = None

    def _get_result(self) -> HttpExecutionResult | None:
        """Return HttpExecutionResult for classification."""
        if self.result is None:
            return None
        if isinstance(self.result, HttpExecutionResult):
            return self.result
        # Build from dict (e.g. from JSON logs)
        d = self.result
        return HttpExecutionResult(
            status_code=d.get("status_code"),
            response_body=d.get("response_body"),
            latency_seconds=d.get("latency_seconds"),
            exception=d.get("exception"),
            headers=d.get("headers") or {},
            success=d.get("success", False),
        )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExecutionLogEntry:
        """Build ExecutionLogEntry from a dict (e.g. JSON log)."""
        return cls(
            method=d.get("method", "GET"),
            url=d.get("url", ""),
            headers=d.get("headers") or {},
            params=d.get("params"),
            json_body=d.get("json") or d.get("json_body"),
            data=d.get("data"),
            result=d.get("result"),
        )


def group_failures_by_type(
    entries: list[ExecutionLogEntry],
) -> dict[FailureType, list[ExecutionLogEntry]]:
    """
    Group execution log entries by failure type.

    Args:
        entries: List of ExecutionLogEntry with request and result.

    Returns:
        Dict mapping FailureType to list of entries that failed with that type.
        Entries with FailureType.NONE are excluded.
    """
    grouped: dict[FailureType, list[ExecutionLogEntry]] = defaultdict(list)
    for entry in entries:
        result = entry._get_result()
        if result is None:
            continue
        classification = classify(result)
        if classification.is_failure:
            grouped[classification.failure_type].append(entry)
    return dict(grouped)


def to_curl(entry: ExecutionLogEntry) -> str:
    """
    Generate a reproducible curl command from an execution log entry.

    Args:
        entry: ExecutionLogEntry with method, url, headers, params, body.

    Returns:
        A curl command string that can be run in a shell.
    """
    parts: list[str] = ["curl"]
    parts.append("-X")
    parts.append(entry.method.upper())

    # Headers
    for key, value in (entry.headers or {}).items():
        # Escape double quotes in value for shell
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'-H "{key}: {escaped}"')

    # URL with query params
    url = entry.url
    params = entry.params or {}
    if params:
        from urllib.parse import urlencode

        qs = urlencode(params, doseq=True)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{qs}"
    parts.append(f'"{url}"')

    # Body
    if entry.json_body is not None:
        body_str = json.dumps(entry.json_body, ensure_ascii=False)
        # For curl -d, we use single quotes and escape single quotes
        escaped = body_str.replace("'", "'\\''")
        parts.append(f"-d '{escaped}'")
        if "content-type" not in {k.lower() for k in (entry.headers or {}).keys()}:
            parts.append("-H \"Content-Type: application/json\"")
    elif entry.data is not None:
        if isinstance(entry.data, (dict, list)):
            body_str = json.dumps(entry.data, ensure_ascii=False)
        else:
            body_str = str(entry.data)
        escaped = body_str.replace("'", "'\\''")
        parts.append(f"-d '{escaped}'")

    return " ".join(parts)


def load_entries_from_logs(logs: list[dict[str, Any]]) -> list[ExecutionLogEntry]:
    """
    Load ExecutionLogEntry list from log dicts (e.g. from JSON file).

    Each log dict should have: method, url, and optionally headers, params,
    json/json_body, data, result.
    """
    return [ExecutionLogEntry.from_dict(log) for log in logs]


def generate_report(
    entries: list[ExecutionLogEntry],
) -> dict[str, list[str]]:
    """
    Group failures by type and return reproducible curl commands per type.

    Args:
        entries: List of ExecutionLogEntry with request and result.

    Returns:
        Dict mapping failure type name (e.g. "server_error") to list of curl
        command strings. One curl per failed request, grouped by failure type.
    """
    grouped = group_failures_by_type(entries)
    report: dict[str, list[str]] = {}
    for failure_type, failed_entries in grouped.items():
        report[failure_type.value] = [to_curl(e) for e in failed_entries]
    return report


def format_report(report: dict[str, list[str]]) -> str:
    """
    Format a report as human-readable text.

    Args:
        report: Output from generate_report.

    Returns:
        Formatted string with failure types and curl commands.
    """
    lines: list[str] = []
    for failure_type, curls in sorted(report.items()):
        lines.append(f"## {failure_type} ({len(curls)} occurrence(s))")
        lines.append("")
        for i, cmd in enumerate(curls, 1):
            lines.append(f"### Example {i}")
            lines.append(cmd)
            lines.append("")
        lines.append("")
    return "\n".join(lines).strip()
