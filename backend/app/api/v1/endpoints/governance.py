"""
Governance API Endpoints
Scan policies, scope enforcement, RBAC, and compliance mappings.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import ScanPolicy, CorrelationGroup
from app.models.schemas import (
    ScanPolicyCreate,
    ScanPolicyResponse,
    CorrelationGroupResponse,
)
from app.services.correlation_service import get_correlation_service
from app.services.audit_service import get_audit_service

router = APIRouter()


# ── Scan Policies ────────────────────────────────────────

@router.get("/policies", response_model=List[ScanPolicyResponse])
async def list_policies(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List all scan policies."""
    query = db.query(ScanPolicy)
    if active_only:
        query = query.filter(ScanPolicy.is_active == True)
    return query.order_by(ScanPolicy.created_at.desc()).all()


@router.post("/policies", response_model=ScanPolicyResponse, status_code=201)
async def create_policy(
    policy_data: ScanPolicyCreate,
    db: Session = Depends(get_db),
):
    """Create a new scan policy."""
    policy = ScanPolicy(
        policy_id=f"pol-{uuid.uuid4().hex[:12]}",
        name=policy_data.name,
        description=policy_data.description,
        allowed_targets=policy_data.allowed_targets,
        excluded_paths=policy_data.excluded_paths,
        allowed_methods=policy_data.allowed_methods,
        allowed_test_families=policy_data.allowed_test_families,
        blocked_test_families=policy_data.blocked_test_families,
        max_payloads_per_test=policy_data.max_payloads_per_test,
        max_requests_per_second=policy_data.max_requests_per_second,
        max_concurrent_requests=policy_data.max_concurrent_requests,
        request_timeout_seconds=policy_data.request_timeout_seconds,
        block_destructive=policy_data.block_destructive,
        sla_critical_hours=policy_data.sla_critical_hours,
        sla_high_hours=policy_data.sla_high_hours,
        sla_medium_hours=policy_data.sla_medium_hours,
        sla_low_hours=policy_data.sla_low_hours,
        compliance_frameworks=policy_data.compliance_frameworks,
        authorized_users=policy_data.authorized_users,
        authorized_roles=policy_data.authorized_roles,
        created_by="local-user",
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    # Audit: log policy creation
    audit = get_audit_service()
    audit.log(
        db,
        action="policy_created",
        category="governance",
        resource_type="policy",
        resource_id=policy.policy_id,
        details={"name": policy.name},
    )

    return policy


@router.get("/policies/{policy_id}", response_model=ScanPolicyResponse)
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    """Get a single scan policy."""
    policy = db.query(ScanPolicy).filter(ScanPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/policies/{policy_id}", response_model=ScanPolicyResponse)
async def update_policy(
    policy_id: str,
    updates: dict,
    db: Session = Depends(get_db),
):
    """Update a scan policy (audited)."""
    policy = db.query(ScanPolicy).filter(ScanPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    previous = {
        "name": policy.name,
        "block_destructive": policy.block_destructive,
        "max_requests_per_second": policy.max_requests_per_second,
    }

    updatable = [
        "name", "description", "is_active", "allowed_targets", "excluded_paths",
        "allowed_methods", "allowed_test_families", "blocked_test_families",
        "max_payloads_per_test", "max_requests_per_second", "max_concurrent_requests",
        "request_timeout_seconds", "block_destructive",
        "sla_critical_hours", "sla_high_hours", "sla_medium_hours", "sla_low_hours",
        "compliance_frameworks", "authorized_users", "authorized_roles",
    ]

    for field in updatable:
        if field in updates:
            setattr(policy, field, updates[field])

    db.commit()
    db.refresh(policy)

    # Audit: log policy change
    audit = get_audit_service()
    audit.log_policy_changed(
        db, policy_id, previous_state=previous,
        new_state={k: updates[k] for k in updates if k in updatable},
    )

    return policy


@router.post("/policies/{policy_id}/validate-target")
async def validate_target_against_policy(
    policy_id: str,
    target_url: str = Query(..., description="URL to validate"),
    db: Session = Depends(get_db),
):
    """Check if a target URL is authorized under a policy."""
    policy = db.query(ScanPolicy).filter(ScanPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    allowed = policy.allowed_targets or []
    excluded = policy.excluded_paths or []

    from urllib.parse import urlparse
    parsed = urlparse(target_url)

    is_allowed = not allowed  # If no explicit targets, everything is allowed
    for pattern in allowed:
        if pattern in target_url or parsed.hostname in pattern:
            is_allowed = True
            break

    is_excluded = False
    for exc_path in excluded:
        if exc_path in (parsed.path or ""):
            is_excluded = True
            break

    return {
        "target_url": target_url,
        "policy_id": policy_id,
        "authorized": is_allowed and not is_excluded,
        "reason": (
            "Target is authorized under policy"
            if is_allowed and not is_excluded
            else "Target is excluded by policy" if is_excluded
            else "Target is not in the allowed targets list"
        ),
    }


# ── Correlation Groups ──────────────────────────────────

@router.get("/correlations", response_model=List[CorrelationGroupResponse])
async def list_correlations(
    scan_id: Optional[int] = None,
    group_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List correlation groups."""
    svc = get_correlation_service()
    if scan_id:
        return svc.get_groups_for_scan(db, scan_id, group_type)

    query = db.query(CorrelationGroup)
    if group_type:
        query = query.filter(CorrelationGroup.group_type == group_type)
    return query.order_by(CorrelationGroup.created_at.desc()).limit(100).all()


@router.post("/correlations/scan/{scan_id}/run")
async def run_correlation(scan_id: int, db: Session = Depends(get_db)):
    """Trigger correlation analysis for a scan."""
    svc = get_correlation_service()
    result = svc.correlate_scan_findings(db, scan_id)

    audit = get_audit_service()
    audit.log(
        db,
        action="correlation_run",
        category="finding",
        resource_type="scan",
        resource_id=str(scan_id),
        details=result,
    )

    return result


@router.patch("/correlations/{correlation_id}/review")
async def review_correlation(
    correlation_id: str,
    reviewed_by: str = Query("analyst", description="Reviewer name"),
    db: Session = Depends(get_db),
):
    """Mark a correlation group as reviewed."""
    svc = get_correlation_service()
    group = svc.mark_group_reviewed(db, correlation_id, reviewed_by)

    if not group:
        raise HTTPException(status_code=404, detail="Correlation group not found")

    return {"message": "Marked as reviewed", "correlation_id": correlation_id}
