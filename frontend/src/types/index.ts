export type ScanStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'

export interface Scan {
  id: number
  scan_id: string
  target_url: string
  scan_type: string
  status: ScanStatus
  progress_percentage: number
  current_phase: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  total_findings: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
}

export interface PhaseSummaryResponse {
  scan_id: string
  status: string
  current_phase: string | null
  started_at: string | null
  completed_at: string | null
  phase_summary: Record<string, {
    window?: string
    status?: string
    [key: string]: any
  }>
}

export interface ScanLogResponse {
  scan_id: string
  status: string
  current_phase: string | null
  source: string
  lines: string[]
  line_count: number
  note?: string
}

export interface Vulnerability {
  id: number
  scan_id: number
  title: string
  description: string
  severity: Severity
  confidence: number
  owasp_category: string
  cwe_id: string | null
  cvss_score: number | null
  affected_parameter: string | null
  vulnerability_type: string | null
  status: string | null
  is_validated: boolean
  is_false_positive: boolean
  request_payload: string | null
  response_evidence: string | null
  poc_curl_command: string | null
  remediation: string | null
  llm_explanation: string | null
  llm_business_impact: string | null
  llm_remediation: string | null
  llm_evidence: string | null
  llm_poc: string | null
  endpoint_url: string | null
  endpoint_method: string | null
  detected_at: string
}

export interface Report {
  id: number
  scan_id: number
  report_id: string
  report_type: string
  file_path: string | null
  generated_at: string
  file_size: number | null
}

export interface DashboardStats {
  total_scans: number
  active_scans: number
  completed_scans: number
  total_vulnerabilities: number
  critical_vulnerabilities: number
  high_vulnerabilities: number
  medium_vulnerabilities: number
  low_vulnerabilities: number
  recent_scans: Scan[]
}

export interface SystemStatus {
  timestamp: string
  llm: {
    enabled: boolean
    healthy: boolean
    base_url: string
    model: string
    model_loaded: boolean
    error: string | null
  }
  services: {
    redis_enabled: boolean
    neo4j_enabled: boolean
    minio_enabled: boolean
  }
}

export interface CreateScanInput {
  target_url: string
  scan_type?: string
  scope_config?: Record<string, any>
  test_config?: Record<string, any>
}

export interface Endpoint {
  id: number
  scan_id: number
  url: string
  method: string
  parameters?: Record<string, any>
  headers?: Record<string, any>
  endpoint_type?: string
  discovery_method?: string
  requires_auth?: boolean
  discovered_at: string
}

// ────────────────────────────────────────────────────────
// Evidence Types
// ────────────────────────────────────────────────────────

export interface EvidenceRecord {
  id: number
  evidence_id: string
  vulnerability_id: number | null
  scan_id: number
  evidence_type: string
  http_method: string | null
  request_url: string | null
  request_headers: Record<string, any> | null
  request_body: string | null
  response_status_code: number | null
  response_headers: Record<string, any> | null
  response_body: string | null
  response_time_ms: number | null
  storage_uri: string | null
  screenshot_uri: string | null
  har_uri: string | null
  tool_name: string | null
  tool_version: string | null
  payload_id: string | null
  payload_value: string | null
  phase: string | null
  is_baseline: boolean
  initiated_by: string | null
  captured_at: string
}

export interface EvidencePair {
  vulnerability_id: number
  phase: string
  baseline: EvidenceRecord | null
  attack: EvidenceRecord | null
  has_comparison: boolean
}

// ────────────────────────────────────────────────────────
// Lineage Types
// ────────────────────────────────────────────────────────

export interface LineageEvent {
  id: number
  lineage_id: string
  scan_id: number
  vulnerability_id: number | null
  evidence_id: number | null
  stage: string
  previous_stage: string | null
  agent_name: string | null
  rule_id: string | null
  rule_version: string | null
  decision_reason: string | null
  confidence_at_stage: number | null
  input_summary: Record<string, any> | null
  output_summary: Record<string, any> | null
  occurred_at: string
}

export interface FindingLineageChain {
  vulnerability_id: number
  title: string
  severity: string
  lineage: LineageEvent[]
  evidence: EvidenceRecord[]
  related_findings: number[]
  correlation_group_id: string | null
}

// ────────────────────────────────────────────────────────
// Correlation Types
// ────────────────────────────────────────────────────────

export interface CorrelationGroup {
  id: number
  correlation_id: string
  scan_id: number
  group_type: 'duplicate' | 'related' | 'exploit_chain'
  title: string
  description: string | null
  root_cause: string | null
  root_vulnerability_id: number | null
  member_vulnerability_ids: number[]
  member_count: number
  highest_severity: string | null
  combined_cvss: number | null
  chain_steps: number[] | null
  chain_impact: string | null
  is_reviewed: boolean
  reviewed_by: string | null
  reviewed_at: string | null
  created_at: string
}

// ────────────────────────────────────────────────────────
// Audit Types
// ────────────────────────────────────────────────────────

export interface AuditLogEntry {
  id: number
  audit_id: string
  action: string
  category: string
  user_id: string | null
  user_role: string | null
  ip_address: string | null
  resource_type: string | null
  resource_id: string | null
  details: Record<string, any> | null
  success: boolean
  error_message: string | null
  occurred_at: string
}

export interface AuditStats {
  period_days: number
  total_entries: number
  by_category: Record<string, number>
  top_actions: Record<string, number>
  failures: number
  success_rate: number
}

// ────────────────────────────────────────────────────────
// Governance / Policy Types
// ────────────────────────────────────────────────────────

export interface ScanPolicy {
  id: number
  policy_id: string
  name: string
  description: string | null
  version: string
  is_active: boolean
  allowed_targets: string[] | null
  excluded_paths: string[] | null
  allowed_methods: string[] | null
  allowed_test_families: string[] | null
  blocked_test_families: string[] | null
  max_payloads_per_test: number
  max_requests_per_second: number
  block_destructive: boolean
  sla_critical_hours: number
  sla_high_hours: number
  sla_medium_hours: number
  sla_low_hours: number
  compliance_frameworks: string[] | null
  created_at: string
}

export interface TargetValidation {
  target_url: string
  policy_id: string
  authorized: boolean
  reason: string
}
