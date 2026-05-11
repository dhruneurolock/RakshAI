"""
Evidence API Endpoints
Retrieve, inspect, and download evidence artifacts for findings.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import EvidenceRecord, Vulnerability
from app.models.schemas import EvidenceResponse, FindingLineageChain
from app.services.evidence_service import get_evidence_service
from app.services.audit_service import get_audit_service

router = APIRouter()


@router.get("/", response_model=List[EvidenceResponse])
async def list_evidence(
    scan_id: Optional[int] = None,
    vulnerability_id: Optional[int] = None,
    evidence_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List evidence records with filtering."""
    query = db.query(EvidenceRecord)

    if scan_id:
        query = query.filter(EvidenceRecord.scan_id == scan_id)
    if vulnerability_id:
        query = query.filter(EvidenceRecord.vulnerability_id == vulnerability_id)
    if evidence_type:
        query = query.filter(EvidenceRecord.evidence_type == evidence_type)

    records = (
        query.order_by(EvidenceRecord.captured_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return records


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """Get a single evidence record by ID. Logs access for audit."""
    svc = get_evidence_service()
    record = svc.get_evidence_by_id(db, evidence_id)

    if not record:
        raise HTTPException(status_code=404, detail="Evidence record not found")

    # Audit trail: log evidence access
    audit = get_audit_service()
    audit.log_evidence_accessed(db, evidence_id)

    return record


@router.get("/vulnerability/{vulnerability_id}/pair")
async def get_baseline_attack_pair(
    vulnerability_id: int,
    phase: str = Query("execution", description="Phase to retrieve pair for"),
    db: Session = Depends(get_db),
):
    """
    Get the baseline + attack evidence pair for side-by-side comparison.
    This is the core analyst workflow for reviewing a finding.
    """
    svc = get_evidence_service()
    pair = svc.get_baseline_and_attack_pair(db, vulnerability_id, phase)

    baseline = pair.get("baseline")
    attack = pair.get("attack")

    return {
        "vulnerability_id": vulnerability_id,
        "phase": phase,
        "baseline": EvidenceResponse.from_orm(baseline) if baseline else None,
        "attack": EvidenceResponse.from_orm(attack) if attack else None,
        "has_comparison": baseline is not None and attack is not None,
    }


@router.get("/vulnerability/{vulnerability_id}/chain")
async def get_finding_lineage_chain(
    vulnerability_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the full lineage chain for a finding:
    all stages, all evidence, and correlated findings.
    """
    svc = get_evidence_service()
    chain = svc.get_finding_lineage_chain(db, vulnerability_id)

    if not chain:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    # Serialize lineage/evidence objects
    from app.models.schemas import LineageEventResponse, EvidenceResponse

    return {
        "vulnerability_id": chain["vulnerability_id"],
        "title": chain["title"],
        "severity": chain["severity"],
        "lineage": [
            LineageEventResponse.from_orm(le) for le in chain.get("lineage", [])
        ],
        "evidence": [
            EvidenceResponse.from_orm(ev) for ev in chain.get("evidence", [])
        ],
        "related_findings": chain.get("related_findings", []),
        "correlation_group_id": chain.get("correlation_group_id"),
    }


@router.get("/scan/{scan_id}/summary")
async def get_scan_evidence_summary(
    scan_id: int,
    db: Session = Depends(get_db),
):
    """Get evidence statistics for a scan."""
    svc = get_evidence_service()
    all_evidence = svc.get_evidence_for_scan(db, scan_id)

    type_counts = {}
    for ev in all_evidence:
        t = ev.evidence_type or "unknown"
        type_counts[t] = type_counts.get(t, 0) + 1

    phase_counts = {}
    for ev in all_evidence:
        p = ev.phase or "unknown"
        phase_counts[p] = phase_counts.get(p, 0) + 1

    return {
        "scan_id": scan_id,
        "total_records": len(all_evidence),
        "by_type": type_counts,
        "by_phase": phase_counts,
    }
