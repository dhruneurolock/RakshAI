import { useQuery } from '@tanstack/react-query'
import { dashboardAPI, scansAPI } from '@/services/endpoints'
import { Gauge, Shield, AlertTriangle, TrendingUp, TrendingDown, Target } from 'lucide-react'

function calculateRiskScore(stats: {
  critical_vulnerabilities: number
  high_vulnerabilities: number
  medium_vulnerabilities: number
  low_vulnerabilities: number
  total_vulnerabilities: number
}) {
  if (stats.total_vulnerabilities === 0) return 0
  const weighted =
    stats.critical_vulnerabilities * 10 +
    stats.high_vulnerabilities * 7 +
    stats.medium_vulnerabilities * 4 +
    stats.low_vulnerabilities * 1
  return Math.min(Math.round((weighted / (stats.total_vulnerabilities * 10)) * 100), 100)
}

function getRiskColor(score: number) {
  if (score >= 75) return { bg: 'bg-red-500', text: 'text-red-600', ring: 'ring-red-200', label: 'Critical Risk' }
  if (score >= 50) return { bg: 'bg-orange-500', text: 'text-orange-600', ring: 'ring-orange-200', label: 'High Risk' }
  if (score >= 25) return { bg: 'bg-amber-500', text: 'text-amber-600', ring: 'ring-amber-200', label: 'Medium Risk' }
  return { bg: 'bg-emerald-500', text: 'text-emerald-600', ring: 'ring-emerald-200', label: 'Low Risk' }
}

export default function RiskScore() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardAPI.stats,
    retry: 1,
  })

  const { data: scans, isLoading: scansLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: scansAPI.list,
    retry: 1,
  })

  const isLoading = statsLoading || scansLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-500">
          <Gauge className="w-5 h-5 animate-pulse" />
          <span>Calculating risk scores...</span>
        </div>
      </div>
    )
  }

  const overallScore = stats ? calculateRiskScore(stats) : 0
  const riskInfo = getRiskColor(overallScore)

  // Per-target risk scores
  const completedScans = scans?.filter((s) => s.status === 'completed') || []
  const targetScores = completedScans.map((scan) => {
    const critical = scan.critical_count || 0
    const high = scan.high_count || 0
    const medium = scan.medium_count || 0
    const low = scan.low_count || 0
    const total = scan.total_findings || 1
    const weighted = critical * 10 + high * 7 + medium * 4 + low * 1
    const score = Math.min(Math.round((weighted / (total * 10)) * 100), 100)
    return { ...scan, score, riskInfo: getRiskColor(score) }
  })

  const riskFactors = [
    {
      label: 'Critical Vulnerabilities',
      value: stats?.critical_vulnerabilities || 0,
      weight: '10x',
      icon: AlertTriangle,
      color: 'text-red-600 bg-red-50',
    },
    {
      label: 'High Vulnerabilities',
      value: stats?.high_vulnerabilities || 0,
      weight: '7x',
      icon: AlertTriangle,
      color: 'text-orange-600 bg-orange-50',
    },
    {
      label: 'Medium Vulnerabilities',
      value: stats?.medium_vulnerabilities || 0,
      weight: '4x',
      icon: Shield,
      color: 'text-amber-600 bg-amber-50',
    },
    {
      label: 'Low Vulnerabilities',
      value: stats?.low_vulnerabilities || 0,
      weight: '1x',
      icon: Shield,
      color: 'text-emerald-600 bg-emerald-50',
    },
  ]

  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Aggregated risk score calculated from vulnerability severity distribution
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overall Risk Score */}
        <div className="lg:col-span-1 bg-white rounded-xl border border-slate-200 p-8 shadow-sm flex flex-col items-center justify-center">
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-6">Overall Risk Score</h3>
          <div className={`relative w-44 h-44 rounded-full ring-8 ${riskInfo.ring} flex items-center justify-center mb-4`}>
            <svg className="w-44 h-44 absolute" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#e2e8f0" strokeWidth="6" />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="6"
                strokeDasharray={`${overallScore * 2.83} 283`}
                strokeDashoffset="0"
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
                className={riskInfo.text}
              />
            </svg>
            <div className="text-center z-10">
              <span className={`text-5xl font-bold ${riskInfo.text}`}>{overallScore}</span>
              <span className="text-slate-400 text-lg">/100</span>
            </div>
          </div>
          <div className={`px-4 py-1.5 rounded-full text-sm font-semibold ${riskInfo.text} bg-opacity-10 ${riskInfo.bg} bg-opacity-10`}>
            {riskInfo.label}
          </div>
          <p className="text-sm text-slate-500 mt-3 text-center">
            Based on {stats?.total_vulnerabilities || 0} findings across {completedScans.length} scans
          </p>
        </div>

        {/* Risk Factors */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-1">Risk Factors</h3>
            <p className="text-sm text-slate-500 mb-5">Weighted contribution to overall risk score</p>
            <div className="space-y-4">
              {riskFactors.map((factor) => {
                const Icon = factor.icon
                return (
                  <div key={factor.label} className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${factor.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-slate-700">{factor.label}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-slate-400">Weight: {factor.weight}</span>
                          <span className="text-sm font-bold text-slate-900">{factor.value}</span>
                        </div>
                      </div>
                      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${
                            factor.weight === '10x' ? 'bg-red-400' :
                            factor.weight === '7x' ? 'bg-orange-400' :
                            factor.weight === '4x' ? 'bg-amber-400' : 'bg-emerald-400'
                          }`}
                          style={{ width: `${Math.min((factor.value / Math.max(stats?.total_vulnerabilities || 1, 1)) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Per-Target Risk Scores */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-1">Risk by Target</h3>
            <p className="text-sm text-slate-500 mb-4">Individual risk scores per scanned target</p>
            <div className="space-y-3">
              {targetScores.length > 0 ? (
                targetScores.slice(0, 8).map((scan) => (
                  <div key={scan.scan_id} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
                    <div className="flex items-center gap-3">
                      <Target className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-medium text-slate-700 truncate max-w-xs">{scan.target_url}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-slate-500">{scan.total_findings} findings</span>
                      <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold ${scan.riskInfo.text}`}>
                        {scan.score >= 50 ? (
                          <TrendingUp className="w-3.5 h-3.5" />
                        ) : (
                          <TrendingDown className="w-3.5 h-3.5" />
                        )}
                        {scan.score}/100
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-slate-400">
                  <Gauge className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No completed scans for risk assessment</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
