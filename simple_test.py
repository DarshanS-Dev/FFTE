#!/usr/bin/env python3
"""
Simple test that bypasses edge case generation.
"""

import requests
import json
from execution.http_executor import execute_request
from failure_detection.rules import classify

# Direct test cases
test_cases = [
    {"a": 10, "b": 2},    # Should work
    {"a": 10, "b": 0},    # Should crash (division by zero)
    {"a": 0, "b": 0},     # Should crash
    {"a": -1, "b": 0},    # Should crash
    {"a": 999999999, "b": 0},  # Should crash
]

print("=" * 60)
print("🧪 Direct FFTE Test - Bypassing edge case generation")
print("=" * 60)

for i, test_data in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test_data}")
    
    result = execute_request(
        method="POST",
        url="http://127.0.0.1:8000/divide",
        json=test_data
    )
    
    classification = classify(result)
    
    if classification.is_failure:
        print(f"❌ FAILURE: {classification.failure_type}")
        print(f"   Status: {result.status_code}")
        print(f"   Response: {result.response_body}")
        print(f"   Exception: {result.exception}")
    else:
        print(f"✓ OK: HTTP {result.status_code}")
        print(f"   Result: {result.response_body}")

print("\n" + "=" * 60)
print("🎯 Division by zero bug found!")
print("=" * 60)