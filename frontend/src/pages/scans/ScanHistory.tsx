import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { scansAPI } from '@/services/endpoints'
import { History, Search, Filter, ChevronDown } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function ScanHistory() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'findings'>('newest')
  const [currentPage, setCurrentPage] = useState(1)
  const perPage = 10

  const { data: scans, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: scansAPI.list,
  })

  const filtered = useMemo(() => {
    let result = scans || []
    if (search) {
      const q = search.toLowerCase()
      result = result.filter((s) => s.target_url.toLowerCase().includes(q))
    }
    if (statusFilter !== 'all') {
      result = result.filter((s) => s.status === statusFilter)
    }
    if (sortBy === 'newest') result = [...result].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    if (sortBy === 'oldest') result = [...result].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    if (sortBy === 'findings') result = [...result].sort((a, b) => (b.total_findings || 0) - (a.total_findings || 0))
    return result
  }, [scans, search, statusFilter, sortBy])

  const totalPages = Math.max(Math.ceil(filtered.length / perPage), 1)
  const paginated = filtered.slice((currentPage - 1) * perPage, currentPage * perPage)

  const statusCounts = {
    all: scans?.length || 0,
    completed: scans?.filter((s) => s.status === 'completed').length || 0,
    running: scans?.filter((s) => s.status === 'running').length || 0,
    failed: scans?.filter((s) => s.status === 'failed').length || 0,
    pending: scans?.filter((s) => s.status === 'pending').length || 0,
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-500">
          <History className="w-5 h-5 animate-pulse" />
          <span>Loading scan history...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">Complete history of all scans with advanced filtering</p>

      {/* Status Tabs */}
      <div className="flex gap-2 flex-wrap">
        {(['all', 'completed', 'running', 'failed', 'pending'] as const).map((status) => (
          <button
            key={status}
            onClick={() => { setStatusFilter(status); setCurrentPage(1) }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === status
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {status.charAt(0).toUpperCase() + status.slice(1)}
            <span className="ml-1.5 text-xs opacity-75">({statusCounts[status]})</span>
          </button>
        ))}
      </div>

      {/* Search and Sort */}
      <div className="flex gap-3 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by target URL..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setCurrentPage(1) }}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500"
          />
        </div>
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest' | 'findings')}
            className="appearance-none bg-white border border-slate-200 text-slate-700 text-sm rounded-lg pl-3 pr-8 py-2.5 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="findings">Most Findings</option>
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Scan Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr className="text-xs uppercase text-slate-500">
              <th className="px-6 py-3 text-left font-medium">Target</th>
              <th className="px-6 py-3 text-left font-medium">Status</th>
              <th className="px-6 py-3 text-left font-medium">Phase</th>
              <th className="px-6 py-3 text-left font-medium">Findings</th>
              <th className="px-6 py-3 text-left font-medium">Progress</th>
              <th className="px-6 py-3 text-left font-medium">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {paginated.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                  <Filter className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No scans match your filters</p>
                </td>
              </tr>
            ) : (
              paginated.map((scan) => (
                <tr
                  key={scan.scan_id}
                  onClick={() => navigate(`/scans/${scan.scan_id}`)}
                  className="hover:bg-cyan-50/40 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-slate-900 truncate block max-w-xs">{scan.target_url}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                      scan.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                      scan.status === 'running' ? 'bg-blue-100 text-blue-700' :
                      scan.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{scan.current_phase || '—'}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-slate-900">{scan.total_findings || 0}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full bg-cyan-500 transition-all"
                          style={{ width: `${scan.progress_percentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500">{scan.progress_percentage}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-3 border-t border-slate-200 bg-slate-50">
            <span className="text-sm text-slate-500">
              Showing {(currentPage - 1) * perPage + 1}–{Math.min(currentPage * perPage, filtered.length)} of {filtered.length}
            </span>
            <div className="flex gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-1 rounded text-sm ${
                    page === currentPage
                      ? 'bg-cyan-600 text-white'
                      : 'text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
