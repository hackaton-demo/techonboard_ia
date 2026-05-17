import { useState } from 'react'
import clsx from 'clsx'
import type { Agent, SeniorityLevel } from '@/types'

interface AgentCardProps {
  agent: Agent
  onSelect: (agent: Agent) => void
}

const seniorityColors: Record<SeniorityLevel, string> = {
  junior: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  mid: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  senior: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  staff: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  lead: 'bg-red-500/20 text-red-300 border-red-500/30',
}

const categoryColors: Record<string, string> = {
  dev: 'text-blue-400',
  ops: 'text-orange-400',
  qa: 'text-green-400',
  ai: 'text-purple-400',
  data: 'text-cyan-400',
  general: 'text-gray-400',
}

export function AgentCard({ agent, onSelect }: AgentCardProps) {
  const [hovered, setHovered] = useState(false)

  const visibleKeywords = agent.stack_keywords.slice(0, 4)
  const hasMore = agent.stack_keywords.length > 4

  return (
    <div
      className={clsx(
        'relative group rounded-xl border border-gray-800 bg-gray-900/80',
        'backdrop-blur-sm cursor-pointer overflow-hidden',
        'transition-all duration-300',
        hovered
          ? 'scale-[1.02] border-indigo-500/50 shadow-lg shadow-indigo-500/10 bg-gray-900'
          : 'hover:border-gray-700'
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => onSelect(agent)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onSelect(agent)
      }}
    >
      {/* Glass shimmer overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="text-4xl leading-none select-none">{agent.icon ?? '🤖'}</div>
          <span
            className={clsx(
              'text-xs font-medium uppercase tracking-wider',
              categoryColors[agent.category] ?? 'text-gray-400'
            )}
          >
            {agent.category}
          </span>
        </div>

        {/* Name */}
        <h3 className="text-lg font-semibold text-white mb-1 leading-tight">
          {agent.name}
        </h3>

        {/* Keywords preview on hover */}
        <div
          className={clsx(
            'overflow-hidden transition-all duration-300',
            hovered ? 'max-h-12 opacity-100 mb-3' : 'max-h-0 opacity-0'
          )}
        >
          <p className="text-xs text-gray-500 leading-relaxed">
            {agent.slug?.replace(/-/g, ' ')}
          </p>
        </div>

        {/* Seniority Badges */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {agent.seniority_levels.map((level) => (
            <span
              key={level}
              className={clsx(
                'px-2 py-0.5 rounded-full text-xs font-medium border',
                seniorityColors[level]
              )}
            >
              {level}
            </span>
          ))}
        </div>

        {/* Stack Keywords */}
        <div className="flex flex-wrap gap-1">
          {visibleKeywords.map((kw) => (
            <span
              key={kw}
              className="px-2 py-0.5 rounded-md text-xs bg-gray-800 text-gray-400 border border-gray-700/50"
            >
              {kw}
            </span>
          ))}
          {hasMore && (
            <span className="px-2 py-0.5 rounded-md text-xs bg-gray-800 text-gray-500 border border-gray-700/50">
              +{agent.stack_keywords.length - 4}
            </span>
          )}
        </div>
      </div>

      {/* Select Button (visible on hover) */}
      <div
        className={clsx(
          'px-6 pb-4 transition-all duration-300',
          hovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
        )}
      >
        <button
          className="w-full py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors duration-200"
          onClick={(e) => {
            e.stopPropagation()
            onSelect(agent)
          }}
        >
          Select Agent
        </button>
      </div>
    </div>
  )
}
