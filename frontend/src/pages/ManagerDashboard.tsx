import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, RefreshCw, Users, CheckCircle, Clock, AlertCircle, Loader2, XCircle, Trash2 } from 'lucide-react'
import clsx from 'clsx'
import { AuditLog } from '@/components/AuditLog'
import { getDashboard, cancelOnboarding, deleteOnboarding } from '@/lib/api'
import type { DashboardData, OnboardingStatus, OnboardingSession } from '@/types'

const statusBadge: Record<OnboardingStatus, { label: string; class: string }> = {
  payment_pending: {
    label: 'Payment pending',
    class: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  },
  interviewing: {
    label: 'Interviewing',
    class: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  },
  provisioning: {
    label: 'Provisioning',
    class: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  },
  active: {
    label: 'Active',
    class: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  },
  completed: {
    label: 'Completed',
    class: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  },
  failed: {
    label: 'Failed',
    class: 'bg-red-500/15 text-red-400 border-red-500/30',
  },
  cancelled: {
    label: 'Cancelled',
    class: 'bg-gray-500/15 text-gray-500 border-gray-600/30',
  },
}

function maskEmail(email: string): string {
  const [user, domain] = email.split('@')
  if (!user || !domain) return email
  const visible = user.slice(0, 2)
  const masked = '*'.repeat(Math.max(0, user.length - 2))
  return `${visible}${masked}@${domain}`
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

interface StatCardProps {
  label: string
  value: number
  icon: React.ReactNode
  colorClass: string
}

function StatCard({ label, value, icon, colorClass }: StatCardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">{label}</span>
        <div className={clsx('p-2 rounded-lg', colorClass)}>{icon}</div>
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  )
}

interface SessionRowProps {
  session: OnboardingSession
  onView: (id: string) => void
  onCancel: (id: string) => void
  onDelete: (id: string) => void
  actionLoading: string | null
}

function SessionRow({ session, onView, onCancel, onDelete, actionLoading }: SessionRowProps) {
  const badge = statusBadge[session.status] ?? statusBadge.failed
  const isLoading = actionLoading === session.id
  const isDone = session.status === 'completed' || session.status === 'cancelled'

  return (
    <tr className="border-b border-gray-800/50 hover:bg-gray-800/20 transition-colors">
      <td className="py-3 px-4 text-sm text-gray-300 font-mono">
        {maskEmail(session.dev_email)}
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="text-base">{session.agent_emoji ?? '🤖'}</span>
          <span className="text-sm text-gray-300">{session.agent_name ?? session.agent_id}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className="text-xs text-gray-400 capitalize">{session.seniority}</span>
      </td>
      <td className="py-3 px-4">
        <span
          className={clsx(
            'px-2.5 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap',
            badge.class
          )}
        >
          {badge.label}
        </span>
      </td>
      <td className="py-3 px-4 text-xs text-gray-500 hidden md:table-cell">
        {formatDate(session.created_at)}
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onView(session.id)}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            View
          </button>
          {!isDone && (
            <button
              onClick={() => onCancel(session.id)}
              disabled={isLoading}
              title="Cancel onboarding"
              className="text-amber-500 hover:text-amber-400 disabled:opacity-40 transition-colors"
            >
              {isLoading ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
            </button>
          )}
          <button
            onClick={() => onDelete(session.id)}
            disabled={isLoading}
            title="Delete permanently"
            className="text-red-500 hover:text-red-400 disabled:opacity-40 transition-colors"
          >
            {isLoading ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
          </button>
        </div>
      </td>
    </tr>
  )
}

export function ManagerDashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const dashboard = await getDashboard()
      setData(dashboard)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading the dashboard')
    } finally {
      setLoading(false)
      setLastRefresh(new Date())
    }
  }, [])

  useEffect(() => {
    void fetchData()
    const interval = setInterval(() => void fetchData(), 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleView = (sessionId: string) => {
    navigate(`/interview/${sessionId}`)
  }

  const handleCancel = async (sessionId: string) => {
    if (!confirm('Cancel this onboarding session? The record will be kept.')) return
    setActionLoading(sessionId)
    try {
      await cancelOnboarding(sessionId)
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel session')
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Permanently delete this session? This cannot be undone.')) return
    setActionLoading(sessionId)
    try {
      await deleteOnboarding(sessionId)
      await fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete session')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full py-24">
        <Loader2 size={36} className="animate-spin text-indigo-500" />
      </div>
    )
  }

  const stats = data?.stats ?? {
    total: 0,
    active: 0,
    completed: 0,
    payment_pending: 0,
    interviewing: 0,
    provisioning: 0,
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            Last updated:{' '}
            {lastRefresh.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => void fetchData()}
            className="p-2 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-800 border border-gray-800 transition-colors"
            title="Refresh"
          >
            <RefreshCw size={16} />
          </button>
          <button
            onClick={() => navigate('/agents')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            New Onboarding
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total"
          value={stats.total}
          icon={<Users size={16} className="text-indigo-400" />}
          colorClass="bg-indigo-500/15"
        />
        <StatCard
          label="Active"
          value={stats.active}
          icon={<CheckCircle size={16} className="text-emerald-400" />}
          colorClass="bg-emerald-500/15"
        />
        <StatCard
          label="Completed"
          value={stats.completed}
          icon={<CheckCircle size={16} className="text-gray-400" />}
          colorClass="bg-gray-500/15"
        />
        <StatCard
          label="Payment pending"
          value={stats.payment_pending}
          icon={<Clock size={16} className="text-amber-400" />}
          colorClass="bg-amber-500/15"
        />
      </div>

      {/* Active Sessions Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h2 className="text-sm font-semibold text-gray-200">Active Onboardings</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/80">
                <th className="text-left py-2.5 px-4 text-xs text-gray-500 font-medium">Developer</th>
                <th className="text-left py-2.5 px-4 text-xs text-gray-500 font-medium">Agent</th>
                <th className="text-left py-2.5 px-4 text-xs text-gray-500 font-medium">Level</th>
                <th className="text-left py-2.5 px-4 text-xs text-gray-500 font-medium">Status</th>
                <th className="text-left py-2.5 px-4 text-xs text-gray-500 font-medium hidden md:table-cell">Date</th>
                <th className="text-left py-2.5 px-4 text-xs text-gray-500 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {!data?.recent_sessions || data.recent_sessions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-gray-600">
                    No onboardings registered
                  </td>
                </tr>
              ) : (
                data.recent_sessions.map((session) => (
                  <SessionRow
                    key={session.id}
                    session={session}
                    onView={handleView}
                    onCancel={(id) => void handleCancel(id)}
                    onDelete={(id) => void handleDelete(id)}
                    actionLoading={actionLoading}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Log */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <AuditLog embedded initialSize={10} />
      </div>
    </div>
  )
}
