import { useState } from 'react'
import {
  Activity, Bot, Brain, CheckCircle2, XCircle, AlertTriangle,
  Database, Server, Cpu, RefreshCw, Loader2, Zap, Shield,
  ChevronDown, ChevronRight,
} from 'lucide-react'
import api from '../services/api'

interface AgentDetail {
  name: string
  role: string
  responsibilities: string[]
  status: string
  importable: boolean
  instantiable: boolean
  has_run_method: boolean
  has_initialize_method: boolean
  error: string | null
}

interface DiagnosticResult {
  overall_status: string
  health_score: number
  checks_passed: number
  checks_total: number
  check_details: Record<string, boolean>
  diagnostic_time_ms: number
  timestamp: string
  agents: { total: number; ready: number; details: AgentDetail[] }
  llm: {
    ollama_service: {
      status: string; url: string; models: { name: string; size_gb: number }[]
      configured_model: string; model_available: boolean; response_time_ms: number | null; error: string | null
    }
    inference_test: {
      status: string; model: string; prompt: string; response: string | null
      response_time_ms: number | null; error: string | null
    }
  }
  infrastructure: {
    database: { status: string; error: string | null }
    neo4j: { status: string; uri: string; authenticated_with: string | null; password_hint?: string; error: string | null }
    redis: { status: string; url: string; error: string | null }
  }
  orchestrator: {
    status: string; importable: boolean; instantiable: boolean
    has_start_scan: boolean; pipeline_phases: string[]; error: string | null
  }
}

