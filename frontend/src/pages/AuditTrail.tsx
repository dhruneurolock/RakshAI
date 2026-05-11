import { useState, useEffect } from 'react'
import { auditAPI } from '../services/endpoints'
import type { AuditLogEntry, AuditStats } from '../types'

const CATEGORY_COLORS: Record<string, string> = {
  scan: '#3b82f6',
  finding: '#ef4444',
  evidence: '#8b5cf6',
  report: '#22c55e',
  governance: '#f59e0b',
  system: '#6b7280',
}

const ACTION_ICONS: Record<string, string> = {
  scan_created: '🚀',
  finding_validated: '✅',
  evidence_accessed: '🔬',
  report_generated: '📄',
  policy_created: '📋',
  policy_changed: '⚙️',
  correlation_run: '🔗',
}

export default function AuditTrail() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [stats, setStats] = useState<AuditStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    category: '',
    action: '',
    days: 30,
  })
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null)
  const [verifyResult, setVerifyResult] = useState<{ valid: boolean; message: string } | null>(null)

  useEffect(() => {
    loadData()
  }, [filters])

  async function loadData() {
    setLoading(true)
    try {
      const [logsData, statsData] = await Promise.all([
        auditAPI.list({
          category: filters.category || undefined,
          action: filters.action || undefined,
          limit: 200,
        }),
        auditAPI.stats(filters.days),
      ])
      setLogs(logsData)
      setStats(statsData)
    } catch (err) {
      console.error('Failed to load audit data:', err)
    }
    setLoading(false)
  }

  async function verifyIntegrity(auditId: string) {
    try {
      const result = await auditAPI.verify(auditId)
      setVerifyResult({
        valid: result.integrity_valid,
        message: result.message,
      })
    } catch (err) {
      setVerifyResult({ valid: false, message: 'Verification failed' })
    }
  }

  return (
    <div style={{ padding: '0' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
        padding: '2rem',
        borderRadius: '16px',
        marginBottom: '1.5rem',
        border: '1px solid rgba(99, 102, 241, 0.2)',
      }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
          🛡️ Audit Trail
        </h1>
        <p style={{ color: '#94a3b8', marginTop: '0.5rem', fontSize: '0.9rem' }}>
          Immutable record of all security-relevant actions
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem',
        }}>
          <div style={{
            background: 'rgba(30, 27, 75, 0.4)', padding: '1.25rem', borderRadius: '12px',
            border: '1px solid rgba(99, 102, 241, 0.15)',
          }}>
            <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>TOTAL ENTRIES</p>
            <p style={{ color: '#e2e8f0', fontSize: '1.75rem', fontWeight: 700, margin: '0.25rem 0 0' }}>
              {stats.total_entries.toLocaleString()}
            </p>
          </div>
          <div style={{
            background: 'rgba(30, 27, 75, 0.4)', padding: '1.25rem', borderRadius: '12px',
            border: '1px solid rgba(34, 197, 94, 0.15)',
          }}>
            <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>SUCCESS RATE</p>
            <p style={{ color: '#4ade80', fontSize: '1.75rem', fontWeight: 700, margin: '0.25rem 0 0' }}>
              {stats.success_rate}%
            </p>
          </div>
          <div style={{
            background: 'rgba(30, 27, 75, 0.4)', padding: '1.25rem', borderRadius: '12px',
            border: '1px solid rgba(239, 68, 68, 0.15)',
          }}>
            <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>FAILURES</p>
            <p style={{ color: '#f87171', fontSize: '1.75rem', fontWeight: 700, margin: '0.25rem 0 0' }}>
              {stats.failures}
            </p>
          </div>
          <div style={{
            background: 'rgba(30, 27, 75, 0.4)', padding: '1.25rem', borderRadius: '12px',
            border: '1px solid rgba(251, 191, 36, 0.15)',
          }}>
            <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>CATEGORIES</p>
            <p style={{ color: '#fbbf24', fontSize: '1.75rem', fontWeight: 700, margin: '0.25rem 0 0' }}>
              {Object.keys(stats.by_category).length}
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{
        display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap',
      }}>
        {['', 'scan', 'finding', 'evidence', 'report', 'governance', 'system'].map(cat => (
          <button
            key={cat}
            onClick={() => setFilters(f => ({ ...f, category: cat }))}
            style={{
              padding: '0.4rem 0.9rem',
              borderRadius: '20px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 600,
              background: filters.category === cat
                ? (CATEGORY_COLORS[cat] || '#6366f1') + '33'
                : 'rgba(255,255,255,0.05)',
              color: filters.category === cat
                ? (CATEGORY_COLORS[cat] || '#a5b4fc')
                : '#94a3b8',
              transition: 'all 0.2s',
            }}
          >
            {cat || 'All'}
          </button>
        ))}
      </div>

      {/* Audit Log Table */}
      <div style={{
        background: 'rgba(30, 27, 75, 0.3)', borderRadius: '12px',
        border: '1px solid rgba(99, 102, 241, 0.1)', overflow: 'hidden',
      }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
            Loading audit logs...
          </div>
        ) : logs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
            <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</p>
            <p>No audit log entries found</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(99, 102, 241, 0.15)' }}>
                {['Time', 'Action', 'Category', 'User', 'Resource', 'Status', 'Verify'].map(h => (
                  <th key={h} style={{
                    padding: '0.75rem 1rem', textAlign: 'left', color: '#94a3b8',
                    fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr
                  key={log.audit_id}
                  onClick={() => setSelectedLog(log)}
                  style={{
                    borderBottom: '1px solid rgba(99, 102, 241, 0.05)',
                    cursor: 'pointer',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(99, 102, 241, 0.05)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={{ padding: '0.6rem 1rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                    {new Date(log.occurred_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '0.6rem 1rem', color: '#e2e8f0', fontSize: '0.85rem', fontWeight: 500 }}>
                    {ACTION_ICONS[log.action] || '🔹'} {log.action}
                  </td>
                  <td style={{ padding: '0.6rem 1rem' }}>
                    <span style={{
                      padding: '0.15rem 0.5rem', borderRadius: '10px', fontSize: '0.7rem', fontWeight: 600,
                      background: (CATEGORY_COLORS[log.category] || '#6b7280') + '22',
                      color: CATEGORY_COLORS[log.category] || '#6b7280',
                    }}>
                      {log.category}
                    </span>
                  </td>
                  <td style={{ padding: '0.6rem 1rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                    {log.user_id || '—'}
                  </td>
                  <td style={{ padding: '0.6rem 1rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                    {log.resource_type ? `${log.resource_type}:${log.resource_id?.slice(0, 8)}...` : '—'}
                  </td>
                  <td style={{ padding: '0.6rem 1rem' }}>
                    <span style={{
                      display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%',
                      background: log.success ? '#22c55e' : '#ef4444',
                    }} />
                  </td>
                  <td style={{ padding: '0.6rem 1rem' }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); verifyIntegrity(log.audit_id) }}
                      style={{
                        padding: '0.2rem 0.5rem', borderRadius: '6px', border: 'none',
                        background: 'rgba(99, 102, 241, 0.1)', color: '#a5b4fc',
                        fontSize: '0.7rem', cursor: 'pointer',
                      }}
                    >
                      🔒 Verify
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Verification Result Toast */}
      {verifyResult && (
        <div
          style={{
            position: 'fixed', bottom: '2rem', right: '2rem',
            padding: '1rem 1.5rem', borderRadius: '12px',
            background: verifyResult.valid ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${verifyResult.valid ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            color: verifyResult.valid ? '#4ade80' : '#f87171',
            fontSize: '0.85rem', fontWeight: 600, zIndex: 1000,
            animation: 'slideUp 0.3s ease',
          }}
          onClick={() => setVerifyResult(null)}
        >
          {verifyResult.valid ? '✅' : '⚠️'} {verifyResult.message}
        </div>
      )}

      {/* Detail Modal */}
      {selectedLog && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 999,
          }}
          onClick={() => setSelectedLog(null)}
        >
          <div
            style={{
              background: '#1e1b4b', borderRadius: '16px', padding: '2rem',
              maxWidth: '600px', width: '90%', maxHeight: '80vh', overflowY: 'auto',
              border: '1px solid rgba(99, 102, 241, 0.3)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{ color: '#e2e8f0', margin: '0 0 1rem 0' }}>
              Audit Entry: {selectedLog.audit_id}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              {[
                ['Action', selectedLog.action],
                ['Category', selectedLog.category],
                ['User', selectedLog.user_id || '—'],
                ['IP', selectedLog.ip_address || '—'],
                ['Resource', `${selectedLog.resource_type}:${selectedLog.resource_id}`],
                ['Status', selectedLog.success ? '✅ Success' : '❌ Failed'],
                ['Time', new Date(selectedLog.occurred_at).toLocaleString()],
              ].map(([label, value]) => (
                <div key={label as string}>
                  <p style={{ color: '#94a3b8', fontSize: '0.7rem', margin: '0 0 0.15rem', textTransform: 'uppercase' }}>
                    {label}
                  </p>
                  <p style={{ color: '#e2e8f0', fontSize: '0.85rem', margin: 0 }}>{value}</p>
                </div>
              ))}
            </div>
            {selectedLog.details && (
              <div style={{ marginTop: '1rem' }}>
                <p style={{ color: '#94a3b8', fontSize: '0.7rem', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                  Details
                </p>
                <pre style={{
                  background: '#0f172a', padding: '1rem', borderRadius: '8px', fontSize: '0.75rem',
                  color: '#a5b4fc', overflow: 'auto', maxHeight: '200px',
                }}>
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
