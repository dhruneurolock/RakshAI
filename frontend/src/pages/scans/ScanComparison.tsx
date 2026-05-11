import { GitCompare, ArrowRight, Construction } from 'lucide-react'

export default function ScanComparison() {
  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Side-by-side comparison of two scan results against the same target
      </p>

      <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 mb-6">
          <GitCompare className="w-8 h-8 text-cyan-600" />
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">Scan Comparison</h3>
        <p className="text-slate-500 max-w-md mx-auto mb-6">
          Compare two scans of the same target side-by-side to identify new, resolved, and persistent vulnerabilities across scan iterations.
        </p>

        <div className="max-w-2xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center mb-8">
            <div className="bg-slate-50 rounded-xl border border-dashed border-slate-300 p-6 text-center">
              <p className="text-sm font-medium text-slate-600">Baseline Scan</p>
              <p className="text-xs text-slate-400 mt-1">Select first scan</p>
            </div>
            <div className="flex justify-center">
              <ArrowRight className="w-6 h-6 text-slate-300" />
            </div>
            <div className="bg-slate-50 rounded-xl border border-dashed border-slate-300 p-6 text-center">
              <p className="text-sm font-medium text-slate-600">Comparison Scan</p>
              <p className="text-xs text-slate-400 mt-1">Select second scan</p>
            </div>
          </div>

          <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 flex items-center gap-3">
            <Construction className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <div className="text-left">
              <p className="text-sm font-medium text-amber-800">Coming Soon</p>
              <p className="text-xs text-amber-700">
                This feature is being developed. It will allow comparing vulnerability deltas, showing new findings, resolved issues, and regression tracking.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          <div className="bg-slate-50 rounded-lg p-4 text-left">
            <p className="text-sm font-semibold text-emerald-700">+ New Findings</p>
            <p className="text-xs text-slate-500 mt-1">Vulnerabilities found only in the comparison scan</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 text-left">
            <p className="text-sm font-semibold text-blue-700">= Persistent</p>
            <p className="text-xs text-slate-500 mt-1">Vulnerabilities present in both scans</p>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 text-left">
            <p className="text-sm font-semibold text-red-700">− Resolved</p>
            <p className="text-xs text-slate-500 mt-1">Vulnerabilities present only in the baseline</p>
          </div>
        </div>
      </div>
    </div>
  )
}
