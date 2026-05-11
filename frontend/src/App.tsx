import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Scans from './pages/Scans'
import ScanDetail from './pages/ScanDetail'
import AttackSurface from './pages/AttackSurface'
import Vulnerabilities from './pages/Vulnerabilities'
import VulnerabilityDetail from './pages/VulnerabilityDetail'
import Reports from './pages/Reports'
import EvidenceViewer from './pages/EvidenceViewer'
import AuditTrail from './pages/AuditTrail'
import Governance from './pages/Governance'
import Diagnostics from './pages/Diagnostics'

// Dashboard submodules
import TrendsAnalytics from './pages/dashboard/TrendsAnalytics'
import RiskScore from './pages/dashboard/RiskScore'

// Scans submodules
import ActiveScans from './pages/scans/ActiveScans'
import ScanHistory from './pages/scans/ScanHistory'
import ScanComparison from './pages/scans/ScanComparison'
import ScheduledScans from './pages/scans/ScheduledScans'

// Attack Surface submodules
import Technologies from './pages/attack-surface/Technologies'
import ApiMap from './pages/attack-surface/ApiMap'
import Subdomains from './pages/attack-surface/Subdomains'

// Findings submodules
import ByOwaspCategory from './pages/findings/ByOwaspCategory'
import ExploitChains from './pages/findings/ExploitChains'
import FalsePositives from './pages/findings/FalsePositives'
import RemediationTracker from './pages/findings/RemediationTracker'

// Reports submodules
import ReportHistory from './pages/reports/ReportHistory'
import ReportTemplates from './pages/reports/ReportTemplates'
import ExportShare from './pages/reports/ExportShare'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard */}
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="dashboard/trends" element={<TrendsAnalytics />} />
        <Route path="dashboard/risk-score" element={<RiskScore />} />

        {/* Scans */}
        <Route path="scans" element={<Scans />} />
        <Route path="scans/:scanId" element={<ScanDetail />} />
        <Route path="scans/active" element={<ActiveScans />} />
        <Route path="scans/history" element={<ScanHistory />} />
        <Route path="scans/compare" element={<ScanComparison />} />
        <Route path="scans/scheduled" element={<ScheduledScans />} />

        {/* Attack Surface */}
        <Route path="attack-surface" element={<AttackSurface />} />
        <Route path="attack-surface/technologies" element={<Technologies />} />
        <Route path="attack-surface/api-map" element={<ApiMap />} />
        <Route path="attack-surface/subdomains" element={<Subdomains />} />

        {/* Findings */}
        <Route path="vulnerabilities" element={<Vulnerabilities />} />
        <Route path="vulnerabilities/:vulnId" element={<VulnerabilityDetail />} />
        <Route path="vulnerabilities/owasp" element={<ByOwaspCategory />} />
        <Route path="vulnerabilities/chains" element={<ExploitChains />} />
        <Route path="vulnerabilities/false-positives" element={<FalsePositives />} />
        <Route path="vulnerabilities/remediation" element={<RemediationTracker />} />

        {/* Reports */}
        <Route path="reports" element={<Reports />} />
        <Route path="reports/history" element={<ReportHistory />} />
        <Route path="reports/templates" element={<ReportTemplates />} />
        <Route path="reports/export" element={<ExportShare />} />

        {/* Legacy routes (kept for backward compatibility) */}
        <Route path="evidence" element={<EvidenceViewer />} />
        <Route path="audit" element={<AuditTrail />} />
        <Route path="governance" element={<Governance />} />
        <Route path="diagnostics" element={<Diagnostics />} />
      </Route>
    </Routes>
  )
}

export default App
