import { Globe2, Construction, Search, Shield } from 'lucide-react'

export default function Subdomains() {
  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Subdomain enumeration results for scanned targets
      </p>

      <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 mb-6">
          <Globe2 className="w-8 h-8 text-cyan-600" />
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">Subdomain Enumeration</h3>
        <p className="text-slate-500 max-w-md mx-auto mb-6">
          Discover subdomains associated with the target domain to expand the attack surface and identify shadow IT or forgotten services.
        </p>

        <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 flex items-center gap-3 max-w-lg mx-auto mb-8">
          <Construction className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div className="text-left">
            <p className="text-sm font-medium text-amber-800">Coming Soon</p>
            <p className="text-xs text-amber-700">
              Subdomain discovery and DNS enumeration will be added to the reconnaissance agent.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          {[
            { icon: Search, label: 'DNS Enumeration', desc: 'Brute-force and dictionary-based subdomain discovery' },
            { icon: Globe2, label: 'Certificate Transparency', desc: 'Query CT logs for issued certificates' },
            { icon: Shield, label: 'Passive Discovery', desc: 'Search engine and threat intel feeds' },
          ].map((item) => {
            const Icon = item.icon
            return (
              <div key={item.label} className="bg-slate-50 rounded-xl border border-slate-200 p-5 text-left opacity-60">
                <Icon className="w-5 h-5 text-cyan-600 mb-3" />
                <p className="text-sm font-semibold text-slate-700">{item.label}</p>
                <p className="text-xs text-slate-500 mt-1">{item.desc}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
