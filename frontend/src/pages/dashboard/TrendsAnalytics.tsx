import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { dashboardAPI, scansAPI } from '@/services/endpoints'
import { TrendingUp, TrendingDown, BarChart3, Activity, Calendar, ArrowUpRight, ArrowDownRight } from 'lucide-react'

export default function TrendsAnalytics() {
  const [timeRange, setTimeRange] = useState(30)

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardAPI.stats,
    retry: 1,
  })

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['dashboard-trends', timeRange],
    queryFn: () => dashboardAPI.trends(timeRange),
    retry: 1,
  })

  const { data: scans } = useQuery({
    queryKey: ['scans'],
    queryFn: scansAPI.list,
    retry: 1,
  })

  const isLoading = statsLoading || trendsLoading

  // Compute scan frequency stats
  const completedScans = scans?.filter((s) => s.status === 'completed') || []
  const failedScans = scans?.filter((s) => s.status === 'failed') || []
  const totalScans = scans?.length || 0

  // Severity distribution for chart-like display
  const severityData = [
    { label: 'Critical', count: stats?.critical_vulnerabilities || 0, color: 'bg-red-500', barColor: 'bg-red-400' },
    { label: 'High', count: stats?.high_vulnerabilities || 0, color: 'bg-orange-500', barColor: 'bg-orange-400' },
    { label: 'Medium', count: stats?.medium_vulnerabilities || 0, color: 'bg-amber-500', barColor: 'bg-amber-400' },
    { label: 'Low', count: stats?.low_vulnerabilities || 0, color: 'bg-emerald-500', barColor: 'bg-emerald-400' },
  ]
  const maxSeverity = Math.max(...severityData.map((d) => d.count), 1)

  // Weekly scan trend simulation based on actual scan data
  const weekLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const scansByDay = weekLabels.map((_, i) => {
    return scans?.filter((s) => {
      const d = new Date(s.created_at)
      return d.getDay() === (i + 1) % 7
    }).length || 0
  })
  const maxDay = Math.max(...scansByDay, 1)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-500">
          <Activity className="w-5 h-5 animate-pulse" />
          <span>Loading trends data...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-500 text-sm">
            Vulnerability trends and scan frequency over time
          </p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 14, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                timeRange === days
                  ? 'bg-cyan-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-500">Total Scans</span>
            <div className="p-2 rounded-lg bg-blue-50">
              <BarChart3 className="w-4 h-4 text-blue-600" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900">{totalScans}</p>
          <div className="flex items-center gap-1 mt-2 text-sm text-emerald-600">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>{completedScans.length} completed</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-500">Total Findings</span>
            <div className="p-2 rounded-lg bg-orange-50">
              <TrendingUp className="w-4 h-4 text-orange-600" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900">{stats?.total_vulnerabilities || 0}</p>
          <div className="flex items-center gap-1 mt-2 text-sm text-red-600">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>{stats?.critical_vulnerabilities || 0} critical</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-500">Success Rate</span>
            <div className="p-2 rounded-lg bg-emerald-50">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900">
            {totalScans > 0 ? Math.round((completedScans.length / totalScans) * 100) : 0}%
          </p>
          <div className="flex items-center gap-1 mt-2 text-sm text-slate-500">
            <span>{completedScans.length}/{totalScans} scans</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-slate-500">Failed Scans</span>
            <div className="p-2 rounded-lg bg-red-50">
              <TrendingDown className="w-4 h-4 text-red-600" />
            </div>
          </div>
          <p className="text-3xl font-bold text-slate-900">{failedScans.length}</p>
          <div className="flex items-center gap-1 mt-2 text-sm text-red-500">
            <ArrowDownRight className="w-3.5 h-3.5" />
            <span>{totalScans > 0 ? Math.round((failedScans.length / totalScans) * 100) : 0}% failure rate</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Vulnerability Severity Distribution</h3>
          <p className="text-sm text-slate-500 mb-6">Breakdown by severity level across all scans</p>
          <div className="space-y-4">
            {severityData.map((item) => (
              <div key={item.label} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${item.color}`} />
                    <span className="font-medium text-slate-700">{item.label}</span>
                  </div>
                  <span className="font-semibold text-slate-900">{item.count}</span>
                </div>
                <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${item.barColor} transition-all duration-700`}
                    style={{ width: `${(item.count / maxSeverity) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scan Frequency */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-lg font-semibold text-slate-900">Scan Frequency</h3>
            <Calendar className="w-5 h-5 text-slate-400" />
          </div>
          <p className="text-sm text-slate-500 mb-6">Scans initiated by day of the week</p>
          <div className="flex items-end gap-3 h-44">
            {weekLabels.map((label, i) => (
              <div key={label} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full flex flex-col items-center justify-end h-32">
                  <span className="text-xs font-medium text-slate-600 mb-1">{scansByDay[i]}</span>
                  <div
                    className="w-full rounded-t-md bg-gradient-to-t from-cyan-600 to-cyan-400 transition-all duration-500"
                    style={{ height: `${Math.max((scansByDay[i] / maxDay) * 100, 4)}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500 font-medium">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Scan Activity */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900 mb-1">Recent Scan Activity</h3>
        <p className="text-sm text-slate-500 mb-4">Last {Math.min(totalScans, 10)} scans</p>
        <div className="space-y-2">
          {(scans || []).slice(0, 10).map((scan) => (
            <div
              key={scan.scan_id}
              className="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`w-2.5 h-2.5 rounded-full ${
                  scan.status === 'completed' ? 'bg-emerald-500' :
                  scan.status === 'running' ? 'bg-blue-500 animate-pulse' :
                  scan.status === 'failed' ? 'bg-red-500' : 'bg-slate-300'
                }`} />
                <span className="text-sm font-medium text-slate-800 truncate max-w-xs">{scan.target_url}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-500">{scan.total_findings} findings</span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${
                  scan.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                  scan.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  scan.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {scan.status}
                </span>
              </div>
            </div>
          ))}
          {totalScans === 0 && (
            <div className="text-center py-8 text-slate-400">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No scan activity yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
