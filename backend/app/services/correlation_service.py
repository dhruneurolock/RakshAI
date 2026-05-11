"""
Correlation Service
Groups repeated findings, links related issues, and flags likely exploit chains.
Reduces duplicate noise and improves analyst workflow.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.models import (
    Vulnerability,
    CorrelationGroup,
    VulnerabilitySeverity,
)

logger = logging.getLogger(__name__)

# Severity ordering for roll-up
SEVERITY_ORDER = {
    VulnerabilitySeverity.CRITICAL: 5,
    VulnerabilitySeverity.HIGH: 4,
    VulnerabilitySeverity.MEDIUM: 3,
    VulnerabilitySeverity.LOW: 2,
    VulnerabilitySeverity.INFO: 1,
}


class CorrelationService:
    """
    Analyze findings within a scan and produce correlation groups:
    - **duplicate**: Same vulnerability type on same endpoint
    - **related**: Same vulnerability type across different endpoints
    - **exploit_chain**: Findings that together form a higher-impact attack path
    """

    def correlate_scan_findings(self, db: Session, scan_id: int) -> Dict[str, Any]:
        """
        Run correlation analysis on all findings for a scan.
        Creates CorrelationGroup records and returns a summary.
        """
        findings = (
            db.query(Vulnerability)
            .filter(
                Vulnerability.scan_id == scan_id,
                Vulnerability.is_false_positive == False,
            )
            .all()
        )

        if not findings:
            return {"groups_created": 0, "duplicates": 0, "chains": 0}

        # Phase 1: Group duplicates (same type + same endpoint)
        duplicate_groups = self._find_duplicates(findings)

        # Phase 2: Group related (same type, different endpoints)
        related_groups = self._find_related(findings, duplicate_groups)

        # Phase 3: Detect exploit chains
        chain_groups = self._detect_exploit_chains(findings)

        # Persist all groups
        total_created = 0
        for group_data in duplicate_groups + related_groups + chain_groups:
            group = self._create_group(db, scan_id, group_data)
            if group:
                total_created += 1

        db.commit()

        summary = {
            "groups_created": total_created,
            "duplicates": len(duplicate_groups),
            "related": len(related_groups),
            "chains": len(chain_groups),
            "total_findings": len(findings),
            "deduplicated_findings": len(findings) - sum(
                max(0, g["member_count"] - 1) for g in duplicate_groups
            ),
        }

        logger.info(f"Correlation complete for scan {scan_id}: {summary}")
        return summary

    def get_groups_for_scan(
        self, db: Session, scan_id: int, group_type: Optional[str] = None
    ) -> List[CorrelationGroup]:
        """Get all correlation groups for a scan."""
        query = db.query(CorrelationGroup).filter(
            CorrelationGroup.scan_id == scan_id
        )
        if group_type:
            query = query.filter(CorrelationGroup.group_type == group_type)
        return query.order_by(CorrelationGroup.created_at.desc()).all()

    def get_related_findings(
        self, db: Session, vulnerability_id: int
    ) -> List[int]:
        """Get IDs of findings correlated with a given finding."""
        groups = db.query(CorrelationGroup).all()
        related = set()
        for group in groups:
            members = group.member_vulnerability_ids or []
            if vulnerability_id in members:
                related.update(m for m in members if m != vulnerability_id)
        return list(related)

    def mark_group_reviewed(
        self, db: Session, correlation_id: str, reviewed_by: str
    ) -> Optional[CorrelationGroup]:
        """Mark a correlation group as reviewed by an analyst."""
        from datetime import datetime

        group = (
            db.query(CorrelationGroup)
            .filter(CorrelationGroup.correlation_id == correlation_id)
            .first()
        )
        if group:
            group.is_reviewed = True
            group.reviewed_by = reviewed_by
            group.reviewed_at = datetime.utcnow()
            db.commit()
            db.refresh(group)
        return group

    # ── Internal grouping logic ──────────────────────────

    def _find_duplicates(
        self, findings: List[Vulnerability]
    ) -> List[Dict[str, Any]]:
        """Group findings with same type + same endpoint URL."""
        buckets: Dict[str, List[Vulnerability]] = defaultdict(list)

        for f in findings:
            key = f"{f.vulnerability_type or 'unknown'}|{f.endpoint_id or 'none'}"
            buckets[key].append(f)

        groups = []
        for key, members in buckets.items():
            if len(members) > 1:
                highest = max(members, key=lambda m: SEVERITY_ORDER.get(m.severity, 0))
                groups.append({
                    "group_type": "duplicate",
                    "title": f"Duplicate: {members[0].vulnerability_type or members[0].title}",
                    "description": f"{len(members)} instances of the same finding on the same endpoint",
                    "member_ids": [m.id for m in members],
                    "member_count": len(members),
                    "root_id": highest.id,
                    "highest_severity": highest.severity.value if highest.severity else None,
                    "combined_cvss": highest.cvss_score,
                })

        return groups

    def _find_related(
        self,
        findings: List[Vulnerability],
        existing_duplicate_groups: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Group findings with same type across different endpoints."""
        # IDs already in duplicate groups
        duplicated_ids = set()
        for dg in existing_duplicate_groups:
            duplicated_ids.update(dg["member_ids"])

        # Group by vulnerability type
        type_buckets: Dict[str, List[Vulnerability]] = defaultdict(list)
        for f in findings:
            if f.id not in duplicated_ids:
                vtype = f.vulnerability_type or "unknown"
                type_buckets[vtype].append(f)

        groups = []
        for vtype, members in type_buckets.items():
            if len(members) > 1:
                # Only group if they span different endpoints
                endpoint_ids = set(m.endpoint_id for m in members if m.endpoint_id)
                if len(endpoint_ids) > 1:
                    highest = max(members, key=lambda m: SEVERITY_ORDER.get(m.severity, 0))
                    groups.append({
                        "group_type": "related",
                        "title": f"Related: {vtype} across {len(endpoint_ids)} endpoints",
                        "description": f"Same vulnerability type found on multiple endpoints",
                        "member_ids": [m.id for m in members],
                        "member_count": len(members),
                        "root_id": highest.id,
                        "highest_severity": highest.severity.value if highest.severity else None,
                        "combined_cvss": highest.cvss_score,
                    })

        return groups

    def _detect_exploit_chains(
        self, findings: List[Vulnerability]
    ) -> List[Dict[str, Any]]:
        """
        Detect potential exploit chains where low-severity findings
        can be combined for higher impact.

        Known chain patterns:
        - Info Disclosure → Auth Bypass → Privilege Escalation
        - SSRF → Internal API Access → Data Exfiltration
        - XSS → Session Hijacking → Account Takeover
        """
        chains = []

        # Index findings by type
        type_index: Dict[str, List[Vulnerability]] = defaultdict(list)
        for f in findings:
            vtype = (f.vulnerability_type or "").lower()
            type_index[vtype].append(f)

        # Chain pattern: Info Disclosure + Auth Bypass
        info_types = ["information_disclosure", "info_disclosure", "sensitive_data_exposure"]
        auth_types = ["auth_bypass", "authentication_bypass", "broken_authentication"]

        info_findings = []
        auth_findings = []
        for t in info_types:
            info_findings.extend(type_index.get(t, []))
        for t in auth_types:
            auth_findings.extend(type_index.get(t, []))

        if info_findings and auth_findings:
            all_chain = info_findings + auth_findings
            chains.append({
                "group_type": "exploit_chain",
                "title": "Exploit Chain: Info Disclosure → Auth Bypass",
                "description": "Information leakage could provide credentials or tokens for authentication bypass",
                "member_ids": [f.id for f in all_chain],
                "member_count": len(all_chain),
                "root_id": all_chain[0].id,
                "highest_severity": "critical",
                "combined_cvss": 9.8,
                "chain_steps": [f.id for f in all_chain],
                "chain_impact": "Complete authentication bypass using leaked credentials",
            })

        # Chain pattern: XSS + Session Management issues
        xss_types = ["xss", "cross_site_scripting", "reflected_xss", "stored_xss"]
        session_types = ["session_fixation", "session_hijacking", "insecure_session"]

        xss_findings = []
        session_findings = []
        for t in xss_types:
            xss_findings.extend(type_index.get(t, []))
        for t in session_types:
            session_findings.extend(type_index.get(t, []))

        if xss_findings and session_findings:
            all_chain = xss_findings + session_findings
            chains.append({
                "group_type": "exploit_chain",
                "title": "Exploit Chain: XSS → Session Hijacking",
                "description": "XSS vulnerability can be used to steal session tokens",
                "member_ids": [f.id for f in all_chain],
                "member_count": len(all_chain),
                "root_id": all_chain[0].id,
                "highest_severity": "high",
                "combined_cvss": 8.1,
                "chain_steps": [f.id for f in all_chain],
                "chain_impact": "Account takeover via session token theft",
            })

        # Chain pattern: SSRF + Internal access
        ssrf_types = ["ssrf", "server_side_request_forgery"]
        ssrf_findings = []
        for t in ssrf_types:
            ssrf_findings.extend(type_index.get(t, []))

        if ssrf_findings and info_findings:
            all_chain = ssrf_findings + info_findings
            chains.append({
                "group_type": "exploit_chain",
                "title": "Exploit Chain: SSRF → Internal Data Access",
                "description": "SSRF can access internal APIs that expose sensitive data",
                "member_ids": [f.id for f in all_chain],
                "member_count": len(all_chain),
                "root_id": all_chain[0].id,
                "highest_severity": "critical",
                "combined_cvss": 9.1,
                "chain_steps": [f.id for f in all_chain],
                "chain_impact": "Access to internal services and data exfiltration",
            })

        return chains

    def _create_group(
        self, db: Session, scan_id: int, group_data: Dict[str, Any]
    ) -> Optional[CorrelationGroup]:
        """Persist a correlation group to the database."""
        try:
            group = CorrelationGroup(
                correlation_id=f"cg-{uuid.uuid4().hex[:16]}",
                scan_id=scan_id,
                group_type=group_data["group_type"],
                title=group_data["title"],
                description=group_data.get("description"),
                root_cause=group_data.get("root_cause"),
                root_vulnerability_id=group_data.get("root_id"),
                member_vulnerability_ids=group_data["member_ids"],
                member_count=group_data["member_count"],
                highest_severity=group_data.get("highest_severity"),
                combined_cvss=group_data.get("combined_cvss"),
                chain_steps=group_data.get("chain_steps"),
                chain_impact=group_data.get("chain_impact"),
            )
            db.add(group)
            return group
        except Exception as e:
            logger.error(f"Failed to create correlation group: {e}")
            return None


# Singleton accessor
_correlation_service = None


def get_correlation_service() -> CorrelationService:
    global _correlation_service
    if _correlation_service is None:
        _correlation_service = CorrelationService()
    return _correlation_service
