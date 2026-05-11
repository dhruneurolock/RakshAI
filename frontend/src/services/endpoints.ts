import api from './api'
import type {
  Scan,
  CreateScanInput,
  DashboardStats,
  Vulnerability,
  Report,
  Endpoint,
  PhaseSummaryResponse,
  ScanLogResponse,
  SystemStatus,
  EvidenceRecord,
  EvidencePair,
  FindingLineageChain,
  CorrelationGroup,
  AuditLogEntry,
  AuditStats,
  ScanPolicy,
  TargetValidation,
} from '@/types'

// Scans API
export const scansAPI = {
  list: async (): Promise<Scan[]> => {
    const { data } = await api.get('/scans/')
    return data
  },

  get: async (scanId: string): Promise<Scan> => {
    const { data } = await api.get(`/scans/${scanId}`)
    return data
  },

  create: async (input: CreateScanInput): Promise<Scan> => {
    const { data } = await api.post('/scans/', input)
    return data
  },

  start: async (scanId: string): Promise<void> => {
    await api.post(`/scans/${scanId}/start`)
  },

  stop: async (scanId: string): Promise<void> => {
    await api.post(`/scans/${scanId}/stop`)
  },

  delete: async (scanId: string): Promise<void> => {
    await api.delete(`/scans/${scanId}`)
  },

  executeDetection: async (scanId: string): Promise<void> => {
    await api.post(`/scans/${scanId}/execute`)
  },

  validate: async (scanId: string): Promise<void> => {
    await api.post(`/scans/${scanId}/validate`)
  },

  generateReport: async (scanId: string, reportType: string = 'pdf'): Promise<void> => {
    await api.post(`/scans/${scanId}/generate-report`, null, {
      params: { report_format: reportType },
      timeout: 180000,
    })
  },

  getPhaseSummary: async (scanId: string): Promise<PhaseSummaryResponse> => {
    const { data } = await api.get(`/scans/${scanId}/phase-summary`)
    return data
  },

  getReports: async (scanId: string): Promise<Report[]> => {
    const { data } = await api.get(`/scans/${scanId}/reports`)
    return data
  },

  getLogs: async (scanId: string, limit: number = 120, scanOnly: boolean = true): Promise<ScanLogResponse> => {
    const { data } = await api.get(`/scans/${scanId}/logs`, {
      params: {
        limit,
        scan_only: scanOnly,
      },
    })
    return data
  },
}

// Vulnerabilities API
export const vulnerabilitiesAPI = {
  list: async (params?: { scan_id?: number; severity?: string }): Promise<Vulnerability[]> => {
    const { data } = await api.get('/vulnerabilities/', { params })
    return data
  },

  get: async (vulnId: number): Promise<Vulnerability> => {
    const { data } = await api.get(`/vulnerabilities/${vulnId}`)
    return data
  },

  markFalsePositive: async (vulnId: number, reason: string): Promise<void> => {
    await api.patch(`/vulnerabilities/${vulnId}/mark-false-positive`, { reason })
  },

  generatePoC: async (vulnId: number): Promise<void> => {
    await api.post(`/vulnerabilities/${vulnId}/generate-poc`)
  },

  generateRemediation: async (vulnId: number): Promise<{ remediation?: unknown; remediation_text?: string }> => {
    const { data } = await api.post(`/vulnerabilities/${vulnId}/generate-remediation`)
    return data
  },

  severityStats: async (scanId?: number) => {
    const { data } = await api.get('/vulnerabilities/stats/by-severity', {
      params: { scan_id: scanId }
    })
    return data
  },

  categoryStats: async (scanId?: number) => {
    const { data } = await api.get('/vulnerabilities/stats/by-category', {
      params: { scan_id: scanId }
    })
    return data
  },
}

// Dashboard API
export const dashboardAPI = {
  stats: async (): Promise<DashboardStats> => {
    const { data } = await api.get('/dashboard/stats')
    return data
  },

  activity: async (limit: number = 10) => {
    const { data } = await api.get('/dashboard/activity', { params: { limit } })
    return data
  },

  trends: async (days: number = 30) => {
    const { data } = await api.get('/dashboard/trends', { params: { days } })
    return data
  },

  systemStatus: async (): Promise<SystemStatus> => {
    const { data } = await api.get('/dashboard/system-status')
    return data
  },
}

// Endpoints API
export const endpointsAPI = {
  list: async (params?: { scan_id?: string }): Promise<Endpoint[]> => {
    if (params?.scan_id) {
      const { data } = await api.get(`/scans/${params.scan_id}/endpoints`)
      return data
    }
    return []
  },

  get: async (scanId: string, endpointId: number): Promise<Endpoint> => {
    const { data } = await api.get(`/scans/${scanId}/endpoints/${endpointId}`)
    return data
  },
}

