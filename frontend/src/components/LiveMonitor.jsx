import React, { useEffect, useRef } from 'react'

export default function LiveMonitor({ output, isStreaming, selectedAgent }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [output])

  const isError = output?.startsWith('⚠')

  return (
    <div className="gemini-section">
      {/* Section header */}
      <div className="gemini-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L9.09 8.26L2 9.27L7 14.14L5.82 21L12 17.77L18.18 21L17 14.14L22 9.27L14.91 8.26L12 2Z"
              fill="#1a73e8" />
          </svg>
          <span style={{ fontWeight: 600, fontSize: 13, color: '#202124' }}>Gemini Analysis</span>
        </div>
        {isStreaming && (
          <div className="gemini-streaming-badge">
            <span className="pulse-dot" />
            Live
          </div>
        )}
      </div>

      {/* Output area */}
      <div className="gemini-body">
        {/* No agent selected */}
        {!selectedAgent && !output && (
          <div className="gemini-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
            <p>Select an agent node,<br />then click Analyze</p>
          </div>
        )}

        {/* Agent selected, waiting */}
        {selectedAgent && !output && !isStreaming && (
          <div className="gemini-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1a73e8" strokeWidth="1.5">
              <path d="M12 2L9.09 8.26L2 9.27L7 14.14L5.82 21L12 17.77L18.18 21L17 14.14L22 9.27L14.91 8.26L12 2Z" />
            </svg>
            <p>Click <strong>Analyze with Gemini</strong><br />to get a live briefing</p>
          </div>
        )}

        {/* Streaming / output */}
        {(output || isStreaming) && (
          <div className="gemini-output-card">
            {selectedAgent && (
              <div className="gemini-agent-label">
                <span className="gemini-label-tag">BRIEFING FOR</span>
                <span className="gemini-agent-name">{selectedAgent.name}</span>
                <span className={`chip chip-${selectedAgent.status}`} style={{ fontSize: 11 }}>
                  {selectedAgent.status?.toUpperCase()}
                </span>
              </div>
            )}

            {isError ? (
              <div className="gemini-error">{output}</div>
            ) : (
              <div className="gemini-text">
                {output}
                {isStreaming && <span className="gemini-cursor" />}
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  )
}
