import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { scansAPI, vulnerabilitiesAPI } from '@/services/endpoints'
import type { Scan, Vulnerability } from '@/types'
import {
  GitCompare, ArrowRight, TrendingUp, TrendingDown, Minus,
  ChevronDown, Search, Plus, CheckCircle2, XCircle
} from 'lucide-react'

function fmtDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function elapsed(start: string | null, end: string | null) {
  if (!start || !end) return '—'
  const ms = new Date(end).getTime() - new Date(start).getTime()
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m ${s % 60}s`
}

function riskScore(s: Scan) {
  return s.critical_count * 10 + s.high_count * 5 + s.medium_count * 2 + s.low_count * 0.5
}

function vulnKey(v: Vulnerability) {
  return `${v.title}||${v.owasp_category}||${v.endpoint_url ?? ''}`
}

type DiffResult = {
  newFindings: Vulnerability[]
  persistent: { baseline: Vulnerability; comparison: Vulnerability }[]
  resolved: Vulnerability[]
}

function computeDiff(baseVulns: Vulnerability[], compVulns: Vulnerability[]): DiffResult {
  const baseMap = new Map<string, Vulnerability>()
  baseVulns.forEach(v => baseMap.set(vulnKey(v), v))
  const compMap = new Map<string, Vulnerability>()
  compVulns.forEach(v => compMap.set(vulnKey(v), v))

  const newFindings: Vulnerability[] = []
  const persistent: { baseline: Vulnerability; comparison: Vulnerability }[] = []
  const resolved: Vulnerability[] = []

  compVulns.forEach(v => {
    const key = vulnKey(v)
    const match = baseMap.get(key)
    if (match) persistent.push({ baseline: match, comparison: v })
    else newFindings.push(v)
  })
  baseVulns.forEach(v => {
    if (!compMap.has(vulnKey(v))) resolved.push(v)
  })
  return { newFindings, persistent, resolved }
}

// ── Delta Badge ─────────────────────────────────────────
function DeltaBadge({ value, color }: { value: number; color: string }) {
  if (value === 0) return <span className="text-xs text-slate-400">—</span>
  const isUp = value > 0
  return (
    <span className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {isUp ? '+' : ''}{value}
    </span>
  )
}

// ── Severity Badge ──────────────────────────────────────
function SeverityBadge({ severity }: { severity: string }) {
  const map: Record<string, string> = {
    critical: 'bg-red-600 text-white', high: 'bg-orange-500 text-white',
    medium: 'bg-amber-500 text-white', low: 'bg-green-600 text-white', info: 'bg-blue-600 text-white',
  }
  return (
    <span className={`px-2.5 py-0.5 rounded text-xs font-semibold capitalize ${map[severity] ?? 'bg-gray-600 text-white'}`}>
      {severity}
    </span>
  )
}

// ── Status Badge ────────────────────────────────────────
function StatusBadge({ status, isValidated }: { status: string | null; isValidated: boolean }) {
  const raw = (status ?? (isValidated ? 'VALIDATED' : 'UNVALIDATED')).toUpperCase()
  if (raw === 'VALIDATED') return <span className="px-2 py-0.5 rounded-full text-xs font-medium border border-amber-400 text-amber-700 bg-amber-50">Validated</span>
  if (raw === 'FALSE_POSITIVE') return <span className="px-2 py-0.5 rounded-full text-xs font-medium border border-red-400 text-red-700 bg-red-50">False Positive</span>
  return <span className="px-2 py-0.5 rounded-full text-xs font-medium border border-gray-300 text-gray-600 bg-gray-50">Raw</span>
}

// ════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════
export default function ScanComparison() {
  const [targetFilter, setTargetFilter] = useState('')
  const [baselineId, setBaselineId] = useState('')
  const [comparisonId, setComparisonId] = useState('')
  const [compared, setCompared] = useState(false)
  const [activeTab, setActiveTab] = useState<'new' | 'persistent' | 'resolved'>('new')

  const { data: allScans = [] } = useQuery({ queryKey: ['scans'], queryFn: scansAPI.list })

  const completedScans = useMemo(() => allScans.filter(s => s.status === 'completed'), [allScans])
  const targets = useMemo(() => [...new Set(completedScans.map(s => s.target_url))], [completedScans])
  const filteredScans = useMemo(() =>
    targetFilter ? completedScans.filter(s => s.target_url === targetFilter) : [],
    [completedScans, targetFilter]
  )

  const baselineScan = useMemo(() => allScans.find(s => s.scan_id === baselineId), [allScans, baselineId])
  const comparisonScan = useMemo(() => allScans.find(s => s.scan_id === comparisonId), [allScans, comparisonId])

  const { data: baseVulns = [] } = useQuery({
    queryKey: ['vulns-base', baselineScan?.id],
    queryFn: () => vulnerabilitiesAPI.list({ scan_id: baselineScan!.id }),
    enabled: !!baselineScan?.id && compared,
  })
  const { data: compVulns = [] } = useQuery({
    queryKey: ['vulns-comp', comparisonScan?.id],
    queryFn: () => vulnerabilitiesAPI.list({ scan_id: comparisonScan!.id }),
    enabled: !!comparisonScan?.id && compared,
  })

  const diff = useMemo(() => computeDiff(baseVulns, compVulns), [baseVulns, compVulns])
  const canCompare = baselineId && comparisonId && baselineId !== comparisonId

  const handleCompare = () => { if (canCompare) setCompared(true) }
  const handleReset = () => { setCompared(false); setBaselineId(''); setComparisonId('') }

  // ── SECTION 1: Scan Selector ────────────────────────
  const renderSelector = () => (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-50 to-blue-50 flex items-center justify-center">
          <GitCompare className="w-5 h-5 text-cyan-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Select Scans to Compare</h3>
          <p className="text-sm text-slate-500">Choose two completed scans against the same target</p>
        </div>
      </div>

      {/* Target filter */}
      <div className="mb-5">
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Target URL</label>
        <div className="relative">
          <select value={targetFilter}
            onChange={e => { setTargetFilter(e.target.value); setBaselineId(''); setComparisonId(''); setCompared(false) }}
            className="w-full appearance-none bg-white border border-slate-300 rounded-lg pl-3 pr-8 py-2.5 text-sm focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500">
            <option value="">Select a target...</option>
            {targets.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Scan selectors */}
      {targetFilter && (
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Baseline Scan</label>
            <div className="relative">
              <select value={baselineId} onChange={e => { setBaselineId(e.target.value); setCompared(false) }}
                className="w-full appearance-none bg-white border border-slate-300 rounded-lg pl-3 pr-8 py-2.5 text-sm focus:outline-none focus:border-cyan-500">
                <option value="">Select baseline...</option>
                {filteredScans.filter(s => s.scan_id !== comparisonId).map(s => (
                  <option key={s.scan_id} value={s.scan_id}>
                    {s.scan_id.slice(0, 8)} — {fmtDate(s.created_at)} — {s.total_findings} findings
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>
          <div className="flex justify-center pb-2.5">
            <ArrowRight className="w-5 h-5 text-slate-300" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Comparison Scan</label>
            <div className="relative">
              <select value={comparisonId} onChange={e => { setComparisonId(e.target.value); setCompared(false) }}
                className="w-full appearance-none bg-white border border-slate-300 rounded-lg pl-3 pr-8 py-2.5 text-sm focus:outline-none focus:border-cyan-500">
                <option value="">Select comparison...</option>
                {filteredScans.filter(s => s.scan_id !== baselineId).map(s => (
                  <option key={s.scan_id} value={s.scan_id}>
                    {s.scan_id.slice(0, 8)} — {fmtDate(s.created_at)} — {s.total_findings} findings
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>
        </div>
      )}

      {/* Action buttons */}
      {targetFilter && (
        <div className="flex gap-3 mt-5">
          <button onClick={handleCompare} disabled={!canCompare}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-5 py-2.5 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
            <GitCompare className="w-4 h-4" /> Compare Scans
          </button>
          {compared && (
            <button onClick={handleReset}
              className="px-5 py-2.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 transition-colors text-sm font-medium">
              Reset
            </button>
          )}
        </div>
      )}
    </div>
  )

  // ── SECTION 2: Summary Delta Cards ──────────────────
  const renderDeltaCards = () => {
    if (!baselineScan || !comparisonScan) return null
    const b = baselineScan, c = comparisonScan
    const riskB = riskScore(b), riskC = riskScore(c)
    const riskDelta = riskC - riskB

    const cards: { label: string; bVal: number; cVal: number; delta: number; colorUp: string; colorDown: string }[] = [
      { label: 'Total Findings', bVal: b.total_findings, cVal: c.total_findings, delta: c.total_findings - b.total_findings, colorUp: 'bg-red-100 text-red-700', colorDown: 'bg-green-100 text-green-700' },
      { label: 'Critical', bVal: b.critical_count, cVal: c.critical_count, delta: c.critical_count - b.critical_count, colorUp: 'bg-red-100 text-red-700', colorDown: 'bg-green-100 text-green-700' },
      { label: 'High', bVal: b.high_count, cVal: c.high_count, delta: c.high_count - b.high_count, colorUp: 'bg-orange-100 text-orange-700', colorDown: 'bg-green-100 text-green-700' },
      { label: 'Medium', bVal: b.medium_count, cVal: c.medium_count, delta: c.medium_count - b.medium_count, colorUp: 'bg-amber-100 text-amber-700', colorDown: 'bg-green-100 text-green-700' },
      { label: 'Low', bVal: b.low_count, cVal: c.low_count, delta: c.low_count - b.low_count, colorUp: 'bg-yellow-100 text-yellow-700', colorDown: 'bg-green-100 text-green-700' },
      { label: 'Info', bVal: b.info_count, cVal: c.info_count, delta: c.info_count - b.info_count, colorUp: 'bg-blue-100 text-blue-700', colorDown: 'bg-blue-100 text-blue-700' },
    ]

    return (
      <div className="space-y-4">
        {/* Risk trend banner */}
        <div className={`rounded-xl border p-4 flex items-center gap-3 ${riskDelta > 0 ? 'bg-red-50 border-red-200' : riskDelta < 0 ? 'bg-green-50 border-green-200' : 'bg-slate-50 border-slate-200'}`}>
          {riskDelta > 0 ? <TrendingUp className="w-5 h-5 text-red-600" /> : riskDelta < 0 ? <TrendingDown className="w-5 h-5 text-green-600" /> : <Minus className="w-5 h-5 text-slate-500" />}
          <div>
            <p className={`text-sm font-semibold ${riskDelta > 0 ? 'text-red-800' : riskDelta < 0 ? 'text-green-800' : 'text-slate-700'}`}>
              {riskDelta > 0 ? '▲ Increased Risk' : riskDelta < 0 ? '▼ Decreased Risk' : '= Stable Risk'}
            </p>
            <p className="text-xs text-slate-500">
              Risk score: {riskB.toFixed(1)} → {riskC.toFixed(1)} · Duration: {elapsed(b.started_at, b.completed_at)} → {elapsed(c.started_at, c.completed_at)}
            </p>
          </div>
        </div>

        {/* Delta metric cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {cards.map(card => (
            <div key={card.label} className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center">
              <p className="text-xs text-slate-500 font-medium mb-2">{card.label}</p>
              <div className="flex items-center justify-center gap-2 mb-1.5">
                <span className="text-lg font-bold text-slate-900">{card.bVal}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
                <span className="text-lg font-bold text-slate-900">{card.cVal}</span>
              </div>
              <DeltaBadge value={card.delta} color={card.delta > 0 ? card.colorUp : card.colorDown} />
            </div>
          ))}
        </div>

        {/* Diff summary row */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-emerald-50 rounded-xl border border-emerald-200 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <Plus className="w-4 h-4 text-emerald-600" />
              <span className="text-2xl font-bold text-emerald-700">{diff.newFindings.length}</span>
            </div>
            <p className="text-xs font-medium text-emerald-600">New Findings</p>
          </div>
          <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <CheckCircle2 className="w-4 h-4 text-blue-600" />
              <span className="text-2xl font-bold text-blue-700">{diff.persistent.length}</span>
            </div>
            <p className="text-xs font-medium text-blue-600">Persistent</p>
          </div>
          <div className="bg-rose-50 rounded-xl border border-rose-200 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <XCircle className="w-4 h-4 text-rose-600" />
              <span className="text-2xl font-bold text-rose-700">{diff.resolved.length}</span>
            </div>
            <p className="text-xs font-medium text-rose-600">Resolved</p>
          </div>
        </div>
      </div>
    )
  }

  // ── SECTION 3: Vulnerability Diff Table ─────────────
  const renderVulnTable = (vulns: Vulnerability[], isPersistent = false, persistentPairs?: { baseline: Vulnerability; comparison: Vulnerability }[]) => {
    const items = isPersistent ? (persistentPairs ?? []) : vulns
    if (items.length === 0) {
      return (
        <div className="text-center py-12 text-slate-400">
          <Search className="w-8 h-8 mx-auto mb-2 opacity-40" />
          <p>No {activeTab === 'new' ? 'new' : activeTab === 'resolved' ? 'resolved' : 'persistent'} findings</p>
        </div>
      )
    }

    return (
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr className="text-xs uppercase text-slate-500">
              <th className="px-4 py-3 text-left font-medium">Severity</th>
              <th className="px-4 py-3 text-left font-medium">Title</th>
              <th className="px-4 py-3 text-left font-medium">OWASP</th>
              <th className="px-4 py-3 text-left font-medium">CWE</th>
              <th className="px-4 py-3 text-left font-medium">CVSS</th>
              <th className="px-4 py-3 text-left font-medium">Confidence</th>
              <th className="px-4 py-3 text-left font-medium">Endpoint</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              {isPersistent && <th className="px-4 py-3 text-left font-medium">Changes</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isPersistent
              ? (persistentPairs ?? []).map(({ baseline: bv, comparison: cv }) => {
                  const sevChanged = bv.severity !== cv.severity
                  const confChanged = Math.round(bv.confidence * 100) !== Math.round(cv.confidence * 100)
                  const cvssChanged = (bv.cvss_score ?? 0) !== (cv.cvss_score ?? 0)
                  return (
                    <tr key={cv.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3"><SeverityBadge severity={cv.severity} /></td>
                      <td className="px-4 py-3"><span className="text-sm font-medium text-slate-900">{cv.title}</span></td>
                      <td className="px-4 py-3 text-sm text-slate-600">{cv.owasp_category}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{cv.cwe_id ?? '—'}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{cv.cvss_score ?? '—'}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{Math.round(cv.confidence * 100)}%</td>
                      <td className="px-4 py-3"><code className="text-xs text-cyan-600 font-mono">{cv.endpoint_url ?? '—'}</code></td>
                      <td className="px-4 py-3"><StatusBadge status={cv.status} isValidated={cv.is_validated} /></td>
                      <td className="px-4 py-3">
                        <div className="space-y-1 text-xs">
                          {sevChanged && <span className="block text-amber-700">Sev: {bv.severity} → {cv.severity}</span>}
                          {confChanged && <span className="block text-blue-700">Conf: {Math.round(bv.confidence * 100)}% → {Math.round(cv.confidence * 100)}%</span>}
                          {cvssChanged && <span className="block text-red-700">CVSS: {bv.cvss_score ?? 0} → {cv.cvss_score ?? 0}</span>}
                          {!sevChanged && !confChanged && !cvssChanged && <span className="text-slate-400">No change</span>}
                        </div>
                      </td>
                    </tr>
                  )
                })
              : vulns.map(v => (
                  <tr key={v.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3"><SeverityBadge severity={v.severity} /></td>
                    <td className="px-4 py-3"><span className="text-sm font-medium text-slate-900">{v.title}</span></td>
                    <td className="px-4 py-3 text-sm text-slate-600">{v.owasp_category}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{v.cwe_id ?? '—'}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{v.cvss_score ?? '—'}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{Math.round(v.confidence * 100)}%</td>
                    <td className="px-4 py-3"><code className="text-xs text-cyan-600 font-mono">{v.endpoint_url ?? '—'}</code></td>
                    <td className="px-4 py-3"><StatusBadge status={v.status} isValidated={v.is_validated} /></td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>
    )
  }

  const renderDiffTable = () => {
    const tabs = [
      { key: 'new' as const, label: `+ New (${diff.newFindings.length})`, color: 'text-emerald-700 border-emerald-500' },
      { key: 'persistent' as const, label: `= Persistent (${diff.persistent.length})`, color: 'text-blue-700 border-blue-500' },
      { key: 'resolved' as const, label: `− Resolved (${diff.resolved.length})`, color: 'text-rose-700 border-rose-500' },
    ]
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="border-b border-slate-200 flex">
          {tabs.map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`px-5 py-3 text-sm font-medium transition-colors border-b-2 ${activeTab === tab.key ? tab.color : 'text-slate-500 border-transparent hover:text-slate-700'}`}>
              {tab.label}
            </button>
          ))}
        </div>
        {activeTab === 'new' && renderVulnTable(diff.newFindings)}
        {activeTab === 'persistent' && renderVulnTable([], true, diff.persistent)}
        {activeTab === 'resolved' && renderVulnTable(diff.resolved)}
      </div>
    )
  }

  // ── SECTION 4: Severity Distribution Chart ───────────
  const renderSeverityChart = () => {
    if (!baselineScan || !comparisonScan) return null
    const b = baselineScan, c = comparisonScan
    const severities: { label: string; bVal: number; cVal: number; barColor: string; bgColor: string }[] = [
      { label: 'Critical', bVal: b.critical_count, cVal: c.critical_count, barColor: 'bg-red-500', bgColor: 'bg-red-100' },
      { label: 'High', bVal: b.high_count, cVal: c.high_count, barColor: 'bg-orange-500', bgColor: 'bg-orange-100' },
      { label: 'Medium', bVal: b.medium_count, cVal: c.medium_count, barColor: 'bg-amber-500', bgColor: 'bg-amber-100' },
      { label: 'Low', bVal: b.low_count, cVal: c.low_count, barColor: 'bg-green-500', bgColor: 'bg-green-100' },
      { label: 'Info', bVal: b.info_count, cVal: c.info_count, barColor: 'bg-blue-500', bgColor: 'bg-blue-100' },
    ]
    const maxVal = Math.max(1, ...severities.flatMap(s => [s.bVal, s.cVal]))

    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-base font-semibold text-slate-900 mb-1">Severity Distribution</h3>
        <p className="text-sm text-slate-500 mb-5">Side-by-side severity breakdown across both scans</p>

        <div className="flex items-center gap-6 mb-5 text-xs font-medium text-slate-500">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-slate-800 inline-block" /> Baseline</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-cyan-500 inline-block" /> Comparison</span>
        </div>

        <div className="space-y-4">
          {severities.map(s => (
            <div key={s.label}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-slate-700 w-16">{s.label}</span>
                <span className="text-xs text-slate-400">{s.bVal} → {s.cVal}</span>
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 w-6 text-right">B</span>
                  <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-slate-700 rounded-full transition-all duration-500"
                      style={{ width: `${(s.bVal / maxVal) * 100}%` }} />
                  </div>
                  <span className="text-xs font-semibold text-slate-700 w-6">{s.bVal}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 w-6 text-right">C</span>
                  <div className="flex-1 h-4 bg-cyan-50 rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                      style={{ width: `${(s.cVal / maxVal) * 100}%` }} />
                  </div>
                  <span className="text-xs font-semibold text-cyan-700 w-6">{s.cVal}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ── SECTION 5: Scan Metadata Side-by-Side ──────────
  const renderMetadata = () => {
    if (!baselineScan || !comparisonScan) return null
    const validatedBase = baseVulns.filter(v => v.is_validated).length
    const validatedComp = compVulns.filter(v => v.is_validated).length
    const fpBase = baseVulns.filter(v => v.is_false_positive).length
    const fpComp = compVulns.filter(v => v.is_false_positive).length

    const rows: { label: string; baseVal: string; compVal: string; mono?: boolean }[] = [
      { label: 'Scan ID', baseVal: baselineScan.scan_id, compVal: comparisonScan.scan_id, mono: true },
      { label: 'Target URL', baseVal: baselineScan.target_url, compVal: comparisonScan.target_url },
      { label: 'Scan Type', baseVal: baselineScan.scan_type, compVal: comparisonScan.scan_type },
      { label: 'Status', baseVal: baselineScan.status, compVal: comparisonScan.status },
      { label: 'Created At', baseVal: fmtDate(baselineScan.created_at), compVal: fmtDate(comparisonScan.created_at) },
      { label: 'Started At', baseVal: fmtDate(baselineScan.started_at), compVal: fmtDate(comparisonScan.started_at) },
      { label: 'Completed At', baseVal: fmtDate(baselineScan.completed_at), compVal: fmtDate(comparisonScan.completed_at) },
      { label: 'Duration', baseVal: elapsed(baselineScan.started_at, baselineScan.completed_at), compVal: elapsed(comparisonScan.started_at, comparisonScan.completed_at) },
      { label: 'Progress', baseVal: `${baselineScan.progress_percentage}%`, compVal: `${comparisonScan.progress_percentage}%` },
      { label: 'Total Findings', baseVal: String(baselineScan.total_findings), compVal: String(comparisonScan.total_findings) },
      { label: 'Validated', baseVal: String(validatedBase), compVal: String(validatedComp) },
      { label: 'False Positives', baseVal: String(fpBase), compVal: String(fpComp) },
      { label: 'Endpoints', baseVal: String(baselineScan.endpoints_discovered ?? 0), compVal: String(comparisonScan.endpoints_discovered ?? 0) },
    ]

    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="text-base font-semibold text-slate-900">Scan Metadata</h3>
          <p className="text-sm text-slate-500 mt-0.5">Side-by-side scan details</p>
        </div>
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr className="text-xs uppercase text-slate-500">
              <th className="px-6 py-3 text-left font-medium w-1/4">Field</th>
              <th className="px-6 py-3 text-left font-medium w-[37.5%]">Baseline</th>
              <th className="px-6 py-3 text-left font-medium w-[37.5%]">Comparison</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map(r => {
              const changed = r.baseVal !== r.compVal
              return (
                <tr key={r.label} className={changed ? 'bg-amber-50/40' : ''}>
                  <td className="px-6 py-3 text-sm font-medium text-slate-700">{r.label}</td>
                  <td className={`px-6 py-3 text-sm ${r.mono ? 'font-mono text-xs' : ''} text-slate-600`}>{r.baseVal}</td>
                  <td className={`px-6 py-3 text-sm ${r.mono ? 'font-mono text-xs' : ''} ${changed ? 'text-cyan-700 font-medium' : 'text-slate-600'}`}>{r.compVal}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    )
  }

  // ── RENDER ──────────────────────────────────────────
  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">Side-by-side comparison of two scan results against the same target</p>
      {renderSelector()}
      {compared && baselineScan && comparisonScan && (
        <>
          {renderDeltaCards()}
          {renderDiffTable()}
          {renderSeverityChart()}
          {renderMetadata()}
        </>
      )}
    </div>
  )
}
