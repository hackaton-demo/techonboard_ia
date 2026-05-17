import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Download, ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'
import { getAuditLog } from '@/lib/api'
import type { AuditEvent, AuditEventType, AuditSeverity } from '@/types'

const severityBadge: Record<AuditSeverity, string> = {
  LOW: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  MEDIUM: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  HIGH: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  CRITICAL: 'bg-red-500/15 text-red-400 border-red-500/30',
}

const typeBadge: Record<AuditEventType, string> = {
  DENY: 'bg-red-500/15 text-red-400 border-red-500/30',
  REDACT: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  LOG: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  HUMAN_REVIEW: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
}

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ts
  }
}

interface AuditLogProps {
  embedded?: boolean
  initialSize?: number
}

export function AuditLog({ embedded = false, initialSize = 10 }: AuditLogProps) {
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const fetchEvents = useCallback(async (p: number) => {
    setLoading(true)
    try {
      const data = await getAuditLog(p, initialSize)
      setEvents(data.items)
      setTotalPages(data.pages)
    } catch {
      // Keep previous events on error
    } finally {
      setLoading(false)
      setLastRefresh(new Date())
    }
  }, [initialSize])

  useEffect(() => {
    void fetchEvents(page)
  }, [fetchEvents, page])

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      void fetchEvents(page)
    }, 10000)
    return () => clearInterval(interval)
  }, [fetchEvents, page])

  const handleExportCSV = () => {
    const headers = ['Timestamp', 'Type', 'Severity', 'Rule', 'Action']
    const rows = events.map((e) => [
      e.timestamp,
      e.event_type,
      e.severity,
      e.rule_triggered,
      e.action_taken,
    ])
    const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-log-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={clsx(embedded ? '' : 'p-6')}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-300">
            Lobster Trap — Audit Log
          </h3>
          {loading && (
            <RefreshCw size={12} className="animate-spin text-gray-500" />
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">
            {lastRefresh.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </span>
          <button
            onClick={() => void fetchEvents(page)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
            title="Refresh"
          >
            <RefreshCw size={14} />
          </button>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-gray-400 hover:text-gray-200 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <Download size={12} />
            Export CSV
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/80">
                <th className="text-left py-2.5 px-3 text-gray-500 font-medium">Timestamp</th>
                <th className="text-left py-2.5 px-3 text-gray-500 font-medium">Type</th>
                <th className="text-left py-2.5 px-3 text-gray-500 font-medium">Severity</th>
                <th className="text-left py-2.5 px-3 text-gray-500 font-medium hidden md:table-cell">Rule</th>
                <th className="text-left py-2.5 px-3 text-gray-500 font-medium hidden lg:table-cell">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading && events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-600">
                    Loading events...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-600">
                    No events registered
                  </td>
                </tr>
              ) : (
                events.map((event, i) => (
                  <tr
                    key={event.id}
                    className={clsx(
                      'border-b border-gray-800/50 transition-colors',
                      i % 2 === 0 ? 'bg-gray-900/30' : 'bg-transparent',
                      'hover:bg-gray-800/30'
                    )}
                  >
                    <td className="py-2.5 px-3 text-gray-400 font-mono whitespace-nowrap">
                      {formatTimestamp(event.timestamp)}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={clsx(
                          'px-2 py-0.5 rounded-full font-medium border',
                          typeBadge[event.event_type]
                        )}
                      >
                        {event.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={clsx(
                          'px-2 py-0.5 rounded-full font-medium border',
                          severityBadge[event.severity]
                        )}
                      >
                        {event.severity}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-gray-400 hidden md:table-cell max-w-[200px] truncate">
                      {event.rule_triggered}
                    </td>
                    <td className="py-2.5 px-3 text-gray-500 hidden lg:table-cell max-w-[180px] truncate">
                      {event.action_taken}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-800 bg-gray-900/50">
            <span className="text-xs text-gray-600">
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded text-gray-500 hover:text-gray-300 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded text-gray-500 hover:text-gray-300 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
