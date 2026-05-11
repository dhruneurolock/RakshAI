"""
Scans API Endpoints
Enterprise Architecture - Uses OrchestratorService for scan management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import json
from datetime import datetime
from collections import deque
from pathlib import Path

from app.core.database import get_db
from app.models.models import Scan, ScanStatus, Report, Vulnerability
from app.models.schemas import ScanCreate, ScanResponse, ScanUpdate, ReportResponse
from app.services.orchestrator import OrchestratorService
from app.services.report_generator import ReportGeneratorService

router = APIRouter()


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(scan_data: ScanCreate, db: Session = Depends(get_db)):
    """Create and start a new security scan"""
    try:
        import uuid as _uuid
        from datetime import datetime as _dt

        # Generate scan ID
        new_scan_id = str(_uuid.uuid4())

        # Create scan record in database
        scan = Scan(
            scan_id=new_scan_id,
            target_url=str(scan_data.target_url),
            scan_type=scan_data.scan_type or "full",
            status=ScanStatus.PENDING,
            progress_percentage=0,
            current_phase="initializing",
            created_at=_dt.utcnow(),
            total_findings=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            info_count=0,
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        # Launch enterprise orchestrator workflow (Phase 1-7 pipeline)
        orchestrator = OrchestratorService()
        policy = (scan_data.test_config or {})
        result = await orchestrator.start_scan(
            scan_id=new_scan_id,
            target_url=str(scan_data.target_url),
            scan_type=scan_data.scan_type or "full",
            user_id="local-user",
            policy=policy,
        )

        if not result.get("success"):
            scan.status = ScanStatus.FAILED
            scan.error_message = result.get("message", "Failed to start orchestrator")
            scan.completed_at = _dt.utcnow()
            db.commit()
            raise HTTPException(status_code=400, detail=scan.error_message)

        if result.get("status") == "QUEUED":
            scan.status = ScanStatus.PENDING
            scan.current_phase = "queued"
        else:
            scan.status = ScanStatus.RUNNING
            scan.current_phase = "phase_1_initialization"
            scan.started_at = _dt.utcnow()
        db.commit()
        db.refresh(scan)

        return scan

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db)
):
    """List all scans with optional filtering"""
    query = db.query(Scan)
    
    if status_filter:
        query = query.filter(Scan.status == status_filter)
    
    scans = query.order_by(Scan.created_at.desc()).offset(skip).limit(limit).all()
    return scans


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """Get scan details"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan


