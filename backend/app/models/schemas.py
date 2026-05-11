"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class ScanStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Scan Schemas
class ScanCreate(BaseModel):
    target_url: HttpUrl
    scan_type: str = "full"
    scope_config: Optional[Dict[str, Any]] = None
    test_config: Optional[Dict[str, Any]] = None


class ScanUpdate(BaseModel):
    status: Optional[ScanStatusEnum] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_phase: Optional[str] = None
    error_message: Optional[str] = None


class ScanResponse(BaseModel):
    id: int
    scan_id: str
    target_url: str
    scan_type: str
    status: ScanStatusEnum
    progress_percentage: int
    current_phase: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    endpoints_discovered: Optional[int] = 0
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    
    class Config:
        from_attributes = True


# Endpoint Schemas
class EndpointCreate(BaseModel):
    scan_id: int
    url: str
    method: str
    parameters: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    endpoint_type: Optional[str] = None
    owasp_categories: Optional[List[str]] = None


class EndpointResponse(BaseModel):
    id: int
    url: str
    method: str
    endpoint_type: Optional[str]
    parameters: Optional[Dict[str, Any]]
    owasp_categories: Optional[List[str]]
    discovered_at: datetime
    
    class Config:
        from_attributes = True


# Vulnerability Schemas
class VulnerabilityCreate(BaseModel):
    scan_id: int
    endpoint_id: Optional[int] = None
    title: str
    description: str
    severity: SeverityEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    owasp_category: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    request_payload: Optional[str] = None
    response_evidence: Optional[str] = None
    poc_code: Optional[str] = None
    remediation: Optional[str] = None


class VulnerabilityResponse(BaseModel):
    id: int
    scan_id: int
    title: str
    description: str
    severity: SeverityEnum
    confidence: float
    owasp_category: str
    cwe_id: Optional[str]
    cvss_score: Optional[float]
    affected_parameter: Optional[str]
    vulnerability_type: Optional[str]
    status: Optional[str]
    is_validated: bool
    is_false_positive: bool
    request_payload: Optional[str]
    response_evidence: Optional[str]
    poc_curl_command: Optional[str]
    remediation: Optional[str]
    llm_explanation: Optional[str]
    llm_business_impact: Optional[str]
    llm_remediation: Optional[str]
    llm_evidence: Optional[str]
    llm_poc: Optional[str]
    endpoint_url: Optional[str] = None
    endpoint_method: Optional[str] = None
    detected_at: datetime
    
    class Config:
        from_attributes = True


# Report Schemas
class ReportCreate(BaseModel):
    scan_id: int
    report_type: str


class ReportResponse(BaseModel):
    id: int
    scan_id: int
    report_id: str
    report_type: str
    file_path: Optional[str]
    generated_at: datetime
    file_size: Optional[int]
    
    class Config:
        from_attributes = True


# WebSocket Message Schemas
class WSMessage(BaseModel):
    type: str  # scan_update, vulnerability_found, phase_change, error
    scan_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Attack Plan Schemas
class AttackPlanResponse(BaseModel):
    id: int
    scan_id: int
    endpoint_id: int
    plan_data: Dict[str, Any]
    execution_status: str
    findings_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard Statistics
class DashboardStats(BaseModel):
    total_scans: int
    active_scans: int
    completed_scans: int
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    recent_scans: List[ScanResponse]


# ────────────────────────────────────────────────────────
# Evidence Schemas
# ────────────────────────────────────────────────────────

class EvidenceCreate(BaseModel):
    vulnerability_id: Optional[int] = None
    scan_id: int
    endpoint_id: Optional[int] = None
    evidence_type: str  # request_response, screenshot, har, replay, raw_output
    http_method: Optional[str] = None
    request_url: Optional[str] = None
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    response_status_code: Optional[int] = None
    response_headers: Optional[Dict[str, Any]] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    tool_name: Optional[str] = None
    tool_version: Optional[str] = None
    payload_id: Optional[str] = None
    payload_value: Optional[str] = None
    phase: Optional[str] = None
    is_baseline: bool = False
    initiated_by: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: int
    evidence_id: str
    vulnerability_id: Optional[int]
    scan_id: int
    evidence_type: str
    http_method: Optional[str]
    request_url: Optional[str]
    request_headers: Optional[Dict[str, Any]]
    request_body: Optional[str]
    response_status_code: Optional[int]
    response_headers: Optional[Dict[str, Any]]
    response_body: Optional[str]
    response_time_ms: Optional[int]
    storage_uri: Optional[str]
    screenshot_uri: Optional[str]
    har_uri: Optional[str]
    tool_name: Optional[str]
    tool_version: Optional[str]
    payload_id: Optional[str]
    payload_value: Optional[str]
    phase: Optional[str]
    is_baseline: bool
    initiated_by: Optional[str]
    captured_at: datetime

    class Config:
        from_attributes = True


