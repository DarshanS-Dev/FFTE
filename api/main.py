from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import ScanRequest, ScanResponse
from core.runner import run

app = FastAPI(title="FFTE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest) -> ScanResponse:
    report = run(
        req.spec_url,
        req.base_url,
        timeout=req.timeout,
        limit_endpoints=req.limit_endpoints,
    )
    return ScanResponse(report=report)
