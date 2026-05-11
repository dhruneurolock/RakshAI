import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, FileText, ShieldAlert, Sparkles, CheckCircle2, Clock3, Target, FileScan } from 'lucide-react'
import { scansAPI, vulnerabilitiesAPI } from '@/services/endpoints'
import type { Report, Scan } from '@/types'

type ReportType = 'executive' | 'technical' | 'compliance'
type ExportFormat = 'all' | 'pdf' | 'word' | 'excel'
type ToastState = { type: 'success' | 'error'; message: string } | null

const reportTypeCards: { id: ReportType; title: string; description: string }[] = [
  {
    id: 'executive',
    title: 'Executive Summary',
    description: 'High-level overview for leadership with business risk and remediation priorities.',
  },
  {
    id: 'technical',
    title: 'Technical Report',
    description: 'Detailed analysis for security engineers with evidence, PoC context, and fix guidance.',
  },
  {
    id: 'compliance',
    title: 'Compliance Report',
    description: 'Audit-ready report mapped to OWASP and control frameworks for regulatory use.',
  },
]

const exportFormats: { id: ExportFormat; title: string; description: string }[] = [
  { id: 'all', title: 'All Formats', description: 'Generate PDF, Word, and Excel in one request.' },
  { id: 'pdf', title: 'PDF Document', description: 'Professional formatted report with charts and tables.' },
  { id: 'word', title: 'Word Document', description: 'Editable document for internal review and redlining.' },
  { id: 'excel', title: 'Excel Workbook', description: 'Tabular export for tracking and compliance review.' },
]

const complianceOptions = [
  { id: 'owasp', title: 'OWASP Top 10', description: 'Map findings to OWASP Top 10 (2021) categories.' },
  { id: 'iso27001', title: 'ISO 27001', description: 'Information security management control mapping.' },
  { id: 'soc2', title: 'SOC 2', description: 'Service Organization Control 2 compliance mapping.' },
]

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function severityCount(scan: Scan | undefined, key: 'critical_count' | 'high_count' | 'medium_count' | 'low_count' | 'info_count') {
  return scan?.[key] ?? 0
}

