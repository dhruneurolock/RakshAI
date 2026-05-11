import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Shield,
  LayoutDashboard,
  ScanSearch,
  FileText,
  Github,
  LogOut,
  Target,
  Bug,
  ChevronDown,
  TrendingUp,
  Gauge,
  PlusCircle,
  Radio,
  History,
  GitCompare,
  CalendarClock,
  Globe2,
  Cpu,
  Network,
  List,
  ShieldAlert,
  Link2,
  Ban,
  ClipboardCheck,
  FileStack,
  Layers,
  Share2,
  Activity,
} from 'lucide-react'

interface NavChild {
  name: string
  href: string
}

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  children: NavChild[]
}

const navigation: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    children: [
      { name: 'Overview', href: '/dashboard' },
      { name: 'Trends & Analytics', href: '/dashboard/trends' },
      { name: 'Risk Score', href: '/dashboard/risk-score' },
    ],
  },
  {
    name: 'Scans',
    href: '/scans',
    icon: ScanSearch,
    children: [
      { name: 'New Scan', href: '/scans' },
      { name: 'Active Scans', href: '/scans/active' },
      { name: 'Scan History', href: '/scans/history' },
      { name: 'Scan Comparison', href: '/scans/compare' },
      { name: 'Scheduled Scans', href: '/scans/scheduled' },
    ],
  },
  {
    name: 'Attack Surface',
    href: '/attack-surface',
    icon: Target,
    children: [
      { name: 'Endpoints', href: '/attack-surface' },
      { name: 'Technologies', href: '/attack-surface/technologies' },
      { name: 'API Map', href: '/attack-surface/api-map' },
      { name: 'Subdomains', href: '/attack-surface/subdomains' },
    ],
  },
  {
    name: 'Findings',
    href: '/vulnerabilities',
    icon: Bug,
    children: [
      { name: 'All Findings', href: '/vulnerabilities' },
      { name: 'By OWASP Category', href: '/vulnerabilities/owasp' },
      { name: 'Exploit Chains', href: '/vulnerabilities/chains' },
      { name: 'False Positives', href: '/vulnerabilities/false-positives' },
      { name: 'Remediation Tracker', href: '/vulnerabilities/remediation' },
    ],
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: FileText,
    children: [
      { name: 'Generate Report', href: '/reports' },
      { name: 'Report History', href: '/reports/history' },
      { name: 'Report Templates', href: '/reports/templates' },
      { name: 'Export & Share', href: '/reports/export' },
    ],
  },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>({})

  // Auto-expand the module that contains the current route
  useEffect(() => {
    const activeModule = navigation.find(
      (item) =>
        location.pathname === item.href ||
        item.children.some((child) => location.pathname === child.href) ||
        (item.href !== '/' && location.pathname.startsWith(item.href))
    )
    if (activeModule) {
      setExpandedModules((prev) => ({ ...prev, [activeModule.name]: true }))
    }
  }, [location.pathname])

  const toggleModule = (moduleName: string) => {
    setExpandedModules((prev) => ({ ...prev, [moduleName]: !prev[moduleName] }))
  }

  const isChildActive = (href: string) => location.pathname === href

  const isModuleActive = (item: NavItem) =>
    location.pathname === item.href ||
    item.children.some((child) => location.pathname === child.href) ||
    (item.href !== '/' && location.pathname.startsWith(item.href))

  // Find active breadcrumb label
  const activeModule = navigation.find((item) => isModuleActive(item))
  const activeChild = activeModule?.children.find((child) => isChildActive(child.href))
  const headerTitle = activeChild
    ? `${activeModule?.name} › ${activeChild.name}`
    : activeModule?.name || 'Dashboard'

  const childIcons: Record<string, React.ElementType> = {
    // Dashboard
    'Overview': LayoutDashboard,
    'Trends & Analytics': TrendingUp,
    'Risk Score': Gauge,
    // Scans
    'New Scan': PlusCircle,
    'Active Scans': Radio,
    'Scan History': History,
    'Scan Comparison': GitCompare,
    'Scheduled Scans': CalendarClock,
    // Attack Surface
    'Endpoints': Globe2,
    'Technologies': Cpu,
    'API Map': Network,
    'Subdomains': Globe2,
    // Findings
    'All Findings': List,
    'By OWASP Category': ShieldAlert,
    'Exploit Chains': Link2,
    'False Positives': Ban,
    'Remediation Tracker': ClipboardCheck,
    // Reports
    'Generate Report': PlusCircle,
    'Report History': FileStack,
    'Report Templates': Layers,
    'Export & Share': Share2,
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-cyan-50 text-slate-900">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 border-r border-slate-800 bg-[#0f1117] text-slate-100 shadow-[0_0_40px_rgba(15,23,42,0.22)] flex flex-col">
        <div className="flex items-center gap-3 p-6 border-b border-slate-800 bg-[#0f1117]">
          <div className="rounded-xl bg-cyan-500/10 p-2 ring-1 ring-cyan-500/30">
            <Shield className="w-7 h-7 text-cyan-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold">RakshAI</h1>
            <p className="text-xs text-slate-400">Rule-Based Pentesting</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin">
          {navigation.map((item) => {
            const Icon = item.icon
            const isExpanded = expandedModules[item.name] ?? false
            const isActive = isModuleActive(item)

            return (
              <div key={item.name}>
                {/* Parent module button */}
                <button
                  onClick={() => toggleModule(item.name)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                    isActive
                      ? 'bg-slate-800/80 text-white'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-[18px] h-[18px] ${isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-400'}`} />
                    <span className="font-medium text-sm">{item.name}</span>
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${
                      isExpanded ? 'rotate-180' : ''
                    }`}
                  />
                </button>

                {/* Submodule list */}
                <div
                  className={`overflow-hidden transition-all duration-200 ease-in-out ${
                    isExpanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="ml-3 pl-3 border-l border-slate-700/50 mt-1 mb-1 space-y-0.5">
                    {item.children.map((child) => {
                      const ChildIcon = childIcons[child.name] || List
                      const childActive = isChildActive(child.href)
                      return (
                        <Link
                          key={child.href}
                          to={child.href}
                          className={`flex items-center gap-2.5 px-3 py-2 rounded-md transition-all duration-150 text-[13px] ${
                            childActive
                              ? 'bg-cyan-500/15 text-cyan-400 font-medium'
                              : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40'
                          }`}
                        >
                          <ChildIcon className={`w-3.5 h-3.5 ${childActive ? 'text-cyan-400' : 'text-slate-600'}`} />
                          {child.name}
                        </Link>
                      )
                    })}
                  </div>
                </div>
              </div>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-800 bg-[#0f1117]">
          <button
            onClick={() => {
              localStorage.removeItem('isAuthenticated')
              navigate('/login')
            }}
            className="flex items-center gap-3 px-4 py-2 mb-3 w-full text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">Sign Out</span>
          </button>
          <Link
            to="/diagnostics"
            className={`flex items-center gap-3 px-4 py-2 mb-3 w-full rounded-lg transition-colors ${
              location.pathname === '/diagnostics'
                ? 'bg-violet-500/15 text-violet-400'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span className="text-sm">System Diagnostics</span>
          </Link>
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <Github className="w-4 h-4" />
            <span>v2.0.0 • Evidence-First</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Audit-Ready • 100% Explainable
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64">
        <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-slate-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-slate-900">
              {headerTitle}
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-600">OWASP Top 10:2025 • Evidence-First</span>
              <div className="w-2 h-2 bg-emerald-500 rounded-full shadow-[0_0_0_4px_rgba(16,185,129,0.15)]" title="System Online"></div>
            </div>
          </div>
        </header>

        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
