"""
OpenAPI spec parser for surface discovery.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class Parameter:
    """OpenAPI parameter specification."""
    name: str
    location: str  # "path", "query", "header", "cookie"
    param_type: Optional[str] = None
    required: bool = False
    schema: Optional[Dict[str, Any]] = None


@dataclass
class Endpoint:
    """Represents an API endpoint discovered from OpenAPI spec."""
    path: str
    method: str  # "get", "post", "put", "delete", etc.
    summary: Optional[str] = None
    parameters: List[Parameter] = None
    request_body_schema: Optional[Dict[str, Any]] = None
    operation_id: Optional[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


def fetch_and_parse(openapi_url: str) -> List[Endpoint]:
    """
    Fetch OpenAPI spec from URL and parse it into Endpoint objects.
    
    Args:
        openapi_url: URL to OpenAPI spec (e.g., http://localhost:8000/openapi.json)
    
    Returns:
        List of discovered Endpoint objects
    """
    try:
        response = requests.get(openapi_url, timeout=10)
        response.raise_for_status()
        spec = response.json()
        return _parse_spec(spec)
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch OpenAPI spec from {openapi_url}: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in OpenAPI spec: {e}")


def _parse_spec(spec: Dict[str, Any]) -> List[Endpoint]:
    """Parse OpenAPI spec dictionary into Endpoint objects."""
    endpoints = []
    
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            # Normalize method to lowercase
            method_lower = method.lower()
            
            # Parse parameters
            parameters = []
            for param_spec in details.get("parameters", []):
                param = Parameter(
                    name=param_spec.get("name", ""),
                    location=param_spec.get("in", ""),
                    param_type=param_spec.get("schema", {}).get("type"),
                    required=param_spec.get("required", False),
                    schema=param_spec.get("schema")
                )
                parameters.append(param)
            
            # Parse request body
            request_body_schema = None
            request_body = details.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                for content_type, content_spec in content.items():
                    if "application/json" in content_type or "json" in content_type:
                        request_body_schema = content_spec.get("schema")
                        break
            
            endpoint = Endpoint(
                path=path,
                method=method_lower,
                summary=details.get("summary"),
                parameters=parameters,
                request_body_schema=request_body_schema,
                operation_id=details.get("operationId")
            )
            endpoints.append(endpoint)
    
    return endpoints


def parse_from_file(file_path: str) -> List[Endpoint]:
    """
    Parse OpenAPI spec from a local file.
    
    Args:
        file_path: Path to OpenAPI spec file (JSON or YAML)
    
    Returns:
        List of discovered Endpoint objects
    """
    import yaml
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            spec = yaml.safe_load(f)
        else:
            spec = json.load(f)
    
    return _parse_spec(spec)