# ────────────────────────────────────────────────────────
# Lineage Schemas
# ────────────────────────────────────────────────────────

class LineageEventCreate(BaseModel):
    scan_id: int
    vulnerability_id: Optional[int] = None
    evidence_id: Optional[int] = None
    stage: str
    previous_stage: Optional[str] = None
    agent_name: Optional[str] = None
    rule_id: Optional[str] = None
    rule_version: Optional[str] = None
    decision_reason: Optional[str] = None
    confidence_at_stage: Optional[float] = None
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[Dict[str, Any]] = None


class LineageEventResponse(BaseModel):
    id: int
    lineage_id: str
    scan_id: int
    vulnerability_id: Optional[int]
    evidence_id: Optional[int]
    stage: str
    previous_stage: Optional[str]
    agent_name: Optional[str]
    rule_id: Optional[str]
    rule_version: Optional[str]
    decision_reason: Optional[str]
    confidence_at_stage: Optional[float]
    input_summary: Optional[Dict[str, Any]]
    output_summary: Optional[Dict[str, Any]]
    occurred_at: datetime

    class Config:
        from_attributes = True


class FindingLineageChain(BaseModel):
    """Full evidence chain for a single finding — used by the frontend lineage timeline."""
    vulnerability_id: int
    title: str
    severity: str
    lineage: List[LineageEventResponse]
    evidence: List[EvidenceResponse]
    related_findings: List[int]  # IDs of correlated findings
    correlation_group_id: Optional[str] = None


# ────────────────────────────────────────────────────────
# Correlation Schemas
# ────────────────────────────────────────────────────────

class CorrelationGroupCreate(BaseModel):
    scan_id: int
    group_type: str  # duplicate, related, exploit_chain
    title: str
    description: Optional[str] = None
    root_cause: Optional[str] = None
    member_vulnerability_ids: List[int]
    chain_steps: Optional[List[int]] = None
    chain_impact: Optional[str] = None


class CorrelationGroupResponse(BaseModel):
    id: int
    correlation_id: str
    scan_id: int
    group_type: str
    title: str
    description: Optional[str]
    root_cause: Optional[str]
    root_vulnerability_id: Optional[int]
    member_vulnerability_ids: List[int]
    member_count: int
    highest_severity: Optional[str]
    combined_cvss: Optional[float]
    chain_steps: Optional[List[int]]
    chain_impact: Optional[str]
    is_reviewed: bool
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ────────────────────────────────────────────────────────
# Audit Schemas
# ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    audit_id: str
    action: str
    category: str
    user_id: Optional[str]
    user_role: Optional[str]
    ip_address: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    success: bool
    error_message: Optional[str]
    occurred_at: datetime

    class Config:
        from_attributes = True


# ────────────────────────────────────────────────────────
# Governance / Policy Schemas
# ────────────────────────────────────────────────────────

class ScanPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    allowed_targets: Optional[List[str]] = None
    excluded_paths: Optional[List[str]] = None
    allowed_methods: Optional[List[str]] = None
    allowed_test_families: Optional[List[str]] = None
    blocked_test_families: Optional[List[str]] = None
    max_payloads_per_test: int = 50
    max_requests_per_second: int = 10
    max_concurrent_requests: int = 5
    request_timeout_seconds: int = 30
    block_destructive: bool = True
    sla_critical_hours: int = 24
    sla_high_hours: int = 72
    sla_medium_hours: int = 168
    sla_low_hours: int = 720
    compliance_frameworks: Optional[List[str]] = None
    authorized_users: Optional[List[str]] = None
    authorized_roles: Optional[List[str]] = None


class ScanPolicyResponse(BaseModel):
    id: int
    policy_id: str
    name: str
    description: Optional[str]
    version: str
    is_active: bool
    allowed_targets: Optional[List[str]]
    excluded_paths: Optional[List[str]]
    allowed_methods: Optional[List[str]]
    allowed_test_families: Optional[List[str]]
    blocked_test_families: Optional[List[str]]
    max_payloads_per_test: int
    max_requests_per_second: int
    block_destructive: bool
    sla_critical_hours: int
    sla_high_hours: int
    sla_medium_hours: int
    sla_low_hours: int
    compliance_frameworks: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True
