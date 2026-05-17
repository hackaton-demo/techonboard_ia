import { useParams, useNavigate } from 'react-router-dom'
import { Download, ExternalLink, CalendarCheck, ArrowLeft, Loader2, AlertCircle } from 'lucide-react'
import { PlanTimeline } from '@/components/PlanTimeline'
import { AccessStatus } from '@/components/AccessStatus'
import { useOnboardingPlan } from '@/hooks/useOnboarding'

function maskEmail(email: string): string {
  const [user, domain] = email.split('@')
  if (!user || !domain) return email
  const visible = user.slice(0, 2)
  const masked = '*'.repeat(Math.max(0, user.length - 2))
  return `${visible}${masked}@${domain}`
}

const CHECKIN_DESCRIPTIONS: Record<number, string> = {
  3: 'Review of first steps, initial questions and expectation alignment',
  7: 'First week evaluation, team feedback and plan for the second week',
  14: 'Final onboarding review, confirmed accesses and first month objectives',
}

export function OnboardingPlan() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { data: plan, isLoading, error } = useOnboardingPlan(sessionId)

  const handleDownloadPDF = () => {
    // UI only for hackathon
    alert('PDF export functionality coming soon')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full py-24">
        <div className="text-center space-y-3">
          <Loader2 size={36} className="animate-spin text-indigo-500 mx-auto" />
          <p className="text-gray-500 text-sm">Loading your onboarding plan...</p>
        </div>
      </div>
    )
  }

  if (error || !plan) {
    return (
      <div className="flex items-center justify-center h-full py-24">
        <div className="text-center space-y-3">
          <AlertCircle size={36} className="text-red-500 mx-auto" />
          <p className="text-gray-400">Could not load the plan</p>
          <button
            onClick={() => navigate(-1)}
            className="text-indigo-400 hover:text-indigo-300 text-sm underline"
          >
            Go back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        <ArrowLeft size={16} />
        Go back
      </button>

      {/* Welcome Header */}
      <div className="relative bg-gradient-to-br from-indigo-900/30 to-gray-900 border border-indigo-500/20 rounded-2xl p-8 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/5 to-transparent pointer-events-none" />
        <div className="relative">
          <div className="text-5xl mb-4">{plan.agent_emoji}</div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Welcome to the team, {maskEmail(plan.dev_email)}
          </h1>
          <p className="text-gray-400 text-sm leading-relaxed max-w-lg">
            {plan.agent_name} has prepared your personalized onboarding plan for the next 14 days.
            As a <span className="text-indigo-400 font-medium capitalize">{plan.seniority} Engineer</span>,
            this plan is designed to help you integrate into the team effectively.
          </p>
          <div className="mt-4 flex items-center gap-2 text-xs text-gray-600">
            <span>Generated on</span>
            <span>{new Date(plan.generated_at).toLocaleDateString('en-US', { day: '2-digit', month: 'long', year: 'numeric' })}</span>
          </div>
        </div>

        {/* Download button */}
        <button
          onClick={handleDownloadPDF}
          className="absolute top-6 right-6 flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/80 hover:bg-gray-800 border border-gray-700 text-xs text-gray-400 hover:text-gray-200 transition-colors"
        >
          <Download size={14} />
          Download PDF
        </button>
      </div>

      {/* Two column layout for wider screens */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Plan Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            14-Day Plan
          </h2>
          <PlanTimeline days={plan.days} todayDay={1} />
        </div>

        {/* Right: Sidebar */}
        <div className="space-y-6">
          {/* Accesses */}
          <div>
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
              Provisioned Accesses
            </h2>
            <AccessStatus accesses={plan.accesses} />
          </div>

          {/* First Ticket */}
          {plan.ticket && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                First Assigned Ticket
              </h3>
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-mono text-indigo-400">{plan.ticket.id}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full border ${
                      plan.ticket.priority === 'high'
                        ? 'bg-red-500/15 text-red-400 border-red-500/30'
                        : plan.ticket.priority === 'medium'
                        ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                        : 'bg-gray-500/15 text-gray-400 border-gray-500/30'
                    }`}
                  >
                    {plan.ticket.priority}
                  </span>
                </div>
                <h4 className="text-sm font-medium text-white leading-tight">
                  {plan.ticket.title}
                </h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  {plan.ticket.description}
                </p>
                <div className="flex flex-wrap gap-1">
                  {plan.ticket.labels.map((label) => (
                    <span
                      key={label}
                      className="text-xs px-2 py-0.5 rounded-md bg-gray-800 text-gray-400 border border-gray-700/50"
                    >
                      {label}
                    </span>
                  ))}
                </div>
                {plan.ticket.url && (
                  <a
                    href={plan.ticket.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors mt-1"
                  >
                    <ExternalLink size={12} />
                    View in Jira
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Check-ins */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <CalendarCheck size={14} />
              Scheduled Check-ins
            </h3>
            <div className="space-y-3">
              {plan.checkin_days.map((day) => (
                <div key={day} className="flex gap-3 items-start">
                  <div className="w-8 h-8 rounded-full bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-xs font-bold text-purple-400 flex-shrink-0">
                    {day}
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-300">Day {day}</p>
                    <p className="text-xs text-gray-600 leading-relaxed mt-0.5">
                      {CHECKIN_DESCRIPTIONS[day] ?? `Day ${day} check-in`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
