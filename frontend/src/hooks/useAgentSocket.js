import { useCallback, useRef, useState, useEffect } from 'react'

const WS_URL =
  typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/monitor`
    : 'ws://localhost:8080/ws/monitor'

export function useAgentSocket() {
  const ws           = useRef(null)
  const pendingAgent = useRef(null)
  const [status, setStatus]         = useState('DISCONNECTED')
  const [output, setOutput]         = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN ||
        ws.current?.readyState === WebSocket.CONNECTING) return

    console.log('[socket] connecting...')
    ws.current = new WebSocket(WS_URL)

    ws.current.onopen = () => {
      console.log('[socket] connected')
      setStatus('CONNECTED')
      // Send any queued analysis request
      if (pendingAgent.current) {
        ws.current.send(JSON.stringify({ agent_id: pendingAgent.current }))
        pendingAgent.current = null
      }
    }

    ws.current.onclose = () => {
      console.log('[socket] disconnected')
      setStatus('DISCONNECTED')
      setIsStreaming(false)
    }

    ws.current.onerror = (err) => {
      console.error('[socket] error', err)
      setStatus('ERROR')
      setIsStreaming(false)
    }

    ws.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.type === 'ready') {
          setStatus('CONNECTED')
          return
        }
        if (msg.type === 'text') {
          setOutput(prev => prev + msg.content)
          setIsStreaming(true)
          return
        }
        if (msg.type === 'done') {
          setIsStreaming(false)
          return
        }
        if (msg.type === 'error') {
          setOutput(`⚠ ${msg.content}`)
          setIsStreaming(false)
        }
      } catch (e) {
        console.error('[socket] parse error', e)
      }
    }
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    connect()
    return () => ws.current?.close()
  }, [connect])

  const analyzeAgent = useCallback((agentId) => {
    setOutput('')
    setIsStreaming(true)

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ agent_id: agentId }))
    } else {
      // Queue the request and reconnect — will fire from onopen
      pendingAgent.current = agentId
      connect()
    }
  }, [connect])

  return { status, output, isStreaming, connect, analyzeAgent }
}
