import { Network, Construction, GitBranch, ArrowRight } from 'lucide-react'

export default function ApiMap() {
  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Visual API route tree and graph visualization
      </p>

      <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 mb-6">
          <Network className="w-8 h-8 text-cyan-600" />
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">API Map</h3>
        <p className="text-slate-500 max-w-md mx-auto mb-6">
          Visualize discovered API routes as an interactive tree or graph. Identify endpoint relationships, parameter flows, and authentication boundaries.
        </p>

        <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 flex items-center gap-3 max-w-lg mx-auto mb-8">
          <Construction className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div className="text-left">
            <p className="text-sm font-medium text-amber-800">Coming Soon</p>
            <p className="text-xs text-amber-700">
              Interactive API graph visualization powered by the Neo4j attack graph is under development.
            </p>
          </div>
        </div>

        {/* Visual mockup of API tree */}
        <div className="max-w-md mx-auto text-left bg-slate-900 rounded-xl p-6 text-sm font-mono">
          <div className="text-cyan-400">/ <span className="text-slate-500">(root)</span></div>
          <div className="ml-4">
            <div className="flex items-center gap-2 text-slate-300">
              <GitBranch className="w-3 h-3 text-slate-500" />
              <span className="text-emerald-400">/api</span>
            </div>
            <div className="ml-6">
              <div className="flex items-center gap-2 text-slate-300">
                <GitBranch className="w-3 h-3 text-slate-500" />
                <span className="text-emerald-400">/v1</span>
              </div>
              <div className="ml-6 space-y-1">
                <div className="flex items-center gap-2 text-slate-400">
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-blue-400">/scans</span>
                  <span className="text-slate-600 text-xs">GET, POST</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-blue-400">/vulnerabilities</span>
                  <span className="text-slate-600 text-xs">GET</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <ArrowRight className="w-3 h-3" />
                  <span className="text-blue-400">/reports</span>
                  <span className="text-slate-600 text-xs">GET, POST</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
