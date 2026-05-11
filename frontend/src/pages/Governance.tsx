import { useState, useEffect } from 'react'
import { governanceAPI } from '../services/endpoints'
import type { ScanPolicy, CorrelationGroup } from '../types'

const GROUP_TYPE_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  duplicate: { icon: '📋', color: '#f59e0b', label: 'Duplicate' },
  related: { icon: '🔗', color: '#3b82f6', label: 'Related' },
  exploit_chain: { icon: '⛓️', color: '#ef4444', label: 'Exploit Chain' },
}

export default function Governance() {
  const [policies, setPolicies] = useState<ScanPolicy[]>([])
  const [correlations, setCorrelations] = useState<CorrelationGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'policies' | 'correlations'>('policies')
  const [showCreatePolicy, setShowCreatePolicy] = useState(false)
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    allowed_targets: '',
    max_requests_per_second: 10,
    block_destructive: true,
  })

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [pols, corrs] = await Promise.all([
        governanceAPI.listPolicies(false),
        governanceAPI.listCorrelations(),
      ])
      setPolicies(pols)
      setCorrelations(corrs)
    } catch (err) {
      console.error('Failed to load governance data:', err)
    }
    setLoading(false)
  }

  async function createPolicy() {
    try {
      const targets = newPolicy.allowed_targets
        ? newPolicy.allowed_targets.split(',').map(t => t.trim()).filter(Boolean)
        : undefined

      await governanceAPI.createPolicy({
        name: newPolicy.name,
        description: newPolicy.description || undefined,
        allowed_targets: targets,
        max_requests_per_second: newPolicy.max_requests_per_second,
        block_destructive: newPolicy.block_destructive,
      } as any)

      setShowCreatePolicy(false)
      setNewPolicy({ name: '', description: '', allowed_targets: '', max_requests_per_second: 10, block_destructive: true })
      loadData()
    } catch (err) {
      console.error('Failed to create policy:', err)
    }
  }

  async function reviewCorrelation(correlationId: string) {
    try {
      await governanceAPI.reviewCorrelation(correlationId)
      loadData()
    } catch (err) {
      console.error('Failed to review correlation:', err)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center', color: '#9ca3af' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚖️</div>
          <p>Loading governance data...</p>
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
          ⚖️ Governance & Compliance
        </h1>
        <p style={{ color: '#94a3b8', marginTop: '0.5rem', fontSize: '0.9rem' }}>
          Scan policies, scope enforcement, and finding correlation
        </p>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          {(['policies', 'correlations'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.5rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
                fontSize: '0.85rem', fontWeight: 600,
                background: activeTab === tab ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                color: activeTab === tab ? '#a5b4fc' : '#94a3b8',
                transition: 'all 0.2s',
              }}
            >
              {tab === 'policies' && '📋 Scan Policies'}
              {tab === 'correlations' && '🔗 Correlations'}
            </button>
          ))}
        </div>
      </div>

      {/* Policies Tab */}
      {activeTab === 'policies' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button
              onClick={() => setShowCreatePolicy(true)}
              style={{
                padding: '0.6rem 1.2rem', borderRadius: '10px', border: 'none', cursor: 'pointer',
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff', fontWeight: 600, fontSize: '0.85rem',
              }}
            >
              + New Policy
            </button>
          </div>

          {policies.length === 0 ? (
            <div style={{
              background: 'rgba(30, 27, 75, 0.3)', padding: '3rem', borderRadius: '12px',
              textAlign: 'center', color: '#94a3b8', border: '1px solid rgba(99, 102, 241, 0.1)',
            }}>
              <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📋</p>
              <p>No scan policies defined yet</p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Policies control what targets, tests, and payloads are authorized.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {policies.map(policy => (
                <div
                  key={policy.policy_id}
                  style={{
                    background: 'rgba(30, 27, 75, 0.35)', borderRadius: '12px', padding: '1.5rem',
                    border: `1px solid ${policy.is_active ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h3 style={{ color: '#e2e8f0', margin: 0, fontSize: '1.1rem' }}>{policy.name}</h3>
                      <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0.25rem 0 0' }}>
                        {policy.description || 'No description'}
                      </p>
                    </div>
                    <span style={{
                      padding: '0.2rem 0.6rem', borderRadius: '8px', fontSize: '0.7rem', fontWeight: 700,
                      background: policy.is_active ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: policy.is_active ? '#4ade80' : '#f87171',
                    }}>
                      {policy.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>

                  <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '1rem',
                  }}>
                    <div>
                      <p style={{ color: '#94a3b8', fontSize: '0.7rem', margin: 0 }}>RATE LIMIT</p>
                      <p style={{ color: '#e2e8f0', fontSize: '0.9rem', margin: '0.15rem 0 0', fontWeight: 600 }}>
                        {policy.max_requests_per_second} req/s
                      </p>
                    </div>
                    <div>
                      <p style={{ color: '#94a3b8', fontSize: '0.7rem', margin: 0 }}>DESTRUCTIVE</p>
                      <p style={{ color: policy.block_destructive ? '#4ade80' : '#f87171', fontSize: '0.9rem', margin: '0.15rem 0 0', fontWeight: 600 }}>
                        {policy.block_destructive ? '🛡 Blocked' : '⚠️ Allowed'}
                      </p>
                    </div>
                    <div>
                      <p style={{ color: '#94a3b8', fontSize: '0.7rem', margin: 0 }}>SLA (Critical)</p>
                      <p style={{ color: '#e2e8f0', fontSize: '0.9rem', margin: '0.15rem 0 0', fontWeight: 600 }}>
                        {policy.sla_critical_hours}h
                      </p>
                    </div>
                    <div>
                      <p style={{ color: '#94a3b8', fontSize: '0.7rem', margin: 0 }}>TARGETS</p>
                      <p style={{ color: '#e2e8f0', fontSize: '0.9rem', margin: '0.15rem 0 0', fontWeight: 600 }}>
                        {policy.allowed_targets?.length || 'Any'}
                      </p>
                    </div>
                  </div>

                  {policy.compliance_frameworks && policy.compliance_frameworks.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
                      {policy.compliance_frameworks.map(fw => (
                        <span key={fw} style={{
                          padding: '0.15rem 0.5rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600,
                          background: 'rgba(99, 102, 241, 0.1)', color: '#a5b4fc',
                        }}>
                          {fw}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Correlations Tab */}
      {activeTab === 'correlations' && (
        <div>
          {correlations.length === 0 ? (
            <div style={{
              background: 'rgba(30, 27, 75, 0.3)', padding: '3rem', borderRadius: '12px',
              textAlign: 'center', color: '#94a3b8', border: '1px solid rgba(99, 102, 241, 0.1)',
            }}>
              <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔗</p>
              <p>No correlation groups found</p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Run correlation analysis on a completed scan to group related findings.
              </p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {correlations.map(group => {
                const config = GROUP_TYPE_CONFIG[group.group_type] || { icon: '🔹', color: '#6b7280', label: group.group_type }
                return (
                  <div
                    key={group.correlation_id}
                    style={{
                      background: 'rgba(30, 27, 75, 0.35)', borderRadius: '12px', padding: '1.5rem',
                      border: `1px solid ${config.color}33`,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{
                            padding: '0.2rem 0.6rem', borderRadius: '8px', fontSize: '0.7rem', fontWeight: 700,
                            background: config.color + '22', color: config.color,
                          }}>
                            {config.icon} {config.label.toUpperCase()}
                          </span>
                          {group.highest_severity && (
                            <span style={{
                              padding: '0.2rem 0.5rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600,
                              background: group.highest_severity === 'critical' ? 'rgba(239, 68, 68, 0.2)' :
                                group.highest_severity === 'high' ? 'rgba(251, 146, 60, 0.2)' : 'rgba(251, 191, 36, 0.2)',
                              color: group.highest_severity === 'critical' ? '#f87171' :
                                group.highest_severity === 'high' ? '#fb923c' : '#fbbf24',
                            }}>
                              {group.highest_severity.toUpperCase()}
                            </span>
                          )}
                        </div>
                        <h3 style={{ color: '#e2e8f0', margin: '0.5rem 0 0', fontSize: '1rem' }}>
                          {group.title}
                        </h3>
                        {group.description && (
                          <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0.25rem 0 0' }}>
                            {group.description}
                          </p>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{
                          padding: '0.3rem 0.8rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700,
                          background: 'rgba(99, 102, 241, 0.1)', color: '#a5b4fc',
                        }}>
                          {group.member_count} findings
                        </span>
                        {!group.is_reviewed && (
                          <button
                            onClick={() => reviewCorrelation(group.correlation_id)}
                            style={{
                              padding: '0.3rem 0.8rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
                              background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80',
                              fontSize: '0.8rem', fontWeight: 600,
                            }}
                          >
                            ✅ Review
                          </button>
                        )}
                        {group.is_reviewed && (
                          <span style={{ color: '#4ade80', fontSize: '0.8rem' }}>
                            ✅ Reviewed by {group.reviewed_by}
                          </span>
                        )}
                      </div>
                    </div>

                    {group.chain_impact && (
                      <div style={{
                        marginTop: '0.75rem', padding: '0.75rem', borderRadius: '8px',
                        background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.1)',
                      }}>
                        <p style={{ color: '#fca5a5', fontSize: '0.8rem', margin: 0 }}>
                          ⚠️ <strong>Impact:</strong> {group.chain_impact}
                        </p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Create Policy Modal */}
      {showCreatePolicy && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 999,
          }}
          onClick={() => setShowCreatePolicy(false)}
        >
          <div
            style={{
              background: '#1e1b4b', borderRadius: '16px', padding: '2rem',
              maxWidth: '500px', width: '90%', border: '1px solid rgba(99, 102, 241, 0.3)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{ color: '#e2e8f0', margin: '0 0 1.5rem 0' }}>📋 Create Scan Policy</h3>

            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>
                  Policy Name *
                </label>
                <input
                  type="text"
                  value={newPolicy.name}
                  onChange={e => setNewPolicy(p => ({ ...p, name: e.target.value }))}
                  style={{
                    width: '100%', padding: '0.6rem', borderRadius: '8px',
                    background: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.2)',
                    color: '#e2e8f0', fontSize: '0.85rem', outline: 'none',
                  }}
                  placeholder="e.g. Production Scan Policy"
                />
              </div>
              <div>
                <label style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>
                  Description
                </label>
                <textarea
                  value={newPolicy.description}
                  onChange={e => setNewPolicy(p => ({ ...p, description: e.target.value }))}
                  style={{
                    width: '100%', padding: '0.6rem', borderRadius: '8px',
                    background: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.2)',
                    color: '#e2e8f0', fontSize: '0.85rem', outline: 'none',
                    minHeight: '60px', resize: 'vertical',
                  }}
                  placeholder="Policy description..."
                />
              </div>
              <div>
                <label style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>
                  Allowed Targets (comma-separated)
                </label>
                <input
                  type="text"
                  value={newPolicy.allowed_targets}
                  onChange={e => setNewPolicy(p => ({ ...p, allowed_targets: e.target.value }))}
                  style={{
                    width: '100%', padding: '0.6rem', borderRadius: '8px',
                    background: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.2)',
                    color: '#e2e8f0', fontSize: '0.85rem', outline: 'none',
                  }}
                  placeholder="e.g. example.com, staging.example.com"
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>
                    Rate Limit (req/s)
                  </label>
                  <input
                    type="number"
                    value={newPolicy.max_requests_per_second}
                    onChange={e => setNewPolicy(p => ({ ...p, max_requests_per_second: parseInt(e.target.value) || 10 }))}
                    style={{
                      width: '100%', padding: '0.6rem', borderRadius: '8px',
                      background: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.2)',
                      color: '#e2e8f0', fontSize: '0.85rem', outline: 'none',
                    }}
                  />
                </div>
                <div>
                  <label style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>
                    Block Destructive
                  </label>
                  <button
                    onClick={() => setNewPolicy(p => ({ ...p, block_destructive: !p.block_destructive }))}
                    style={{
                      width: '100%', padding: '0.6rem', borderRadius: '8px', border: 'none', cursor: 'pointer',
                      background: newPolicy.block_destructive ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: newPolicy.block_destructive ? '#4ade80' : '#f87171',
                      fontWeight: 600, fontSize: '0.85rem',
                    }}
                  >
                    {newPolicy.block_destructive ? '🛡 Blocked' : '⚠️ Allowed'}
                  </button>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
              <button
                onClick={() => setShowCreatePolicy(false)}
                style={{
                  padding: '0.6rem 1.2rem', borderRadius: '10px', border: '1px solid rgba(99, 102, 241, 0.2)',
                  background: 'transparent', color: '#94a3b8', cursor: 'pointer', fontSize: '0.85rem',
                }}
              >
                Cancel
              </button>
              <button
                onClick={createPolicy}
                disabled={!newPolicy.name}
                style={{
                  padding: '0.6rem 1.2rem', borderRadius: '10px', border: 'none', cursor: 'pointer',
                  background: newPolicy.name ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#374151',
                  color: '#fff', fontWeight: 600, fontSize: '0.85rem',
                  opacity: newPolicy.name ? 1 : 0.5,
                }}
              >
                Create Policy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
