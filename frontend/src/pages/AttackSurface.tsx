import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { endpointsAPI, scansAPI } from '@/services/endpoints'
import { Search, Shield, Lock, Unlock, Globe, Database } from 'lucide-react'

export default function AttackSurface() {
  const [searchQuery, setSearchQuery] = useState('')
  const [methodFilter, setMethodFilter] = useState<string>('all')
  const [authFilter, setAuthFilter] = useState<string>('all')
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [selectedScan, setSelectedScan] = useState<string>('')

  // Fetch all scans
  const { data: scans } = useQuery({
    queryKey: ['scans'],
    queryFn: scansAPI.list,
  })

  const latestCompletedScan = scans?.find((scan) => scan.status === 'completed')
  const defaultScan = latestCompletedScan || (scans && scans.length > 0 ? scans[0] : undefined)

  // Auto-select latest completed scan first (fallback to most recent)
  const currentScan = selectedScan || defaultScan?.scan_id || ''
  const currentScanMeta = scans?.find((scan) => scan.scan_id === currentScan)

  // Fetch endpoints for selected scan
  const { data: endpoints, isLoading } = useQuery({
    queryKey: ['endpoints', currentScan],
    queryFn: () => currentScan ? endpointsAPI.list({ scan_id: currentScan }) : Promise.resolve([]),
    refetchInterval: 5000,
    enabled: !!currentScan,
  })

  // Filter endpoints based on search and filters
  const filteredEndpoints = endpoints?.filter((endpoint) => {
    const matchesSearch = endpoint.url.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesMethod = methodFilter === 'all' || endpoint.method === methodFilter
    const matchesAuth = authFilter === 'all' || 
      (authFilter === 'required' && endpoint.requires_auth) ||
      (authFilter === 'not-required' && !endpoint.requires_auth)
    const matchesSource = sourceFilter === 'all' || endpoint.discovery_method?.includes(sourceFilter)
    
    return matchesSearch && matchesMethod && matchesAuth && matchesSource
  }) || []

  const methodCounts = {
    GET: endpoints?.filter(e => e.method === 'GET').length || 0,
    POST: endpoints?.filter(e => e.method === 'POST').length || 0,
    PUT: endpoints?.filter(e => e.method === 'PUT').length || 0,
    DELETE: endpoints?.filter(e => e.method === 'DELETE').length || 0,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Attack Surface</h2>
          <p className="text-gray-600 mt-1">
            Mapped endpoints and attack vectors
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={currentScan}
            onChange={(e) => setSelectedScan(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {scans?.map((scan) => (
              <option key={scan.scan_id} value={scan.scan_id}>
                {scan.target_url} - {scan.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Endpoints</p>
              <p className="text-2xl font-bold text-gray-900">{endpoints?.length || 0}</p>
            </div>
            <Shield className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">GET</p>
              <p className="text-2xl font-bold text-green-600">{methodCounts.GET}</p>
            </div>
            <Database className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">POST</p>
              <p className="text-2xl font-bold text-blue-600">{methodCounts.POST}</p>
            </div>
            <Database className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">PUT</p>
              <p className="text-2xl font-bold text-orange-600">{methodCounts.PUT}</p>
            </div>
            <Database className="w-8 h-8 text-orange-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">DELETE</p>
              <p className="text-2xl font-bold text-red-600">{methodCounts.DELETE}</p>
            </div>
            <Database className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Discovered Endpoints</h3>
          <p className="text-sm text-gray-600">
            {filteredEndpoints.length} of {endpoints?.length || 0} endpoints
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search endpoints..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Method Filter */}
          <select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Methods</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
            <option value="PATCH">PATCH</option>
          </select>

          {/* Auth Filter */}
          <select
            value={authFilter}
            onChange={(e) => setAuthFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Auth States</option>
            <option value="required">Auth Required</option>
            <option value="not-required">No Auth</option>
          </select>

          {/* Source Filter */}
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Sources</option>
            <option value="http">HTTP Crawl</option>
            <option value="playwright">Playwright</option>
            <option value="api">API</option>
          </select>
        </div>

        {/* Endpoints Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Endpoint
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parameters
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Auth Required
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Source
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    Loading endpoints...
                  </td>
                </tr>
              ) : filteredEndpoints.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No endpoints discovered yet. Create a scan to start discovering endpoints.
                    {currentScanMeta?.status === 'running' && latestCompletedScan && latestCompletedScan.scan_id !== currentScan && (
                      <div className="mt-3">
                        <button
                          onClick={() => setSelectedScan(latestCompletedScan.scan_id)}
                          className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                        >
                          View latest completed scan endpoints
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                filteredEndpoints.map((endpoint) => (
                  <tr key={endpoint.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <code className="text-sm text-blue-600 font-mono">
                          {endpoint.url}
                        </code>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${getMethodColor(
                          endpoint.method
                        )}`}
                      >
                        {endpoint.method}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 ? (
                          Object.keys(endpoint.parameters).map((param) => (
                            <span
                              key={param}
                              className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                            >
                              {param}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">None</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {endpoint.requires_auth ? (
                          <>
                            <Lock className="w-4 h-4 text-orange-500" />
                            <span className="text-sm text-orange-600">Yes</span>
                          </>
                        ) : (
                          <>
                            <Unlock className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-500">No</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {endpoint.discovery_method?.includes('api') ? (
                          <>
                            <Database className="w-4 h-4 text-blue-500" />
                            <span className="text-sm text-blue-600">API</span>
                          </>
                        ) : (
                          <>
                            <Globe className="w-4 h-4 text-green-500" />
                            <span className="text-sm text-green-600">Web</span>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function getMethodColor(method: string): string {
  const colors: Record<string, string> = {
    GET: 'bg-green-100 text-green-700 border border-green-300',
    POST: 'bg-blue-100 text-blue-700 border border-blue-300',
    PUT: 'bg-orange-100 text-orange-700 border border-orange-300',
    DELETE: 'bg-red-100 text-red-700 border border-red-300',
    PATCH: 'bg-purple-100 text-purple-700 border border-purple-300',
  }
  return colors[method] || 'bg-gray-100 text-gray-700 border border-gray-300'
}
