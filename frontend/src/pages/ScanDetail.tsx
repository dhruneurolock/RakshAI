import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { scansAPI, vulnerabilitiesAPI } from '@/services/endpoints'
import { ArrowLeft, Clock, CheckCircle, XCircle, Loader2, AlertTriangle, ShieldCheck } from 'lucide-react'
import type { Vulnerability } from '@/types'

function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: 'bg-red-600 text-white',
    high:     'bg-orange-500 text-white',
    medium:   'bg-amber-500 text-white',
    low:      'bg-green-600 text-white',
    info:     'bg-blue-600 text-white',
  }
  return (
    <span className={`px-2.5 py-0.5 rounded text-xs font-semibold capitalize ${map[severity] ?? 'bg-gray-600 text-white'}`}>
      {severity}
    </span>
  )
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircle className="w-5 h-5 text-green-500" />
  if (status === 'running')   return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
  if (status === 'failed')    return <XCircle className="w-5 h-5 text-red-500" />
  return <Clock className="w-5 h-5 text-gray-400" />
}

function SeverityCard({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className={`rounded-lg border p-4 text-center ${color}`}>
      <div className="text-2xl font-bold">{count}</div>
      <div className="text-sm font-medium mt-1">{label}</div>
    </div>
  )
}

function fmtDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function elapsed(start: string | null, end: string | null, currentTime: number = Date.now()) {
  if (!start) return '—'
  const ms = new Date(end ?? currentTime).getTime() - new Date(start).getTime()
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  const mins = Math.floor(s / 60)
  const secs = s % 60
  return `${mins}m ${secs}s`
}

