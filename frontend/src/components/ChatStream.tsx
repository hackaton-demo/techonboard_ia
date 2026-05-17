import { useEffect, useRef } from 'react'
import clsx from 'clsx'
import type { InterviewMessage } from '@/types'

interface ChatStreamProps {
  messages: InterviewMessage[]
  agentEmoji: string
  agentName: string
  isTyping?: boolean
}

function formatTime(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3 bg-gray-800/60 rounded-2xl rounded-tl-sm w-fit">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  )
}

interface MessageBubbleProps {
  message: InterviewMessage
  agentEmoji: string
}

function MessageBubble({ message, agentEmoji }: MessageBubbleProps) {
  const isAgent = message.role === 'agent'

  return (
    <div
      className={clsx(
        'flex gap-3 max-w-[85%]',
        isAgent ? 'self-start' : 'self-end flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center text-base flex-shrink-0 mt-1',
          isAgent ? 'bg-gray-800 border border-gray-700' : 'bg-indigo-600/30 border border-indigo-500/40'
        )}
      >
        {isAgent ? agentEmoji : '👤'}
      </div>

      {/* Bubble */}
      <div className="flex flex-col gap-1">
        <div
          className={clsx(
            'px-4 py-3 rounded-2xl text-sm leading-relaxed',
            isAgent
              ? 'bg-gray-800/80 text-gray-200 rounded-tl-sm border border-gray-700/50'
              : 'bg-indigo-600/80 text-white rounded-tr-sm border border-indigo-500/40'
          )}
        >
          {message.content}
          {message.streaming && (
            <span className="inline-block w-1 h-4 bg-current ml-0.5 animate-pulse align-middle" />
          )}
        </div>
        <span
          className={clsx(
            'text-xs text-gray-600',
            isAgent ? 'text-left pl-1' : 'text-right pr-1'
          )}
        >
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
}

export function ChatStream({ messages, agentEmoji, agentName, isTyping = false }: ChatStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="text-5xl">{agentEmoji}</div>
              <p className="text-gray-500 text-sm">
                {agentName} is ready to start the interview
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} agentEmoji={agentEmoji} />
          ))
        )}

        {isTyping && (
          <div className="flex gap-3 self-start max-w-[85%]">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-base flex-shrink-0 mt-1 bg-gray-800 border border-gray-700">
              {agentEmoji}
            </div>
            <TypingIndicator />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
