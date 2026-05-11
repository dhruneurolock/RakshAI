"""
Evidence Service
Manages first-class evidence artifacts (request/response pairs, screenshots, HAR files).
Reuses the existing StorageService for persistence — no parallel storage system.
"""

import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import EvidenceRecord, Vulnerability, LineageEvent
from app.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


class EvidenceService:
    """
    Create, store, and retrieve evidence artifacts.
    Every test attempt (success or failure) should produce an evidence record
    so analysts have a complete audit trail.
    """

    async def capture_request_response(
        self,
        db: Session,
        scan_id: int,
        vulnerability_id: Optional[int],
        endpoint_id: Optional[int],
        *,
        http_method: str,
        request_url: str,
        request_headers: Optional[Dict[str, Any]] = None,
        request_body: Optional[str] = None,
        response_status_code: Optional[int] = None,
        response_headers: Optional[Dict[str, Any]] = None,
        response_body: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        tool_name: Optional[str] = None,
        tool_version: Optional[str] = None,
        payload_id: Optional[str] = None,
        payload_value: Optional[str] = None,
        phase: str = "execution",
        is_baseline: bool = False,
        initiated_by: Optional[str] = None,
    ) -> EvidenceRecord:
        """Capture a full HTTP request/response pair as an evidence record."""
        evidence_id = f"ev-{uuid.uuid4().hex[:16]}"

        record = EvidenceRecord(
            evidence_id=evidence_id,
            scan_id=scan_id,
            vulnerability_id=vulnerability_id,
            endpoint_id=endpoint_id,
            evidence_type="request_response",
            http_method=http_method,
            request_url=request_url,
            request_headers=request_headers,
            request_body=request_body,
            response_status_code=response_status_code,
            response_headers=response_headers,
            response_body=self._truncate(response_body, max_len=50000),
            response_time_ms=response_time_ms,
            tool_name=tool_name,
            tool_version=tool_version,
            payload_id=payload_id,
            payload_value=payload_value,
            phase=phase,
            is_baseline=is_baseline,
            initiated_by=initiated_by,
        )

        db.add(record)
        db.flush()

        # Optionally persist full response body to storage if it's large
        if response_body and len(response_body) > 50000:
            try:
                storage = await get_storage_service()
                uri = await storage.upload_raw_output(
                    str(scan_id),
                    f"evidence/{evidence_id}_response",
                    response_body.encode("utf-8", errors="replace"),
                )
                record.storage_uri = uri
            except Exception as e:
                logger.warning(f"Failed to persist large response body: {e}")

        db.commit()
        db.refresh(record)
        logger.info(f"Captured evidence {evidence_id} for scan {scan_id}, phase={phase}")
        return record

    async def capture_screenshot(
        self,
        db: Session,
        scan_id: int,
        vulnerability_id: int,
        screenshot_data: bytes,
        *,
        phase: str = "poc_generation",
        initiated_by: Optional[str] = None,
    ) -> EvidenceRecord:
        """Capture a screenshot artifact."""
        evidence_id = f"ev-{uuid.uuid4().hex[:16]}"

        storage = await get_storage_service()
        uri = await storage.upload_screenshot(
            str(scan_id), evidence_id, screenshot_data
        )

        record = EvidenceRecord(
            evidence_id=evidence_id,
            scan_id=scan_id,
            vulnerability_id=vulnerability_id,
            evidence_type="screenshot",
            screenshot_uri=uri,
            phase=phase,
            initiated_by=initiated_by,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    async def capture_har(
        self,
        db: Session,
        scan_id: int,
        vulnerability_id: Optional[int],
        har_data: Dict[str, Any],
        *,
        phase: str = "execution",
        initiated_by: Optional[str] = None,
    ) -> EvidenceRecord:
        """Capture a HAR file artifact."""
        evidence_id = f"ev-{uuid.uuid4().hex[:16]}"

        storage = await get_storage_service()
        uri = await storage.upload_http_trace(
            str(scan_id), evidence_id, har_data
        )

        record = EvidenceRecord(
            evidence_id=evidence_id,
            scan_id=scan_id,
            vulnerability_id=vulnerability_id,
            evidence_type="har",
            har_uri=uri,
            phase=phase,
            initiated_by=initiated_by,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def get_evidence_for_vulnerability(
        self, db: Session, vulnerability_id: int
    ) -> List[EvidenceRecord]:
        """Get all evidence records for a vulnerability."""
        return (
            db.query(EvidenceRecord)
            .filter(EvidenceRecord.vulnerability_id == vulnerability_id)
            .order_by(EvidenceRecord.captured_at.asc())
            .all()
        )

    def get_evidence_for_scan(
        self, db: Session, scan_id: int, evidence_type: Optional[str] = None
    ) -> List[EvidenceRecord]:
        """Get all evidence records for a scan, optionally filtered by type."""
        query = db.query(EvidenceRecord).filter(EvidenceRecord.scan_id == scan_id)
        if evidence_type:
            query = query.filter(EvidenceRecord.evidence_type == evidence_type)
        return query.order_by(EvidenceRecord.captured_at.asc()).all()

    def get_evidence_by_id(
        self, db: Session, evidence_id: str
    ) -> Optional[EvidenceRecord]:
        """Get a single evidence record by its evidence_id."""
        return (
            db.query(EvidenceRecord)
            .filter(EvidenceRecord.evidence_id == evidence_id)
            .first()
        )

    def get_baseline_and_attack_pair(
        self, db: Session, vulnerability_id: int, phase: str = "execution"
    ) -> Dict[str, Optional[EvidenceRecord]]:
        """Get baseline + attack evidence pair for side-by-side comparison."""
        records = (
            db.query(EvidenceRecord)
            .filter(
                EvidenceRecord.vulnerability_id == vulnerability_id,
                EvidenceRecord.phase == phase,
                EvidenceRecord.evidence_type == "request_response",
            )
            .order_by(EvidenceRecord.captured_at.asc())
            .all()
        )
        baseline = next((r for r in records if r.is_baseline), None)
        attack = next((r for r in records if not r.is_baseline), None)
        return {"baseline": baseline, "attack": attack}

    def get_finding_lineage_chain(
        self, db: Session, vulnerability_id: int
    ) -> Dict[str, Any]:
        """
        Build a complete lineage chain for a finding:
        all lineage events + all evidence records + correlated findings.
        """
        vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
        if not vuln:
            return {}

        lineage = (
            db.query(LineageEvent)
            .filter(LineageEvent.vulnerability_id == vulnerability_id)
            .order_by(LineageEvent.occurred_at.asc())
            .all()
        )

        evidence = self.get_evidence_for_vulnerability(db, vulnerability_id)

        # Find correlated findings
        from app.models.models import CorrelationGroup
        groups = (
            db.query(CorrelationGroup)
            .filter(
                CorrelationGroup.scan_id == vuln.scan_id,
            )
            .all()
        )
        related_ids = []
        correlation_id = None
        for group in groups:
            members = group.member_vulnerability_ids or []
            if vulnerability_id in members:
                related_ids = [m for m in members if m != vulnerability_id]
                correlation_id = group.correlation_id
                break

        return {
            "vulnerability_id": vulnerability_id,
            "title": vuln.title,
            "severity": str(vuln.severity.value) if vuln.severity else "unknown",
            "lineage": lineage,
            "evidence": evidence,
            "related_findings": related_ids,
            "correlation_group_id": correlation_id,
        }

    @staticmethod
    def _truncate(text: Optional[str], max_len: int = 50000) -> Optional[str]:
        if text and len(text) > max_len:
            return text[:max_len] + f"\n... [truncated, total {len(text)} chars]"
        return text


# Singleton accessor
_evidence_service = None


def get_evidence_service() -> EvidenceService:
    global _evidence_service
    if _evidence_service is None:
        _evidence_service = EvidenceService()
    return _evidence_service
