"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import scans, vulnerabilities, dashboard, reports, evidence, audit, governance, diagnostics

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["vulnerabilities"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(governance.router, prefix="/governance", tags=["governance"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
