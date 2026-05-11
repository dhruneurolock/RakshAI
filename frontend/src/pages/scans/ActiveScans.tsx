import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { scansAPI, dashboardAPI } from '@/services/endpoints'
import { Radio, Loader2, CheckCircle2, Circle, StopCircle, Clock, Activity, Bot, Server } from 'lucide-react'

type FlowState = 'pending' | 'running' | 'completed' | 'failed'

function buildFlowStates(currentPhase?: string | null, scanStatus?: string): Array<{ name: string; state: FlowState }> {
  const agents = ['Orchestrator', 'Coordinator', 'ReconAgent', 'StrategyAgent', 'ExecutorAgent', 'ValidatorAgent', 'PoCAgent', 'ReportGenerator']
  const map: Record<string, number> = {
    phase_1_initialization: 1, phase_2_reconnaissance: 3, phase_3_strategy_planning: 4,
    phase_4_exploit_testing: 5, phase_4_validation: 6, phase_5_validation: 6,
    phase_6_poc_generation: 7, phase_7_reporting: 8, completed: 9,
  }
  const stage = currentPhase ? (map[currentPhase] ?? 1) : 0
  const failed = scanStatus === 'failed'
  return agents.map((name, index) => {
    const position = index + 1
    if (failed && position === Math.min(stage, 8)) return { name, state: 'failed' as FlowState }
    if (stage >= 9) return { name, state: 'completed' as FlowState }
    if (position < stage) return { name, state: 'completed' as FlowState }
    if (position === stage && scanStatus === 'running') return { name, state: 'running' as FlowState }
    return { name, state: 'pending' as FlowState }
  })
}

export default function ActiveScans() {
  const navigate = useNavigate()

  const { data: scans, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: scansAPI.list,
    refetchInterval: 3000,
  })

  const { data: systemStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: dashboardAPI.systemStatus,
    refetchInterval: 5000,
  })

  const activeScans = scans?.filter((s) => s.status === 'running') || []
  const pendingScans = scans?.filter((s) => s.status === 'pending') || []
  const allActive = [...activeScans, ...pendingScans]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-slate-500">
          <Radio className="w-5 h-5 animate-pulse" />
          <span>Loading active scans...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Real-time monitoring of running scans with live agent pipeline
      </p>

      {/* System Status Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full ${systemStatus?.llm?.healthy ? 'bg-emerald-500' : 'bg-red-500'}`} />
              <span className="text-sm text-slate-600">LLM: {systemStatus?.llm?.healthy ? 'Online' : 'Offline'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-slate-400" />
              <span className="text-sm text-slate-600">{systemStatus?.llm?.model ?? 'No model'}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Server className="w-4 h-4" />
            <span>{activeScans.length} running · {pendingScans.length} queued</span>
          </div>
        </div>
      </div>

      {allActive.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
          <Clock className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-700 mb-2">No Active Scans</h3>
          <p className="text-sm text-slate-500 mb-4">All scans have completed or there are no scans in progress.</p>
          <button
            onClick={() => navigate('/scans')}
            className="px-4 py-2 bg-cyan-600 text-white rounded-lg text-sm font-medium hover:bg-cyan-500 transition-colors"
          >
            Start New Scan
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {allActive.map((scan) => (
            <div
              key={scan.scan_id}
              className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/scans/${scan.scan_id}`)}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold text-slate-900">{scan.target_url}</h3>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Phase: {scan.current_phase || 'Initializing'} · {scan.progress_percentage}% complete
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {scan.status === 'running' && (
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span className="text-xs font-medium">Running</span>
                    </div>
                  )}
                  {scan.status === 'pending' && (
                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 text-slate-600">
                      <Clock className="w-3.5 h-3.5" />
                      <span className="text-xs font-medium">Queued</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2 bg-slate-100 rounded-full mb-4 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-cyan-400 transition-all duration-500"
                  style={{ width: `${scan.progress_percentage}%` }}
                />
              </div>

              {/* Agent Pipeline */}
              <div className="grid grid-cols-4 md:grid-cols-8 gap-2">
                {buildFlowStates(scan.current_phase, scan.status).map((node) => (
                  <div key={node.name} className="flex flex-col items-center gap-1">
                    {node.state === 'running' && <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />}
                    {node.state === 'completed' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                    {node.state === 'pending' && <Circle className="w-4 h-4 text-slate-300" />}
                    {node.state === 'failed' && <StopCircle className="w-4 h-4 text-red-600" />}
                    <span className="text-[10px] text-slate-500 text-center leading-tight">{node.name}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
