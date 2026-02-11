#!/usr/bin/env python3
"""
Expo demo version - simplified and more visual.
"""

import time
from execution.http_executor import execute_request
from failure_detection.rules import classify

def print_banner(text):
    """Print a fancy banner."""
    print("\n" + "=" * 60)
    print(f"✨ {text}")
    print("=" * 60)

def run_demo():
    print_banner("FFTE EXPO DEMO: Failure-First Testing Engine")
    
    print("\n🎯 Target: Vulnerable FastAPI Division Endpoint")
    print("   Endpoint: POST /divide")
    print("   Bug: Division by zero (no validation)")
    
    time.sleep(1)
    
    print_banner("Step 1: Normal Request (Should Work)")
    print("Testing: 10 ÷ 2 = ?")
    
    result = execute_request(
        method="POST",
        url="http://127.0.0.1:8000/divide",
        json={"a": 10, "b": 2}
    )
    
    print(f"✓ Response: {result.response_body}")
    print(f"✓ Status: {result.status_code}")
    
    time.sleep(1)
    
    print_banner("Step 2: FFTE Attack - Division by Zero")
    print("Testing: 10 ÷ 0 = ? (THIS SHOULD CRASH!)")
    
    result = execute_request(
        method="POST",
        url="http://127.0.0.1:8000/divide",
        json={"a": 10, "b": 0}
    )
    
    classification = classify(result)
    
    if classification.is_failure:
        print(f"\n💥 CRASH DETECTED!")
        print(f"   Failure Type: {classification.failure_type}")
        print(f"   Status Code: {result.status_code}")
        print(f"   Error: {result.exception or result.response_body}")
    else:
        print(f"\n⚠️  No failure detected (unexpected!)")
    
    time.sleep(1)
    
    print_banner("Step 3: FFTE Automates This")
    print("📊 FFTE would automatically test:")
    print("   1. Discover all API endpoints from OpenAPI")
    print("   2. Generate edge cases (0, null, max int, SQL injection, etc.)")
    print("   3. Execute tests with all edge cases")
    print("   4. Classify failures (crash, timeout, error, etc.)")
    print("   5. Generate reproducible bug reports")
    
    print("\n🔧 Try it yourself:")
    print("   curl -X POST 'http://127.0.0.1:8000/divide' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"a\": 10, \"b\": 0}'")
    
    print_banner("DEMO COMPLETE")
    print("🚀 FFTE finds bugs that vibe coding misses!")

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure victim API is running:")
        print("   uvicorn victim:app --reload")