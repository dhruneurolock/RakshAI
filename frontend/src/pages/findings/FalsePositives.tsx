import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { vulnerabilitiesAPI } from '@/services/endpoints'
import { Ban, Search, AlertTriangle } from 'lucide-react'
import type { Vulnerability } from '@/types'

export default function FalsePositives() {
  const navigate = useNavigate()

  const { data: vulnerabilities = [], isLoading } = useQuery({
    queryKey: ['vulnerabilities'],
    queryFn: () => vulnerabilitiesAPI.list(),
  })

  const falsePositives = useMemo(() => {
    return (vulnerabilities as Vulnerability[]).filter(
      (v) => (v.status ?? '').toUpperCase() === 'FALSE_POSITIVE'
    )
  }, [vulnerabilities])

  const validatedCount = (vulnerabilities as Vulnerability[]).filter(
    (v) => (v.status ?? (v.is_validated ? 'VALIDATED' : '')).toUpperCase() === 'VALIDATED'
  ).length

  const totalCount = (vulnerabilities as Vulnerability[]).length
  const fpRate = totalCount > 0 ? Math.round((falsePositives.length / totalCount) * 100) : 0

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-500">
          <Ban className="w-5 h-5 animate-pulse" />
          <span>Loading false positives...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Review and manage findings marked as false positives
      </p>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Total Findings</p>
          <p className="text-3xl font-bold text-slate-900 mt-1">{totalCount}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">False Positives</p>
          <p className="text-3xl font-bold text-red-600 mt-1">{falsePositives.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">Validated</p>
          <p className="text-3xl font-bold text-emerald-600 mt-1">{validatedCount}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <p className="text-sm text-slate-500">FP Rate</p>
          <p className="text-3xl font-bold text-amber-600 mt-1">{fpRate}%</p>
        </div>
      </div>

      {/* False Positives Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900">False Positive Findings</h3>
          <p className="text-sm text-slate-500 mt-0.5">{falsePositives.length} findings marked as false positive</p>
        </div>

        {falsePositives.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <Ban className="w-10 h-10 mb-3 opacity-50" />
            <p className="font-medium">No False Positives</p>
            <p className="text-sm mt-1">All findings are genuine — great validation accuracy!</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-xs uppercase text-slate-500">
                <th className="px-6 py-3 text-left font-medium">Severity</th>
                <th className="px-6 py-3 text-left font-medium">Finding</th>
                <th className="px-6 py-3 text-left font-medium">Endpoint</th>
                <th className="px-6 py-3 text-left font-medium">OWASP</th>
                <th className="px-6 py-3 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {falsePositives.map((vuln) => (
                <tr
                  key={vuln.id}
                  onClick={() => navigate(`/vulnerabilities/${vuln.id}`)}
                  className="hover:bg-red-50/40 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold capitalize ${
                      vuln.severity === 'critical' ? 'bg-red-600 text-white' :
                      vuln.severity === 'high' ? 'bg-orange-500 text-white' :
                      vuln.severity === 'medium' ? 'bg-amber-500 text-white' : 'bg-emerald-600 text-white'
                    }`}>
                      {vuln.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-slate-900">{vuln.title}</td>
                  <td className="px-6 py-4">
                    <code className="text-xs text-blue-600 font-mono">{vuln.endpoint_url || '/*'}</code>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{vuln.owasp_category}</td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 border border-red-200">
                      False Positive
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
