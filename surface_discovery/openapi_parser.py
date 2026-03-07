"""OpenAPI spec parser with $ref resolution and robust error handling."""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests


@dataclass
class Parameter:
    name: str
    location: str
    param_type: Optional[str] = None
    required: bool = False
    schema: Optional[Dict[str, Any]] = None


@dataclass
class Endpoint:
    path: str
    method: str
    summary: Optional[str] = None
    parameters: List[Parameter] = None
    request_body_schema: Optional[Dict[str, Any]] = None
    operation_id: Optional[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


def resolve_refs(schema: Any, spec: Dict[str, Any]) -> Any:
    """Resolve all $ref in schema recursively."""
    if not isinstance(schema, dict):
        return schema
    
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/"):
            parts = ref[2:].split("/")
            obj = spec
            for part in parts:
                obj = obj.get(part, {})
            return resolve_refs(obj, spec)
    
    result = {}
    for k, v in schema.items():
        if isinstance(v, dict):
            result[k] = resolve_refs(v, spec)
        elif isinstance(v, list):
            result[k] = [resolve_refs(item, spec) if isinstance(item, dict) else item for item in v]
        else:
            result[k] = v
    return result


def _parse_parameters(params_data: Any, spec: Dict[str, Any]) -> List[Parameter]:
    """Parse parameters from various formats."""
    if not params_data:
        return []
    
    # Handle if params_data is a list
    if isinstance(params_data, list):
        params = []
        for p in params_data:
            if not isinstance(p, dict):
                continue
            params.append(Parameter(
                name=p.get("name", ""),
                location=p.get("in", ""),
                param_type=p.get("schema", {}).get("type") if isinstance(p.get("schema"), dict) else None,
                required=p.get("required", False),
                schema=resolve_refs(p.get("schema", {}), spec) if isinstance(p.get("schema"), dict) else {}
            ))
        return params
    
    # Handle if params_data is a dict (shouldn't happen but be safe)
    if isinstance(params_data, dict):
        return []
    
    return []


def _parse_request_body(req_body: Any, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse request body schema from various formats."""
    if not req_body or not isinstance(req_body, dict):
        return None
    
    content = req_body.get("content", {})
    if not isinstance(content, dict):
        return None
    
    # Try to find JSON content type
    for ct, ct_spec in content.items():
        if not isinstance(ct_spec, dict):
            continue
        if "json" in ct.lower():
            schema = ct_spec.get("schema", {})
            if isinstance(schema, dict):
                return resolve_refs(schema, spec)
    
    return None


def fetch_and_parse(openapi_url: str) -> tuple[List[Endpoint], Optional[str], dict]:
    """Fetch and parse OpenAPI spec from URL with robust error handling.

    Returns:
        (endpoints, base_url) – *base_url* is extracted from the spec's
        ``servers`` (OpenAPI 3.x) or ``host``/``schemes``/``basePath``
        (OpenAPI 2.0) and may be ``None`` if the spec provides neither.
    """
    try:
        response = requests.get(openapi_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch OpenAPI spec from {openapi_url}: {e}")
    
    try:
        spec = response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in OpenAPI spec: {e}")
    
    if not isinstance(spec, dict):
        raise ValueError("OpenAPI spec must be a JSON object")
    
    # --- Extract base URL from spec ---
    base_url: Optional[str] = None
    if "servers" in spec and isinstance(spec["servers"], list) and len(spec["servers"]) > 0:
        base_url = spec["servers"][0].get("url")
    elif "host" in spec:  # OpenAPI 2.0
        scheme = spec.get("schemes", ["https"])[0]
        base_path = spec.get("basePath", "")
        base_url = f"{scheme}://{spec['host']}{base_path}"
    
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        raise ValueError("'paths' in OpenAPI spec must be an object")
    
    endpoints = []
    
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            print(f"⚠️  Skipping path {path}: path item is not an object")
            continue
        
        # Iterate through HTTP methods
        for method, operation in path_item.items():
            # Skip non-method keys like 'summary', 'description', 'parameters', '$ref'
            if method.lower() not in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']:
                continue
            
            # Ensure operation is a dict
            if not isinstance(operation, dict):
                print(f"⚠️  Skipping {method.upper()} {path}: operation is not an object")
                continue
            
            # Parse parameters
            params = _parse_parameters(operation.get("parameters", []), spec)
            
            # Parse request body
            body_schema = _parse_request_body(operation.get("requestBody"), spec)
            
            if body_schema is None:
                for p in operation.get("parameters", []):
                    if isinstance(p, dict) and p.get("in") == "body":
                        schema = p.get("schema", {})
                        if isinstance(schema, dict):
                            body_schema = resolve_refs(schema, spec)
                        break
            
            endpoints.append(Endpoint(
                path=path,
                method=method.lower(),
                summary=operation.get("summary"),
                parameters=params,
                request_body_schema=body_schema,
                operation_id=operation.get("operationId")
            ))
    
    if not endpoints:
        raise ValueError("No valid endpoints found in OpenAPI spec")
    
    return endpoints, base_url, spec


def parse_from_file(file_path: str) -> List[Endpoint]:
    """Parse OpenAPI spec from a local file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try JSON first
            try:
                spec = json.load(f)
            except json.JSONDecodeError:
                # Try YAML
                f.seek(0)
                import yaml
                spec = yaml.safe_load(f)
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")
    
    if not isinstance(spec, dict):
        raise ValueError("OpenAPI spec must be a JSON/YAML object")
    
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        raise ValueError("'paths' in OpenAPI spec must be an object")
    
    endpoints = []
    
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        
        for method, operation in path_item.items():
            if method.lower() not in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']:
                continue
            
            if not isinstance(operation, dict):
                continue
            
            params = _parse_parameters(operation.get("parameters", []), spec)
            body_schema = _parse_request_body(operation.get("requestBody"), spec)
            
            if body_schema is None:
                for p in operation.get("parameters", []):
                    if isinstance(p, dict) and p.get("in") == "body":
                        schema = p.get("schema", {})
                        if isinstance(schema, dict):
                            body_schema = resolve_refs(schema, spec)
                        break
            
            endpoints.append(Endpoint(
                path=path,
                method=method.lower(),
                summary=operation.get("summary"),
                parameters=params,
                request_body_schema=body_schema,
                operation_id=operation.get("operationId")
            ))
    
    if not endpoints:
        raise ValueError("No valid endpoints found in OpenAPI spec")
    
    return endpoints