export default function ScanDetail() {
  const { scanId } = useParams<{ scanId: string }>()
  const navigate = useNavigate()
  const [currentTime, setCurrentTime] = useState(Date.now())
  const logContainerRef = useRef<HTMLDivElement | null>(null)

  const { data: scan, isLoading: scanLoading } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => scansAPI.get(scanId!),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'running' || status === 'pending' ? 3000 : false
    },
    enabled: !!scanId,
  })

  // Update current time every second for real-time elapsed duration
  useEffect(() => {
    if (scan?.status === 'running' || scan?.status === 'pending') {
      const timer = setInterval(() => {
        setCurrentTime(Date.now())
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [scan?.status])

  const { data: vulns = [], isLoading: vulnsLoading } = useQuery({
    queryKey: ['vulnerabilities', scan?.id],
    queryFn: () => vulnerabilitiesAPI.list({ scan_id: scan!.id }),
    enabled: !!scan?.id,
  })

  const { data: phaseSummary } = useQuery({
    queryKey: ['scan-phase-summary', scanId],
    queryFn: () => scansAPI.getPhaseSummary(scanId!),
    enabled: !!scanId,
    refetchInterval: (query) => {
      const phase = query.state.data?.current_phase
      return phase && phase !== 'completed' ? 3000 : false
    },
  })

  const { data: logs } = useQuery({
    queryKey: ['scan-logs', scanId],
    queryFn: () => scansAPI.getLogs(scanId!, 160, true),
    enabled: !!scanId,
    refetchInterval: () => {
      if (scan?.status === 'running' || scan?.status === 'pending') {
        return 2000
      }
      return 5000
    },
  })

  useEffect(() => {
    if (!logContainerRef.current) {
      return
    }
    logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
  }, [logs?.lines])

  if (scanLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  if (!scan) {
    return (
      <div className="text-center py-16 text-gray-500">
        <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>Scan not found.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/scans')}
          className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold text-gray-900 truncate">{scan.target_url}</h1>
          <p className="text-sm text-gray-500 capitalize">{scan.scan_type} scan · {scan.scan_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusIcon status={scan.status} />
          <span className={`text-sm font-medium capitalize ${
            scan.status === 'completed' ? 'text-green-600' :
            scan.status === 'running'   ? 'text-blue-600'  :
            scan.status === 'failed'    ? 'text-red-600'   : 'text-gray-500'
          }`}>{scan.status}</span>
        </div>
      </div>

      {/* Progress (if running) */}
      {scan.status === 'running' && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{scan.current_phase ?? 'Processing…'}</span>
            <span>{scan.progress_percentage}%</span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${scan.progress_percentage}%` }}
            />
          </div>
        </div>
      )}
      {/* Meta cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Started</p>
          <p className="text-sm font-medium text-gray-800 mt-1">{fmtDate(scan.started_at)}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Completed</p>
          <p className="text-sm font-medium text-gray-800 mt-1">{fmtDate(scan.completed_at)}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Duration</p>
          <p className="text-sm font-medium text-gray-800 mt-1">{elapsed(scan.started_at, scan.completed_at, currentTime)}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide">Total Findings</p>
          <p className="text-sm font-medium text-gray-800 mt-1">{scan.total_findings}</p>
        </div>
      </div>

      {/* Phase Summary */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Pipeline Phases</h2>
        </div>
        <div className="p-4 space-y-3">
          {Object.entries(phaseSummary?.phase_summary ?? {}).length === 0 ? (
            <p className="text-sm text-gray-500">Phase summary will appear as the scan progresses.</p>
          ) : (
            Object.entries(phaseSummary?.phase_summary ?? {}).map(([phaseKey, details]) => (
              <div key={phaseKey} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900 capitalize">{phaseKey.replace('_', ' ')}</p>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${details?.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                    {details?.status ?? 'running'}
                  </span>
                </div>
                {details?.window && <p className="text-xs text-gray-500 mt-1">{details.window}</p>}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Live Backend Logs */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Live Backend Logs</h2>
          <span className="text-xs text-gray-500">
            {scan.status === 'running' || scan.status === 'pending' ? 'Auto-refresh: 2s' : 'Auto-refresh: 5s'}
          </span>
        </div>
        <div className="p-4 space-y-2">
          {logs?.note && (
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
              {logs.note}
            </p>
          )}
          <p className="text-xs text-gray-500">
            Source: {logs?.source ?? 'unknown'} · Lines: {logs?.line_count ?? 0}
          </p>
          <div
            ref={logContainerRef}
            className="h-64 overflow-auto rounded-lg bg-gray-950 text-green-300 border border-gray-800 p-3"
          >
            {logs?.lines && logs.lines.length > 0 ? (
              <pre className="text-xs leading-5 whitespace-pre-wrap break-words font-mono">
                {logs.lines.join('\n')}
              </pre>
            ) : (
              <p className="text-xs text-gray-400 font-mono">No scan-specific logs yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Severity breakdown */}
      <div className="grid grid-cols-5 gap-3">
        <SeverityCard label="Critical" count={scan.critical_count} color="border-red-200 bg-red-50 text-red-700" />
        <SeverityCard label="High"     count={scan.high_count}     color="border-orange-200 bg-orange-50 text-orange-700" />
        <SeverityCard label="Medium"   count={scan.medium_count}   color="border-amber-200 bg-amber-50 text-amber-700" />
        <SeverityCard label="Low"      count={scan.low_count}      color="border-green-200 bg-green-50 text-green-700" />
        <SeverityCard label="Info"     count={scan.info_count}     color="border-blue-200 bg-blue-50 text-blue-700" />
      </div>

      {/* Findings table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">Findings ({vulns.length})</h2>
        </div>

        {vulnsLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          </div>
        ) : vulns.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <ShieldCheck className="w-10 h-10 mx-auto mb-2 text-gray-300" />
            <p>No findings detected.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">OWASP</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Endpoint</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {vulns.map((v: Vulnerability) => (
                  <tr
                    key={v.id}
                    onClick={() => navigate(`/vulnerabilities/${v.id}`)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-gray-900">{v.title}</span>
                    </td>
                    <td className="px-4 py-3">
                      <SeverityBadge severity={v.severity} />
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">{v.vulnerability_type ?? '—'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">{v.owasp_category ?? '—'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${v.confidence >= 0.9 ? 'bg-green-500' : v.confidence >= 0.7 ? 'bg-amber-400' : 'bg-red-500'}`}
                            style={{ width: `${Math.round(v.confidence * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{Math.round(v.confidence * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-500 font-mono truncate max-w-[180px] block">{v.endpoint_url ?? '—'}</span>
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
