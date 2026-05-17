import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Send, ArrowRight, Loader2, Wifi, WifiOff } from 'lucide-react'
import clsx from 'clsx'
import { ChatStream } from '@/components/ChatStream'
import { useOnboarding } from '@/hooks/useOnboarding'
import type { InterviewMessage, WebSocketMessage } from '@/types'
import { useWebSocket } from '@/hooks/useWebSocket'

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function Interview() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const { data: session } = useOnboarding(sessionId)
  const { status: wsStatus, lastMessage, sendMessage } = useWebSocket(
    `interview/${sessionId ?? ''}`
  )

  const [messages, setMessages] = useState<InterviewMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [interviewDone, setInterviewDone] = useState(false)
  const currentStreamingIdRef = useRef<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Process incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return

    const msg = lastMessage as WebSocketMessage

    if (msg.type === 'token' && msg.content) {
      if (!currentStreamingIdRef.current) {
        const id = generateId()
        currentStreamingIdRef.current = id
        const newMsg: InterviewMessage = {
          id,
          role: 'agent',
          content: msg.content,
          timestamp: new Date().toISOString(),
          streaming: true,
        }
        setMessages((prev) => [...prev, newMsg])
        setIsTyping(false)
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === currentStreamingIdRef.current
              ? { ...m, content: m.content + msg.content }
              : m
          )
        )
      }
    } else if (msg.type === 'message' && msg.content) {
      currentStreamingIdRef.current = null
      if (msg.role === 'agent') {
        setIsTyping(false)
        const id = generateId()
        const newMsg: InterviewMessage = {
          id,
          role: 'agent',
          content: msg.content,
          timestamp: new Date().toISOString(),
          streaming: false,
        }
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last?.streaming) {
            return prev.map((m, i) =>
              i === prev.length - 1 ? { ...m, streaming: false } : m
            )
          }
          return [...prev, newMsg]
        })
      }
    } else if (msg.type === 'interview_complete') {
      currentStreamingIdRef.current = null
      setMessages((prev) =>
        prev.map((m) => (m.streaming ? { ...m, streaming: false } : m))
      )
      setIsTyping(false)
      setInterviewDone(true)
      setIsAnalyzing(true)
    } else if (msg.type === 'status') {
      currentStreamingIdRef.current = null
      setMessages((prev) =>
        prev.map((m) => (m.streaming ? { ...m, streaming: false } : m))
      )
      const statusVal = msg.message ?? msg.status ?? ''
      if (statusVal === 'starting_provisioning' || statusVal === 'provisioning' || statusVal === 'active') {
        setIsAnalyzing(true)
        setInterviewDone(true)
      }
    } else if (msg.type === 'done') {
      currentStreamingIdRef.current = null
      setMessages((prev) =>
        prev.map((m) => (m.streaming ? { ...m, streaming: false } : m))
      )
      setIsTyping(false)
      setInterviewDone(true)
    } else if (msg.type === 'plan_ready') {
      setIsAnalyzing(false)
    } else if (msg.type === 'error') {
      currentStreamingIdRef.current = null
      setIsTyping(false)
    }
  }, [lastMessage])

  // Show typing indicator when agent starts responding
  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text) return

    const userMsg: InterviewMessage = {
      id: generateId(),
      role: 'developer',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsTyping(true)
    currentStreamingIdRef.current = null

    sendMessage({ type: 'message', content: text })
    inputRef.current?.focus()
  }, [input, sendMessage])

  const agentName = session?.agent_name ?? 'Agent'
  const agentEmoji = session?.agent_emoji ?? '🤖'
  const seniority = session?.seniority ?? ''

  const isConnected = wsStatus === 'open'

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-64px)]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-xl">
              {agentEmoji}
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">{agentName}</h2>
              <p className="text-xs text-gray-500 capitalize">{seniority} interview</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Connection indicator */}
            <div className="flex items-center gap-1.5 text-xs">
              {isConnected ? (
                <>
                  <Wifi size={14} className="text-emerald-400" />
                  <span className="text-emerald-400">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff size={14} className="text-red-400" />
                  <span className="text-red-400">
                    {wsStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                  </span>
                </>
              )}
            </div>

            {/* Ver Plan button */}
            {interviewDone && (
              <button
                onClick={() => navigate(`/plan/${sessionId}`)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
              >
                View my Plan
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Analyzing State */}
      {isAnalyzing && (
        <div className="mx-6 mt-4 p-4 rounded-xl bg-indigo-900/20 border border-indigo-500/30 flex items-center gap-3">
          <Loader2 size={18} className="animate-spin text-indigo-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-indigo-300">Analyzing your profile...</p>
            <p className="text-xs text-indigo-400/70 mt-0.5">
              Generating your personalized onboarding plan
            </p>
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden">
        <ChatStream
          messages={messages}
          agentEmoji={agentEmoji}
          agentName={agentName}
          isTyping={isTyping && !isAnalyzing}
        />
      </div>

      {/* Input Area — also visible while analyzing so user can add context */}
      {(!interviewDone || isAnalyzing) && (
        <div className="px-4 py-4 border-t border-gray-800 bg-gray-950/80">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder={
                  !isConnected ? 'Waiting for connection...'
                  : isAnalyzing ? 'Add extra context for your plan...'
                  : 'Type your answer...'
                }
                disabled={!isConnected || isTyping}
                className={clsx(
                  'w-full px-4 py-3 bg-gray-800 border rounded-xl text-sm text-gray-200',
                  'focus:outline-none transition-colors',
                  'placeholder:text-gray-600',
                  isConnected && !isTyping
                    ? 'border-gray-700 focus:border-indigo-500'
                    : 'border-gray-800 opacity-60 cursor-not-allowed'
                )}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!isConnected || !input.trim() || isTyping}
              className={clsx(
                'p-3 rounded-xl transition-all duration-200 flex-shrink-0',
                isConnected && input.trim() && !isTyping
                  ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
                  : 'bg-gray-800 text-gray-600 cursor-not-allowed'
              )}
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-xs text-gray-700 mt-2 text-center">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      )}

      {/* Interview Done Footer */}
      {interviewDone && !isAnalyzing && (
        <div className="px-4 py-4 border-t border-gray-800 bg-gray-950/80 text-center">
          <p className="text-sm text-gray-500 mb-3">Interview completed</p>
          <button
            onClick={() => navigate(`/plan/${sessionId}`)}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium flex items-center gap-2 mx-auto transition-colors"
          >
            View my Onboarding Plan
            <ArrowRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
