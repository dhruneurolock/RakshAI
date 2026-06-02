import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scheduledScansAPI } from '@/services/endpoints'
import type { ScheduledScan, ScheduledScanCreate } from '@/types'
import {
  CalendarClock, Plus, Trash2, Zap, X, Clock,
  ChevronDown, CalendarDays, RotateCcw, Activity
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const FREQ_OPTIONS = ['hourly', 'daily', 'weekly', 'monthly', 'custom'] as const
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function FreqBadge({ freq }: { freq: string }) {
  const map: Record<string, string> = {
    hourly: 'bg-blue-100 text-blue-700',
    daily: 'bg-cyan-100 text-cyan-700',
    weekly: 'bg-violet-100 text-violet-700',
    monthly: 'bg-amber-100 text-amber-700',
    custom: 'bg-slate-100 text-slate-700',
  }
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${map[freq] ?? map.custom}`}>
      {freq}
    </span>
  )
}

// ════════════════════════════════════════════════════════
// MAIN COMPONENT
// ════════════════════════════════════════════════════════
export default function ScheduledScans() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState<Partial<ScheduledScanCreate>>({ frequency: 'daily', scan_type: 'full', hour: 2, minute: 0 })

  const { data: schedules = [], isLoading } = useQuery({
    queryKey: ['scheduled-scans'],
    queryFn: scheduledScansAPI.list,
    refetchInterval: 15000,
  })

  const createMut = useMutation({
    mutationFn: scheduledScansAPI.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['scheduled-scans'] }); setShowModal(false); resetForm() },
  })
  const deleteMut = useMutation({
    mutationFn: scheduledScansAPI.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduled-scans'] }),
  })
  const toggleMut = useMutation({
    mutationFn: scheduledScansAPI.toggle,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduled-scans'] }),
  })
  const triggerMut = useMutation({
    mutationFn: scheduledScansAPI.trigger,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['scheduled-scans'] }),
  })

  const resetForm = () => setForm({ frequency: 'daily', scan_type: 'full', hour: 2, minute: 0 })

  const handleCreate = () => {
    if (!form.name || !form.target_url || !form.frequency) return
    createMut.mutate(form as ScheduledScanCreate)
  }

  const stats = useMemo(() => ({
    total: schedules.length,
    active: schedules.filter(s => s.is_active).length,
    totalRuns: schedules.reduce((sum, s) => sum + s.total_runs, 0),
    nextUp: schedules.filter(s => s.is_active).sort((a, b) =>
      new Date(a.next_run_at).getTime() - new Date(b.next_run_at).getTime()
    )[0] ?? null,
  }), [schedules])

  // ── Summary Cards ──────────────────────────────────
  const renderStats = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-2">
          <CalendarDays className="w-4 h-4 text-cyan-600" />
          <span className="text-xs font-medium text-slate-500 uppercase">Total Schedules</span>
        </div>
        <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-4 h-4 text-emerald-600" />
          <span className="text-xs font-medium text-slate-500 uppercase">Active</span>
        </div>
        <p className="text-2xl font-bold text-emerald-700">{stats.active}</p>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-2">
          <RotateCcw className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-medium text-slate-500 uppercase">Total Executions</span>
        </div>
        <p className="text-2xl font-bold text-slate-900">{stats.totalRuns}</p>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="w-4 h-4 text-amber-600" />
          <span className="text-xs font-medium text-slate-500 uppercase">Next Upcoming</span>
        </div>
        {stats.nextUp ? (
          <div>
            <p className="text-sm font-semibold text-slate-900 truncate">{stats.nextUp.name}</p>
            <p className="text-xs text-slate-500">{formatDistanceToNow(new Date(stats.nextUp.next_run_at), { addSuffix: true })}</p>
          </div>
        ) : (
          <p className="text-sm text-slate-400">No active schedules</p>
        )}
      </div>
    </div>
  )

  // ── Schedule Table ─────────────────────────────────
  const renderTable = () => (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Scheduled Scans</h3>
          <p className="text-sm text-slate-500 mt-0.5">{schedules.length} schedule{schedules.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={() => { resetForm(); setShowModal(true) }}
          className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-medium px-4 py-2 rounded-lg transition-colors text-sm">
          <Plus className="w-4 h-4" /> New Schedule
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32 text-slate-400">Loading...</div>
      ) : schedules.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <CalendarClock className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p>No scheduled scans yet</p>
          <p className="text-xs mt-1">Create your first schedule to automate security assessments</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-xs uppercase text-slate-500">
                <th className="px-5 py-3 text-left font-medium">Name</th>
                <th className="px-5 py-3 text-left font-medium">Target</th>
                <th className="px-5 py-3 text-left font-medium">Frequency</th>
                <th className="px-5 py-3 text-left font-medium">Next Run</th>
                <th className="px-5 py-3 text-left font-medium">Last Run</th>
                <th className="px-5 py-3 text-left font-medium">Runs</th>
                <th className="px-5 py-3 text-left font-medium">Status</th>
                <th className="px-5 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {schedules.map((s: ScheduledScan) => (
                <tr key={s.schedule_id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-3">
                    <span className="text-sm font-medium text-slate-900">{s.name}</span>
                    <span className="block text-xs text-slate-400 capitalize">{s.scan_type} scan</span>
                  </td>
                  <td className="px-5 py-3">
                    <span className="text-sm text-slate-600 truncate block max-w-[180px]">{s.target_url}</span>
                  </td>
                  <td className="px-5 py-3"><FreqBadge freq={s.frequency} /></td>
                  <td className="px-5 py-3 text-sm text-slate-600">
                    {s.is_active ? formatDistanceToNow(new Date(s.next_run_at), { addSuffix: true }) : '—'}
                  </td>
                  <td className="px-5 py-3 text-sm text-slate-500">
                    {s.last_run_at ? formatDistanceToNow(new Date(s.last_run_at), { addSuffix: true }) : 'Never'}
                  </td>
                  <td className="px-5 py-3 text-sm font-semibold text-slate-700">{s.total_runs}</td>
                  <td className="px-5 py-3">
                    <button onClick={() => toggleMut.mutate(s.schedule_id)}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${s.is_active ? 'bg-emerald-500' : 'bg-slate-300'}`}>
                      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${s.is_active ? 'translate-x-4' : 'translate-x-0.5'}`} />
                    </button>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => triggerMut.mutate(s.schedule_id)} title="Trigger now"
                        className="p-1.5 text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors">
                        <Zap className="w-4 h-4" />
                      </button>
                      <button onClick={() => { if (window.confirm('Delete this schedule?')) deleteMut.mutate(s.schedule_id) }}
                        title="Delete" className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )

  // ── Create Modal ───────────────────────────────────
  const renderModal = () => {
    if (!showModal) return null
    const freq = form.frequency || 'daily'
    return (
      <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShowModal(false)}>
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900">New Scheduled Scan</h3>
            <button onClick={() => setShowModal(false)} className="p-1 text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
          </div>
          <div className="p-6 space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Schedule Name</label>
              <input value={form.name || ''} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Nightly API Scan" className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
            </div>
            {/* Target URL */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Target URL</label>
              <input value={form.target_url || ''} onChange={e => setForm(f => ({ ...f, target_url: e.target.value }))}
                placeholder="https://example.com" className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
            </div>
            {/* Scan Type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Scan Type</label>
              <div className="relative">
                <select value={form.scan_type || 'full'} onChange={e => setForm(f => ({ ...f, scan_type: e.target.value }))}
                  className="w-full appearance-none border border-slate-300 rounded-lg px-3 py-2.5 pr-8 text-sm focus:outline-none focus:border-cyan-500">
                  <option value="full">Full Scan</option>
                  <option value="quick">Quick Scan</option>
                  <option value="targeted">Targeted Scan</option>
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>
            {/* Frequency */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Frequency</label>
              <div className="grid grid-cols-5 gap-2">
                {FREQ_OPTIONS.map(f => (
                  <button key={f} onClick={() => setForm(prev => ({ ...prev, frequency: f }))}
                    className={`py-2 rounded-lg text-xs font-medium capitalize transition-colors ${freq === f ? 'bg-cyan-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
            {/* Time Config */}
            {(freq === 'daily' || freq === 'weekly' || freq === 'monthly') && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Hour (0-23)</label>
                  <input type="number" min={0} max={23} value={form.hour ?? 2}
                    onChange={e => setForm(f => ({ ...f, hour: parseInt(e.target.value) || 0 }))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Minute (0-59)</label>
                  <input type="number" min={0} max={59} value={form.minute ?? 0}
                    onChange={e => setForm(f => ({ ...f, minute: parseInt(e.target.value) || 0 }))}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500" />
                </div>
              </div>
            )}
            {freq === 'weekly' && (
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Day of Week</label>
                <div className="relative">
                  <select value={form.day_of_week ?? 0} onChange={e => setForm(f => ({ ...f, day_of_week: parseInt(e.target.value) }))}
                    className="w-full appearance-none border border-slate-300 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:border-cyan-500">
                    {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>
            )}
            {freq === 'monthly' && (
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Day of Month (1-28)</label>
                <input type="number" min={1} max={28} value={form.day_of_month ?? 1}
                  onChange={e => setForm(f => ({ ...f, day_of_month: parseInt(e.target.value) || 1 }))}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500" />
              </div>
            )}
            {freq === 'custom' && (
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Cron Expression</label>
                <input value={form.cron_expression || ''} onChange={e => setForm(f => ({ ...f, cron_expression: e.target.value }))}
                  placeholder="0 2 * * 1" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-cyan-500" />
                <p className="text-[11px] text-slate-400 mt-1">Format: minute hour day-of-month month day-of-week</p>
              </div>
            )}
          </div>
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-2xl">
            <button onClick={() => setShowModal(false)}
              className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-100 transition-colors">
              Cancel
            </button>
            <button onClick={handleCreate} disabled={createMut.isPending || !form.name || !form.target_url}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-cyan-600 rounded-lg hover:bg-cyan-700 transition-colors disabled:opacity-40">
              <CalendarClock className="w-4 h-4" />
              {createMut.isPending ? 'Creating...' : 'Create Schedule'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">Configure recurring and cron-based automated security scans</p>
      {renderStats()}
      {renderTable()}
      {renderModal()}
    </div>
  )
}
