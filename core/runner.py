"""
Core runner module.

This contains the reusable FFTE scanning workflow used by both the CLI and the API.
"""

from __future__ import annotations

import json
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import Optional
from uuid import UUID

from surface_discovery.openapi_parser import Endpoint, Parameter, fetch_and_parse
from input_generation.edge_cases import (
    generate_edge_cases_flat,
    generate_sample_object,
    classify_edge_case_type,
    QUERY_PARAM_EDGE_CASES,
)
from execution.http_executor import execute_request, HttpExecutionResult
from reporting.report import ExecutionLogEntry, generate_report
from failure_detection.rules import classify

from sqlmodel import Session
from db.database import engine
from db.models import TestExecution, Scan

logger = logging.getLogger("ffte.core.runner")

def _path_param_value(param_type: str | None) -> str:
    """Return a placeholder value for a path parameter."""
    if param_type in ("integer", "number"):
        return "1"
    return "test"


def _safe_default_for_param(param: Parameter) -> str:
    """Return a safe default string value for a query parameter.

    Uses the parameter's type and schema format so non-target params
    pass input validation while the target param is being fuzzed.
    """
    ptype = param.param_type
    fmt = (param.schema or {}).get("format", "") if param.schema else ""

    if ptype in ("integer", "number"):
        return "1"
    if ptype == "boolean":
        return "true"
    if ptype == "string":
        if fmt == "date":
            return "2024-01-01"
        if fmt == "date-time":
            return "2024-01-01T00:00:00Z"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt == "email":
            return "test@example.com"
        return "test"
    return "1"


def _build_url(base_url: str, path: str, path_params: dict[str, str]) -> str:
    """Build full URL with path parameters substituted."""
    url = path
    for name, value in path_params.items():
        url = url.replace("{" + name + "}", value)
    return urljoin(base_url.rstrip("/") + "/", url.lstrip("/"))


def _build_params(endpoint: Endpoint) -> tuple[dict[str, str], dict[str, str]]:
    """Build path params and query params from endpoint parameters."""
    path_params: dict[str, str] = {}
    query_params: dict[str, str] = {}

    for p in endpoint.parameters:
        val = _path_param_value(p.param_type)
        if p.location == "path":
            path_params[p.name] = val
        elif p.location == "query":
            query_params[p.name] = val

    return path_params, query_params


def _dry_run_report(
    endpoints: list[Endpoint],
    base_url: str,
    max_cases_per_field: int,
) -> dict[str, list[str]]:
    """Print a table of every test case that *would* be sent, then return."""
    rows: list[tuple[str, str, str, str, str, str]] = []  # endpoint, method, param, location, ec_type, wire_value

    for endpoint in endpoints:
        path_params, _qp = _build_params(endpoint)
        url = _build_url(base_url, endpoint.path, path_params)

        # Query-param rows
        query_param_list = [
            p for p in endpoint.parameters if p.location == "query"
        ]
        for qp in query_param_list:
            for ec_type, ec_value in QUERY_PARAM_EDGE_CASES[:max_cases_per_field]:
                rows.append((url, endpoint.method.upper(), qp.name, "query", ec_type, ec_value))

        # Body-param rows
        if endpoint.request_body_schema:
            edge_cases = generate_edge_cases_flat(endpoint.request_body_schema)
            for field, values in edge_cases.items():
                for v in values[:max_cases_per_field]:
                    try:
                        wire_value = json.dumps(v, ensure_ascii=False)
                    except (ValueError, TypeError, OverflowError):
                        wire_value = repr(v)
                    rows.append((url, endpoint.method.upper(), field, "body", classify_edge_case_type(v), wire_value))

    if not rows:
        print("No test cases to run.")
        return {}

    # Column widths
    headers = ("ENDPOINT", "METHOD", "PARAM", "LOCATION", "EDGE_CASE_TYPE", "WIRE_VALUE")
    widths = [len(h) for h in headers]
    display_rows: list[tuple[str, str, str, str, str, str, str]] = []  # + flag column

    for ep, method, param, loc, ec_type, wire in rows:
        flag = ""
        if loc == "query" and wire in ("inf", "nan"):
            flag = " ⚠️  float() silently accepts this"
        elif loc == "body":
            try:
                json.loads(wire)
            except (json.JSONDecodeError, ValueError):
                flag = " 🔴  json.dumps would crash"

        display_rows.append((ep, method, param, loc, ec_type, wire[:60], flag))
        for i, val in enumerate((ep, method, param, loc, ec_type, wire[:60])):
            widths[i] = max(widths[i], len(str(val)))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print()
    print("🔍 DRY-RUN — planned test cases:")
    print("=" * (sum(widths) + 2 * (len(widths) - 1)))
    print(fmt.format(*headers))
    print("-" * (sum(widths) + 2 * (len(widths) - 1)))

    for row in display_rows:
        line = fmt.format(*row[:6])
        if row[6]:
            line += row[6]
        print(line)

    print()
    print(f"Total: {len(rows)} test cases across {len(endpoints)} endpoints")
    return {}


