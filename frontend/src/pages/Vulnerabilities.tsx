import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { scansAPI, vulnerabilitiesAPI } from '@/services/endpoints'
import { Search, ChevronDown } from 'lucide-react'
import type { Scan, Vulnerability } from '@/types'

// ── Severity badge ────────────────────────────────────────────────────────────
function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: 'bg-red-600 text-white',
    high:     'bg-orange-500 text-white',
    medium:   'bg-amber-500 text-white',
    low:      'bg-green-600 text-white',
    info:     'bg-blue-600 text-white',
  }
  return (
    <span className={`px-3 py-1 rounded text-xs font-semibold capitalize min-w-[72px] inline-block text-center ${map[severity] ?? 'bg-gray-600 text-white'}`}>
      {severity}
    </span>
  )
}

// ── Status badge ──────────────────────────────────────────────────────────────
function StatusBadge({ status, isValidated }: { status: string | null; isValidated: boolean }) {
  const raw = (status ?? (isValidated ? 'VALIDATED' : 'UNVALIDATED')).toUpperCase()

  if (raw === 'VALIDATED' || raw === 'CONFIRMED') {
    const isConfirmed = raw === 'CONFIRMED'
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${isConfirmed ? 'border-green-500 text-green-700 bg-green-50' : 'border-amber-400 text-amber-700 bg-amber-50'}`}>
        {isConfirmed ? 'Confirmed' : 'Validated'}
      </span>
    )
  }
  if (raw === 'FALSE_POSITIVE') {
    return <span className="px-3 py-1 rounded-full text-xs font-medium border border-red-400 text-red-700 bg-red-50">False Positive</span>
  }
  // Raw / Unvalidated
  return <span className="px-3 py-1 rounded-full text-xs font-medium border border-gray-400 text-gray-600 bg-gray-50">Raw</span>
}

// ── Confidence bar ────────────────────────────────────────────────────────────
function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const color = pct >= 90 ? 'bg-green-500' : pct >= 70 ? 'bg-amber-400' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm text-gray-600 w-8 text-right">{pct}%</span>
    </div>
  )
}

// ── Select dropdown ───────────────────────────────────────────────────────────
function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="appearance-none bg-white border border-gray-300 text-gray-700 text-sm rounded-lg pl-3 pr-8 py-2 focus:outline-none focus:border-blue-500 cursor-pointer"
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
  )
}

// ── OWASP short label ─────────────────────────────────────────────────────────
const OWASP_LABELS: Record<string, string> = {
  A01: 'A01:2021 - Broken Access Control',
  A02: 'A02:2021 - Cryptographic Failures',
  A03: 'A03:2021 - Injection',
  A04: 'A04:2021 - Insecure Design',
  A05: 'A05:2021 - Security Misconfiguration',
  A06: 'A06:2021 - Vulnerable Components',
  A07: 'A07:2021 - Auth Failures',
  A08: 'A08:2021 - Software & Data Integrity',
  A09: 'A09:2021 - Logging Failures',
  A10: 'A10:2021 - SSRF',
}

function owaspLabel(cat: string) {
  const key = cat?.slice(0, 3).toUpperCase()
  return OWASP_LABELS[key] ?? cat
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Vulnerabilities() {
  const [search, setSearch] = useState('')
  const [targetFilter, setTargetFilter] = useState('All Targets')
  const [severityFilter, setSeverityFilter] = useState('All Severities')
  const [statusFilter, setStatusFilter] = useState('All Statuses')
  const [confidenceFilter, setConfidenceFilter] = useState('All Confidence')
  const navigate = useNavigate()

  const { data: vulnerabilities = [], isLoading } = useQuery({
    queryKey: ['vulnerabilities'],
    queryFn: () => vulnerabilitiesAPI.list(),
    refetchInterval: 10000,
  })

  const { data: scans = [] } = useQuery<Scan[]>({
    queryKey: ['scans'],
    queryFn: () => scansAPI.list(),
    refetchInterval: 10000,
  })

  const scanTargetMap = useMemo(() => {
    return new Map(scans.map((scan) => [scan.id, scan.target_url]))
  }, [scans])

  const targetOptions = useMemo(() => {
    const uniqueTargets = Array.from(
      new Set(scans.map((scan) => scan.target_url).filter(Boolean))
    )
    return ['All Targets', ...uniqueTargets]
  }, [scans])

  const filtered = useMemo(() => {
    return (vulnerabilities as Vulnerability[]).filter(v => {
      const targetUrl = scanTargetMap.get(v.scan_id) ?? ''

      const q = search.toLowerCase()
      const targetUrlLower = targetUrl.toLowerCase()
      if (q && !v.title.toLowerCase().includes(q) && !(v.endpoint_url ?? '').toLowerCase().includes(q) && !v.owasp_category.toLowerCase().includes(q) && !targetUrlLower.includes(q)) return false

      if (targetFilter !== 'All Targets' && targetUrl !== targetFilter) return false

      if (severityFilter !== 'All Severities' && v.severity.toLowerCase() !== severityFilter.toLowerCase()) return false

      if (statusFilter !== 'All Statuses') {
        const raw = (v.status ?? (v.is_validated ? 'VALIDATED' : 'UNVALIDATED')).toUpperCase()
        if (statusFilter === 'Confirmed' && raw !== 'CONFIRMED') return false
        if (statusFilter === 'Validated' && raw !== 'VALIDATED') return false
        if (statusFilter === 'Raw' && raw !== 'UNVALIDATED') return false
      }

      if (confidenceFilter !== 'All Confidence') {
        const pct = v.confidence * 100
        if (confidenceFilter === 'High (≥90%)' && pct < 90) return false
        if (confidenceFilter === 'Medium (70–89%)' && (pct < 70 || pct >= 90)) return false
        if (confidenceFilter === 'Low (<70%)' && pct >= 70) return false
      }

      return true
    })
  }, [vulnerabilities, search, targetFilter, severityFilter, statusFilter, confidenceFilter, scanTargetMap])

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      {/* Header */}
      <p className="text-gray-500 mb-6 text-sm">Detected vulnerabilities and security issues</p>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        {/* Panel header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">All Findings</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {isLoading ? 'Loading…' : `${filtered.length} of ${(vulnerabilities as Vulnerability[]).length} findings`}
          </p>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 flex flex-wrap gap-3 border-b border-gray-200">
          {/* Search */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search findings..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full bg-white border border-gray-300 text-gray-800 text-sm rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-blue-500 placeholder-gray-400"
            />
          </div>

          <Select value={severityFilter} onChange={setSeverityFilter}
            options={['All Severities', 'Critical', 'High', 'Medium', 'Low', 'Info']} />
          <Select value={targetFilter} onChange={setTargetFilter}
            options={targetOptions} />
          <Select value={statusFilter} onChange={setStatusFilter}
            options={['All Statuses', 'Confirmed', 'Validated', 'Raw']} />
          <Select value={confidenceFilter} onChange={setConfidenceFilter}
            options={['All Confidence', 'High (≥90%)', 'Medium (70–89%)', 'Low (<70%)']} />
        </div>

        {/* Table */}
        {isLoading ? (
          <div className="flex items-center justify-center h-48 text-gray-400">Loading findings…</div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
            <Search className="w-8 h-8 opacity-40" />
            <p>No findings match your filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs uppercase text-gray-500 border-b border-gray-200 bg-gray-50">
                  <th className="px-6 py-3 text-left font-medium">Severity</th>
                  <th className="px-6 py-3 text-left font-medium">Vulnerability</th>
                  <th className="px-6 py-3 text-left font-medium">Target</th>
                  <th className="px-6 py-3 text-left font-medium text-blue-600">Endpoint</th>
                  <th className="px-6 py-3 text-left font-medium">Confidence</th>
                  <th className="px-6 py-3 text-left font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filtered.map(vuln => (
                  <tr
                    key={vuln.id}
                    onClick={() => navigate(`/vulnerabilities/${vuln.id}`)}
                    className="hover:bg-blue-50/40 transition-colors cursor-pointer"
                  >
                    {/* Severity */}
                    <td className="px-6 py-4">
                      <SeverityBadge severity={vuln.severity} />
                    </td>

                    {/* Vulnerability name + OWASP */}
                    <td className="px-6 py-4">
                      <p className="text-sm font-semibold text-gray-900">{vuln.title}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{owaspLabel(vuln.owasp_category)}</p>
                    </td>

                    {/* Target */}
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-700 break-all">
                        {scanTargetMap.get(vuln.scan_id) ?? 'N/A'}
                      </span>
                    </td>

                    {/* Endpoint */}
                    <td className="px-6 py-4">
                      <code className="text-sm text-blue-600 font-mono">
                        {vuln.endpoint_url ?? vuln.affected_parameter ?? '/*'}
                      </code>
                    </td>

                    {/* Confidence bar */}
                    <td className="px-6 py-4">
                      <ConfidenceBar value={vuln.confidence} />
                    </td>

                    {/* Status */}
                    <td className="px-6 py-4">
                      <StatusBadge status={vuln.status} isValidated={vuln.is_validated} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
