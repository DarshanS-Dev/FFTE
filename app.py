#!/usr/bin/env python3
"""
FFTE orchestrator: wires surface discovery, input generation, execution,
failure detection, and reporting into a single fuzzing workflow.
"""

from __future__ import annotations

import sys
from core.runner import run
from reporting.report import format_report


def main():
    """Command-line interface."""
    # Default to testing the victim.py API
    if len(sys.argv) > 1:
        spec_url = sys.argv[1]
        base_url = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        print("Using default test API (victim.py)")
        spec_url = "http://127.0.0.1:8000/openapi.json"
        base_url = "http://127.0.0.1:8000"
    
    try:
        print("=" * 60)
        print("🚀 Starting FFTE - Failure-First Testing Engine")
        print("=" * 60)
        print(f"\n🔍 Target: {spec_url}")
        print(f"🌐 Base URL: {base_url}\n")
        
        # Run the core FFTE workflow
        report = run(
            spec_url=spec_url,
            base_url=base_url,
            timeout=10.0,
            limit_endpoints=None
        )
        
        # Format and display report
        formatted_report = format_report(report)
        
        if formatted_report:
            print("\n" + "=" * 60)
            print("📋 FAILURE REPORT")
            print("=" * 60)
            print(formatted_report)
            
            # Save report to file
            with open("ffte_report.txt", "w") as f:
                f.write(formatted_report)
            print(f"\n💾 Report saved to ffte_report.txt")
            
            # Count failures
            failure_count = sum(len(commands) for commands in report.values())
            print(f"\n📈 Summary: Found {failure_count} failures")
            
            return 0
        else:
            print("\n✅ No failures detected!")
            return 0
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())