import { useState, useEffect, useRef, useCallback } from 'react'
import type { WebSocketMessage } from '@/types'

export type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error'

interface UseWebSocketReturn {
  status: WebSocketStatus
  messages: WebSocketMessage[]
  lastMessage: WebSocketMessage | null
  sendMessage: (data: unknown) => void
  disconnect: () => void
}

const MAX_RECONNECT_ATTEMPTS = 3
const BASE_RECONNECT_DELAY = 1000

export function useWebSocket(path: string): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>('connecting')
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const shouldReconnectRef = useRef(true)
  const pathRef = useRef(path)

  pathRef.current = path

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/${pathRef.current}`
    setStatus('connecting')

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('open')
        reconnectAttemptsRef.current = 0
      }

      ws.onmessage = (event: MessageEvent<string>) => {
        try {
          const msg = JSON.parse(event.data) as WebSocketMessage
          setMessages((prev) => [...prev, msg])
          setLastMessage(msg)
        } catch {
          // Handle raw text messages
          const msg: WebSocketMessage = { type: 'token', content: event.data }
          setMessages((prev) => [...prev, msg])
          setLastMessage(msg)
        }
      }

      ws.onerror = () => {
        setStatus('error')
      }

      ws.onclose = () => {
        setStatus('closed')
        wsRef.current = null

        if (
          shouldReconnectRef.current &&
          reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS
        ) {
          const delay =
            BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current)
          reconnectAttemptsRef.current += 1

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }
    } catch {
      setStatus('error')
    }
  }, [])

  useEffect(() => {
    shouldReconnectRef.current = true
    connect()

    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])

  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('closed')
  }, [])

  return { status, messages, lastMessage, sendMessage, disconnect }
}
