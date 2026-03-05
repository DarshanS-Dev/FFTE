"""CLI entry point for FFTE — Failure-First Testing Engine.

Usage:
    python -m ffte --target http://127.0.0.1:8000/openapi.json
    python -m ffte --dry-run --target http://127.0.0.1:8000/openapi.json
"""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ffte",
        description="Failure-First Testing Engine — fuzz API endpoints discovered from an OpenAPI spec.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="URL of the OpenAPI spec (e.g. http://127.0.0.1:8000/openapi.json)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override the base URL for requests (extracted from spec by default)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print planned test cases without sending any HTTP requests or writing to the database",
    )
    parser.add_argument(
        "--intensity",
        type=int,
        default=5,
        choices=range(1, 11),
        metavar="1-10",
        help="Fuzzing intensity from 1 (minimal) to 10 (exhaustive). Default: 5",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds. Default: 10",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of endpoints to scan",
    )

    args = parser.parse_args()

    # Import here so --help is fast and doesn't require all dependencies
    from core.runner import run

    report = run(
        spec_url=args.target,
        base_url=args.base_url,
        timeout=args.timeout,
        limit_endpoints=args.limit,
        fuzzing_intensity=args.intensity,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        from reporting.report import format_report

        if report:
            print(format_report(report))
        else:
            print("✅ No failures detected.")


if __name__ == "__main__":
    main()
