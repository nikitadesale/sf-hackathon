import React, { useCallback, useEffect } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from 'reactflow'

// ── Custom node ──────────────────────────────────────────────────────────────

function AgentNode({ data, selected }) {
  const score = data.risk_score ?? 0
  const scoreClass = score >= 60 ? 'high' : score >= 30 ? 'med' : 'low'

  return (
    <div className={`agent-node ${data.status} ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="agent-node-name" title={data.name}>{data.name}</div>
          <span className={`chip chip-${data.status}`}>
            {data.status.toUpperCase()}
          </span>
        </div>
        <span className={`risk-score-badge ${scoreClass}`}>{Math.round(score)}</span>
      </div>

      <div className="agent-node-meta">
        <span>{data.source === 'cloud_run' ? '☁ Cloud Run' : '🤖 Vertex AI'}</span>
        {data.ingress === 'public' && (
          <span style={{ color: 'var(--red)', fontWeight: 500 }}>🔓 No Auth</span>
        )}
      </div>

      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  )
}

const nodeTypes = { agentNode: AgentNode }

// ── Main graph ───────────────────────────────────────────────────────────────

export default function AgentGraph({ nodes: initialNodes, edges: initialEdges, onNodeClick }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Sync when parent fetches agents after a scan
  useEffect(() => { setNodes(initialNodes ?? []) }, [initialNodes, setNodes])
  useEffect(() => { setEdges(initialEdges ?? []) }, [initialEdges, setEdges])

  const handleNodeClick = useCallback((_, node) => {
    onNodeClick?.(node.data, node.id)
  }, [onNodeClick])

  if (!nodes.length) {
    return (
      <div className="empty-state" style={{ height: '100%' }}>
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
          <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
        </svg>
        <p>No agents discovered yet.</p>
        <p style={{ fontSize: 12 }}>Click <strong>Scan Now</strong> to discover agents in your GCP environment.</p>
      </div>
    )
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      fitView
      fitViewOptions={{ padding: 0.3 }}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#dadce0" gap={20} size={1} />
      <Controls style={{ boxShadow: 'var(--shadow-sm)' }} />
      <MiniMap
        nodeColor={(n) => {
          const s = n.data?.status
          return s === 'approved' ? '#1e8e3e' : s === 'shadow' ? '#e37400' : '#d93025'
        }}
        style={{ border: '1px solid var(--border)', borderRadius: 4 }}
      />
    </ReactFlow>
  )
}
