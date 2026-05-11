import { useQuery } from '@tanstack/react-query'
import { dashboardAPI } from '@/services/endpoints'
import {
  AlertTriangle,
  Shield,
  Activity,
  TrendingUp,
  AlertCircle,
  Info,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'

export default function Dashboard() {
  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardAPI.stats,
    refetchInterval: 5000, // Refresh every 5 seconds
    retry: 1, // Only retry once
    retryDelay: 1000,
    staleTime: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  if (isError || !stats) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-lg">
          <div className="flex items-start">
            <AlertTriangle className="w-6 h-6 text-yellow-600 mr-3 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                Backend API Not Running
              </h3>
              <p className="text-yellow-700 mb-4">
                The RakshAI backend is currently not available. You're viewing the frontend UI only.
              </p>
              <div className="bg-white rounded-lg p-4 mb-4">
                <p className="text-sm font-semibold text-gray-700 mb-2">To run the full application:</p>
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                  <li>Install Docker Desktop from <a href="https://www.docker.com/products/docker-desktop" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">docker.com</a></li>
                  <li>Open terminal and run: <code className="bg-gray-100 px-2 py-1 rounded text-xs">docker-compose up -d</code></li>
                  <li>Wait for services to start (~2 minutes)</li>
                  <li>Access the app at <a href="http://localhost:3000" className="text-blue-600 hover:underline">http://localhost:3000</a></li>
                </ol>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm font-semibold text-blue-800 mb-1">📚 Documentation:</p>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• <strong>QUICK-START.md</strong> - Quick reference guide</li>
                  <li>• <strong>DEPLOYMENT.md</strong> - Full deployment instructions</li>
                  <li>• <strong>README.md</strong> - Project overview</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        {/* Demo UI Preview */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">UI Preview (Demo Mode)</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatCard title="Total Scans" value={0} icon={Shield} color="blue" />
            <StatCard title="Active Scans" value={0} icon={Activity} color="green" />
            <StatCard title="Vulnerabilities" value={0} icon={AlertTriangle} color="orange" />
            <StatCard title="Completed" value={0} icon={TrendingUp} color="purple" />
          </div>
        </div>
      </div>
    )
  }

  const severityCards = [
    {
      name: 'Critical',
      count: stats.critical_vulnerabilities,
      icon: AlertCircle,
      color: 'bg-red-100 text-red-600',
      borderColor: 'border-red-500',
    },
    {
      name: 'High',
      count: stats.high_vulnerabilities,
      icon: AlertTriangle,
      color: 'bg-orange-100 text-orange-600',
      borderColor: 'border-orange-500',
    },
    {
      name: 'Medium',
      count: stats.medium_vulnerabilities,
      icon: AlertTriangle,
      color: 'bg-yellow-100 text-yellow-600',
      borderColor: 'border-yellow-500',
    },
    {
      name: 'Low',
      count: stats.low_vulnerabilities,
      icon: Info,
      color: 'bg-blue-100 text-blue-600',
      borderColor: 'border-blue-500',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total Scans"
          value={stats.total_scans}
          icon={Shield}
          color="blue"
        />
        <StatCard
          title="Active Scans"
          value={stats.active_scans}
          icon={Activity}
          color="green"
        />
        <StatCard
          title="Vulnerabilities"
          value={stats.total_vulnerabilities}
          icon={AlertTriangle}
          color="orange"
        />
        <StatCard
          title="Completed"
          value={stats.completed_scans}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Severity Breakdown */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold mb-4">Vulnerability Severity</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {severityCards.map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.name}
                className={`p-4 rounded-lg border-l-4 ${item.color} ${item.borderColor}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </div>
                <p className="text-3xl font-bold">{item.count}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Scans */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Scans</h3>
          <Link
            to="/scans"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            View All
          </Link>
        </div>
        <div className="space-y-3">
          {stats.recent_scans.map((scan) => (
            <Link
              key={scan.id}
              to={`/scans/${scan.scan_id}`}
              className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{scan.target_url}</p>
                  <p className="text-sm text-gray-500">
                    {formatDistanceToNow(new Date(scan.created_at), {
                      addSuffix: true,
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                      scan.status
                    )}`}
                  >
                    {scan.status}
                  </span>
                  <span className="text-sm font-semibold text-gray-700">
                    {scan.total_findings} findings
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string
  value: number
  icon: any
  color: string
}) {
  const colors = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    purple: 'bg-purple-100 text-purple-600',
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-600 text-sm font-medium">{title}</span>
        <div className={`p-2 rounded-lg ${colors[color as keyof typeof colors]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'bg-gray-100 text-gray-700',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-700',
  }
  return colors[status] || colors.pending
}
