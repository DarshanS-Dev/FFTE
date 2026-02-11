#!/usr/bin/env python3
"""
Test client for FFTE API.
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_all_endpoints():
    """Test all API endpoints."""
    
    print("=" * 60)
    print("🧪 Testing FFTE API Endpoints")
    print("=" * 60)
    
    # 1. Health check
    print("\n1️⃣ Testing /api/health")
    response = requests.get(f"{API_BASE}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # 2. Start a scan
    print("\n2️⃣ Testing /api/scan/start")
    scan_data = {
        "target_url": "http://127.0.0.1:8000/openapi.json",
        "scan_name": "Demo Scan - Victim API",
        "max_cases_per_field": 2
    }
    response = requests.post(f"{API_BASE}/api/scan/start", json=scan_data)
    print(f"   Status: {response.status_code}")
    scan_result = response.json()
    print(f"   Response: {scan_result}")
    
    if "scan_id" in scan_result:
        scan_id = scan_result["scan_id"]
        
        # 3. Check scan status
        print(f"\n3️⃣ Testing /api/scan/{scan_id}")
        for i in range(10):  # Wait up to 10 seconds
            response = requests.get(f"{API_BASE}/api/scan/{scan_id}")
            status = response.json()
            print(f"   Check {i+1}: {status['status']} - Progress: {status['progress']}%")
            
            if status["status"] == "completed":
                print(f"   ✅ Scan completed!")
                break
            elif status["status"] == "failed":
                print(f"   ❌ Scan failed!")
                break
            
            time.sleep(1)  # Wait 1 second between checks
        
        # 4. Get scan results
        print(f"\n4️⃣ Testing /api/scan/{scan_id}/results")
        response = requests.get(f"{API_BASE}/api/scan/{scan_id}/results")
        if response.status_code == 200:
            results = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Failures found: {results['statistics']['failures']}")
            print(f"   Report preview: {results['formatted_report'][:200]}...")
        else:
            print(f"   Results not ready yet: {response.status_code}")
    
    # 5. List all scans
    print("\n5️⃣ Testing /api/scans")
    response = requests.get(f"{API_BASE}/api/scans")
    scans = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Total scans: {len(scans)}")
    
    # 6. Demo endpoint
    print("\n6️⃣ Testing /api/demo/victim-test")
    response = requests.get(f"{API_BASE}/api/demo/victim-test")
    print(f"   Status: {response.status_code}")
    demo_result = response.json()
    print(f"   Test: {demo_result['test']}")
    print(f"   Failure detected: {demo_result['is_failure']}")
    
    print("\n" + "=" * 60)
    print("✅ API Test Complete!")
    print("=" * 60)

def quick_demo():
    """Quick demo for expo presentation."""
    
    print("🎤 EXPO DEMO: FFTE REST API")
    print("=" * 60)
    
    # Show API is running
    print("\n1️⃣ Checking API health...")
    health = requests.get(f"{API_BASE}/api/health").json()
    print(f"   Status: {health['status']}")
    print(f"   Active scans: {health['scans_count']}")
    
    # Start a scan
    print("\n2️⃣ Starting FFTE scan on vulnerable API...")
    scan_request = {
        "target_url": "http://127.0.0.1:8000/openapi.json",
        "scan_name": "EXPO DEMO - Division Bug Hunt",
        "max_cases_per_field": 1
    }
    
    response = requests.post(f"{API_BASE}/api/scan/start", json=scan_request)
    scan_id = response.json()["scan_id"]
    print(f"   Scan ID: {scan_id}")
    print(f"   Target: {scan_request['target_url']}")
    
    # Show real-time progress
    print("\n3️⃣ Monitoring scan progress...")
    for i in range(8):
        status = requests.get(f"{API_BASE}/api/scan/{scan_id}").json()
        print(f"   Progress: {status['progress']:.1f}% | Status: {status['status']}")
        
        if status["status"] == "completed":
            print(f"   ✅ Scan completed in {i+1} seconds!")
            print(f"   🔍 Found {status['failures_found']} failures")
            break
        elif status["status"] == "failed":
            print(f"   ❌ Scan failed")
            break
            
        time.sleep(1)
    
    # Show results
    print("\n4️⃣ Getting results...")
    results = requests.get(f"{API_BASE}/api/scan/{scan_id}/results")
    if results.status_code == 200:
        data = results.json()
        print(f"   📊 Statistics:")
        print(f"      - Endpoints tested: {data['statistics']['endpoints']}")
        print(f"      - Tests executed: {data['statistics']['tests']}")
        print(f"      - Failures found: {data['statistics']['failures']}")
        
        # Show one example failure
        if data['statistics']['failures'] > 0:
            print(f"\n   💥 Example failure found:")
            report_lines = data['formatted_report'].split('\n')
            for line in report_lines[:6]:  # Show first 6 lines
                print(f"      {line}")
    
    print("\n" + "=" * 60)
    print("🚀 FFTE API Demo Complete!")
    print("💡 Try it yourself with curl:")
    print(f'   curl -X POST "{API_BASE}/api/scan/start" \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"target_url": "http://127.0.0.1:8000/openapi.json"}\'')
    print("=" * 60)

if __name__ == "__main__":
    try:
        quick_demo()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure FFTE API is running:")
        print("   python ffte_api.py")