"""
Dashboard API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import requests

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Scan, Vulnerability, ScanStatus, VulnerabilitySeverity
from app.models.schemas import DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    # Total scans
    total_scans = db.query(Scan).count()
    
    # Active scans
    active_scans = db.query(Scan).filter(
        Scan.status == ScanStatus.RUNNING
    ).count()
    
    # Completed scans
    completed_scans = db.query(Scan).filter(
        Scan.status == ScanStatus.COMPLETED
    ).count()
    
    # Total vulnerabilities (excluding false positives)
    total_vulns = db.query(Vulnerability).filter(
        Vulnerability.is_false_positive == False
    ).count()
    
    # Critical vulnerabilities
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.CRITICAL,
        Vulnerability.is_false_positive == False
    ).count()
    
    # High vulnerabilities
    high_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.HIGH,
        Vulnerability.is_false_positive == False
    ).count()
    
    # Medium vulnerabilities
    medium_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.MEDIUM,
        Vulnerability.is_false_positive == False
    ).count()
    
    # Low vulnerabilities
    low_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == VulnerabilitySeverity.LOW,
        Vulnerability.is_false_positive == False
    ).count()
    
    # Recent scans (last 5)
    recent_scans = db.query(Scan).order_by(
        Scan.created_at.desc()
    ).limit(5).all()
    
    return {
        "total_scans": total_scans,
        "active_scans": active_scans,
        "completed_scans": completed_scans,
        "total_vulnerabilities": total_vulns,
        "critical_vulnerabilities": critical_vulns,
        "high_vulnerabilities": high_vulns,
        "medium_vulnerabilities": medium_vulns,
        "low_vulnerabilities": low_vulns,
        "recent_scans": recent_scans
    }


@router.get("/activity")
async def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent activity feed"""
    # Recent scans
    recent_scans = db.query(Scan).order_by(
        Scan.created_at.desc()
    ).limit(limit).all()
    
    # Recent vulnerabilities
    recent_vulns = db.query(Vulnerability).filter(
        Vulnerability.is_false_positive == False
    ).order_by(
        Vulnerability.detected_at.desc()
    ).limit(limit).all()
    
    activity = []
    
    for scan in recent_scans:
        activity.append({
            "type": "scan",
            "timestamp": scan.created_at,
            "data": {
                "scan_id": scan.scan_id,
                "target_url": scan.target_url,
                "status": scan.status.value
            }
        })
    
    for vuln in recent_vulns:
        activity.append({
            "type": "vulnerability",
            "timestamp": vuln.detected_at,
            "data": {
                "title": vuln.title,
                "severity": vuln.severity.value,
                "scan_id": vuln.scan.scan_id if vuln.scan else None
            }
        })
    
    # Sort by timestamp
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activity[:limit]


@router.get("/trends")
async def get_trends(days: int = 30, db: Session = Depends(get_db)):
    """Get vulnerability trends over time"""
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get vulnerabilities grouped by date
    vulns = db.query(
        func.date(Vulnerability.detected_at).label('date'),
        Vulnerability.severity,
        func.count(Vulnerability.id).label('count')
    ).filter(
        Vulnerability.detected_at >= start_date,
        Vulnerability.is_false_positive == False
    ).group_by(
        func.date(Vulnerability.detected_at),
        Vulnerability.severity
    ).all()
    
    # Format data for charting
    trends = {}
    for date, severity, count in vulns:
        date_str = str(date)
        if date_str not in trends:
            trends[date_str] = {
                "date": date_str,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }
        
        severity_key = severity.value.lower()
        trends[date_str][severity_key] = count
    
    return list(trends.values())


@router.get("/system-status")
async def get_system_status():
    """Get runtime system status for UI monitoring (LLM, Redis, Neo4j, MinIO flags + LLM health)."""
    llm_status = {
        "enabled": settings.OLLAMA_ENABLED,
        "healthy": False,
        "base_url": settings.OLLAMA_BASE_URL,
        "model": settings.OLLAMA_MODEL,
        "model_loaded": False,
        "error": None,
    }

    if settings.OLLAMA_ENABLED:
        try:
            response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=4)
            response.raise_for_status()
            body = response.json() if response.content else {}
            models = body.get("models", [])
            llm_status["healthy"] = True
            llm_status["model_loaded"] = any(
                (m.get("name") or "").split(":")[0] == settings.OLLAMA_MODEL.split(":")[0]
                for m in models
            )
        except Exception as error:
            llm_status["error"] = str(error)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "llm": llm_status,
        "services": {
            "redis_enabled": settings.REDIS_ENABLED,
            "neo4j_enabled": settings.NEO4J_ENABLED,
            "minio_enabled": settings.MINIO_ENABLED,
        },
    }
