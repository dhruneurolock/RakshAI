import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { scansAPI, dashboardAPI } from '@/services/endpoints'
import { Clock, CheckCircle2, Play, StopCircle, Trash2, Bot, Server, Circle, Loader2 } from 'lucide-react'

export default function Scans() {
  const navigate = useNavigate()
  const [targetUrl, setTargetUrl] = useState('')
  const [scanType, setScanType] = useState('full')
  const [authentication, setAuthentication] = useState('none')
  const [payloadSafety, setPayloadSafety] = useState(true)
  const queryClient = useQueryClient()

  const { data: scans } = useQuery({
    queryKey: ['scans'],
    queryFn: scansAPI.list,
    refetchInterval: 3000,
  })

  const { data: systemStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: dashboardAPI.systemStatus,
    refetchInterval: 5000,
  })

  // Get the most recent running scan
  const activeScan = scans?.find(s => s.status === 'running')
  const trackedScan = activeScan ?? scans?.[0]

  const createMutation = useMutation({
    mutationFn: scansAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      setTargetUrl('')
    },
  })

  const stopMutation = useMutation({
    mutationFn: scansAPI.stop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: scansAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
  })

  const handleStartScan = () => {
    createMutation.mutate({
      target_url: targetUrl,
      scan_type: scanType,
      test_config: {
        authentication,
        payload_safety: payloadSafety,
      },
    })
  }

  const handleStopScan = (scanId: string) => {
    if (window.confirm('Are you sure you want to stop this scan?')) {
      stopMutation.mutate(scanId)
    }
  }

  const handleDeleteScan = (scanId: string) => {
    if (window.confirm('Are you sure you want to delete this scan? This action cannot be undone.')) {
      deleteMutation.mutate(scanId)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-gray-600">
          Configure and launch a new security assessment
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scan Configuration */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Scan Configuration</h2>
          <p className="text-gray-600 text-sm mb-6">Define target and scan parameters</p>

          <div className="space-y-6">
            {/* Target URL */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target URL
              </label>
              <input
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter target URL (for example: https://example.com)"
              />
            </div>

            {/* Scan Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scan Type
              </label>
              <select
                value={scanType}
                onChange={(e) => setScanType(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="full">Full Scan - Complete vulnerability assessment</option>
                <option value="quick">Quick Scan - Essential checks only</option>
                <option value="targeted">Targeted Scan - Specific vulnerabilities</option>
              </select>
            </div>

            {/* Authentication */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Authentication
              </label>
              <select
                value={authentication}
                onChange={(e) => setAuthentication(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="none">No Authentication</option>
                <option value="basic">Basic Authentication</option>
                <option value="bearer">Bearer Token</option>
                <option value="session">Session Cookie</option>
              </select>
            </div>

            {/* Payload Safety Mode */}
            <div>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Payload Safety Mode
                  </label>
                  <p className="text-sm text-gray-500">
                    Prevents destructive operations during testing
                  </p>
                </div>
                <button
                  onClick={() => setPayloadSafety(!payloadSafety)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    payloadSafety ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      payloadSafety ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Start Scan Button */}
            <button
              onClick={handleStartScan}
              disabled={createMutation.isPending || !targetUrl}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-5 h-5" />
              {createMutation.isPending ? 'Starting Scan...' : 'Start Scan'}
            </button>
          </div>
        </div>

        {/* Scan Status */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Scan Status</h2>
            <p className="text-gray-600 text-sm mb-6">Real-time scan progress</p>

            <div className="flex flex-col items-center justify-center py-8">
              {activeScan ? (
                <>
                  <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 border-t-blue-600 mb-4"></div>
                  <p className="text-gray-900 font-medium">{activeScan.status}</p>
                  <p className="text-gray-600 text-sm">{activeScan.current_phase || 'Processing...'}</p>
                  <p className="text-blue-600 text-sm mt-2">{activeScan.progress_percentage}% complete</p>
                </>
              ) : (
                <>
                  <Clock className="w-16 h-16 text-gray-400 mb-4" />
                  <p className="text-gray-600">No active scan</p>
                </>
              )}
            </div>
          </div>

          {/* Data Flow Monitor */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">Data Flow Monitor</h2>
              <span className="text-xs text-gray-500">Live</span>
            </div>
            <p className="text-gray-600 text-sm mb-4">Agent-by-agent execution pipeline</p>

            <div className="space-y-2">
              {buildFlowStates(trackedScan?.current_phase, trackedScan?.status).map((node) => (
                <div key={node.name} className="flex items-center justify-between border border-gray-200 rounded-lg px-3 py-2">
                  <span className="text-sm text-gray-800">{node.name}</span>
                  <div className="flex items-center gap-2">
                    {node.state === 'running' && <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />}
                    {node.state === 'completed' && <CheckCircle2 className="w-4 h-4 text-green-600" />}
                    {node.state === 'pending' && <Circle className="w-4 h-4 text-gray-300" />}
                    {node.state === 'failed' && <StopCircle className="w-4 h-4 text-red-600" />}
                    <span className={`text-xs font-medium ${
                      node.state === 'running' ? 'text-blue-600' :
                      node.state === 'completed' ? 'text-green-600' :
                      node.state === 'failed' ? 'text-red-600' : 'text-gray-500'
                    }`}>
                      {node.state}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LLM Status */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900">LLM Status</h2>
              <Bot className="w-5 h-5 text-blue-600" />
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Ollama Service</span>
                <span className={`font-medium ${systemStatus?.llm?.healthy ? 'text-green-600' : 'text-red-600'}`}>
                  {systemStatus?.llm?.healthy ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Model</span>
                <span className={`font-medium ${systemStatus?.llm?.model_loaded ? 'text-green-600' : 'text-amber-600'}`}>
                  {systemStatus?.llm?.model_loaded ? 'Loaded' : 'Not Loaded'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Model Name</span>
                <span className="text-gray-800">{systemStatus?.llm?.model ?? 'N/A'}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 pt-1">
                <Server className="w-3 h-3" />
                {systemStatus?.llm?.base_url ?? 'No endpoint configured'}
              </div>
              {systemStatus?.llm?.error && (
                <p className="text-xs text-red-600 mt-1 break-all">{systemStatus.llm.error}</p>
              )}
            </div>
          </div>

          {/* Scan Capabilities */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Scan Capabilities</h2>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-gray-700">OWASP Top 10 coverage</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-gray-700">Autonomous validation</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-gray-700">Real-time detection</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-gray-700">Advanced payloads</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Scans */}
      {scans && scans.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Scans</h3>
          <div className="space-y-3">
            {scans.slice(0, 5).map((scan) => (
              <div
                key={scan.scan_id}
                onClick={() => navigate(`/scans/${scan.scan_id}`)}
                className="flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
              >
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{scan.target_url}</p>
                  <div className="flex items-center gap-4 mt-1">
                    <span className={`text-sm ${getStatusColor(scan.status)}`}>
                      {scan.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {scan.current_phase || 'Pending'}
                    </span>
                    {scan.total_findings > 0 && (
                      <span className="text-sm text-gray-600">
                        {scan.total_findings} findings
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm text-gray-600">{scan.progress_percentage}%</div>
                    <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${scan.progress_percentage}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {scan.status === 'running' && (
                      <button
                        onClick={() => handleStopScan(scan.scan_id)}
                        disabled={stopMutation.isPending}
                        className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Stop scan"
                      >
                        <StopCircle className="w-5 h-5" />
                      </button>
                    )}
                    {scan.status !== 'running' && (
                      <button
                        onClick={() => handleDeleteScan(scan.scan_id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete scan"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

type FlowState = 'pending' | 'running' | 'completed' | 'failed'

function buildFlowStates(currentPhase?: string | null, scanStatus?: string): Array<{ name: string; state: FlowState }> {
  const agents = [
    'Orchestrator',
    'Coordinator',
    'ReconAgent',
    'StrategyAgent',
    'ExecutorAgent',
    'ValidatorAgent',
    'PoCAgent',
    'ReportGenerator',
  ]

  const map: Record<string, number> = {
    phase_1_initialization: 1,
    phase_2_reconnaissance: 3,
    phase_3_strategy_planning: 4,
    phase_4_exploit_testing: 5,
    phase_4_validation: 6,
    phase_5_validation: 6,
    phase_6_poc_generation: 7,
    phase_7_reporting: 8,
    completed: 9,
  }

  const stage = currentPhase ? (map[currentPhase] ?? 1) : 0
  const failed = scanStatus === 'failed'

  return agents.map((name, index) => {
    const position = index + 1
    if (failed && position === Math.min(stage, 8)) {
      return { name, state: 'failed' as FlowState }
    }
    if (stage >= 9) {
      return { name, state: 'completed' as FlowState }
    }
    if (position < stage) {
      return { name, state: 'completed' as FlowState }
    }
    if (position === stage && scanStatus === 'running') {
      return { name, state: 'running' as FlowState }
    }
    return { name, state: 'pending' as FlowState }
  })
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'text-gray-600',
    running: 'text-blue-600',
    completed: 'text-green-600',
    failed: 'text-red-600',
    cancelled: 'text-orange-600',
  }
  return colors[status] || 'text-gray-600'
}
