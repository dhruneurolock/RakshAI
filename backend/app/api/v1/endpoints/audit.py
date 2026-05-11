"""
Audit API Endpoints
Immutable audit trail for compliance and governance.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.models import AuditLog
from app.models.schemas import AuditLogResponse
from app.services.audit_service import get_audit_service

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    category: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    since: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """
    List audit log entries with filtering.
    Audit logs are immutable — no update or delete endpoints exist.
    """
    svc = get_audit_service()

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid 'since' format. Use ISO 8601.")

    logs = svc.get_logs(
        db,
        category=category,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        since=since_dt,
        limit=limit,
        offset=skip,
    )
    return logs


@router.get("/{audit_id}", response_model=AuditLogResponse)
async def get_audit_log(audit_id: str, db: Session = Depends(get_db)):
    """Get a single audit log entry."""
    svc = get_audit_service()
    entry = svc.get_log_by_id(db, audit_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    return entry


@router.get("/{audit_id}/verify")
async def verify_audit_integrity(audit_id: str, db: Session = Depends(get_db)):
    """Verify that an audit record hasn't been tampered with."""
    svc = get_audit_service()
    entry = svc.get_log_by_id(db, audit_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    is_valid = svc.verify_integrity(db, audit_id)

    return {
        "audit_id": audit_id,
        "integrity_valid": is_valid,
        "record_hash": entry.record_hash,
        "message": "Record integrity verified" if is_valid else "WARNING: Record may have been tampered with!",
    }


@router.get("/scan/{scan_id}/trail", response_model=List[AuditLogResponse])
async def get_scan_audit_trail(scan_id: str, db: Session = Depends(get_db)):
    """Get the complete audit trail for a specific scan."""
    svc = get_audit_service()
    trail = svc.get_scan_audit_trail(db, scan_id)
    return trail


@router.get("/stats/summary")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get audit log statistics for the dashboard."""
    from datetime import timedelta
    from sqlalchemy import func

    since = datetime.utcnow() - timedelta(days=days)

    total = db.query(AuditLog).filter(AuditLog.occurred_at >= since).count()

    by_category = dict(
        db.query(AuditLog.category, func.count(AuditLog.id))
        .filter(AuditLog.occurred_at >= since)
        .group_by(AuditLog.category)
        .all()
    )

    by_action = dict(
        db.query(AuditLog.action, func.count(AuditLog.id))
        .filter(AuditLog.occurred_at >= since)
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
        .all()
    )

    failures = (
        db.query(AuditLog)
        .filter(AuditLog.occurred_at >= since, AuditLog.success == False)
        .count()
    )

    return {
        "period_days": days,
        "total_entries": total,
        "by_category": by_category,
        "top_actions": by_action,
        "failures": failures,
        "success_rate": round((total - failures) / total * 100, 1) if total > 0 else 100.0,
    }
