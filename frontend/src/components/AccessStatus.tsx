import clsx from 'clsx'
import type { AccessItem } from '@/types'

interface AccessStatusProps {
  accesses: AccessItem[]
}

const stateConfig = {
  granted: {
    icon: '✅',
    label: 'Granted',
    badgeClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  requires_approval: {
    icon: '⏳',
    label: 'Requires approval',
    badgeClass: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  },
  blocked: {
    icon: '🚫',
    label: 'Blocked',
    badgeClass: 'bg-red-500/15 text-red-400 border-red-500/30',
  },
}

export function AccessStatus({ accesses }: AccessStatusProps) {
  if (!accesses || accesses.length === 0) {
    return (
      <div className="text-center py-6 text-gray-600 text-sm">
        No accesses registered
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {accesses.map((access, index) => {
        const config = stateConfig[access.state]

        return (
          <div
            key={`${access.resource}-${index}`}
            className={clsx(
              'flex items-center justify-between p-3.5 rounded-xl',
              'border border-gray-800 bg-gray-900/60',
              'opacity-0 animate-fade-in'
            )}
            style={{
              animationDelay: `${index * 80}ms`,
              animationFillMode: 'forwards',
            }}
          >
            <div className="flex items-center gap-3">
              <span className="text-xl w-7 text-center select-none" role="img" aria-label={config.label}>
                {config.icon}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-200">{access.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{access.resource}</p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              {access.via_lobster_trap && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-purple-500/15 text-purple-400 border border-purple-500/30 whitespace-nowrap">
                  via Lobster Trap
                </span>
              )}
              <span
                className={clsx(
                  'px-2.5 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap',
                  config.badgeClass
                )}
              >
                {config.label}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