// Reports API
export const reportsAPI = {
  list: async (scanId?: number): Promise<Report[]> => {
    const { data } = await api.get('/reports/', { params: { scan_id: scanId } })
    return data
  },

  get: async (reportId: string): Promise<Report> => {
    const { data } = await api.get(`/reports/${reportId}`)
    return data
  },

  download: async (reportId: string): Promise<Blob> => {
    const { data } = await api.get(`/reports/${reportId}/download`, {
      responseType: 'blob'
    })
    return data
  },

  delete: async (reportId: string): Promise<void> => {
    await api.delete(`/reports/${reportId}`)
  },
}

// ────────────────────────────────────────────────────────
// Evidence API
// ────────────────────────────────────────────────────────

export const evidenceAPI = {
  list: async (params?: {
    scan_id?: number
    vulnerability_id?: number
    evidence_type?: string
  }): Promise<EvidenceRecord[]> => {
    const { data } = await api.get('/evidence/', { params })
    return data
  },

  get: async (evidenceId: string): Promise<EvidenceRecord> => {
    const { data } = await api.get(`/evidence/${evidenceId}`)
    return data
  },

  getBaselineAttackPair: async (
    vulnerabilityId: number,
    phase: string = 'execution'
  ): Promise<EvidencePair> => {
    const { data } = await api.get(`/evidence/vulnerability/${vulnerabilityId}/pair`, {
      params: { phase },
    })
    return data
  },

  getLineageChain: async (vulnerabilityId: number): Promise<FindingLineageChain> => {
    const { data } = await api.get(`/evidence/vulnerability/${vulnerabilityId}/chain`)
    return data
  },

  getScanSummary: async (scanId: number): Promise<{
    scan_id: number
    total_records: number
    by_type: Record<string, number>
    by_phase: Record<string, number>
  }> => {
    const { data } = await api.get(`/evidence/scan/${scanId}/summary`)
    return data
  },
}

// ────────────────────────────────────────────────────────
// Audit API
// ────────────────────────────────────────────────────────

export const auditAPI = {
  list: async (params?: {
    category?: string
    action?: string
    user_id?: string
    resource_type?: string
    resource_id?: string
    since?: string
    skip?: number
    limit?: number
  }): Promise<AuditLogEntry[]> => {
    const { data } = await api.get('/audit/', { params })
    return data
  },

  get: async (auditId: string): Promise<AuditLogEntry> => {
    const { data } = await api.get(`/audit/${auditId}`)
    return data
  },

  verify: async (auditId: string): Promise<{
    audit_id: string
    integrity_valid: boolean
    record_hash: string
    message: string
  }> => {
    const { data } = await api.get(`/audit/${auditId}/verify`)
    return data
  },

  scanTrail: async (scanId: string): Promise<AuditLogEntry[]> => {
    const { data } = await api.get(`/audit/scan/${scanId}/trail`)
    return data
  },

  stats: async (days: number = 30): Promise<AuditStats> => {
    const { data } = await api.get('/audit/stats/summary', { params: { days } })
    return data
  },
}

// ────────────────────────────────────────────────────────
// Governance API
// ────────────────────────────────────────────────────────

export const governanceAPI = {
  listPolicies: async (activeOnly: boolean = true): Promise<ScanPolicy[]> => {
    const { data } = await api.get('/governance/policies', {
      params: { active_only: activeOnly },
    })
    return data
  },

  createPolicy: async (policy: Partial<ScanPolicy>): Promise<ScanPolicy> => {
    const { data } = await api.post('/governance/policies', policy)
    return data
  },

  getPolicy: async (policyId: string): Promise<ScanPolicy> => {
    const { data } = await api.get(`/governance/policies/${policyId}`)
    return data
  },

  updatePolicy: async (policyId: string, updates: Partial<ScanPolicy>): Promise<ScanPolicy> => {
    const { data } = await api.patch(`/governance/policies/${policyId}`, updates)
    return data
  },

  validateTarget: async (policyId: string, targetUrl: string): Promise<TargetValidation> => {
    const { data } = await api.post(`/governance/policies/${policyId}/validate-target`, null, {
      params: { target_url: targetUrl },
    })
    return data
  },

  listCorrelations: async (params?: {
    scan_id?: number
    group_type?: string
  }): Promise<CorrelationGroup[]> => {
    const { data } = await api.get('/governance/correlations', { params })
    return data
  },

  runCorrelation: async (scanId: number): Promise<{
    groups_created: number
    duplicates: number
    related: number
    chains: number
  }> => {
    const { data } = await api.post(`/governance/correlations/scan/${scanId}/run`)
    return data
  },

  reviewCorrelation: async (correlationId: string, reviewedBy: string = 'analyst'): Promise<void> => {
    await api.patch(`/governance/correlations/${correlationId}/review`, null, {
      params: { reviewed_by: reviewedBy },
    })
  },
}
