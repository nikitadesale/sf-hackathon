import React, { useState, useEffect, useCallback } from 'react'
import AgentGraph from './components/AgentGraph'
import SidePanel from './components/SidePanel'
import { useAgentSocket } from './hooks/useAgentSocket'

const POLL_INTERVAL = 15000

export default function App() {
  const [nodes, setNodes]           = useState([])
  const [edges, setEdges]           = useState([])
  const [stats, setStats]           = useState({ total: 0, shadow: 0, compromised: 0, approved: 0 })
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [scanning, setScanning]     = useState(false)
  const [lastScan, setLastScan]     = useState(null)
  const [toast, setToast]           = useState(null)

  const { output, isStreaming, connect, analyzeAgent } = useAgentSocket()

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch('/api/agents')
      if (!res.ok) return
      const data = await res.json()
      setNodes(data.nodes ?? [])
      setEdges(data.edges ?? [])

      const all = data.nodes ?? []
      setStats({
        total:       all.length,
        approved:    all.filter(n => n.data.status === 'approved').length,
        shadow:      all.filter(n => n.data.status === 'shadow').length,
        compromised: all.filter(n => n.data.status === 'compromised').length,
      })
    } catch (e) {
      console.error('fetchAgents error', e)
    }
  }, [])

  const handleScan = async () => {
    setScanning(true)
    showToast('Scanning GCP environment...')
    try {
      const scanRes = await fetch('/api/scan', { method: 'POST' })
      if (!scanRes.ok) throw new Error(`HTTP ${scanRes.status}`)
      const scanData = await scanRes.json()
      if (scanData.warning) console.warn('[scan]', scanData.warning)
      // Immediately load the graph from the now-populated memory cache
      await fetchAgents()
      setLastScan(new Date())
      showToast(`Scan complete — ${scanData.total} agents found`)
    } catch (e) {
      console.error('Scan error:', e)
      showToast(`Scan failed: ${e.message}`)
    } finally {
      setScanning(false)
    }
  }

  const handleNodeClick = useCallback((agentData, agentId) => {
    setSelectedAgent(agentData)
    setSelectedId(agentId)
  }, [])

  const handleAnalyze = useCallback((agentId) => {
    analyzeAgent(agentId)
  }, [analyzeAgent])

  // Connect WebSocket and start polling on mount
  useEffect(() => {
    connect()
    fetchAgents()
    const interval = setInterval(fetchAgents, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [connect, fetchAgents])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>

      {/* Top bar */}
      <header className="topbar">
        <div className="topbar-logo">
          {/* Google Cloud-style icon */}
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5z" fill="var(--blue)" />
            <path d="M2 17l10 5 10-5" stroke="var(--blue)" strokeWidth="2" fill="none" />
            <path d="M2 12l10 5 10-5" stroke="var(--blue)" strokeWidth="2" fill="none" />
          </svg>
          <span>ShadowAgentMap</span>
        </div>

        <div className="topbar-divider" />

        <div className="topbar-project">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
          </svg>
          waybackhome-rw9xuoxqhoap3wax3s
        </div>

        <div className="topbar-right">
          {lastScan && (
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Last scan: {lastScan.toLocaleTimeString()}
            </span>
          )}
          <button
            className="btn btn-primary"
            onClick={handleScan}
            disabled={scanning}
          >
            {scanning ? <><span className="spinner" /> Scanning...</> : '⟳ Scan Now'}
          </button>
        </div>
      </header>

      {/* Stats banner */}
      <div className="stats-banner">
        <div className="stat-item">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Agents Discovered</span>
        </div>
        <div className="stat-item">
          <span className="stat-value green">{stats.approved}</span>
          <span className="stat-label">Authorized</span>
        </div>
        <div className="stat-item">
          <span className="stat-value orange">{stats.shadow}</span>
          <span className="stat-label">Shadow Agents</span>
        </div>
        <div className="stat-item">
          <span className="stat-value red">{stats.compromised}</span>
          <span className="stat-label">Compromised</span>
        </div>
        <div className="stat-item">
          <span className="stat-value red" style={{ fontSize: 16 }}>
            {stats.shadow + stats.compromised > 0 ? `${stats.shadow + stats.compromised} at risk` : 'Clean'}
          </span>
          <span className="stat-label">Threat Exposure</span>
        </div>
      </div>

      {/* Main layout: graph + side panel */}
      <div className="main-layout">
        <div className="graph-area">
          <AgentGraph
            nodes={nodes}
            edges={edges}
            onNodeClick={handleNodeClick}
          />
        </div>

        <SidePanel
          agent={selectedAgent}
          agentId={selectedId}
          output={output}
          isStreaming={isStreaming}
          onAnalyze={handleAnalyze}
        />
      </div>

      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
