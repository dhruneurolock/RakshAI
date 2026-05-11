"""
Vulnerabilities API Endpoints
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.agents.poc_generator import PoCAgent
from app.models.models import Vulnerability, VulnerabilitySeverity, Endpoint
from app.models.schemas import VulnerabilityResponse

router = APIRouter()


def _format_remediation_text(remediation_payload: Any) -> str:
    """Convert remediation payload (dict/list/string) to a readable plain-text format."""
    if remediation_payload is None:
        return ""

    if isinstance(remediation_payload, str):
        return remediation_payload.strip()

    if isinstance(remediation_payload, list):
        lines = [str(item).strip() for item in remediation_payload if str(item).strip()]
        return "\n".join(f"{idx}. {line}" for idx, line in enumerate(lines, start=1))

    if not isinstance(remediation_payload, dict):
        return str(remediation_payload).strip()

    sections: List[str] = []

    executive_summary = str(remediation_payload.get("executive_summary") or "").strip()
    if executive_summary:
        sections.append(f"Executive Summary:\n{executive_summary}")

    root_cause = str(remediation_payload.get("root_cause") or "").strip()
    if root_cause:
        sections.append(f"Root Cause:\n{root_cause}")

    remediation_steps = remediation_payload.get("remediation_steps")
    if isinstance(remediation_steps, list) and remediation_steps:
        step_lines = [
            f"{idx}. {str(step).strip()}"
            for idx, step in enumerate(remediation_steps, start=1)
            if str(step).strip()
        ]
        if step_lines:
            sections.append("Remediation Steps:\n" + "\n".join(step_lines))

    code_example = str(remediation_payload.get("code_example") or "").strip()
    if code_example:
        sections.append(f"Code Example:\n{code_example}")

    testing_instructions = remediation_payload.get("testing_instructions")
    if isinstance(testing_instructions, list) and testing_instructions:
        test_lines = [
            f"{idx}. {str(item).strip()}"
            for idx, item in enumerate(testing_instructions, start=1)
            if str(item).strip()
        ]
        if test_lines:
            sections.append("Testing Instructions:\n" + "\n".join(test_lines))

    timeline = str(remediation_payload.get("timeline") or "").strip()
    if timeline:
        sections.append(f"Timeline:\n{timeline}")

    business_impact = str(remediation_payload.get("business_impact") or "").strip()
    if business_impact:
        sections.append(f"Risk If Not Addressed:\n{business_impact}")

    if sections:
        return "\n\n".join(sections)

    return json.dumps(remediation_payload)


def _attach_endpoint_url(vuln: Vulnerability, db: Session) -> VulnerabilityResponse:
    """Build VulnerabilityResponse and resolve endpoint URL + method."""
    data = VulnerabilityResponse.from_orm(vuln)
    if vuln.endpoint_id:
        ep = db.query(Endpoint).filter(Endpoint.id == vuln.endpoint_id).first()
        if ep:
            from urllib.parse import urlparse
            parsed = urlparse(ep.url)
            data.endpoint_url = parsed.path or ep.url
            data.endpoint_method = ep.method
    return data


@router.get("/", response_model=List[VulnerabilityResponse])
async def list_vulnerabilities(
    scan_id: Optional[int] = None,
    severity: Optional[str] = None,
    validated_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List vulnerabilities with filtering"""
    query = db.query(Vulnerability)

    if scan_id:
        query = query.filter(Vulnerability.scan_id == scan_id)

    if severity:
        try:
            sev_enum = VulnerabilitySeverity[severity.upper()]
            query = query.filter(Vulnerability.severity == sev_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid severity level")

    if validated_only:
        query = query.filter(Vulnerability.is_validated == True)

    # Exclude false positives by default
    query = query.filter(Vulnerability.is_false_positive == False)

    vulnerabilities = query.order_by(
        Vulnerability.severity.desc(),
        Vulnerability.detected_at.desc()
    ).offset(skip).limit(limit).all()

    return [_attach_endpoint_url(v, db) for v in vulnerabilities]


@router.get("/{vuln_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(vuln_id: int, db: Session = Depends(get_db)):
    """Get vulnerability details"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return _attach_endpoint_url(vuln, db)


@router.patch("/{vuln_id}/mark-false-positive")
async def mark_false_positive(
    vuln_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Mark a vulnerability as false positive"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    vuln.is_false_positive = True
    vuln.status = "FALSE_POSITIVE"
    vuln.validation_notes = payload.get("reason", "")
    db.commit()
    return {"message": "Marked as false positive"}



@router.patch("/{vuln_id}/mark-false-positive")
async def mark_false_positive(
    vuln_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Mark vulnerability as false positive"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    vuln.is_false_positive = True
    vuln.validation_notes = f"Marked as false positive: {reason}"
    db.commit()
    
    return {"message": "Marked as false positive", "vuln_id": vuln_id}


@router.post("/{vuln_id}/generate-poc")
async def create_poc(vuln_id: int, db: Session = Depends(get_db)):
    """Generate PoC for vulnerability using enterprise PoCAgent"""
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    if not vuln.is_validated:
        raise HTTPException(status_code=400, detail="Cannot generate PoC for unvalidated vulnerability")
    
    try:
        # Generate PoC using new agent
        poc_agent = PoCAgent(f"poc_agent_{vuln_id}")
        await poc_agent.initialize()
        finding_data = {
            "id": vuln.id,
            "vulnerability_type": vuln.vulnerability_type,
            "endpoint_url": vuln.endpoint.url if vuln.endpoint else "",
            "attack_vector": vuln.attack_vector or {},
            "evidence": vuln.raw_evidence or {}
        }
        result = await poc_agent.run(str(vuln.scan_id))
        
        return {
            "message": "PoC generated successfully",
            "vuln_id": vuln_id,
            "poc_data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PoC: {str(e)}")



@router.post("/{vuln_id}/generate-remediation")
async def generate_remediation(
    vuln_id: int,
    db: Session = Depends(get_db)
):
    """Generate instant LLM-based remediation solution for vulnerability"""
    try:
        vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
        if not vuln:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        from app.agents.remediation_agent import RemediationAgent
        agent = RemediationAgent(f"remediation_agent_{vuln_id}")
        await agent.initialize()
        
        result = await agent.run(scan_id=str(vuln.scan_id), vulnerability_id=vuln_id)
        
        if result.get('status') == 'success':
            remediation_payload = result.get('remediation')
            remediation_text = _format_remediation_text(remediation_payload)

            if remediation_text:
                vuln.remediation = remediation_text

            if isinstance(remediation_payload, (dict, list)):
                vuln.llm_remediation = json.dumps(remediation_payload)
            elif isinstance(remediation_payload, str):
                vuln.llm_remediation = remediation_payload

            db.add(vuln)
            db.commit()

            return {
                "message": "Remediation generated",
                "vulnerability_id": vuln_id,
                "remediation": remediation_payload,
                "remediation_text": remediation_text,
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message'))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@router.get("/stats/by-severity")
async def get_severity_stats(
    scan_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get vulnerability statistics by severity"""
    query = db.query(Vulnerability).filter(Vulnerability.is_false_positive == False)
    
    if scan_id:
        query = query.filter(Vulnerability.scan_id == scan_id)
    
    all_vulns = query.all()
    
    stats = {
        "total": len(all_vulns),
        "critical": len([v for v in all_vulns if v.severity == VulnerabilitySeverity.CRITICAL]),
        "high": len([v for v in all_vulns if v.severity == VulnerabilitySeverity.HIGH]),
        "medium": len([v for v in all_vulns if v.severity == VulnerabilitySeverity.MEDIUM]),
        "low": len([v for v in all_vulns if v.severity == VulnerabilitySeverity.LOW]),
        "info": len([v for v in all_vulns if v.severity == VulnerabilitySeverity.INFO])
    }
    
    return stats


@router.get("/stats/by-category")
async def get_category_stats(
    scan_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get vulnerability statistics by OWASP category"""
    query = db.query(Vulnerability).filter(Vulnerability.is_false_positive == False)
    
    if scan_id:
        query = query.filter(Vulnerability.scan_id == scan_id)
    
    all_vulns = query.all()
    
    # Count by category
    category_counts = {}
    for vuln in all_vulns:
        category = vuln.owasp_category
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return category_counts


