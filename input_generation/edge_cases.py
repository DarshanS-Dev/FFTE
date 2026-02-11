"""
Generic edge-case generator based on JSON Schema types.

Produces a list of candidate values per field for fuzzing, testing,
or input generation from JSON Schema definitions.
"""

from __future__ import annotations

import math
from typing import Any

# --- Edge-case values per JSON Schema type ---

NUMBER_EDGE_CASES: list[float] = [
    0,
    -0.0,
    1,
    -1,
    0.5,
    -0.5,
    math.inf,
    -math.inf,
    float("nan"),
    1e10,
    -1e10,
    1e-10,
    -1e-10,
]

INTEGER_EDGE_CASES: list[int] = [
    0,
    1,
    -1,
    2**31 - 1,
    -(2**31),
    2**63 - 1,
    -(2**63),
]

STRING_EDGE_CASES: list[str] = [
    "",
    " ",
    "a",
    "A",
    "0",
    "hello",
    "Hello, World!",
    "A" * 1000,
    "\x00",
    "\n",
    "\t",
    "\\",
    "\"",
    "日本語",
    "emoji: \U0001f600",
    "sql' OR '1'='1",
    "<script>alert(1)</script>",
    "null",
    "true",
    "false",
]

BOOLEAN_EDGE_CASES: list[bool] = [True, False]

ARRAY_EDGE_CASES: list[list[Any]] = [
    [],
    [None],
    [0],
    [""],
    [True],
]

OBJECT_EDGE_CASES: list[dict[str, Any]] = [
    {},
    {"key": None},
    {"key": ""},
    {"key": 0},
]


def _get_candidates_for_type(
    schema: dict[str, Any],
    fallback_type: str | None = None,
) -> list[Any]:
    """
    Return candidate values for a schema based on its type and constraints.

    Args:
        schema: JSON Schema object (may have type, enum, format, minimum, etc.).
        fallback_type: Type to use when schema has no explicit type.

    Returns:
        List of candidate values for edge-case testing.
    """
    raw_type = schema.get("type", fallback_type)
    if isinstance(raw_type, list):
        if "null" in raw_type:
            nullable = True
            schema_type = next((t for t in raw_type if t != "null"), fallback_type)
        else:
            schema_type = raw_type[0] if raw_type else fallback_type
            nullable = False
    else:
        schema_type = raw_type
        nullable = schema.get("nullable", False)

    # Enum overrides type
    if "enum" in schema:
        return list(schema["enum"])

    def _add_null(candidates: list[Any]) -> list[Any]:
        if nullable and None not in candidates:
            return [None] + candidates
        return candidates

    if schema_type == "number":
        candidates = list(NUMBER_EDGE_CASES)
        if "minimum" in schema or "maximum" in schema:
            mn = schema.get("minimum", -math.inf)
            mx = schema.get("maximum", math.inf)
            candidates = [v for v in candidates if not math.isnan(v) and mn <= v <= mx]
        return _add_null(candidates)

    if schema_type == "integer":
        candidates = list(INTEGER_EDGE_CASES)
        if "minimum" in schema or "maximum" in schema:
            mn = schema.get("minimum", -(2**63))
            mx = schema.get("maximum", 2**63 - 1)
            candidates = [v for v in candidates if mn <= v <= mx]
        return _add_null(candidates)

    if schema_type == "string":
        candidates = list(STRING_EDGE_CASES)
        fmt = schema.get("format", "")
        if fmt == "email":
            candidates.extend(["a@b.com", "invalid", "a@", "@b.com"])
        elif fmt == "uuid":
            candidates.extend(["00000000-0000-0000-0000-000000000000", "invalid"])
        elif fmt == "date-time":
            candidates.extend(["2024-01-01T00:00:00Z", "invalid"])
        elif fmt == "date":
            candidates.extend(["2024-01-01", "invalid"])
        if "minLength" in schema:
            candidates.append("x" * schema["minLength"])
        if "maxLength" in schema:
            candidates.append("x" * min(schema["maxLength"], 1000))
        return _add_null(candidates)

    if schema_type == "boolean":
        return _add_null(list(BOOLEAN_EDGE_CASES))

    if schema_type == "array":
        items_schema = schema.get("items", {})
        if isinstance(items_schema, dict):
            item_candidates = _get_candidates_for_type(items_schema)
            candidates = list(ARRAY_EDGE_CASES)
            for c in item_candidates[:5]:  # limit combinations
                candidates.append([c])
        else:
            candidates = list(ARRAY_EDGE_CASES)
        if "minItems" in schema:
            n = schema["minItems"]
            candidates.append([None] * n)
        return _add_null(candidates)

    if schema_type == "object":
        props = schema.get("properties", {})
        if props:
            obj_candidates = []
            for _ in range(3):  # few sampled objects
                obj = {}
                for key, prop_schema in list(props.items())[:5]:
                    cs = _get_candidates_for_type(prop_schema)
                    if cs:
                        obj[key] = cs[0]
                obj_candidates.append(obj)
            candidates = list(OBJECT_EDGE_CASES) + obj_candidates
        else:
            candidates = list(OBJECT_EDGE_CASES)
        return _add_null(candidates)

    # Unknown or any type
    return _add_null(
        [None, 0, 1, "", " ", True, False, [], {}]
    )


