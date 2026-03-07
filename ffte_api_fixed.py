#!/usr/bin/env python3
"""
FFTE API Service - FIXED v3 with correct test counting.
"""

import uuid
import json
import logging
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sqlalchemy import func, case

from db.config import create_db_and_tables, engine, get_session
from db.models import Scan, TestExecution

logger = logging.getLogger("ffte.api")

# ================ Data Models ================
class ScanRequest(BaseModel):
    spec_url: str | None = None  # URL to OpenAPI JSON
    target_url: str | None = None # Legacy alias
    base_url: str | None = None
    scan_name: str | None = "Unnamed Scan"
    max_cases_per_field: int = 3  # Keep for backwards compatibility
    fuzzing_intensity: int = 5  # 1-10 scale from frontend slider

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
    source: str = "memory"

class ScanResult(BaseModel):
    """Complete scan results."""
    scan_id: str
    status: str
    failures: List[Dict] = []  # List of dicts with method, url, type, payload
    report: Dict[str, List[str]]  # failure_type -> list of curl commands
    formatted_report: str
    statistics: Dict[str, int]
    ml_insights: Optional[Dict] = None  # avg probability, high/low risk counts


class ScanSummaryItem(BaseModel):
    """Summary of a single scan for list endpoint."""
    scan_id: str
    scan_name: str
    target_url: str
    status: str  # pending | running | completed | failed
    start_time: datetime
    end_time: Optional[datetime]
    tests_executed: int = 0
    failures_found: int = 0


class ScansListResponse(BaseModel):
    """Paginated list of scans with summary info."""
    total: int
    scans: List[ScanSummaryItem]
    warning: Optional[str] = None

