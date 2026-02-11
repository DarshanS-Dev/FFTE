"""
Core runner module.

This contains the reusable FFTE scanning workflow used by both the CLI and the API.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from surface_discovery.openapi_parser import Endpoint, fetch_and_parse
from input_generation.edge_cases import generate_edge_cases_flat, generate_sample_object
from execution.http_executor import execute_request
from reporting.report import ExecutionLogEntry, generate_report


def _path_param_value(param_type: str | None) -> str:
    """Return a placeholder value for a path parameter."""
    if param_type in ("integer", "number"):
        return "1"
    return "test"


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


def run(
    spec_url: str,
    base_url: str | None = None,
    *,
    timeout: float = 10.0,
    limit_endpoints: int | None = None,
) -> dict[str, list[str]]:
    """Run the full failure-first fuzzing workflow."""
    if base_url is None:
        parsed = urlparse(spec_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    endpoints = fetch_and_parse(spec_url)
    if limit_endpoints is not None:
        endpoints = endpoints[:limit_endpoints]

    entries: list[ExecutionLogEntry] = []

    for endpoint in endpoints:
        path_params, query_params = _build_params(endpoint)
        url = _build_url(base_url, endpoint.path, path_params)

        # FAILURE-FIRST LOGIC
        if endpoint.request_body_schema:
            edge_cases = generate_edge_cases_flat(endpoint.request_body_schema)

            for field, values in edge_cases.items():
                for v in values[:3]:  # limit explosion
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

                    entries.append(
                        ExecutionLogEntry(
                            method=endpoint.method,
                            url=url,
                            params=query_params if query_params else None,
                            json_body=json_body,
                            result=result,
                        )
                    )
        else:
            # Endpoints without request body
            result = execute_request(
                method=endpoint.method,
                url=url,
                timeout=timeout,
                params=query_params if query_params else None,
                json=None,
            )

            entries.append(
                ExecutionLogEntry(
                    method=endpoint.method,
                    url=url,
                    params=query_params if query_params else None,
                    json_body=None,
                    result=result,
                )
            )

    return generate_report(entries)
