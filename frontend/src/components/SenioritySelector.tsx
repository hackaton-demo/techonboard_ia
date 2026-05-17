import { X } from 'lucide-react'
import clsx from 'clsx'
import type { Agent, SeniorityLevel } from '@/types'

const SENIORITY_PRICES: Record<SeniorityLevel, number> = {
  junior: 0.50,
  mid: 1.00,
  senior: 1.00,
  staff: 2.00,
  lead: 2.00,
}

interface SenioritySelectorProps {
  agent: Agent
  onSelect: (level: SeniorityLevel) => void
  onCancel: () => void
}

const seniorityConfig: Record<
  SeniorityLevel,
  { label: string; description: string; accesses: string; color: string; bgColor: string }
> = {
  junior: {
    label: 'Junior',
    description: '0–2 years of experience',
    accesses: 'Read repository access, dev environments, Jira viewer',
    color: 'text-emerald-300',
    bgColor: 'bg-emerald-500/10 border-emerald-500/30 hover:bg-emerald-500/20',
  },
  mid: {
    label: 'Mid',
    description: '2–5 years of experience',
    accesses: 'Read/write repos, CI/CD viewer, staging env, Jira contributor',
    color: 'text-blue-300',
    bgColor: 'bg-blue-500/10 border-blue-500/30 hover:bg-blue-500/20',
  },
  senior: {
    label: 'Senior',
    description: '5–8 years of experience',
    accesses: 'Full repo access, CI/CD manage, prod read, architecture docs',
    color: 'text-purple-300',
    bgColor: 'bg-purple-500/10 border-purple-500/30 hover:bg-purple-500/20',
  },
  staff: {
    label: 'Staff Engineer',
    description: '8+ years, cross-team impact',
    accesses: 'Prod access, infra manage, on-call, design review access',
    color: 'text-amber-300',
    bgColor: 'bg-amber-500/10 border-amber-500/30 hover:bg-amber-500/20',
  },
  lead: {
    label: 'Tech Lead',
    description: 'Technical team leadership',
    accesses: 'Full access, admin roles, budget view, hiring pipeline',
    color: 'text-red-300',
    bgColor: 'bg-red-500/10 border-red-500/30 hover:bg-red-500/20',
  },
}

export function SenioritySelector({ agent, onSelect, onCancel }: SenioritySelectorProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-lg bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{agent.icon ?? '🤖'}</span>
            <div>
              <h2 className="text-base font-semibold text-white">
                {agent.name}
              </h2>
              <p className="text-xs text-gray-500">Select the developer's level</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Seniority Options */}
        <div className="p-4 space-y-2">
          {agent.seniority_levels.map((level) => {
            const config = seniorityConfig[level]
            return (
              <button
                key={level}
                onClick={() => onSelect(level)}
                className={clsx(
                  'w-full text-left p-4 rounded-xl border transition-all duration-200',
                  config.bgColor
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={clsx('font-semibold text-sm', config.color)}>
                        {config.label}
                      </span>
                      <span className="text-xs text-gray-500">{config.description}</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {config.accesses}
                    </p>
                  </div>
                  <div className="ml-4 text-right flex-shrink-0">
                    <div className="text-xs font-semibold text-indigo-400">
                      {SENIORITY_PRICES[level]} USDC
                    </div>
                    <div className="text-xs text-gray-600">via x402</div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