def generate_edge_cases(schema: dict[str, Any]) -> dict[str, list[Any]]:
    """
    Generate edge-case candidate values per field from a JSON Schema.

    Handles objects with properties, arrays of objects, and nested structures.
    Resolves $ref relative to the given schema when possible.

    Args:
        schema: JSON Schema (e.g. from OpenAPI requestBody.content.*.schema).

    Returns:
        Dict mapping each field path (e.g. "items.id") to a list of candidate values.
    """
    result: dict[str, list[Any]] = {}

    def _walk(s: dict[str, Any], path: str = "") -> None:
        schema_type = s.get("type")
        if "$ref" in s:
            # Caller should resolve refs before calling; skip for now
            return

        if schema_type == "object":
            obj_path = path or "value"
            result[obj_path] = _get_candidates_for_type(s)
            props = s.get("properties", {})
            for key, prop_schema in props.items():
                field_path = f"{path}.{key}" if path else key
                if isinstance(prop_schema, dict):
                    result[field_path] = _get_candidates_for_type(prop_schema)
                    _walk(prop_schema, field_path)
                else:
                    result[field_path] = [None, 0, "", True, False, [], {}]

        elif schema_type == "array":
            array_path = path or "value"
            result[array_path] = _get_candidates_for_type(s)
            items = s.get("items", {})
            if isinstance(items, dict):
                item_path = f"{path}[]" if path else "[]"
                result[item_path] = _get_candidates_for_type(items)
                _walk(items, item_path)

        elif schema_type is not None:
            field_path = path or "value"
            result[field_path] = _get_candidates_for_type(s)

    _walk(schema)
    return result


def generate_edge_cases_flat(schema: dict[str, Any]) -> dict[str, list[Any]]:
    """
    Generate edge-case values per leaf field only (no nested paths).

    Use when you need a flat mapping of top-level or leaf field names
    to their candidate values.
    """
    all_cases = generate_edge_cases(schema)
    # Keep leaf paths: those whose path is not a prefix of another
    paths = sorted(all_cases.keys())
    leaf_paths = [
        p for i, p in enumerate(paths)
        if not any(p2.startswith(p + ".") or p2.startswith(p + "[]") for p2 in paths[i + 1:])
    ]
    return {p: all_cases[p] for p in leaf_paths}


def generate_sample_object(
    schema: dict[str, Any],
    field_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a sample object using first candidate per field.

    Useful for quick smoke-test payloads. Override specific fields via
    field_overrides (use dot-notation paths like "user.email").
    """
    cases = generate_edge_cases(schema)
    obj: dict[str, Any] = {}
    field_overrides = field_overrides or {}

    for path, candidates in cases.items():
        if "[]" in path or not path:
            continue
        parts = path.split(".")
        value = field_overrides.get(path)
        if value is None and candidates:
            value = candidates[0]
        if value is not None:
            _set_nested(obj, parts, value)
    return obj


def _set_nested(obj: dict[str, Any], path: list[str], value: Any) -> None:
    for key in path[:-1]:
        if key not in obj:
            obj[key] = {}
        obj = obj[key]
    obj[path[-1]] = value