# ================ Scan Manager ================
class ScanManager:
    """Manages all scans in the system."""
    
    def __init__(self):
        self.scans: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def create_scan(self, request: ScanRequest) -> str:
        """Create a new scan and return its ID."""
        url = request.spec_url or request.target_url
        if not url:
            raise ValueError("spec_url or target_url is required")
            
        scan_id = str(uuid.uuid4())
        
        scan_data = {
            "scan_id": scan_id,
            "request": {**request.model_dump(), "target_url": url, "spec_url": url},
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

# ================ Real Scanner (uses core.runner) ================
from core.runner import run as core_run

class FFTEScanner:
    """Runs FFTE scans using the actual core runner."""
    
    def __init__(self, scan_manager: ScanManager):
        self.scan_manager = scan_manager
    
    def run_scan(self, scan_id: str):
        """Run a scan in a background thread."""
        try:
            scan = self.scan_manager.get_scan(scan_id)
            if not scan:
                return
            
            request_data = scan["request"]
            spec_url = request_data.get("target_url") or request_data.get("spec_url")
            base_url = request_data.get("base_url")
            max_cases = request_data.get("max_cases_per_field", 3)
            fuzzing_intensity = request_data.get("fuzzing_intensity", 5)  # Default to 5 (medium)
            
            if not spec_url:
                raise ValueError("No spec_url or target_url provided")
            
            # Update status to running
            self.scan_manager.update_scan(scan_id, status="running", progress=10.0)
            
            # Run the actual FFTE core scanner
            print(f"🔍 Starting scan on: {spec_url}")
            print(f"   Base URL: {base_url or 'auto-detect'}")
            print(f"   Fuzzing intensity: {fuzzing_intensity}/10")
            
            # Use the actual core runner from core/runner.py
            report = core_run(
                spec_url=spec_url,
                base_url=base_url,
                timeout=10.0,
                limit_endpoints=None,
                scan_id=scan_id,
                fuzzing_intensity=fuzzing_intensity,
            )
            
            # Count statistics
            from reporting.report import format_report
            
            total_failures = sum(len(cmds) for cmds in report.values())
            formatted = format_report(report)
            
            # Convert report to failures list for UI
            failures_list = []
            for failure_type, curl_commands in report.items():
                for cmd in curl_commands:
                    # Parse curl command to extract method, url, payload
                    method = "POST" if "-X POST" in cmd else "GET"
                    url = ""
                    payload = "{}"
                    
                    # Extract URL (between quotes after curl)
                    import re
                    url_match = re.search(r'"(https?://[^"]+)"', cmd)
                    if url_match:
                        url = url_match.group(1)
                    
                    # Extract payload (after -d)
                    payload_match = re.search(r"-d '([^']+)'", cmd)
                    if payload_match:
                        payload = payload_match.group(1)
                    
                    failures_list.append({
                        "method": method,
                        "url": url,
                        "type": failure_type,
                        "payload": payload
                    })
            
            # ===== FIX: Calculate actual total tests executed =====
            from surface_discovery.openapi_parser import fetch_and_parse
            from input_generation.edge_cases import generate_edge_cases_flat, QUERY_PARAM_EDGE_CASES
            
            total_tests_executed = 0
            endpoint_count = 0
            
            try:
                endpoints, _, raw_spec = fetch_and_parse(spec_url)
                endpoint_count = len(endpoints)
            
                if fuzzing_intensity <= 3:
                    effective_max_cases = 3
                elif fuzzing_intensity <= 5:
                    effective_max_cases = 10
                elif fuzzing_intensity <= 7:
                    effective_max_cases = 30
                elif fuzzing_intensity <= 9:
                    effective_max_cases = 50
                else:
                    effective_max_cases = 100
            
                for endpoint in endpoints:
                    query_param_list = [
                        p for p in endpoint.parameters if p.location == "query"
                    ]
            
                    if query_param_list:
                        for qp in query_param_list:
                            total_tests_executed += min(
                                len(QUERY_PARAM_EDGE_CASES), effective_max_cases
                            )
            
                    if endpoint.request_body_schema:
                        edge_cases = generate_edge_cases_flat(
                            endpoint.request_body_schema, root_spec=raw_spec
                        )
                        for field, values in edge_cases.items():
                            total_tests_executed += min(len(values), effective_max_cases)
                    elif not query_param_list:
                        total_tests_executed += 1
                
                print(f"📊 Tests executed: {total_tests_executed}, Failures: {total_failures}")
                
            except Exception as e:
                logger.warning("Could not calculate exact test count: %s", e)
                total_tests_executed = max(total_failures * 3, total_failures + 20)
            
            # Update with results
            self.scan_manager.update_scan(
                scan_id,
                status="completed",
                progress=100.0,
                end_time=datetime.now(),
                tests_executed=total_tests_executed,
                failures_found=total_failures,
                results={
                    "report": report,
                    "failures": failures_list,
                    "formatted_report": formatted,
                    "statistics": {
                        "total_tests": total_tests_executed,
                        "failures": total_failures,
                        "endpoints": endpoint_count
                    }
                }
            )

            # Also persist completed status to the database when available
            try:
                with Session(engine) as db_session:
                    db_scan_id = uuid.UUID(scan_id)
                    db_scan = db_session.exec(
                        select(Scan).where(Scan.id == db_scan_id)
                    ).first()
                    if db_scan is not None:
                        db_scan.status = "completed"
                        db_scan.end_time = datetime.now()
                        db_session.add(db_scan)
                        db_session.commit()
            except Exception as exc:
                logger.error(
                    "Failed to mark scan %s as completed in database from API layer: %s",
                    scan_id,
                    exc,
                )
            
            print(f"✅ Scan completed: {total_failures} failures found out of {total_tests_executed} tests")
            
        except Exception as e:
            logger.exception("Scan %s failed with an unhandled exception: %s", scan_id, e)

            # Update in-memory scan state
            self.scan_manager.update_scan(
                scan_id,
                status="failed",
                error="An internal error occurred. Check server logs for details.",
                progress=100.0,
                end_time=datetime.now()
            )

            # Also persist failed status to the database when available
            try:
                with Session(engine) as db_session:
                    db_scan_id = uuid.UUID(scan_id)
                    db_scan = db_session.exec(
                        select(Scan).where(Scan.id == db_scan_id)
                    ).first()
                    if db_scan is not None:
                        db_scan.status = "failed"
                        db_scan.end_time = datetime.now()
                        db_session.add(db_scan)
                        db_session.commit()
            except Exception as exc:
                logger.error(
                    "Failed to mark scan %s as failed in database from API layer: %s",
                    scan_id,
                    exc,
                )

# ================ FastAPI App ================
app = FastAPI(
    title="FFTE API",
    description="Failure-First Testing Engine - REST API (FIXED v3.0)",
    version="3.0.0",
)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize database schema on service startup."""
    try:
        create_db_and_tables()
    except Exception as exc:
        # Do not crash the service if DB is unavailable; we can still run scans in-memory.
        logger.error(
            "Database initialization failed on startup; API will run without persistence: %s",
            exc,
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
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    session: Optional[Session] = Depends(get_session),
):
    # Ensure one of the URLs is present
    url = request.spec_url or request.target_url
    if not url:
        raise HTTPException(status_code=422, detail="spec_url or target_url required")
    
    scan_id = scan_manager.create_scan(request)
    
    # Get endpoint info for UI preview (non-blocking)
    try:
        from surface_discovery.openapi_parser import fetch_and_parse
        endpoints, _, _ = fetch_and_parse(url)
        endpoint_previews = [{"method": e.method.upper(), "path": e.path} for e in endpoints[:10]]
    except:
        endpoint_previews = []
        
    scan_manager.update_scan(scan_id, endpoints=endpoint_previews)
    
    # Persist scan in database (source of truth) when available
    if session is not None:
        try:
            db_scan = Scan(
                id=uuid.UUID(scan_id),
                scan_name=request.scan_name or "UNNAMED_ALPHA",
                target_url=url,
                status="pending",
                start_time=datetime.now(),
            )
            session.add(db_scan)
            session.commit()
            logger.info("Persisted scan %s to database.", scan_id)
        except Exception as exc:
            logger.error("Failed to persist scan %s to database: %s", scan_id, exc)
            try:
                session.rollback()
            except Exception:
                # Ignore rollback errors
                pass
    
    # Run scan in background
    background_tasks.add_task(scanner.run_scan, scan_id)
    
    return {"scan_id": scan_id, "status": "started"}

@app.get("/api/scan/{scan_id}", response_model=ScanStatus)
async def get_scan_status(
    scan_id: str,
    session: Optional[Session] = Depends(get_session),
):
    """
    Get status and progress of a scan.
    """
    # First try to load from database (source of truth)
    db_scan = None
    if session is not None:
        try:
            db_scan_id = uuid.UUID(scan_id)
            db_scan = session.exec(select(Scan).where(Scan.id == db_scan_id)).first()
            
            # If scan is in DB and already completed/failed, we return history from DB
            if db_scan and db_scan.status in ("completed", "failed"):
                counts_stmt = (
                    select(
                        func.count(TestExecution.id).label("tests_executed"),
                        func.sum(case((TestExecution.caused_failure == True, 1), else_=0)).label("failures_found"),
                    )
                    .where(TestExecution.scan_id == db_scan_id)
                )
                counts = session.exec(counts_stmt).first()
                tests_executed = counts[0] if counts and counts[0] is not None else 0
                failures_found = counts[1] if counts and counts[1] is not None else 0
                
                # Reconstruct endpoints list from test_executions
                endpoint_rows = session.exec(
                    select(TestExecution.endpoint, TestExecution.http_method)
                    .where(TestExecution.scan_id == db_scan_id)
                    .distinct()
                ).all()
                endpoint_list = [
                    {"method": (method or "GET").upper(), "path": endpoint}
                    for endpoint, method in endpoint_rows
                    if endpoint is not None
                ]
                
                return ScanStatus(
                    scan_id=scan_id,
                    status=db_scan.status,
                    progress=100.0,
                    start_time=db_scan.start_time,
                    end_time=db_scan.end_time,
                    target_url=db_scan.target_url,
                    scan_name=db_scan.scan_name or "Unnamed Scan",
                    tests_executed=tests_executed,
                    failures_found=failures_found,
                    endpoints=endpoint_list,
                    source="database"
                )
        except ValueError:
            db_scan = None
        except Exception as exc:
            logger.error("Failed to read scan %s from database: %s", scan_id, exc)
            db_scan = None

    # Always try to get in-memory scan as well for progress and stats
    scan = scan_manager.get_scan(scan_id)

    if not db_scan and not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    status = (scan["status"] if scan else db_scan.status) if db_scan else scan["status"]
    progress = scan["progress"] if scan else 0.0
    start_time = (
        db_scan.start_time
        if db_scan and db_scan.start_time
        else (scan["start_time"] if scan else datetime.now())
    )
    end_time = (
        db_scan.end_time
        if db_scan and db_scan.end_time
        else (scan.get("end_time") if scan else None)
    )
    target_url = (
        db_scan.target_url
        if db_scan
        else scan["request"]["target_url"]
    )
    scan_name = (
        db_scan.scan_name
        if db_scan
        else scan["request"].get("scan_name") or "UNNAMED_ALPHA"
    )

    return ScanStatus(
        scan_id=scan_id,
        status=status,
        progress=progress,
        start_time=start_time,
        end_time=end_time,
        target_url=target_url,
        scan_name=scan_name,
        tests_executed=scan.get("tests_executed", 0) if scan else 0,
        failures_found=scan.get("failures_found", 0) if scan else 0,
        endpoints=scan.get("endpoints", []) if scan else [],
        source="memory"
    )

@app.get("/api/scans", response_model=ScansListResponse)
async def list_scans(
    session: Optional[Session] = Depends(get_session),
    limit: int = Query(50, ge=1, le=200, description="Max scans to return"),
    offset: int = Query(0, ge=0, description="Number of scans to skip"),
):
    """
    List all previous scans with summary information, newest first.
    Supports pagination via limit and offset.
    """
    if session is None:
        logger.warning("GET /api/scans: database unavailable, returning empty list")
        return ScansListResponse(
            total=0,
            scans=[],
            warning="Database unavailable",
        )

    try:
        # Total count of scans
        total_stmt = select(func.count(Scan.id))
        total = session.exec(total_stmt).one() or 0

        # Scans ordered by start_time DESC with pagination
        scans_stmt = (
            select(Scan)
            .order_by(Scan.start_time.desc())
            .limit(limit)
            .offset(offset)
        )
        db_scans = list(session.exec(scans_stmt).all())

        if not db_scans:
            return ScansListResponse(total=total, scans=[])

        # Aggregate test_executions counts per scan (tests_executed, failures_found)
        scan_ids = [s.id for s in db_scans]
        counts_stmt = (
            select(
                TestExecution.scan_id,
                func.count(TestExecution.id).label("tests_executed"),
                func.sum(case((TestExecution.caused_failure == True, 1), else_=0)).label("failures_found"),
            )
            .where(TestExecution.scan_id.in_(scan_ids))
            .group_by(TestExecution.scan_id)
        )
        counts_rows = session.exec(counts_stmt).all()
        count_map: Dict[Any, tuple] = {}
        for row in counts_rows:
            count_map[row.scan_id] = (row.tests_executed or 0, row.failures_found or 0)

        # Enrich with in-memory status when available (running progress)
        summaries: List[ScanSummaryItem] = []
        for db_scan in db_scans:
            scan_id_str = str(db_scan.id)
            mem_scan = scan_manager.get_scan(scan_id_str)
            tests_executed, failures_found = count_map.get(db_scan.id, (0, 0))
            if mem_scan:
                tests_executed = mem_scan.get("tests_executed", tests_executed)
                failures_found = mem_scan.get("failures_found", failures_found)
            status = (mem_scan["status"] if mem_scan else db_scan.status) or "pending"
            summaries.append(
                ScanSummaryItem(
                    scan_id=scan_id_str,
                    scan_name=db_scan.scan_name or "Unnamed Scan",
                    target_url=db_scan.target_url,
                    status=status,
                    start_time=db_scan.start_time,
                    end_time=db_scan.end_time,
                    tests_executed=tests_executed,
                    failures_found=failures_found,
                )
            )

        return ScansListResponse(total=total, scans=summaries)

    except Exception as exc:
        logger.exception("GET /api/scans failed: %s", exc)
        return ScansListResponse(
            total=0,
            scans=[],
            warning="Failed to load scans from database",
        )

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
async def get_scan_results(
    scan_id: str,
    session: Optional[Session] = Depends(get_session),
):
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

    # --- Compute ml_insights from DB rows for this scan ---
    ml_insights: Optional[Dict] = None
    if session is not None:
        try:
            db_scan_id = uuid.UUID(scan_id)
            ml_rows = session.exec(
                select(TestExecution.ml_failure_probability)
                .where(TestExecution.scan_id == db_scan_id)
            ).all()
            scores = [s for s in ml_rows if s is not None]
            if scores:
                avg_prob = round(sum(scores) / len(scores), 4)
                high_risk = sum(1 for s in scores if s > 0.7)
                low_risk  = sum(1 for s in scores if s < 0.3)
                ml_insights = {
                    "avg_failure_probability": avg_prob,
                    "high_risk_count": high_risk,
                    "low_risk_count": low_risk,
                }
        except Exception as exc:
            logger.warning("Could not compute ml_insights for scan %s: %s", scan_id, exc)

    return ScanResult(
        scan_id=scan_id,
        status=scan["status"],
        failures=results.get("failures", []),
        report=results["report"],
        formatted_report=results["formatted_report"],
        statistics=results["statistics"],
        ml_insights=ml_insights,
    )

@app.get("/api/scan/{scan_id}/report")
async def get_scan_report(
    scan_id: str,
    session: Session = Depends(get_session)
):
    """
    Get the full detailed report for a specific scan directly from the database.
    """
    try:
        db_scan_id = uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scan_id format")

    # 1. Fetch scan from database by scan_id
    scan = session.exec(select(Scan).where(Scan.id == db_scan_id)).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    # 2. Fetch ALL test_executions for this scan
    try:
        executions = session.exec(
            select(TestExecution).where(TestExecution.scan_id == db_scan_id)
        ).all()
    except Exception as e:
        logger.error(f"Failed to fetch test executions for scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error while fetching test executions")

    # 3. Calculate duration
    start_dt = scan.start_time
    end_dt = scan.end_time or datetime.now()
    duration_seconds = int((end_dt - start_dt).total_seconds())

    # 4. Group failures by failure_type and Generating stats
    total_tests = len(executions)
    endpoints_tested = len(set(e.endpoint for e in executions if e.endpoint))
    
    failures = []
    failures_by_type = {}
    curl_commands = []

    for ex in executions:
        if ex.caused_failure and ex.failure_type:
            failure_type = ex.failure_type
            failures_by_type[failure_type] = failures_by_type.get(failure_type, 0) + 1
            
            failures.append({
                "endpoint": ex.endpoint,
                "http_method": ex.http_method,
                "field_name": ex.field_name,
                "field_type": ex.field_type,
                "edge_case_type": ex.edge_case_type,
                "edge_case_value": ex.edge_case_value,
                "failure_type": ex.failure_type,
                "status_code": ex.status_code,
                "response_time_ms": ex.response_time_ms,
                "ml_failure_probability": ex.ml_failure_probability,
                "timestamp": ex.timestamp.isoformat() if ex.timestamp else None
            })
            
            # 5. Generate curl commands for each failure
            url_base = scan.target_url.rstrip('/') if scan.target_url else ""
            endp = ex.endpoint if ex.endpoint else ""
            url = f"{url_base}{endp}"
            method = ex.http_method or "GET"
            cmd = f"curl -X {method} '{url}' -H 'Content-Type: application/json'"
            
            if ex.field_name is not None and ex.edge_case_value is not None:
                # Try to parse edge_case_value as JSON if possible, else string
                val = ex.edge_case_value
                try:
                    val = json.loads(ex.edge_case_value)
                except:
                    pass
                
                payload = json.dumps({ex.field_name: val})
                cmd += f" -d '{payload}'"
            
            curl_commands.append(cmd)

    total_failures = len(failures)
    failure_rate = round((total_failures / total_tests * 100), 1) if total_tests > 0 else 0.0

    # --- ml_insights ---
    scores = [
        ex.ml_failure_probability
        for ex in executions
        if ex.ml_failure_probability is not None
    ]
    if scores:
        ml_insights = {
            "avg_failure_probability": round(sum(scores) / len(scores), 4),
            "high_risk_count": sum(1 for s in scores if s > 0.7),
            "low_risk_count":  sum(1 for s in scores if s < 0.3),
        }
    else:
        ml_insights = None

    return {
        "scan_id": scan_id,
        "scan_name": scan.scan_name,
        "target_url": scan.target_url,
        "status": scan.status,
        "start_time": start_dt.isoformat(),
        "end_time": scan.end_time.isoformat() if scan.end_time else None,
        "duration_seconds": duration_seconds,
        "statistics": {
            "total_tests": total_tests,
            "total_failures": total_failures,
            "endpoints_tested": endpoints_tested,
            "failure_rate": failure_rate
        },
        "ml_insights": ml_insights,
        "failures_by_type": failures_by_type,
        "failures": failures,
        "curl_commands": curl_commands
    }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "ffte-api-fixed-v3",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "scans_count": len(scan_manager.list_scans())
    }

# ================ Run the API ================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FFTE API Server (FIXED v3.0)...")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🔗 Available endpoints:")
    print("   POST   /api/scan/start     - Start new scan")
    print("   GET    /api/scan/{id}      - Get scan status")
    print("   GET    /api/scans          - List all scans")
    print("   DELETE /api/scan/{id}      - Delete scan")
    print("   GET    /api/health         - Health check")
    uvicorn.run(app, host="0.0.0.0", port=8001)