function formatDate(value?: string | null) {
  if (!value) return 'N/A'
  return new Date(value).toLocaleDateString(undefined, {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function Reports() {
  const queryClient = useQueryClient()
  const [selectedScanId, setSelectedScanId] = useState<string>('')
  const [selectedReportType, setSelectedReportType] = useState<ReportType>('compliance')
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('all')
  const [selectedStandards, setSelectedStandards] = useState<string[]>(['owasp'])
  const [toast, setToast] = useState<ToastState>(null)

  const { data: scans = [], isLoading: scansLoading } = useQuery<Scan[]>({
    queryKey: ['scans'],
    queryFn: () => scansAPI.list(),
  })

  useEffect(() => {
    if (!selectedScanId && scans.length > 0) {
      const preferred = scans.find((scan) => (scan.status ?? '').toLowerCase() === 'completed') ?? scans[0]
      setSelectedScanId(String(preferred.id))
    }
  }, [scans, selectedScanId])

  const selectedScan = useMemo(
    () => scans.find((scan) => String(scan.id) === selectedScanId),
    [scans, selectedScanId]
  )

  const { data: scanReports = [], isLoading: reportsLoading } = useQuery<Report[]>({
    queryKey: ['scan-reports', selectedScan?.scan_id],
    queryFn: () => (selectedScan ? scansAPI.getReports(selectedScan.scan_id) : Promise.resolve([])),
    enabled: !!selectedScan,
  })

  const { data: totalVulns = [], isLoading: vulnsLoading } = useQuery({
    queryKey: ['reports-vulnerabilities', selectedScan?.id],
    queryFn: () => (selectedScan ? vulnerabilitiesAPI.list({ scan_id: selectedScan.id }) : Promise.resolve([])),
    enabled: !!selectedScan,
  })

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedScan) {
        throw new Error('Select a scan first')
      }

      try {
        await scansAPI.generateReport(selectedScan.scan_id, selectedFormat)
      } catch (error) {
        // Fallback: if Excel generation fails, try downloading latest existing Excel report.
        if (selectedFormat === 'excel') {
          const existingReports = await scansAPI.getReports(selectedScan.scan_id)
          const latestExcel = existingReports.find((report) =>
            ['xlsx', 'excel'].includes((report.report_type ?? '').toLowerCase())
          )

          if (latestExcel) {
            window.open(`${API_BASE_URL}/api/v1/reports/${latestExcel.report_id}/download`, '_blank', 'noopener,noreferrer')
            setToast({ type: 'success', message: 'Latest Excel report downloaded.' })
            return
          }
        }

        throw error
      }
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['scan-reports', selectedScan?.scan_id] })

      if (!selectedScan || selectedFormat === 'all') {
        return
      }

      const refreshedReports = await queryClient.fetchQuery({
        queryKey: ['scan-reports', selectedScan.scan_id],
        queryFn: () => scansAPI.getReports(selectedScan.scan_id),
      })

      const formatMap: Record<ExportFormat, string[]> = {
        all: ['pdf', 'docx', 'xlsx', 'json'],
        pdf: ['pdf'],
        word: ['docx', 'word'],
        excel: ['xlsx', 'excel'],
      }

      const wantedTypes = formatMap[selectedFormat]
      const latestMatch = refreshedReports.find((report) =>
        wantedTypes.includes((report.report_type ?? '').toLowerCase())
      )

      if (latestMatch) {
        window.open(`${API_BASE_URL}/api/v1/reports/${latestMatch.report_id}/download`, '_blank', 'noopener,noreferrer')
        const extensionMap: Record<string, string> = {
          pdf: '.pdf',
          docx: '.docx',
          xlsx: '.xlsx',
          json: '.json',
        }
        const fileExt = extensionMap[(latestMatch.report_type || '').toLowerCase()] || ''
        setToast({ type: 'success', message: `Report generated and download started${fileExt ? ` (${fileExt})` : ''}.` })
      } else {
        setToast({ type: 'success', message: 'Report generated successfully.' })
      }
    },
    onError: () => {
      setToast({ type: 'error', message: 'Unable to generate report. Please try again.' })
    },
  })

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 4000)
    return () => clearTimeout(timer)
  }, [toast])

  const toggleStandard = (id: string) => {
    setSelectedStandards((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    )
  }

  const completedCount = scans.filter((scan) => (scan.status ?? '').toLowerCase() === 'completed').length
  const totalFindings = selectedScan?.total_findings ?? 0
  const reportFeatures = [
    'Executive summary',
    'Detailed vulnerability analysis',
    'Risk assessment matrix',
    'Remediation prioritization',
    'Compliance mapping',
    'Trend analysis',
  ]

  return (
    <div className="space-y-6 bg-gradient-to-br from-slate-50 via-white to-cyan-50 min-h-[calc(100vh-7rem)] p-1 md:p-0">
      {toast && (
        <div
          className={`fixed top-5 right-5 z-50 rounded-xl border px-4 py-3 text-sm shadow-lg backdrop-blur ${
            toast.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
              : 'border-red-200 bg-red-50 text-red-900'
          }`}
          role="status"
          aria-live="polite"
        >
          {toast.message}
        </div>
      )}
      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.55fr)_420px] gap-6">
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6 md:p-8">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <p className="text-sm font-medium text-cyan-700">Generate comprehensive security reports</p>
                <h3 className="mt-2 text-2xl font-semibold text-slate-900">Report Configuration</h3>
                <p className="mt-1 text-sm text-slate-500">Customize report content, compliance scope, and export format.</p>
              </div>
              <div className="rounded-xl border border-cyan-200 bg-cyan-50 px-4 py-3 text-sm text-cyan-900">
                <div className="font-semibold">Ready to generate</div>
                <div className="text-cyan-700">{completedCount} completed scans available</div>
              </div>
            </div>

            <div className="mt-8 space-y-6">
              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Target className="h-4 w-4 text-cyan-600" />
                  Target URL
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <select
                    value={selectedScanId}
                    onChange={(event) => setSelectedScanId(event.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                    disabled={scansLoading || scans.length === 0}
                  >
                    {scans.length === 0 ? (
                      <option value="">No scans available</option>
                    ) : (
                      scans.map((scan) => (
                        <option key={scan.id} value={String(scan.id)}>
                          {scan.target_url} ({(scan.status ?? 'unknown').toUpperCase()} - {formatDate(scan.created_at)})
                        </option>
                      ))
                    )}
                  </select>
                  <p className="mt-2 text-xs text-slate-500">
                    Select a target to generate and download reports for that specific scan.
                  </p>
                </div>
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <FileText className="h-4 w-4 text-cyan-600" />
                  Report Type
                </div>
                <div className="space-y-3">
                  {reportTypeCards.map((card) => (
                    <button
                      key={card.id}
                      onClick={() => setSelectedReportType(card.id)}
                      className={`w-full rounded-xl border px-4 py-4 text-left transition-all ${
                        selectedReportType === card.id
                          ? 'border-cyan-300 bg-cyan-50 shadow-sm'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`mt-1 h-3 w-3 rounded-full ${selectedReportType === card.id ? 'bg-cyan-500' : 'bg-slate-300'}`} />
                        <div>
                          <div className="font-semibold text-slate-900">{card.title}</div>
                          <div className="text-sm text-slate-500">{card.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <ShieldAlert className="h-4 w-4 text-cyan-600" />
                  Compliance Standards
                </div>
                <div className="grid gap-3">
                  {complianceOptions.map((option) => {
                    const checked = selectedStandards.includes(option.id)
                    return (
                      <label
                        key={option.id}
                        className={`flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-4 transition-colors ${
                          checked ? 'border-cyan-300 bg-cyan-50' : 'border-slate-200 bg-white hover:bg-slate-50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleStandard(option.id)}
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
                        />
                        <div>
                          <div className="font-medium text-slate-900">{option.title}</div>
                          <div className="text-sm text-slate-500">{option.description}</div>
                        </div>
                      </label>
                    )
                  })}
                </div>
              </section>

              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Download className="h-4 w-4 text-cyan-600" />
                  Export Format
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  {exportFormats.map((format) => (
                    <button
                      key={format.id}
                      onClick={() => setSelectedFormat(format.id)}
                      className={`rounded-xl border px-4 py-4 text-left transition-colors ${
                        selectedFormat === format.id
                          ? 'border-cyan-300 bg-cyan-50'
                          : 'border-slate-200 bg-white hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center gap-2 text-cyan-700">
                        <FileScan className="h-4 w-4" />
                        <span className="font-semibold text-slate-900">{format.title}</span>
                      </div>
                      <div className="mt-1 text-sm text-slate-500">{format.description}</div>
                    </button>
                  ))}
                </div>
              </section>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-slate-200 pt-6">
              <button
                onClick={() => generateMutation.mutate()}
                disabled={!selectedScan || generateMutation.isPending}
                className="inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Sparkles className="h-4 w-4" />
                {generateMutation.isPending ? 'Generating Report…' : 'Generate Report'}
              </button>
              {generateMutation.isError && (
                <p className="text-sm text-red-600">Unable to generate the report. Latest available report can still be downloaded from Recent Reports.</p>
              )}
              {!selectedScan && !scansLoading && (
                <p className="text-sm text-amber-600">No completed scan selected.</p>
              )}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
            {[
              { label: 'Total Findings', value: totalFindings, tone: 'text-slate-900' },
              { label: 'Critical', value: severityCount(selectedScan, 'critical_count'), tone: 'text-red-600' },
              { label: 'High', value: severityCount(selectedScan, 'high_count'), tone: 'text-orange-500' },
              { label: 'Medium', value: severityCount(selectedScan, 'medium_count'), tone: 'text-amber-500' },
              { label: 'Low', value: severityCount(selectedScan, 'low_count'), tone: 'text-emerald-600' },
              { label: 'Info', value: severityCount(selectedScan, 'info_count'), tone: 'text-blue-600' },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="text-sm text-slate-500">{item.label}</div>
                <div className={`mt-2 text-3xl font-semibold ${item.tone}`}>{item.value}</div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
            <h3 className="flex items-center gap-2 text-base font-semibold text-slate-900">
              <Target className="h-4 w-4 text-cyan-600" />
              Report Features
            </h3>
            <ul className="mt-4 grid gap-3 md:grid-cols-2 text-sm text-slate-600">
              {reportFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                  <CheckCircle2 className="h-4 w-4 text-cyan-600" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900">Report Summary</h3>
            <div className="mt-5 space-y-4 text-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <span className="text-slate-500">Total Findings</span>
                <span className="font-semibold text-slate-900">{selectedScan?.total_findings ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Critical</span>
                <span className="font-semibold text-red-600">{severityCount(selectedScan, 'critical_count')}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">High</span>
                <span className="font-semibold text-orange-500">{severityCount(selectedScan, 'high_count')}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Medium</span>
                <span className="font-semibold text-amber-500">{severityCount(selectedScan, 'medium_count')}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Low</span>
                <span className="font-semibold text-emerald-600">{severityCount(selectedScan, 'low_count')}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Info</span>
                <span className="font-semibold text-blue-600">{severityCount(selectedScan, 'info_count')}</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900">Scan Information</h3>
            <div className="mt-5 space-y-4 text-sm">
              <div className="flex items-start gap-3">
                <Clock3 className="mt-0.5 h-4 w-4 text-cyan-600" />
                <div>
                  <div className="text-slate-500">Scan Date</div>
                  <div className="font-medium text-slate-900">{formatDate(selectedScan?.created_at)}</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Target className="mt-0.5 h-4 w-4 text-cyan-600" />
                <div>
                  <div className="text-slate-500">Target</div>
                  <div className="font-medium break-all text-slate-900">{selectedScan?.target_url ?? 'No scan selected'}</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <ShieldAlert className="mt-0.5 h-4 w-4 text-cyan-600" />
                <div>
                  <div className="text-slate-500">Status</div>
                  <div className="font-medium text-slate-900 capitalize">{selectedScan?.status ?? 'Unknown'}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-6 shadow-sm">
            <h3 className="text-base font-semibold text-cyan-900">Recent Reports</h3>
            <div className="mt-4 space-y-3">
              {reportsLoading || scansLoading || vulnsLoading ? (
                <div className="text-sm text-cyan-800/70">Loading reports…</div>
              ) : scanReports.length > 0 ? (
                scanReports.slice(0, 5).map((report) => (
                  <a
                    key={report.report_id}
                    href={`http://localhost:8000/api/v1/reports/${report.report_id}/download`}
                    className="flex items-center justify-between rounded-xl border border-cyan-200 bg-white px-4 py-3 text-sm transition-colors hover:bg-cyan-50"
                  >
                    <div>
                      <div className="font-medium text-slate-900 uppercase">{report.report_type}</div>
                      <div className="text-slate-500">{formatDate(report.generated_at)}</div>
                    </div>
                    <Download className="h-4 w-4 text-cyan-600" />
                  </a>
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-cyan-200 bg-white px-4 py-5 text-sm text-cyan-800/80">
                  No reports generated yet. Use the button on the left to create one.
                </div>
              )}
            </div>
          </div>

        </aside>
      </div>
    </div>
  )
}
