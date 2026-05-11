"""Database models for RakshAI"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class ScanStatus(str, enum.Enum):
    """
    Scan status enumeration - Enterprise workflow states
    Complete state machine from LAYER 2 orchestration
    """
    # Initial states
    QUEUED = "queued"
    INITIALIZING = "initializing"
    
    # Discovery phase
    DISCOVERING = "discovering"
    
    # Planning phase
    PLANNING = "planning"
    
    # Testing phase
    TESTING = "testing"
    
    # Validation phase
    VALIDATING = "validating"
    
    # PoC generation
    POC_GENERATION = "poc_generation"
    
    # Reporting phase
    AGGREGATING = "aggregating"
    REPORTING = "reporting"
    
    # Final states
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    # Legacy compatibility
    PENDING = "pending"  # Maps to QUEUED
    RUNNING = "running"  # Maps to TESTING


class VulnerabilitySeverity(str, enum.Enum):
    """Vulnerability severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Scan(Base):
    """Scan model - represents a penetration test scan"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String(100), unique=True, index=True, nullable=False)
    target_url = Column(String(500), nullable=False)
    scan_type = Column(String(50), default="full")  # full, quick, custom
    status = Column(Enum(ScanStatus), default=ScanStatus.QUEUED, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    scope_config = Column(JSON, nullable=True)  # Allowed paths, excluded paths
    test_config = Column(JSON, nullable=True)   # Which OWASP categories to test
    policy = Column(JSON, nullable=True)        # Enterprise policy constraints
    
    # LLM-generated strategy
    strategy = Column(JSON, nullable=True)      # Attack strategy from Coordinator
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_phase = Column(String(100), nullable=True)
    
    # Attack graph statistics
    endpoints_discovered = Column(Integer, default=0)
    attacks_planned = Column(Integer, default=0)
    attacks_executed = Column(Integer, default=0)
    
    # Results summary
    total_findings = Column(Integer, default=0)
    validated_findings = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Relationships
    endpoints = relationship("Endpoint", back_populates="scan", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan", cascade="all, delete-orphan")
    evidence_records = relationship("EvidenceRecord", back_populates="scan", cascade="all, delete-orphan")
    lineage_events = relationship("LineageEvent", back_populates="scan", cascade="all, delete-orphan")
    correlation_groups = relationship("CorrelationGroup", back_populates="scan", cascade="all, delete-orphan")


class Endpoint(Base):
    """Discovered endpoints during scan"""
    __tablename__ = "endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    
    url = Column(String(1000), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, etc.
    
    # Endpoint characteristics
    parameters = Column(JSON, nullable=True)  # Query params, form fields, etc.
    headers = Column(JSON, nullable=True)
    cookies = Column(JSON, nullable=True)
    
    # Classification
    endpoint_type = Column(String(50), nullable=True)  # api, form, page, etc.
    requires_auth = Column(Boolean, default=False)
    
    # OWASP mapping
    owasp_categories = Column(JSON, nullable=True)  # List of applicable OWASP categories
    
    # Discovery metadata
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    discovery_method = Column(String(50), nullable=True)  # crawl, sitemap, manual
    
    # Relationships
    scan = relationship("Scan", back_populates="endpoints")
    vulnerabilities = relationship("Vulnerability", back_populates="endpoint")


class Vulnerability(Base):
    """Detected vulnerabilities"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=True)
    
    # Vulnerability details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(VulnerabilitySeverity), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Classification
    owasp_category = Column(String(50), nullable=False, index=True)  # A01, A02, etc.
    cwe_id = Column(String(20), nullable=True)  # CWE-79, CWE-89, etc.
    cvss_score = Column(Float, nullable=True)
    vulnerability_type = Column(String(50), nullable=True)  # IDOR, SQLi, XSS, etc.
    
    # Evidence
    request_payload = Column(Text, nullable=True)
    response_evidence = Column(Text, nullable=True)
    poc_code = Column(Text, nullable=True)
    
    # Metadata
    affected_parameter = Column(String(200), nullable=True)
    attack_vector = Column(String(100), nullable=True)
    
    # Enterprise Validation System
    status = Column(String(50), default="UNVALIDATED")  # UNVALIDATED, VALIDATING, VALIDATED, FALSE_POSITIVE
    validation_replays = Column(Integer, default=0)  # Number of successful replays
    validation_count = Column(Integer, default=0)  # Total validation attempts
    is_validated = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)
    validation_notes = Column(Text, nullable=True)
    
    # PoC Evidence URLs (MinIO storage)
    poc_screenshot_url = Column(String(500), nullable=True)
    poc_http_trace_url = Column(String(500), nullable=True)
    poc_curl_command = Column(Text, nullable=True)
    
    # Remediation
    remediation = Column(Text, nullable=True)
    references = Column(JSON, nullable=True)  # List of reference URLs
    
    # LLM-generated content
    llm_explanation = Column(Text, nullable=True)
    llm_business_impact = Column(Text, nullable=True)
    llm_remediation = Column(Text, nullable=True)
    llm_evidence = Column(Text, nullable=True)
    llm_poc = Column(Text, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    validated_at = Column(DateTime(timezone=True), nullable=True)
    poc_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    scan = relationship("Scan", back_populates="vulnerabilities")
    endpoint = relationship("Endpoint", back_populates="vulnerabilities")
    evidence_records = relationship("EvidenceRecord", back_populates="vulnerability", cascade="all, delete-orphan")
    lineage_events = relationship("LineageEvent", back_populates="vulnerability", cascade="all, delete-orphan")


class Report(Base):
    """Generated security reports"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    
    report_id = Column(String(100), unique=True, index=True, nullable=False)
    report_type = Column(String(50), nullable=False)  # xml, pdf, json, html
    
    # Report content
    file_path = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)  # For XML/JSON reports
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    file_size = Column(Integer, nullable=True)
    
    # Relationships
    scan = relationship("Scan", back_populates="reports")


class AttackPlan(Base):
    """Generated attack plans from rule engine"""
    __tablename__ = "attack_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False)
    
    # Plan details
    plan_data = Column(JSON, nullable=False)  # Complete attack plan
    
    # Execution tracking
    execution_status = Column(String(50), default="pending")
    execution_started_at = Column(DateTime(timezone=True), nullable=True)
    execution_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    findings_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EvidenceRecord(Base):
    """
    First-class evidence entity for request/response artifacts, screenshots,
    HAR captures, replay metadata, tool versions, payload IDs, and timestamps.
    Each evidence record is tied to a vulnerability and optionally to a specific
    lineage event so analysts can trace exactly what was sent and received.
    """
    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(100), unique=True, index=True, nullable=False)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True)

    # Evidence type classification
    evidence_type = Column(String(50), nullable=False, index=True)  # request_response, screenshot, har, replay, raw_output

    # HTTP request/response capture
    http_method = Column(String(10), nullable=True)
    request_url = Column(String(2000), nullable=True)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(Text, nullable=True)
    response_status_code = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Storage URIs (MinIO or local paths)
    storage_uri = Column(String(1000), nullable=True)       # Primary artifact URI
    screenshot_uri = Column(String(1000), nullable=True)    # Screenshot path
    har_uri = Column(String(1000), nullable=True)           # HAR capture path

    # Tool and payload attribution
    tool_name = Column(String(100), nullable=True)          # sqlmap, dalfox, etc.
    tool_version = Column(String(50), nullable=True)
    payload_id = Column(String(100), nullable=True)         # Reference to YAML payload
    payload_value = Column(Text, nullable=True)             # Actual payload used

    # Context metadata
    phase = Column(String(50), nullable=True)               # discovery, execution, validation, replay
    is_baseline = Column(Boolean, default=False)            # True for baseline (no-payload) request
    user_session = Column(String(200), nullable=True)       # User/session attribution
    initiated_by = Column(String(100), nullable=True)       # Who triggered this action

    # Timestamps
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vulnerability = relationship("Vulnerability", back_populates="evidence_records")
    scan = relationship("Scan", back_populates="evidence_records")


class LineageEvent(Base):
    """
    Lineage event tracking: records every stage a finding passes through,
    from initial discovery to validation to report inclusion.
    Enables full traceability for compliance and analyst review.
    """
    __tablename__ = "lineage_events"

    id = Column(Integer, primary_key=True, index=True)
    lineage_id = Column(String(100), unique=True, index=True, nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=True)
    evidence_id = Column(Integer, ForeignKey("evidence_records.id", ondelete="SET NULL"), nullable=True)

    # Lineage stage
    stage = Column(String(50), nullable=False, index=True)  # discovered, rule_selected, payload_bound, executed, validated, reported
    previous_stage = Column(String(50), nullable=True)

    # Decision explanation (deterministic rule traceability)
    agent_name = Column(String(100), nullable=True)         # Which agent/component acted
    rule_id = Column(String(100), nullable=True)            # YAML rule file reference
    rule_version = Column(String(50), nullable=True)        # Rule version tag
    decision_reason = Column(Text, nullable=True)           # Why this test/payload was selected
    confidence_at_stage = Column(Float, nullable=True)

    # Input/output summary for this stage
    input_summary = Column(JSON, nullable=True)
    output_summary = Column(JSON, nullable=True)

    # Timestamps
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    scan = relationship("Scan", back_populates="lineage_events")
    vulnerability = relationship("Vulnerability", back_populates="lineage_events")


class CorrelationGroup(Base):
    """
    Groups related findings together for deduplication and exploit-chain detection.
    Reduces noise by showing analysts one 'root cause' with multiple affected instances.
    """
    __tablename__ = "correlation_groups"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String(100), unique=True, index=True, nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)

    # Group metadata
    group_type = Column(String(50), nullable=False, index=True)  # duplicate, related, exploit_chain
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Root cause analysis
    root_cause = Column(Text, nullable=True)
    root_vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id", ondelete="SET NULL"), nullable=True)

    # Affected instances (JSON list of vulnerability IDs)
    member_vulnerability_ids = Column(JSON, nullable=False, default=list)
    member_count = Column(Integer, default=0)

    # Severity roll-up
    highest_severity = Column(String(20), nullable=True)
    combined_cvss = Column(Float, nullable=True)

    # Chain analysis (for exploit_chain type)
    chain_steps = Column(JSON, nullable=True)  # Ordered list of vuln IDs forming the chain
    chain_impact = Column(Text, nullable=True)

    # Status
    is_reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    scan = relationship("Scan", back_populates="correlation_groups")


class AuditLog(Base):
    """
    Immutable audit trail for all security-relevant actions.
    Covers scans, findings, evidence access, report generation,
    and policy changes for compliance (SOC2, 21 CFR Part 11).
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(100), unique=True, index=True, nullable=False)

    # Action classification
    action = Column(String(100), nullable=False, index=True)  # scan_created, finding_validated, evidence_accessed, report_generated, policy_changed
    category = Column(String(50), nullable=False, index=True)  # scan, finding, evidence, report, governance, system

    # Actor
    user_id = Column(String(100), nullable=True)
    user_role = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Target resource
    resource_type = Column(String(50), nullable=True)  # scan, vulnerability, evidence, report
    resource_id = Column(String(100), nullable=True)

    # Action details
    details = Column(JSON, nullable=True)
    previous_state = Column(JSON, nullable=True)  # For state changes
    new_state = Column(JSON, nullable=True)

    # Policy context
    policy_id = Column(String(100), nullable=True)
    scope_context = Column(JSON, nullable=True)  # Target scope at time of action

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Immutability: hash of the record for tamper detection
    record_hash = Column(String(64), nullable=True)

    # Timestamp (never editable)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())


