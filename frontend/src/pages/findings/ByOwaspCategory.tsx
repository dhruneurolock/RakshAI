import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { vulnerabilitiesAPI } from '@/services/endpoints'
import { ShieldAlert, ChevronRight } from 'lucide-react'
import type { Vulnerability } from '@/types'

const OWASP_CATEGORIES = [
  { id: 'A01', name: 'Broken Access Control', color: 'bg-red-500' },
  { id: 'A02', name: 'Cryptographic Failures', color: 'bg-orange-500' },
  { id: 'A03', name: 'Injection', color: 'bg-amber-500' },
  { id: 'A04', name: 'Insecure Design', color: 'bg-yellow-500' },
  { id: 'A05', name: 'Security Misconfiguration', color: 'bg-lime-500' },
  { id: 'A06', name: 'Vulnerable Components', color: 'bg-emerald-500' },
  { id: 'A07', name: 'Authentication Failures', color: 'bg-teal-500' },
  { id: 'A08', name: 'Software & Data Integrity', color: 'bg-cyan-500' },
  { id: 'A09', name: 'Logging Failures', color: 'bg-blue-500' },
  { id: 'A10', name: 'SSRF', color: 'bg-violet-500' },
]

function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-amber-500 text-white',
    low: 'bg-emerald-600 text-white',
    info: 'bg-blue-600 text-white',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold capitalize ${map[severity] ?? 'bg-slate-600 text-white'}`}>
      {severity}
    </span>
  )
}

export default function ByOwaspCategory() {
  const navigate = useNavigate()

  const { data: vulnerabilities = [], isLoading } = useQuery({
    queryKey: ['vulnerabilities'],
    queryFn: () => vulnerabilitiesAPI.list(),
  })

  const grouped = useMemo(() => {
    const map = new Map<string, Vulnerability[]>()
    ;(vulnerabilities as Vulnerability[]).forEach((v) => {
      const key = v.owasp_category?.slice(0, 3).toUpperCase() || 'UNK'
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(v)
    })
    return map
  }, [vulnerabilities])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-500">
          <ShieldAlert className="w-5 h-5 animate-pulse" />
          <span>Loading findings by OWASP category...</span>
        </div>
      </div>
    )
  }

  const totalFindings = (vulnerabilities as Vulnerability[]).length
  const maxCount = Math.max(...OWASP_CATEGORIES.map((c) => grouped.get(c.id)?.length || 0), 1)

  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Vulnerabilities organized by OWASP Top 10:2025 categories
      </p>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {OWASP_CATEGORIES.map((cat) => {
          const count = grouped.get(cat.id)?.length || 0
          return (
            <div key={cat.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${cat.color}`} />
                <span className="text-xs font-semibold text-slate-600">{cat.id}</span>
              </div>
              <p className="text-2xl font-bold text-slate-900">{count}</p>
              <p className="text-xs text-slate-500 mt-0.5 truncate">{cat.name}</p>
            </div>
          )
        })}
      </div>

      {/* Distribution Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900 mb-1">Category Distribution</h3>
        <p className="text-sm text-slate-500 mb-5">{totalFindings} total findings across OWASP categories</p>
        <div className="space-y-3">
          {OWASP_CATEGORIES.map((cat) => {
            const count = grouped.get(cat.id)?.length || 0
            return (
              <div key={cat.id} className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-600 w-8">{cat.id}</span>
                <div className="flex-1">
                  <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${cat.color} transition-all duration-700`}
                      style={{ width: `${(count / maxCount) * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm font-bold text-slate-900 w-8 text-right">{count}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Category Sections */}
      {OWASP_CATEGORIES.map((cat) => {
        const findings = grouped.get(cat.id) || []
        if (findings.length === 0) return null
        return (
          <div key={cat.id} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${cat.color}`} />
              <h3 className="font-semibold text-slate-900">{cat.id} — {cat.name}</h3>
              <span className="text-sm text-slate-500">({findings.length})</span>
            </div>
            <div className="divide-y divide-slate-100">
              {findings.slice(0, 5).map((vuln) => (
                <div
                  key={vuln.id}
                  onClick={() => navigate(`/vulnerabilities/${vuln.id}`)}
                  className="flex items-center justify-between px-6 py-3 hover:bg-cyan-50/40 cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <SeverityBadge severity={vuln.severity} />
                    <span className="text-sm font-medium text-slate-800">{vuln.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <code className="text-xs text-blue-600 font-mono">{vuln.endpoint_url || '/*'}</code>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </div>
                </div>
              ))}
              {findings.length > 5 && (
                <div className="px-6 py-3 text-sm text-cyan-600 font-medium">
                  +{findings.length - 5} more findings in this category
                </div>
              )}
            </div>
          </div>
        )
      })}

      {totalFindings === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
          <ShieldAlert className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-700 mb-2">No Findings Yet</h3>
          <p className="text-sm text-slate-500">Run a scan to discover vulnerabilities organized by OWASP categories.</p>
        </div>
      )}
    </div>
  )
}