const StatusBadge = ({ ok, label }: { ok: boolean; label?: string }) => (
  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
    ok ? 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30'
       : 'bg-red-500/15 text-red-400 ring-1 ring-red-500/30'
  }`}>
    {ok ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
    {label || (ok ? 'Online' : 'Offline')}
  </span>
)

export default function Diagnostics() {
  const [result, setResult] = useState<DiagnosticResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedAgents, setExpandedAgents] = useState<Record<string, boolean>>({})

  const runDiagnostics = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get('/diagnostics/system-check', { timeout: 180000 })
      setResult(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Diagnostics failed')
    } finally {
      setLoading(false)
    }
  }

  const toggleAgent = (name: string) =>
    setExpandedAgents(prev => ({ ...prev, [name]: !prev[name] }))

  const scoreColor = (score: number) =>
    score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400'

  const scoreRing = (score: number) =>
    score >= 80 ? 'ring-emerald-500/40' : score >= 50 ? 'ring-amber-500/40' : 'ring-red-500/40'

  const scoreBg = (score: number) =>
    score >= 80 ? 'from-emerald-500/10 to-emerald-500/5' : score >= 50 ? 'from-amber-500/10 to-amber-500/5' : 'from-red-500/10 to-red-500/5'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/10 to-cyan-500/10 ring-1 ring-violet-500/20">
              <Activity className="w-6 h-6 text-violet-500" />
            </div>
            System Diagnostics
          </h1>
          <p className="text-slate-500 mt-1 text-sm">
            Verify all agents, LLM inference, and infrastructure before starting a scan
          </p>
        </div>
        <button
          onClick={runDiagnostics}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-cyan-600 text-white rounded-xl font-semibold text-sm hover:shadow-lg hover:shadow-violet-500/25 transition-all disabled:opacity-60"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {loading ? 'Running Diagnostics…' : 'Run System Check'}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <XCircle className="w-5 h-5 shrink-0" /> {error}
        </div>
      )}

      {!result && !loading && (
        <div className="flex flex-col items-center justify-center py-24 text-slate-400">
          <Activity className="w-16 h-16 mb-4 opacity-30" />
          <p className="text-lg font-medium">Click "Run System Check" to begin</p>
          <p className="text-sm mt-1">This will test all agents, LLM, and infrastructure services</p>
        </div>
      )}

      {loading && !result && (
        <div className="flex flex-col items-center justify-center py-24 text-slate-400">
          <Loader2 className="w-12 h-12 animate-spin mb-4 text-violet-500" />
          <p className="text-lg font-medium text-slate-600">Running system diagnostics…</p>
          <p className="text-sm mt-1">Testing agents, LLM inference (may take up to 2 min on cold start), and infrastructure</p>
        </div>
      )}

      {result && (
        <>
          {/* Health Score Card */}
          <div className={`rounded-2xl bg-gradient-to-r ${scoreBg(result.health_score)} border ring-1 ${scoreRing(result.health_score)} p-6 flex items-center gap-8`}>
            <div className="text-center">
              <div className={`text-5xl font-black ${scoreColor(result.health_score)}`}>
                {result.health_score}%
              </div>
              <div className="text-xs text-slate-500 mt-1 font-semibold uppercase tracking-wider">Health Score</div>
            </div>
            <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-800">{result.checks_passed}/{result.checks_total}</div>
                <div className="text-xs text-slate-500">Checks Passed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-800">{result.agents.ready}/{result.agents.total}</div>
                <div className="text-xs text-slate-500">Agents Ready</div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold ${result.llm.inference_test.status === 'working' ? 'text-emerald-600' : 'text-red-600'}`}>
                  {result.llm.inference_test.status === 'working' ? '✓' : '✗'}
                </div>
                <div className="text-xs text-slate-500">LLM Inference</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-800">{result.diagnostic_time_ms}ms</div>
                <div className="text-xs text-slate-500">Check Duration</div>
              </div>
            </div>
            <div className={`px-4 py-2 rounded-xl text-sm font-bold uppercase tracking-wider ${
              result.overall_status === 'healthy' ? 'bg-emerald-500/20 text-emerald-600' :
              result.overall_status === 'degraded' ? 'bg-amber-500/20 text-amber-600' :
              'bg-red-500/20 text-red-600'
            }`}>
              {result.overall_status}
            </div>
          </div>

          {/* Infrastructure Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Database */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-blue-500" />
                  <span className="font-semibold text-slate-800">Database</span>
                </div>
                <StatusBadge ok={result.infrastructure.database.status === 'online'} />
              </div>
              <p className="text-xs text-slate-500">PostgreSQL / SQLite</p>
              {result.infrastructure.database.error && (
                <p className="text-xs text-red-500 mt-2 break-all">{result.infrastructure.database.error}</p>
              )}
            </div>
            {/* Neo4j */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Server className="w-5 h-5 text-green-500" />
                  <span className="font-semibold text-slate-800">Neo4j</span>
                </div>
                <StatusBadge ok={result.infrastructure.neo4j.status === 'online'} />
              </div>
              <p className="text-xs text-slate-500 truncate">{result.infrastructure.neo4j.uri}</p>
              {(result.infrastructure.neo4j as any).password_hint && (
                <p className="text-xs text-amber-600 mt-2 bg-amber-50 border border-amber-200 rounded-md px-2 py-1">
                  💡 {(result.infrastructure.neo4j as any).password_hint}
                </p>
              )}
              {result.infrastructure.neo4j.error && (
                <p className="text-xs text-red-500 mt-2 break-all">{result.infrastructure.neo4j.error}</p>
              )}
            </div>
            {/* Redis */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-red-500" />
                  <span className="font-semibold text-slate-800">Redis</span>
                </div>
                <StatusBadge ok={result.infrastructure.redis.status === 'online'} />
              </div>
              <p className="text-xs text-slate-500 truncate">{result.infrastructure.redis.url}</p>
              {result.infrastructure.redis.error && (
                <p className="text-xs text-red-500 mt-2 break-all">{result.infrastructure.redis.error}</p>
              )}
            </div>
          </div>

          {/* LLM Section */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-violet-50 to-cyan-50">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-violet-500" />
                <span className="font-bold text-slate-800">LLM Service (Ollama)</span>
                <StatusBadge ok={result.llm.ollama_service.status === 'online'} />
              </div>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Ollama service */}
              <div className="space-y-3">
                <h4 className="font-semibold text-sm text-slate-700">Service Status</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-500">URL</span><span className="font-mono text-xs">{result.llm.ollama_service.url}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Configured Model</span><span className="font-mono text-xs">{result.llm.ollama_service.configured_model || '—'}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Model Available</span><StatusBadge ok={result.llm.ollama_service.model_available} label={result.llm.ollama_service.model_available ? 'Found' : 'Not Found'} /></div>
                  {result.llm.ollama_service.response_time_ms && (
                    <div className="flex justify-between"><span className="text-slate-500">Response Time</span><span>{result.llm.ollama_service.response_time_ms}ms</span></div>
                  )}
                </div>
                {result.llm.ollama_service.models.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-slate-600 mb-1">Available Models:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {result.llm.ollama_service.models.map((m, i) => (
                        <span key={i} className={`px-2 py-0.5 rounded-md text-xs font-mono ${
                          result.llm.ollama_service.configured_model && m.name.includes(result.llm.ollama_service.configured_model)
                            ? 'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-300'
                            : 'bg-slate-100 text-slate-600'
                        }`}>{m.name} ({m.size_gb}GB)</span>
                      ))}
                    </div>
                  </div>
                )}
                {result.llm.ollama_service.error && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-600">{result.llm.ollama_service.error}</div>
                )}
              </div>
              {/* Inference test */}
              <div className="space-y-3">
                <h4 className="font-semibold text-sm text-slate-700 flex items-center gap-2">
                  Inference Test
                  <StatusBadge ok={result.llm.inference_test.status === 'working'} label={result.llm.inference_test.status === 'working' ? 'Working' : 'Failed'} />
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-500">Model</span><span className="font-mono text-xs">{result.llm.inference_test.model || '—'}</span></div>
                  {result.llm.inference_test.response_time_ms && (
                    <div className="flex justify-between"><span className="text-slate-500">Inference Time</span><span className="font-semibold">{result.llm.inference_test.response_time_ms}ms</span></div>
                  )}
                </div>
                {result.llm.inference_test.response && (
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700 break-all">
                    <span className="text-slate-400">LLM Response: </span>{result.llm.inference_test.response}
                  </div>
                )}
                {result.llm.inference_test.error && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-600">{result.llm.inference_test.error}</div>
                )}
              </div>
            </div>
          </div>

          {/* Agents Section */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-cyan-50 to-blue-50">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-cyan-500" />
                <span className="font-bold text-slate-800">Agent Pipeline</span>
                <span className="text-xs text-slate-500 ml-2">{result.agents.ready}/{result.agents.total} ready</span>
              </div>
            </div>
            <div className="divide-y divide-slate-100">
              {result.agents.details.map((agent, idx) => {
                const isExpanded = expandedAgents[agent.name] ?? false
                const ok = agent.status === 'ready'
                return (
                  <div key={idx}>
                    <button
                      onClick={() => toggleAgent(agent.name)}
                      className="w-full px-6 py-3.5 flex items-center gap-3 hover:bg-slate-50 transition-colors text-left"
                    >
                      {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                      <div className={`w-2 h-2 rounded-full ${ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
                      <span className="font-semibold text-sm text-slate-800 w-48">{agent.name}</span>
                      <span className="text-xs text-slate-500 flex-1 truncate">{agent.role.split('—')[0]}</span>
                      <StatusBadge ok={ok} label={ok ? 'Ready' : 'Error'} />
                    </button>
                    {isExpanded && (
                      <div className="px-6 pb-4 pl-16 space-y-3">
                        <p className="text-sm text-slate-600">{agent.role}</p>
                        <div className="flex gap-4 text-xs">
                          <span className={agent.importable ? 'text-emerald-600' : 'text-red-500'}>
                            {agent.importable ? '✓' : '✗'} Import
                          </span>
                          <span className={agent.instantiable ? 'text-emerald-600' : 'text-red-500'}>
                            {agent.instantiable ? '✓' : '✗'} Instantiate
                          </span>
                          <span className={agent.has_run_method ? 'text-emerald-600' : 'text-red-500'}>
                            {agent.has_run_method ? '✓' : '✗'} run()
                          </span>
                          <span className={agent.has_initialize_method ? 'text-emerald-600' : 'text-red-500'}>
                            {agent.has_initialize_method ? '✓' : '✗'} initialize()
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {agent.responsibilities.map((r, j) => (
                            <span key={j} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md text-xs">{r}</span>
                          ))}
                        </div>
                        {agent.error && <p className="text-xs text-red-500 break-all">Error: {agent.error}</p>}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Orchestrator Section */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-amber-50 to-orange-50">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-amber-500" />
                <span className="font-bold text-slate-800">Orchestrator Pipeline</span>
                <StatusBadge ok={result.orchestrator.status === 'ready'} label={result.orchestrator.status === 'ready' ? 'Ready' : 'Not Ready'} />
              </div>
            </div>
            <div className="p-6 space-y-3">
              <div className="flex gap-6 text-xs">
                <span className={result.orchestrator.importable ? 'text-emerald-600' : 'text-red-500'}>
                  {result.orchestrator.importable ? '✓' : '✗'} Importable
                </span>
                <span className={result.orchestrator.instantiable ? 'text-emerald-600' : 'text-red-500'}>
                  {result.orchestrator.instantiable ? '✓' : '✗'} Instantiable
                </span>
                <span className={result.orchestrator.has_start_scan ? 'text-emerald-600' : 'text-red-500'}>
                  {result.orchestrator.has_start_scan ? '✓' : '✗'} start_scan()
                </span>
              </div>
              <div className="space-y-1.5">
                {result.orchestrator.pipeline_phases.map((phase, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-r from-violet-500 to-cyan-500 text-white text-xs font-bold flex items-center justify-center shrink-0">{i + 1}</div>
                    <span className="text-slate-700">{phase}</span>
                  </div>
                ))}
              </div>
              {result.orchestrator.error && <p className="text-xs text-red-500">{result.orchestrator.error}</p>}
            </div>
          </div>

          {/* Check Details Grid */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-slate-400" /> Individual Check Results
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(result.check_details).map(([key, passed]) => (
                <div key={key} className={`p-3 rounded-lg border ${passed ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
                  <div className="flex items-center gap-2">
                    {passed ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                    <span className="text-sm font-medium text-slate-700">{key.replace(/_/g, ' ')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
