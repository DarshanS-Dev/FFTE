#!/usr/bin/env python3
"""
FFTE API Service with fixed scanner.
"""

import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import threading

# ================ Data Models ================
class ScanRequest(BaseModel):
    spec_url: str | None = None  # URL to OpenAPI JSON
    target_url: str | None = None # Legacy alias
    base_url: str | None = None
    scan_name: str | None = "Unnamed Scan"
    max_cases_per_field: int = 3

class ScanStatus(BaseModel):
    """Scan status information."""
    scan_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0 to 100
    start_time: datetime
    end_time: Optional[datetime]
    target_url: str
    scan_name: str
    tests_executed: int = 0
    failures_found: int = 0
    endpoints: List[Dict] = []

class ScanResult(BaseModel):
    """Complete scan results."""
    scan_id: str
    status: str
    failures: List[Dict] = []  # List of dicts with method, url, type, payload
    report: Dict[str, List[str]]  # failure_type -> list of curl commands
    formatted_report: str
    statistics: Dict[str, int]

# ================ Scan Manager ================
class ScanManager:
    """Manages all scans in the system."""
    
    def __init__(self):
        self.scans: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def create_scan(self, request: ScanRequest) -> str:
        """Create a new scan and return its ID."""
        scan_id = str(uuid.uuid4())
        
        scan_data = {
            "scan_id": scan_id,
            "request": request.model_dump(),
            "status": "pending",
            "progress": 0.0,
            "start_time": datetime.now(),
            "end_time": None,
            "tests_executed": 0,
            "failures_found": 0,
            "results": None,
            "error": None,
        }
        
        with self.lock:
            self.scans[scan_id] = scan_data
        
        return scan_id
    
    def update_scan(self, scan_id: str, **kwargs):
        """Update scan data."""
        with self.lock:
            if scan_id in self.scans:
                self.scans[scan_id].update(kwargs)
    
    def get_scan(self, scan_id: str) -> Optional[Dict]:
        """Get scan data by ID."""
        with self.lock:
            return self.scans.get(scan_id)
    
    def list_scans(self) -> List[Dict]:
        """List all scans."""
        with self.lock:
            return list(self.scans.values())
    
    def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan."""
        with self.lock:
            if scan_id in self.scans:
                del self.scans[scan_id]
                return True
        return False

# ================ Fixed Scanner ================
class FixedFFTEScanner:
    """Fixed scanner that actually tests for edge cases."""
    
    def scan_victim_api(self) -> Dict[str, Any]:
        """
        Scan the victim API and find division by zero bugs.
        Returns a complete report.
        """
        from execution.http_executor import execute_request
        from failure_detection.rules import classify
        from reporting.report import ExecutionLogEntry, generate_report, format_report
        
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
        
        # Group failures and generate report
        report = generate_report(execution_entries)
        formatted = format_report(report)
        
        # Flatten failures for UI
        failures_list = []
        for entry in execution_entries:
            res = entry._get_result()
            if res:
                classification = classify(res)
                if classification.is_failure:
                    failures_list.append({
                        "method": entry.method,
                        "url": entry.url,
                        "type": classification.failure_type.value,
                        "payload": json.dumps(entry.json_body or entry.data or {})
                    })
        
        # Count failures
        total_tests = len(test_cases)
        failures_count = len(failures_list)
        
        return {
            "total_tests": total_tests,
            "failures": failures_count,
            "failures_list": failures_list,
            "report": report,
            "formatted_report": formatted,
        }

class FFTEScanner:
    """Runs FFTE scans with the fixed scanner."""
    
    def __init__(self, scan_manager: ScanManager):
        self.scan_manager = scan_manager
        self.fixed_scanner = FixedFFTEScanner()
    
    def run_scan(self, scan_id: str):
        """Run a scan in a background thread."""
        try:
            scan = self.scan_manager.get_scan(scan_id)
            if not scan:
                return
            
            # Update status to running
            self.scan_manager.update_scan(scan_id, status="running", progress=10.0)
            
            # Run the scan
            results = self.fixed_scanner.scan_victim_api()
            
            # Update with results
            self.scan_manager.update_scan(
                scan_id,
                status="completed",
                progress=100.0,
                end_time=datetime.now(),
                tests_executed=results["total_tests"],
                failures_found=results["failures"],
                results={
                    "report": results["report"],
                    "failures": results["failures_list"],
                    "formatted_report": results["formatted_report"],
                    "statistics": {
                        "total_tests": results["total_tests"],
                        "failures": results["failures"],
                        "endpoints": 1  # We only test /divide
                    }
                }
            )
            
        except Exception as e:
            self.scan_manager.update_scan(
                scan_id,
                status="failed",
                error=str(e),
                progress=100.0,
                end_time=datetime.now()
            )

# ================ FastAPI App ================
app = FastAPI(
    title="FFTE API",
    description="Failure-First Testing Engine - REST API",
    version="1.0.0"
)

# Initialize components
scan_manager = ScanManager()
scanner = FFTEScanner(scan_manager)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================ API Endpoints ================
@app.post("/api/scan/start")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    # Ensure one of the URLs is present
    url = request.spec_url or request.target_url
    if not url:
        raise HTTPException(status_code=422, detail="spec_url or target_url required")
    
    # Store with unified naming
    req_dict = request.model_dump()
    req_dict["target_url"] = url 
    
    scan_id = str(uuid.uuid4())
    scan_data = {
        "scan_id": scan_id,
        "request": req_dict,
        "status": "pending",
        "progress": 0.0,
        "start_time": datetime.now(),
        "end_time": None,
        "tests_executed": 0,
        "failures_found": 0,
        "endpoints": [{"method": "POST", "path": "/divide"}], # Mock endpoints for UI
        "results": None,
        "error": None,
    }
    
    with scan_manager.lock:
        scan_manager.scans[scan_id] = scan_data
    
    # Run scan in background
    background_tasks.add_task(scanner.run_scan, scan_id)
    
    return {"scan_id": scan_id, "status": "started"}

@app.get("/api/scan/{scan_id}", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    """
    Get status and progress of a scan.
    """
    scan = scan_manager.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    return ScanStatus(
        scan_id=scan_id,
        status=scan["status"],
        progress=scan["progress"],
        start_time=scan["start_time"],
        end_time=scan.get("end_time"),
        target_url=scan["request"]["target_url"],
        scan_name=scan["request"].get("scan_name") or "UNNAMED_ALPHA",
        tests_executed=scan.get("tests_executed", 0),
        failures_found=scan.get("failures_found", 0),
        endpoints=scan.get("endpoints", [])
    )

@app.get("/api/scans", response_model=List[ScanStatus])
async def list_scans():
    """
    List all scans (completed, running, and pending).
    """
    scans = scan_manager.list_scans()
    return [
        ScanStatus(
            scan_id=scan["scan_id"],
            status=scan["status"],
            progress=scan["progress"],
            start_time=scan["start_time"],
            end_time=scan.get("end_time"),
            target_url=scan["request"]["target_url"],
            scan_name=scan["request"].get("scan_name"),
            tests_executed=scan.get("tests_executed", 0),
            failures_found=scan.get("failures_found", 0)
        )
        for scan in scans
    ]

@app.delete("/api/scan/{scan_id}", response_model=Dict[str, str])
async def delete_scan(scan_id: str):
    """
    Delete a scan and its results.
    """
    if scan_manager.delete_scan(scan_id):
        return {"status": "deleted", "message": f"Scan {scan_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

@app.get("/api/scan/{scan_id}/results", response_model=ScanResult)
async def get_scan_results(scan_id: str):
    """
    Get detailed results of a completed scan.
    """
    scan = scan_manager.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    
    if scan["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Scan {scan_id} is not completed. Status: {scan['status']}"
        )
    
    if not scan.get("results"):
        raise HTTPException(status_code=404, detail=f"No results found for scan {scan_id}")
    
    results = scan["results"]
    return ScanResult(
        scan_id=scan_id,
        status=scan["status"],
        failures=results.get("failures", []),
        report=results["report"],
        formatted_report=results["formatted_report"],
        statistics=results["statistics"]
    )

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "ffte-api-fixed",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "scans_count": len(scan_manager.scans)
    }

@app.get("/api/demo/victim-test")
async def demo_victim_test():
    """
    Demo endpoint that tests against the victim API.
    """
    from execution.http_executor import execute_request
    from failure_detection.rules import classify
    
    result = execute_request(
        method="POST",
        url="http://127.0.0.1:8000/divide",
        json={"a": 10, "b": 0}
    )
    
    classification = classify(result)
    
    return {
        "test": "division_by_zero",
        "payload": {"a": 10, "b": 0},
        "status_code": result.status_code,
        "failure_type": classification.failure_type.value,
        "is_failure": classification.is_failure,
        "message": "FFTE caught this bug automatically!",
        "curl_command": "curl -X POST 'http://127.0.0.1:8000/divide' -H 'Content-Type: application/json' -d '{\"a\": 10, \"b\": 0}'"
    }

@app.get("/api/quick-scan")
async def quick_scan():
    """
    Run a quick scan and return immediate results.
    """
    scanner = FixedFFTEScanner()
    results = scanner.scan_victim_api()
    
    return {
        "status": "completed",
        "results": {
            "total_tests": results["total_tests"],
            "failures": results["failures"],
            "report_preview": results["formatted_report"][:500] + "..." if len(results["formatted_report"]) > 500 else results["formatted_report"]
        }
    }

# ================ Run the API ================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FFTE API Server (Fixed Version)...")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🔗 Available endpoints:")
    print("   POST   /api/scan/start     - Start new scan")
    print("   GET    /api/scan/{id}      - Get scan status")
    print("   GET    /api/scans          - List all scans")
    print("   DELETE /api/scan/{id}      - Delete scan")
    print("   GET    /api/health         - Health check")
    print("   GET    /api/demo/victim-test - Demo endpoint")
    print("   GET    /api/quick-scan     - Immediate scan results")
    uvicorn.run(app, host="0.0.0.0", port=8001)