class ScanPolicy(Base):
    """
    Governance policy defining what targets, actions, and test families
    are authorized for a given scan. Enforces scope boundaries and
    role-based access controls.
    """
    __tablename__ = "scan_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String(100), unique=True, index=True, nullable=False)

    # Policy metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)

    # Scope enforcement
    allowed_targets = Column(JSON, nullable=True)    # List of authorized target URLs/domains
    excluded_paths = Column(JSON, nullable=True)     # Paths to never test
    allowed_methods = Column(JSON, nullable=True)    # HTTP methods allowed

    # Test family controls
    allowed_test_families = Column(JSON, nullable=True)  # OWASP categories to test
    blocked_test_families = Column(JSON, nullable=True)
    max_payloads_per_test = Column(Integer, default=50)

    # Safety controls
    max_requests_per_second = Column(Integer, default=10)
    max_concurrent_requests = Column(Integer, default=5)
    request_timeout_seconds = Column(Integer, default=30)
    block_destructive = Column(Boolean, default=True)

    # SLA tracking
    sla_critical_hours = Column(Integer, default=24)    # Hours to resolve critical
    sla_high_hours = Column(Integer, default=72)
    sla_medium_hours = Column(Integer, default=168)     # 7 days
    sla_low_hours = Column(Integer, default=720)        # 30 days

    # Compliance mappings
    compliance_frameworks = Column(JSON, nullable=True)  # ["OWASP", "PCI-DSS", "SOC2", "NIST"]

    # Role-based access
    created_by = Column(String(100), nullable=True)
    authorized_users = Column(JSON, nullable=True)   # Users allowed to run scans under this policy
    authorized_roles = Column(JSON, nullable=True)   # Roles allowed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
