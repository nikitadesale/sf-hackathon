import React from 'react'
import LiveMonitor from './LiveMonitor'

export default function SidePanel({ agent, agentId, output, isStreaming, onAnalyze }) {
  return (
    <div className="side-panel">
      <div className="side-panel-scroll">
      {agent ? (
        <>
          {/* Agent details */}
          <div className="panel-header">
            <span>Agent Details</span>
            <span className={`chip chip-${agent.status}`}>{agent.status.toUpperCase()}</span>
          </div>

          <div className="panel-section">
            <div className="panel-section-title">Identity</div>
            <div className="detail-row">
              <span className="detail-key">Name</span>
              <span className="detail-value">{agent.name}</span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Source</span>
              <span className="detail-value">{agent.source === 'cloud_run' ? 'Cloud Run' : 'Vertex AI'}</span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Deployed by</span>
              <span className="detail-value" style={{ fontFamily: 'Roboto Mono', fontSize: 11 }}>
                {agent.deployed_by}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Endpoint</span>
              <span className="detail-value" style={{ fontFamily: 'Roboto Mono', fontSize: 11 }}>
                {agent.endpoint || '—'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Auth</span>
              <span
                className="detail-value"
                style={{ color: agent.ingress === 'public' ? 'var(--red)' : 'var(--green)', fontWeight: 500 }}
              >
                {agent.ingress === 'public' ? '🔓 None (public)' : '🔒 Required'}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-key">Last seen</span>
              <span className="detail-value">
                {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : '—'}
              </span>
            </div>
          </div>

          {/* Risk score */}
          <div className="panel-section">
            <div className="panel-section-title">Risk Score</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <span
                className={`risk-score-badge ${agent.risk_score >= 60 ? 'high' : agent.risk_score >= 30 ? 'med' : 'low'}`}
                style={{ fontSize: 32 }}
              >
                {Math.round(agent.risk_score)}
              </span>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>out of 100</div>
                <div style={{ height: 6, width: 120, background: 'var(--border)', borderRadius: 3, marginTop: 4 }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${agent.risk_score}%`,
                      borderRadius: 3,
                      background: agent.risk_score >= 60 ? 'var(--red)' : agent.risk_score >= 30 ? 'var(--orange)' : 'var(--green)',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>
            </div>

            {agent.risk_reasons?.length > 0 && (
              <>
                <div className="panel-section-title" style={{ marginTop: 8 }}>Risk Factors</div>
                {agent.risk_reasons.map((r, i) => (
                  <div key={i} className="risk-reason-item">{r}</div>
                ))}
              </>
            )}
          </div>

          {/* Analyze button */}
          <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border)' }}>
            <button
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center' }}
              onClick={() => onAnalyze(agentId)}
              disabled={isStreaming}
            >
              {isStreaming
                ? <><span className="spinner" /> Analyzing...</>
                : '⚡ Analyze with Gemini'}
            </button>
          </div>

          {/* Live monitor */}
          <LiveMonitor output={output} isStreaming={isStreaming} selectedAgent={agent} />
        </>
      ) : (
        <>
          <div className="panel-header">Agent Details</div>
          <LiveMonitor output={output} isStreaming={isStreaming} selectedAgent={null} />
        </>
      )}
      </div>
    </div>
  )
}
