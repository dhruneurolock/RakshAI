"""
Audit Service
Immutable audit trail for all security-relevant actions.
Covers scans, findings, evidence access, report generation, and policy changes.
"""

import logging
import uuid
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """
    Records every security-relevant action with immutable hashing for tamper
    detection. Supports compliance with SOC2, ISO 27001, and 21 CFR Part 11.
    """

    def log(
        self,
        db: Session,
        *,
        action: str,
        category: str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        policy_id: Optional[str] = None,
        scope_context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an immutable audit log entry.
        The record_hash field makes tampering detectable.
        """
        audit_id = f"aud-{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()

        entry = AuditLog(
            audit_id=audit_id,
            action=action,
            category=category,
            user_id=user_id or "system",
            user_role=user_role,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            previous_state=previous_state,
            new_state=new_state,
            policy_id=policy_id,
            scope_context=scope_context,
            success=success,
            error_message=error_message,
            occurred_at=now,
        )

        # Compute tamper-detection hash
        entry.record_hash = self._compute_hash(
            audit_id=audit_id,
            action=action,
            category=category,
            user_id=user_id or "system",
            resource_type=resource_type,
            resource_id=resource_id,
            timestamp=now.isoformat(),
            details=details,
        )

        db.add(entry)
        db.commit()

        logger.info(
            f"Audit: [{category}] {action} by {user_id or 'system'} "
            f"on {resource_type}:{resource_id} — {'OK' if success else 'FAIL'}"
        )
        return entry

    def get_logs(
        self,
        db: Session,
        *,
        category: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Query audit logs with optional filters."""
        query = db.query(AuditLog)

        if category:
            query = query.filter(AuditLog.category == category)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if since:
            query = query.filter(AuditLog.occurred_at >= since)

        return (
            query.order_by(AuditLog.occurred_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_log_by_id(
        self, db: Session, audit_id: str
    ) -> Optional[AuditLog]:
        """Get a single audit entry."""
        return (
            db.query(AuditLog)
            .filter(AuditLog.audit_id == audit_id)
            .first()
        )

    def verify_integrity(self, db: Session, audit_id: str) -> bool:
        """Verify an audit record hasn't been tampered with."""
        entry = self.get_log_by_id(db, audit_id)
        if not entry:
            return False

        expected_hash = self._compute_hash(
            audit_id=entry.audit_id,
            action=entry.action,
            category=entry.category,
            user_id=entry.user_id,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            timestamp=entry.occurred_at.isoformat() if entry.occurred_at else "",
            details=entry.details,
        )
        return entry.record_hash == expected_hash

    def get_scan_audit_trail(
        self, db: Session, scan_id: str
    ) -> List[AuditLog]:
        """Get complete audit trail for a scan."""
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "scan",
                AuditLog.resource_id == scan_id,
            )
            .order_by(AuditLog.occurred_at.asc())
            .all()
        )

    # ── Convenience methods for common audit events ──────

    def log_scan_created(
        self, db: Session, scan_id: str, target_url: str,
        user_id: str = "system", policy_id: Optional[str] = None
    ) -> AuditLog:
        return self.log(
            db,
            action="scan_created",
            category="scan",
            user_id=user_id,
            resource_type="scan",
            resource_id=scan_id,
            details={"target_url": target_url},
            policy_id=policy_id,
        )

    def log_finding_validated(
        self, db: Session, scan_id: str, vuln_id: int,
        status: str, confidence: float, user_id: str = "system"
    ) -> AuditLog:
        return self.log(
            db,
            action="finding_validated",
            category="finding",
            user_id=user_id,
            resource_type="vulnerability",
            resource_id=str(vuln_id),
            details={
                "scan_id": scan_id,
                "validation_status": status,
                "confidence": confidence,
            },
        )

    def log_evidence_accessed(
        self, db: Session, evidence_id: str,
        user_id: str = "system", ip_address: Optional[str] = None
    ) -> AuditLog:
        return self.log(
            db,
            action="evidence_accessed",
            category="evidence",
            user_id=user_id,
            ip_address=ip_address,
            resource_type="evidence",
            resource_id=evidence_id,
        )

    def log_report_generated(
        self, db: Session, scan_id: str, report_format: str,
        user_id: str = "system"
    ) -> AuditLog:
        return self.log(
            db,
            action="report_generated",
            category="report",
            user_id=user_id,
            resource_type="scan",
            resource_id=scan_id,
            details={"format": report_format},
        )

    def log_policy_changed(
        self, db: Session, policy_id: str,
        previous_state: Dict[str, Any], new_state: Dict[str, Any],
        user_id: str = "system"
    ) -> AuditLog:
        return self.log(
            db,
            action="policy_changed",
            category="governance",
            user_id=user_id,
            resource_type="policy",
            resource_id=policy_id,
            previous_state=previous_state,
            new_state=new_state,
        )

    @staticmethod
    def _compute_hash(**fields) -> str:
        """Compute SHA-256 hash for tamper detection."""
        canonical = json.dumps(fields, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Singleton accessor
_audit_service = None


def get_audit_service() -> AuditService:
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