@router.patch("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: str,
    scan_update: ScanUpdate,
    db: Session = Depends(get_db)
):
    """Update scan status/progress"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Update fields
    if scan_update.status is not None:
        scan.status = scan_update.status
        if scan_update.status == ScanStatus.RUNNING and not scan.started_at:
            scan.started_at = datetime.utcnow()
        elif scan_update.status in [ScanStatus.COMPLETED, ScanStatus.FAILED]:
            scan.completed_at = datetime.utcnow()
    
    if scan_update.progress_percentage is not None:
        scan.progress_percentage = scan_update.progress_percentage
    
    if scan_update.current_phase is not None:
        scan.current_phase = scan_update.current_phase
    
    if scan_update.error_message is not None:
        scan.error_message = scan_update.error_message
    
    db.commit()
    db.refresh(scan)
    
    return scan


@router.post("/{scan_id}/start")
async def start_scan(scan_id: str, db: Session = Depends(get_db)):
    """Start/resume a scan (note: new scans auto-start via orchestrator)"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status == ScanStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Scan is already running")
    
    if scan.status == ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan already completed. Create a new scan instead.")
    
    # For failed/cancelled scans, restart via orchestrator
    try:
        orchestrator = OrchestratorService()
        result = await orchestrator.start_scan(
            scan_id=scan.scan_id,
            target_url=scan.target_url,
            scan_type=scan.scan_type or "full",
            user_id="local-user",
            policy=scan.test_config or {},
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to restart scan"))

        if result.get("status") == "QUEUED":
            scan.status = ScanStatus.PENDING
            scan.current_phase = "queued"
            scan.started_at = None
        else:
            scan.status = ScanStatus.RUNNING
            scan.current_phase = "phase_1_initialization"
            scan.started_at = datetime.utcnow()
        scan.completed_at = None
        scan.error_message = None
        db.commit()

        return {"message": "Scan restarted", "scan_id": scan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scan: {str(e)}")


@router.post("/{scan_id}/stop")
async def stop_scan(scan_id: str, db: Session = Depends(get_db)):
    """Stop a running scan"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status != ScanStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Scan is not running")
    
    scan.status = ScanStatus.CANCELLED
    scan.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Scan stopped", "scan_id": scan_id}


@router.get("/{scan_id}/endpoints")
async def get_scan_endpoints(scan_id: str, db: Session = Depends(get_db)):
    """Get all endpoints discovered in a scan"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    endpoints = scan.endpoints
    
    return [
        {
            "id": ep.id,
            "scan_id": scan.id,
            "url": ep.url,
            "method": ep.method,
            "endpoint_type": ep.endpoint_type,
            "parameters": ep.parameters,
            "headers": ep.headers if hasattr(ep, 'headers') else None,
            "discovery_method": ep.discovery_method,
            "requires_auth": ep.requires_auth if hasattr(ep, 'requires_auth') else False,
            "discovered_at": ep.discovered_at.isoformat() if ep.discovered_at else None
        }
        for ep in endpoints
    ]


@router.get("/{scan_id}/phase-summary")
async def get_scan_phase_summary(scan_id: str, db: Session = Depends(get_db)):
    """Get phase summary for a completed/running scan from strategy payload."""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    strategy = scan.strategy or {}
    phase_summary = strategy.get("phase_summary", {})

    return {
        "scan_id": scan.scan_id,
        "status": str(scan.status),
        "current_phase": scan.current_phase,
        "phase_summary": phase_summary,
        "started_at": scan.started_at.isoformat() if scan.started_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }


@router.get("/{scan_id}/logs")
async def get_scan_logs(
    scan_id: str,
    limit: int = Query(120, ge=20, le=1000),
    scan_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get recent backend log lines with optional scan-id filtering for live UI diagnostics."""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    candidate_log_paths = [
        Path("backend.log"),
        Path("./backend.log"),
        Path("logs/backend.log"),
        Path("../backend.log"),
    ]
    log_path = next((path for path in candidate_log_paths if path.exists() and path.is_file()), None)

    if log_path is None:
        return {
            "scan_id": scan_id,
            "status": str(scan.status),
            "current_phase": scan.current_phase,
            "source": "none",
            "lines": [],
            "line_count": 0,
            "note": "backend.log not found",
        }

    recent_lines = deque(maxlen=5000)
    with log_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            recent_lines.append(line.rstrip("\n"))

    lines = list(recent_lines)
    if scan_only:
        scan_markers = [scan_id, f"[{scan_id}]", f"scan {scan_id}"]
        lines = [line for line in lines if any(marker in line for marker in scan_markers)]

    lines = lines[-limit:]

    return {
        "scan_id": scan_id,
        "status": str(scan.status),
        "current_phase": scan.current_phase,
        "source": str(log_path),
        "lines": lines,
        "line_count": len(lines),
    }


@router.get("/{scan_id}/reports", response_model=List[ReportResponse])
async def get_scan_reports(scan_id: str, db: Session = Depends(get_db)):
    """Get reports generated specifically for a scan."""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    reports = (
        db.query(Report)
        .filter(Report.scan_id == scan.id)
        .order_by(Report.generated_at.desc())
        .all()
    )
    return reports


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, db: Session = Depends(get_db)):
    """Delete a scan and all related data"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    db.delete(scan)
    db.commit()
    
    return {"message": "Scan deleted", "scan_id": scan_id}


@router.post("/{scan_id}/generate-report")
async def generate_scan_report(
    scan_id: str,
    report_format: str = "pdf",
    db: Session = Depends(get_db)
):
    """Generate final report in PDF, Word, or Excel format"""
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Scan must be completed before generating report")
    
    # Validate report format
    if report_format not in ["pdf", "word", "excel", "all"]:
        raise HTTPException(status_code=400, detail="Invalid report format. Use 'pdf', 'word', 'excel', or 'all'")
    
    try:
        findings = (
            db.query(Vulnerability)
            .filter(
                Vulnerability.scan_id == scan.id,
                Vulnerability.is_false_positive == False,
            )
            .all()
        )

        findings_payload = []
        for vuln in findings:
            findings_payload.append({
                "title": vuln.title,
                "description": vuln.description,
                "severity": str(vuln.severity).split(".")[-1] if str(vuln.severity).startswith("VulnerabilitySeverity.") else str(vuln.severity),
                "type": vuln.vulnerability_type,
                "status": vuln.status,
                "owasp_category": vuln.owasp_category,
                "endpoint_url": vuln.endpoint.url if vuln.endpoint else scan.target_url,
                "confidence": vuln.confidence,
                "llm_explanation": vuln.llm_explanation,
                "llm_business_impact": vuln.llm_business_impact,
                "remediation": vuln.remediation,
            })

        scan_data = {
            "target_url": scan.target_url,
            "scan_type": scan.scan_type,
            "duration": (
                int((scan.completed_at - scan.started_at).total_seconds())
                if scan.started_at and scan.completed_at
                else None
            ),
        }

        # Generate report using report service
        report_service = ReportGeneratorService()
        await report_service.initialize()
        report_result = await report_service.generate_report(
            scan_id=scan_id,
            scan_data=scan_data,
            findings=findings_payload,
            format=report_format
        )

        raw_urls = report_result.get("report_urls", {}) if report_result.get("success") else {}
        report_urls = {k: v for k, v in raw_urls.items() if isinstance(v, str) and v.strip()}

        if not report_urls:
            summary_payload = {
                "scan_id": scan.scan_id,
                "target_url": scan.target_url,
                "scan_type": scan.scan_type,
                "generated_at": datetime.utcnow().isoformat(),
                "validated_findings": len(findings_payload),
                "severity_breakdown": {
                    "critical": sum(1 for f in findings_payload if str(f.get("severity", "")).upper() == "CRITICAL"),
                    "high": sum(1 for f in findings_payload if str(f.get("severity", "")).upper() == "HIGH"),
                    "medium": sum(1 for f in findings_payload if str(f.get("severity", "")).upper() == "MEDIUM"),
                    "low": sum(1 for f in findings_payload if str(f.get("severity", "")).upper() == "LOW"),
                    "info": sum(1 for f in findings_payload if str(f.get("severity", "")).upper() == "INFO"),
                },
                "findings": findings_payload,
                "fallback_reason": report_result.get("error", "No binary report output available"),
            }

            report_record = Report(
                scan_id=scan.id,
                report_id=str(uuid.uuid4()),
                report_type="json",
                file_path=None,
                content=json.dumps(summary_payload),
            )
            db.add(report_record)
            db.commit()

            return {
                "message": "Report generated successfully using JSON fallback",
                "scan_id": scan_id,
                "report_format": "json",
                "fallback_used": True,
                "report_url": "db:reports.content",
                "report_urls": {"json": "db:reports.content"},
            }
        
        type_map = {
            "pdf": "pdf",
            "word": "docx",
            "excel": "xlsx",
        }
        for key, location in report_urls.items():
            report_record = Report(
                scan_id=scan.id,
                report_id=str(uuid.uuid4()),
                report_type=type_map.get(key, key),
                file_path=location,
                content=None,
            )
            db.add(report_record)
        db.commit()

        primary_key = report_format if report_format in report_urls else next(iter(report_urls.keys()))

        return {
            "message": "Report generated successfully",
            "scan_id": scan_id,
            "report_format": report_format,
            "report_url": report_urls.get(primary_key),
            "report_urls": report_urls,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# Legacy endpoints (deprecated - orchestrator handles workflow automatically)
# These are kept for backwards compatibility but should not be used with new architecture

@router.post("/{scan_id}/execute")
async def execute_scan_detection(scan_id: str, db: Session = Depends(get_db)):
    """[DEPRECATED] Execute detection phase - orchestrator handles this automatically"""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. The orchestrator handles the complete workflow automatically."
    )


@router.post("/{scan_id}/validate")
async def validate_scan_findings(scan_id: str, db: Session = Depends(get_db)):
    """[DEPRECATED] Validate findings - orchestrator handles this automatically"""
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. The orchestrator handles validation automatically."
    )
