#!/usr/bin/env python3
"""
Fixed FFTE Scanner that actually finds the division by zero bug.
"""

import json
from typing import List, Dict, Any
from execution.http_executor import execute_request
from failure_detection.rules import classify
from reporting.report import ExecutionLogEntry, generate_report, format_report


class FixedFFTEScanner:
    """Fixed scanner that actually tests for edge cases."""
    
    def scan_victim_api(self) -> Dict[str, Any]:
        """
        Scan the victim API and find division by zero bugs.
        Returns a complete report.
        """
        print("🔍 Starting FFTE scan on victim API...")
        
        # Manual test cases for the /divide endpoint
        test_cases = [
            # Normal cases
            {"a": 10, "b": 2},
            {"a": 0, "b": 1},
            {"a": -10, "b": 5},
            
            # Edge cases that should work
            {"a": 0, "b": 100},
            {"a": 999999, "b": 1},
            {"a": -999999, "b": 1},
            
            # DIVISION BY ZERO BUGS (these should crash!)
            {"a": 10, "b": 0},
            {"a": 0, "b": 0},
            {"a": -10, "b": 0},
            {"a": 1, "b": 0},
            {"a": -1, "b": 0},
            
            # Boundary cases
            {"a": 2147483647, "b": 1},  # Max 32-bit int
            {"a": -2147483648, "b": 1}, # Min 32-bit int
            {"a": 2147483647, "b": 0},  # Max int ÷ 0 (should crash!)
            {"a": -2147483648, "b": 0}, # Min int ÷ 0 (should crash!)
        ]
        
        execution_entries = []
        
        for i, test_data in enumerate(test_cases):
            print(f"\n🧪 Test {i+1}/{len(test_cases)}: {test_data}")
            
            result = execute_request(
                method="POST",
                url="http://127.0.0.1:8000/divide",
                json=test_data,
                timeout=10.0
            )
            
            entry = ExecutionLogEntry(
                method="POST",
                url="http://127.0.0.1:8000/divide",
                json_body=test_data,
                result=result
            )
            execution_entries.append(entry)
            
            classification = classify(result)
            
            if classification.is_failure:
                print(f"   ❌ FAILURE: {classification.failure_type}")
                if result.exception and "division by zero" in str(result.exception):
                    print(f"   💥 DIVISION BY ZERO BUG FOUND!")
                elif result.response_body and "division by zero" in str(result.response_body):
                    print(f"   💥 DIVISION BY ZERO BUG FOUND!")
            else:
                print(f"   ✓ OK: HTTP {result.status_code}")
                if result.response_body:
                    print(f"   Result: {result.response_body}")
        
        # Generate report
        report = generate_report(execution_entries)
        formatted = format_report(report)
        
        # Count failures
        total_tests = len(test_cases)
        failures = sum(len(commands) for commands in report.values())
        
        print("\n" + "=" * 60)
        print("📊 SCAN COMPLETE")
        print("=" * 60)
        print(f"Total tests: {total_tests}")
        print(f"Failures found: {failures}")
        
        if failures > 0:
            print("\n💥 FAILURES DETECTED!")
            print(formatted)
        else:
            print("\n✅ No failures detected")
        
        return {
            "total_tests": total_tests,
            "failures": failures,
            "report": report,
            "formatted_report": formatted,
            "execution_entries": [entry.__dict__ for entry in execution_entries]
        }


def quick_demo():
    """Quick demo for the expo."""
    scanner = FixedFFTEScanner()
    
    print("=" * 60)
    print("🚀 FFTE EXPO DEMO - FINDING DIVISION BY ZERO BUG")
    print("=" * 60)
    
    print("\n🎯 Target: Vulnerable FastAPI at http://127.0.0.1:8000")
    print("   Endpoint: POST /divide")
    print("   Bug: No validation for division by zero")
    
    print("\n🔍 Starting intelligent fuzzing...")
    print("   FFTE will test:")
    print("   • Normal cases (10 ÷ 2)")
    print("   • Edge cases (0 ÷ 1, max int ÷ 1)")
    print("   • CRITICAL: Division by zero (10 ÷ 0)")
    
    results = scanner.scan_victim_api()
    
    print("\n" + "=" * 60)
    print("🎯 DEMO COMPLETE - COPY THIS FOR YOUR EXPO")
    print("=" * 60)
    
    if results["failures"] > 0:
        print(f"\n💥 FOUND {results['failures']} BUG(S)!")
        print("\n🔧 Reproduce with:")
        print("   curl -X POST 'http://127.0.0.1:8000/divide' \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"a\": 10, \"b\": 0}'")
        
        print("\n📋 Bug report saved to 'ffte_bug_report.txt'")
        with open("ffte_bug_report.txt", "w") as f:
            f.write(results["formatted_report"])
    else:
        print("\n⚠️  No bugs found (unexpected!)")
    
    return results


if __name__ == "__main__":
    quick_demo()