import { ClipboardCheck, Construction, CheckCircle2, Clock, ArrowRight, RotateCcw } from 'lucide-react'

export default function RemediationTracker() {
  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Track remediation progress for discovered vulnerabilities
      </p>

      <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 mb-6">
          <ClipboardCheck className="w-8 h-8 text-cyan-600" />
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">Remediation Tracker</h3>
        <p className="text-slate-500 max-w-lg mx-auto mb-6">
          Track the lifecycle of every vulnerability from discovery to fix verification. Assign owners, set deadlines, and validate remediation.
        </p>

        <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 flex items-center gap-3 max-w-lg mx-auto mb-8">
          <Construction className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div className="text-left">
            <p className="text-sm font-medium text-amber-800">Coming Soon</p>
            <p className="text-xs text-amber-700">
              Remediation workflow tracking with SLA monitoring and assignment is under development.
            </p>
          </div>
        </div>

        {/* Workflow Mockup */}
        <div className="flex items-center justify-center gap-3 flex-wrap max-w-2xl mx-auto mb-8">
          {[
            { icon: Clock, label: 'Open', desc: 'Newly discovered', color: 'bg-red-100 border-red-200 text-red-700' },
            { icon: RotateCcw, label: 'In Progress', desc: 'Being remediated', color: 'bg-amber-100 border-amber-200 text-amber-700' },
            { icon: CheckCircle2, label: 'Fixed', desc: 'Patch applied', color: 'bg-blue-100 border-blue-200 text-blue-700' },
            { icon: ClipboardCheck, label: 'Verified', desc: 'Re-scan confirms fix', color: 'bg-emerald-100 border-emerald-200 text-emerald-700' },
          ].map((step, i, arr) => {
            const Icon = step.icon
            return (
              <div key={step.label} className="flex items-center gap-3">
                <div className={`rounded-xl border px-4 py-3 text-left ${step.color}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-semibold">{step.label}</span>
                  </div>
                  <p className="text-xs opacity-80">{step.desc}</p>
                </div>
                {i < arr.length - 1 && <ArrowRight className="w-4 h-4 text-slate-300 flex-shrink-0" />}
              </div>
            )
          })}
        </div>

        {/* Placeholder stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
          {[
            { label: 'Open', value: '—', color: 'text-red-600' },
            { label: 'In Progress', value: '—', color: 'text-amber-600' },
            { label: 'Fixed', value: '—', color: 'text-blue-600' },
            { label: 'Verified', value: '—', color: 'text-emerald-600' },
          ].map((stat) => (
            <div key={stat.label} className="bg-slate-50 rounded-xl border border-slate-200 p-4 opacity-60">
              <p className="text-sm text-slate-500">{stat.label}</p>
              <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
