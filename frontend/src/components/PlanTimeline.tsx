import clsx from 'clsx'
import { CalendarCheck } from 'lucide-react'
import type { PlanDay } from '@/types'

interface PlanTimelineProps {
  days: PlanDay[]
  todayDay?: number
}

const WEEK_LABELS = ['Week 1 — Integration', 'Week 2 — Deep Dive']

function getDayStatus(day: number, todayDay: number, completed?: boolean) {
  if (completed) return 'completed'
  if (day === todayDay) return 'today'
  if (day < todayDay) return 'past'
  return 'future'
}

const statusStyles = {
  completed: {
    circle: 'bg-emerald-600 border-emerald-500 text-white',
    connector: 'bg-emerald-700/50',
    card: 'border-gray-800 bg-gray-900/50',
    dayNum: 'text-emerald-400',
    title: 'text-gray-300',
    desc: 'text-gray-500',
  },
  today: {
    circle: 'bg-indigo-600 border-indigo-400 text-white ring-2 ring-indigo-500/40',
    connector: 'bg-gray-700',
    card: 'border-indigo-500/40 bg-indigo-900/10',
    dayNum: 'text-indigo-400',
    title: 'text-white',
    desc: 'text-gray-400',
  },
  past: {
    circle: 'bg-gray-800 border-gray-700 text-gray-500',
    connector: 'bg-gray-800',
    card: 'border-gray-800/50 bg-gray-900/30',
    dayNum: 'text-gray-600',
    title: 'text-gray-500',
    desc: 'text-gray-600',
  },
  future: {
    circle: 'bg-gray-800 border-gray-700 text-gray-400',
    connector: 'bg-gray-800',
    card: 'border-gray-800 bg-gray-900/50',
    dayNum: 'text-gray-500',
    title: 'text-gray-300',
    desc: 'text-gray-500',
  },
}

interface DayItemProps {
  day: PlanDay
  isLast: boolean
  todayDay: number
}

function DayItem({ day, isLast, todayDay }: DayItemProps) {
  const status = getDayStatus(day.day, todayDay, day.completed)
  const styles = statusStyles[status]

  return (
    <div className="flex gap-4">
      {/* Timeline line + circle */}
      <div className="flex flex-col items-center flex-shrink-0 w-10">
        <div
          className={clsx(
            'w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold flex-shrink-0 transition-all',
            styles.circle
          )}
        >
          {status === 'completed' ? '✓' : day.day}
        </div>
        {!isLast && <div className={clsx('w-0.5 flex-1 mt-1 min-h-4', styles.connector)} />}
      </div>

      {/* Content Card */}
      <div className={clsx('flex-1 mb-3 p-3.5 rounded-xl border transition-all', styles.card)}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={clsx('text-xs font-medium', styles.dayNum)}>
                Day {day.day}
              </span>
              {day.is_checkin && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-500/15 text-purple-400 border border-purple-500/30">
                  <CalendarCheck size={10} />
                  Check-in
                </span>
              )}
              {status === 'today' && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Today
                </span>
              )}
            </div>
            <p className={clsx('text-sm font-semibold leading-tight mb-1', styles.title)}>
              {day.title}
            </p>
            <p className={clsx('text-xs leading-relaxed', styles.desc)}>
              {day.description}
            </p>
          </div>
        </div>
        {day.tasks && day.tasks.length > 0 && status !== 'past' && (
          <ul className="mt-2 space-y-0.5">
            {day.tasks.map((task, i) => (
              <li key={i} className="flex items-start gap-1.5 text-xs text-gray-500">
                <span className="mt-0.5 text-gray-700">•</span>
                <span>{task}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export function PlanTimeline({ days, todayDay = 1 }: PlanTimelineProps) {
  const week1 = days.filter((d) => d.day <= 7)
  const week2 = days.filter((d) => d.day > 7)

  const renderWeek = (weekDays: PlanDay[], label: string) => (
    <div key={label}>
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-4 pl-14">
        {label}
      </h3>
      <div>
        {weekDays.map((day, i) => (
          <DayItem
            key={day.day}
            day={day}
            isLast={i === weekDays.length - 1}
            todayDay={todayDay}
          />
        ))}
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {week1.length > 0 && renderWeek(week1, WEEK_LABELS[0])}
      {week2.length > 0 && renderWeek(week2, WEEK_LABELS[1])}
    </div>
  )
}
