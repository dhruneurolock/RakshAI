import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { evidenceAPI } from '../services/endpoints'
import type { EvidenceRecord, EvidencePair, FindingLineageChain } from '../types'

const STAGE_COLORS: Record<string, string> = {
  discovered: '#3b82f6',
  rule_selected: '#8b5cf6',
  payload_bound: '#f59e0b',
  executed: '#ef4444',
  validated: '#22c55e',
  reported: '#06b6d4',
}

const STAGE_ICONS: Record<string, string> = {
  discovered: '🔍',
  rule_selected: '📋',
  payload_bound: '🔗',
  executed: '⚡',
  validated: '✅',
  reported: '📄',
}

export default function EvidenceViewer() {
  const [searchParams] = useSearchParams()
  const vulnId = searchParams.get('vulnerability_id')
  const scanId = searchParams.get('scan_id')

  const [evidence, setEvidence] = useState<EvidenceRecord[]>([])
  const [pair, setPair] = useState<EvidencePair | null>(null)
  const [chain, setChain] = useState<FindingLineageChain | null>(null)
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'evidence' | 'lineage' | 'comparison'>('evidence')

  useEffect(() => {
    loadData()
  }, [vulnId, scanId])

  async function loadData() {
    setLoading(true)
    try {
      if (vulnId) {
        const vid = parseInt(vulnId)
        const [evList, pairData, chainData] = await Promise.all([
          evidenceAPI.list({ vulnerability_id: vid }),
          evidenceAPI.getBaselineAttackPair(vid).catch(() => null),
          evidenceAPI.getLineageChain(vid).catch(() => null),
        ])
        setEvidence(evList)
        setPair(pairData)
        setChain(chainData)
      } else if (scanId) {
        const evList = await evidenceAPI.list({ scan_id: parseInt(scanId) })
        setEvidence(evList)
      }
    } catch (err) {
      console.error('Failed to load evidence:', err)
    }
    setLoading(false)
  }

  function formatHeaders(headers: Record<string, any> | null): string {
    if (!headers) return ''
    return Object.entries(headers)
      .map(([k, v]) => `${k}: ${v}`)
      .join('\n')
  }

  function getStatusColor(code: number | null): string {
    if (!code) return '#6b7280'
    if (code < 300) return '#22c55e'
    if (code < 400) return '#f59e0b'
    if (code < 500) return '#ef4444'
    return '#dc2626'
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center', color: '#9ca3af' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem', animation: 'pulse 2s infinite' }}>🔬</div>
          <p>Loading evidence...</p>
        </div>
      </div>
    )
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
          🔬 Evidence Viewer
        </h1>
        <p style={{ color: '#94a3b8', marginTop: '0.5rem', fontSize: '0.9rem' }}>
          {chain ? `Finding: ${chain.title}` : `${evidence.length} evidence records`}
        </p>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          {(['evidence', 'lineage', 'comparison'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: 600,
                background: activeTab === tab ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                color: activeTab === tab ? '#a5b4fc' : '#94a3b8',
                transition: 'all 0.2s',
              }}
            >
              {tab === 'evidence' && '📦 Artifacts'}
              {tab === 'lineage' && '🔗 Lineage'}
              {tab === 'comparison' && '⚖️ Comparison'}
            </button>
          ))}
        </div>
      </div>

      {/* Evidence List Tab */}
      {activeTab === 'evidence' && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedEvidence ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
          {/* Evidence List */}
          <div>
            {evidence.length === 0 ? (
              <div style={{
                background: 'rgba(30, 27, 75, 0.3)', padding: '3rem', borderRadius: '12px',
                textAlign: 'center', color: '#94a3b8', border: '1px solid rgba(99, 102, 241, 0.1)',
              }}>
                <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</p>
                <p>No evidence records found</p>
              </div>
            ) : (
              evidence.map(ev => (
                <div
                  key={ev.evidence_id}
                  onClick={() => setSelectedEvidence(ev)}
                  style={{
                    background: selectedEvidence?.evidence_id === ev.evidence_id
                      ? 'rgba(99, 102, 241, 0.15)'
                      : 'rgba(30, 27, 75, 0.3)',
                    padding: '1rem',
                    borderRadius: '10px',
                    marginBottom: '0.75rem',
                    cursor: 'pointer',
                    border: selectedEvidence?.evidence_id === ev.evidence_id
                      ? '1px solid rgba(99, 102, 241, 0.4)'
                      : '1px solid rgba(99, 102, 241, 0.1)',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{
                        padding: '0.25rem 0.5rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 700,
                        background: ev.is_baseline ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: ev.is_baseline ? '#4ade80' : '#f87171',
                      }}>
                        {ev.is_baseline ? 'BASELINE' : 'ATTACK'}
                      </span>
                      <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '0.85rem' }}>
                        {ev.http_method} {ev.request_url?.split('?')[0]?.slice(-40)}
                      </span>
                    </div>
                    <span style={{
                      color: getStatusColor(ev.response_status_code),
                      fontWeight: 700, fontSize: '0.85rem',
                    }}>
                      {ev.response_status_code || '—'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                    <span>🔧 {ev.tool_name || 'manual'}</span>
                    <span>📂 {ev.phase || 'unknown'}</span>
                    {ev.response_time_ms && <span>⏱ {ev.response_time_ms}ms</span>}
                    <span>📅 {new Date(ev.captured_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Detail Panel */}
          {selectedEvidence && (
            <div style={{
              background: 'rgba(30, 27, 75, 0.4)', borderRadius: '12px', padding: '1.5rem',
              border: '1px solid rgba(99, 102, 241, 0.15)', position: 'sticky', top: '1rem',
              maxHeight: 'calc(100vh - 200px)', overflowY: 'auto',
            }}>
              <h3 style={{ color: '#e2e8f0', margin: '0 0 1rem 0', fontSize: '1rem' }}>
                📋 {selectedEvidence.evidence_id}
              </h3>

              {/* Request */}
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#a5b4fc', fontSize: '0.8rem', marginBottom: '0.5rem' }}>REQUEST</h4>
                <pre style={{
                  background: '#0f172a', padding: '1rem', borderRadius: '8px', fontSize: '0.75rem',
                  color: '#22c55e', overflow: 'auto', maxHeight: '200px', whiteSpace: 'pre-wrap',
                  border: '1px solid rgba(34, 197, 94, 0.2)',
                }}>
{`${selectedEvidence.http_method} ${selectedEvidence.request_url}\n${formatHeaders(selectedEvidence.request_headers)}${selectedEvidence.request_body ? '\n\n' + selectedEvidence.request_body : ''}`}
                </pre>
              </div>

              {/* Response */}
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ color: '#a5b4fc', fontSize: '0.8rem', marginBottom: '0.5rem' }}>RESPONSE</h4>
                <pre style={{
                  background: '#0f172a', padding: '1rem', borderRadius: '8px', fontSize: '0.75rem',
                  color: '#f87171', overflow: 'auto', maxHeight: '300px', whiteSpace: 'pre-wrap',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                }}>
{`HTTP ${selectedEvidence.response_status_code}\n${formatHeaders(selectedEvidence.response_headers)}\n\n${selectedEvidence.response_body || '(empty body)'}`}
                </pre>
              </div>

              {/* Payload */}
              {selectedEvidence.payload_value && (
                <div>
                  <h4 style={{ color: '#a5b4fc', fontSize: '0.8rem', marginBottom: '0.5rem' }}>PAYLOAD</h4>
                  <pre style={{
                    background: '#0f172a', padding: '1rem', borderRadius: '8px', fontSize: '0.75rem',
                    color: '#fbbf24', overflow: 'auto', whiteSpace: 'pre-wrap',
                    border: '1px solid rgba(251, 191, 36, 0.2)',
                  }}>
                    {selectedEvidence.payload_value}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Lineage Timeline Tab */}
      {activeTab === 'lineage' && chain && (
        <div style={{
          background: 'rgba(30, 27, 75, 0.3)', borderRadius: '12px', padding: '2rem',
          border: '1px solid rgba(99, 102, 241, 0.1)',
        }}>
          <h3 style={{ color: '#e2e8f0', margin: '0 0 1.5rem 0' }}>
            🔗 Finding Lineage: {chain.title}
          </h3>

          {chain.lineage.length === 0 ? (
            <p style={{ color: '#94a3b8' }}>No lineage events recorded for this finding.</p>
          ) : (
            <div style={{ position: 'relative', paddingLeft: '2rem' }}>
              {/* Vertical line */}
              <div style={{
                position: 'absolute', left: '0.9rem', top: '0.5rem', bottom: '0.5rem',
                width: '2px', background: 'rgba(99, 102, 241, 0.3)',
              }} />

              {chain.lineage.map((event, idx) => (
                <div key={event.lineage_id} style={{ position: 'relative', marginBottom: '1.5rem' }}>
                  {/* Dot */}
                  <div style={{
                    position: 'absolute', left: '-1.65rem', top: '0.25rem',
                    width: '14px', height: '14px', borderRadius: '50%',
                    background: STAGE_COLORS[event.stage] || '#6b7280',
                    border: '2px solid #0f172a',
                  }} />

                  <div style={{
                    background: 'rgba(15, 23, 42, 0.6)', padding: '1rem', borderRadius: '10px',
                    border: `1px solid ${STAGE_COLORS[event.stage] || '#6b7280'}33`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '0.9rem' }}>
                        {STAGE_ICONS[event.stage] || '🔹'} {event.stage.toUpperCase()}
                      </span>
                      <span style={{ color: '#64748b', fontSize: '0.75rem' }}>
                        {new Date(event.occurred_at).toLocaleString()}
                      </span>
                    </div>
                    {event.agent_name && (
                      <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0.25rem 0 0' }}>
                        Agent: {event.agent_name}
                      </p>
                    )}
                    {event.rule_id && (
                      <p style={{ color: '#a78bfa', fontSize: '0.8rem', margin: '0.25rem 0 0' }}>
                        Rule: {event.rule_id} (v{event.rule_version || '?'})
                      </p>
                    )}
                    {event.decision_reason && (
                      <p style={{ color: '#cbd5e1', fontSize: '0.8rem', margin: '0.5rem 0 0',
                        fontStyle: 'italic', background: 'rgba(99, 102, 241, 0.05)',
                        padding: '0.5rem', borderRadius: '6px',
                      }}>
                        💡 {event.decision_reason}
                      </p>
                    )}
                    {event.confidence_at_stage !== null && event.confidence_at_stage !== undefined && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <div style={{
                          width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)',
                          borderRadius: '2px', overflow: 'hidden',
                        }}>
                          <div style={{
                            width: `${event.confidence_at_stage * 100}%`, height: '100%',
                            background: event.confidence_at_stage >= 0.85 ? '#22c55e' : '#f59e0b',
                            borderRadius: '2px',
                          }} />
                        </div>
                        <span style={{ color: '#94a3b8', fontSize: '0.7rem' }}>
                          Confidence: {(event.confidence_at_stage * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Related findings */}
          {chain.related_findings.length > 0 && (
            <div style={{
              marginTop: '1.5rem', padding: '1rem', borderRadius: '10px',
              background: 'rgba(251, 191, 36, 0.05)', border: '1px solid rgba(251, 191, 36, 0.15)',
            }}>
              <h4 style={{ color: '#fbbf24', margin: '0 0 0.5rem 0', fontSize: '0.85rem' }}>
                🔗 Correlated Findings ({chain.related_findings.length})
              </h4>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {chain.related_findings.map(id => (
                  <Link
                    key={id}
                    to={`/vulnerabilities/${id}`}
                    style={{
                      padding: '0.25rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem',
                      background: 'rgba(251, 191, 36, 0.1)', color: '#fbbf24',
                      textDecoration: 'none', border: '1px solid rgba(251, 191, 36, 0.2)',
                    }}
                  >
                    Finding #{id}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Comparison Tab */}
      {activeTab === 'comparison' && pair && pair.has_comparison && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          {/* Baseline */}
          <div style={{
            background: 'rgba(30, 27, 75, 0.3)', borderRadius: '12px', padding: '1.5rem',
            border: '1px solid rgba(34, 197, 94, 0.2)',
          }}>
            <h3 style={{ color: '#4ade80', margin: '0 0 1rem 0', fontSize: '1rem' }}>
              ✅ Baseline (No Payload)
            </h3>
            {pair.baseline && (
              <>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                  Status: <strong style={{ color: getStatusColor(pair.baseline.response_status_code) }}>
                    {pair.baseline.response_status_code}
                  </strong>
                  {pair.baseline.response_time_ms && ` • ${pair.baseline.response_time_ms}ms`}
                </p>
                <pre style={{
                  background: '#0f172a', padding: '1rem', borderRadius: '8px', fontSize: '0.7rem',
                  color: '#22c55e', overflow: 'auto', maxHeight: '400px', whiteSpace: 'pre-wrap',
                  marginTop: '0.75rem',
                }}>
                  {pair.baseline.response_body || '(empty body)'}
                </pre>
              </>
            )}
          </div>

          {/* Attack */}
          <div style={{
            background: 'rgba(30, 27, 75, 0.3)', borderRadius: '12px', padding: '1.5rem',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}>
            <h3 style={{ color: '#f87171', margin: '0 0 1rem 0', fontSize: '1rem' }}>
              ⚡ Attack (With Payload)
            </h3>
            {pair.attack && (
              <>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                  Status: <strong style={{ color: getStatusColor(pair.attack.response_status_code) }}>
                    {pair.attack.response_status_code}
                  </strong>
                  {pair.attack.response_time_ms && ` • ${pair.attack.response_time_ms}ms`}
                </p>
                {pair.attack.payload_value && (
                  <pre style={{
                    background: 'rgba(251, 191, 36, 0.1)', padding: '0.5rem', borderRadius: '6px',
                    fontSize: '0.7rem', color: '#fbbf24', marginTop: '0.5rem',
                  }}>
                    Payload: {pair.attack.payload_value}
                  </pre>
                )}
                <pre style={{
                  background: '#0f172a', padding: '1rem', borderRadius: '8px', fontSize: '0.7rem',
                  color: '#f87171', overflow: 'auto', maxHeight: '400px', whiteSpace: 'pre-wrap',
                  marginTop: '0.75rem',
                }}>
                  {pair.attack.response_body || '(empty body)'}
                </pre>
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === 'comparison' && (!pair || !pair.has_comparison) && (
        <div style={{
          background: 'rgba(30, 27, 75, 0.3)', padding: '3rem', borderRadius: '12px',
          textAlign: 'center', color: '#94a3b8', border: '1px solid rgba(99, 102, 241, 0.1)',
        }}>
          <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⚖️</p>
          <p>No baseline/attack comparison available for this finding.</p>
          <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>
            Comparison requires both a baseline and attack evidence record.
          </p>
        </div>
      )}

      {activeTab === 'lineage' && !chain && (
        <div style={{
          background: 'rgba(30, 27, 75, 0.3)', padding: '3rem', borderRadius: '12px',
          textAlign: 'center', color: '#94a3b8', border: '1px solid rgba(99, 102, 241, 0.1)',
        }}>
          <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔗</p>
          <p>Select a vulnerability to view its lineage chain.</p>
        </div>
      )}
    </div>
  )
}