def run(
    spec_url: str,
    base_url: str | None = None,
    *,
    timeout: float = 10.0,
    limit_endpoints: int | None = None,
    scan_id: Optional[str] = None,
    fuzzing_intensity: int = 5,
    dry_run: bool = False,
) -> dict[str, list[str]]:
    """Run the full failure-first fuzzing workflow."""

    # Map fuzzing intensity (1-10 slider) to number of test cases per field
    # Scale: 1 = minimal (3 cases), 10 = exhaustive (100 cases)
    if fuzzing_intensity <= 3:
        max_cases_per_field = 3  # Low: 1-3 on slider = 3 cases
    elif fuzzing_intensity <= 5:
        max_cases_per_field = 10  # Medium: 4-5 = 10 cases
    elif fuzzing_intensity <= 7:
        max_cases_per_field = 30  # High: 6-7 = 30 cases
    elif fuzzing_intensity <= 9:
        max_cases_per_field = 50  # Very High: 8-9 = 50 cases
    else:
        max_cases_per_field = 100  # Extreme: 10 = 100 cases (test everything)

    intensity_label = {1: "Low", 2: "Low", 3: "Low", 4: "Medium", 5: "Medium",
                       6: "High", 7: "High", 8: "Very High", 9: "Very High",
                       10: "Extreme"}
    label = intensity_label.get(fuzzing_intensity, "Medium")
    print(f"🎚️  Fuzzing intensity: {fuzzing_intensity}/10 ({label} - {max_cases_per_field} cases per field)")

    endpoints, extracted_base_url = fetch_and_parse(spec_url)

    if base_url is None and extracted_base_url:
        base_url = extracted_base_url
        print(f"🔗 Using base URL from spec: {base_url}")

    if base_url is None:
        parsed = urlparse(spec_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    if limit_endpoints is not None:
        endpoints = endpoints[:limit_endpoints]

    # ── DRY-RUN MODE ─────────────────────────────────────────────────
    if dry_run:
        return _dry_run_report(endpoints, base_url, max_cases_per_field)

    entries: list[ExecutionLogEntry] = []

    # Optional DB session for recording executions
    db_session: Session | None = None
    db_scan_uuid: UUID | None = None
    if scan_id is not None:
        try:
            db_scan_uuid = UUID(scan_id)
            db_session = Session(engine)
            logger.info("Database logging enabled for scan %s", scan_id)
        except Exception as exc:
            logger.warning(
                "Database unavailable for scan %s; continuing without persistence: %s",
                scan_id,
                exc,
            )
            db_session = None
            db_scan_uuid = None

    try:
        for endpoint in endpoints:
            path_params, query_params = _build_params(endpoint)
            url = _build_url(base_url, endpoint.path, path_params)

            # --- QUERY PARAMETER FUZZING ---
            query_param_list = [
                p for p in endpoint.parameters if p.location == "query"
            ]
            if query_param_list:
                for qp in query_param_list:
                    for ec_type, ec_value in QUERY_PARAM_EDGE_CASES[:max_cases_per_field]:
                        fuzzed_params = {
                            p.name: _safe_default_for_param(p)
                            for p in query_param_list
                        }
                        fuzzed_params[qp.name] = ec_value

                        result = execute_request(
                            method=endpoint.method,
                            url=url,
                            timeout=timeout,
                            params=fuzzed_params,
                            json=None,
                        )

                        # Persist query-param test execution
                        if db_session is not None and db_scan_uuid is not None:
                            try:
                                classification = classify(result)
                                caused_failure = classification.is_failure
                                failure_type = (
                                    classification.failure_type.value
                                    if caused_failure
                                    else None
                                )
                                response_time_ms = (
                                    result.latency_seconds * 1000.0
                                    if result.latency_seconds is not None
                                    else None
                                )

                                if not ec_type:
                                    logger.warning(
                                        "edge_case_type is None for param %s"
                                        " — this row will be invisible in reports",
                                        qp.name,
                                    )

                                exec_record = TestExecution(
                                    scan_id=db_scan_uuid,
                                    endpoint=endpoint.path,
                                    http_method=endpoint.method.lower(),
                                    field_name=qp.name,
                                    field_type=qp.schema.get("type") if qp.schema else None,
                                    is_required=qp.required,
                                    edge_case_type=ec_type,
                                    edge_case_value=str(ec_value),
                                    status_code=result.status_code,
                                    failure_type=failure_type,
                                    caused_failure=caused_failure,
                                    response_time_ms=response_time_ms,
                                    timestamp=datetime.utcnow(),
                                )
                                db_session.add(exec_record)
                                db_session.commit()
                            except Exception as exc:
                                logger.error(
                                    "Failed to persist TestExecution for scan %s: %s",
                                    db_scan_uuid,
                                    exc,
                                )
                                db_session.rollback()

                        entries.append(
                            ExecutionLogEntry(
                                method=endpoint.method,
                                url=url,
                                params=fuzzed_params,
                                json_body=None,
                                result=result,
                            )
                        )

            # --- BODY FUZZING ---
            if endpoint.request_body_schema:
                edge_cases = generate_edge_cases_flat(endpoint.request_body_schema)

                for field, values in edge_cases.items():
                    for v in values[:max_cases_per_field]:  # dynamic limit from intensity
                        try:
                            json_body = generate_sample_object(
                                endpoint.request_body_schema,
                                {field: v},
                            )
                        except Exception:
                            json_body = {}

                        result = execute_request(
                            method=endpoint.method,
                            url=url,
                            timeout=timeout,
                            params=query_params if query_params else None,
                            json=json_body,
                        )

                        # Persist execution details per test case when DB is available
                        if db_session is not None and db_scan_uuid is not None:
                            try:
                                classification = classify(result)
                                failure_type = classification.failure_type.value
                                caused_failure = classification.is_failure
                                response_time_ms = (
                                    result.latency_seconds * 1000.0
                                    if result.latency_seconds is not None
                                    else None
                                )

                                exec_record = TestExecution(
                                    scan_id=db_scan_uuid,
                                    endpoint=endpoint.path,
                                    http_method=endpoint.method.lower(),
                                    field_name=field,
                                    field_type=None,
                                    is_required=None,
                            edge_case_type=classify_edge_case_type(v),
                                    edge_case_value=str(v),
                                    status_code=result.status_code,
                                    failure_type=failure_type,
                                    caused_failure=caused_failure,
                                    response_time_ms=response_time_ms,
                                    timestamp=datetime.utcnow(),
                                )
                                db_session.add(exec_record)
                                db_session.commit()
                            except Exception as exc:
                                logger.error(
                                    "Failed to persist TestExecution for scan %s: %s",
                                    db_scan_uuid,
                                    exc,
                                )
                                db_session.rollback()

                        entries.append(
                            ExecutionLogEntry(
                                method=endpoint.method,
                                url=url,
                                params=query_params if query_params else None,
                                json_body=json_body,
                                result=result,
                            )
                        )
            elif not query_param_list:
                # Endpoints without request body or query params
                result = execute_request(
                    method=endpoint.method,
                    url=url,
                    timeout=timeout,
                    params=query_params if query_params else None,
                    json=None,
                )

                if db_session is not None and db_scan_uuid is not None:
                    try:
                        classification = classify(result)
                        failure_type = classification.failure_type.value
                        caused_failure = classification.is_failure
                        response_time_ms = (
                            result.latency_seconds * 1000.0
                            if result.latency_seconds is not None
                            else None
                        )

                        exec_record = TestExecution(
                            scan_id=db_scan_uuid,
                            endpoint=endpoint.path,
                            http_method=endpoint.method.lower(),
                            field_name=None,
                            field_type=None,
                            is_required=None,
                            edge_case_type=None,
                            edge_case_value=None,
                            status_code=result.status_code,
                            failure_type=failure_type,
                            caused_failure=caused_failure,
                            response_time_ms=response_time_ms,
                            timestamp=datetime.utcnow(),
                        )
                        db_session.add(exec_record)
                        db_session.commit()
                    except Exception as exc:
                        logger.error(
                            "Failed to persist TestExecution for scan %s: %s",
                            db_scan_uuid,
                            exc,
                        )
                        db_session.rollback()

                entries.append(
                    ExecutionLogEntry(
                        method=endpoint.method,
                        url=url,
                        params=query_params if query_params else None,
                        json_body=None,
                        result=result,
                    )
                )

        # On successful completion, mark the scan as completed in the database
        if db_session is not None and db_scan_uuid is not None:
            try:
                db_scan = db_session.get(Scan, db_scan_uuid)
                if db_scan is not None:
                    db_scan.status = "completed"
                    db_scan.end_time = datetime.utcnow()
                    db_session.add(db_scan)
                    db_session.commit()
            except Exception as exc:
                logger.error(
                    "Failed to mark scan %s as completed in database: %s",
                    db_scan_uuid,
                    exc,
                )
                db_session.rollback()

        return generate_report(entries)

    except Exception:
        # On failure, mark the scan as failed in the database
        if db_session is not None and db_scan_uuid is not None:
            try:
                db_scan = db_session.get(Scan, db_scan_uuid)
                if db_scan is not None:
                    db_scan.status = "failed"
                    db_scan.end_time = datetime.utcnow()
                    db_session.add(db_scan)
                    db_session.commit()
            except Exception as exc:
                logger.error(
                    "Failed to mark scan %s as failed in database: %s",
                    db_scan_uuid,
                    exc,
                )
                db_session.rollback()
        raise

    finally:
        if db_session is not None:
            db_session.close()
