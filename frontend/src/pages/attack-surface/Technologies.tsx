import { Cpu, Construction, Server, Code2, Database, Globe } from 'lucide-react'

export default function Technologies() {
  return (
    <div className="space-y-6">
      <p className="text-slate-500 text-sm">
        Detected technology stack across scanned targets
      </p>

      <div className="bg-white rounded-xl border border-slate-200 p-12 shadow-sm text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-50 to-blue-50 mb-6">
          <Cpu className="w-8 h-8 text-cyan-600" />
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">Technology Detection</h3>
        <p className="text-slate-500 max-w-md mx-auto mb-6">
          Automatically identify web frameworks, servers, libraries, and CMS platforms used by the target application to reveal known vulnerability patterns.
        </p>

        <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 flex items-center gap-3 max-w-lg mx-auto mb-8">
          <Construction className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div className="text-left">
            <p className="text-sm font-medium text-amber-800">Coming Soon</p>
            <p className="text-xs text-amber-700">
              Technology fingerprinting is being integrated into the reconnaissance agent.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
          {[
            { icon: Server, label: 'Web Servers', desc: 'Apache, Nginx, IIS' },
            { icon: Code2, label: 'Frameworks', desc: 'React, Django, Laravel' },
            { icon: Database, label: 'Databases', desc: 'MySQL, PostgreSQL, MongoDB' },
            { icon: Globe, label: 'CMS', desc: 'WordPress, Drupal, Joomla' },
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
