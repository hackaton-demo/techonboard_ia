import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Loader2, AlertCircle } from 'lucide-react'
import clsx from 'clsx'
import { AgentCard } from '@/components/AgentCard'
import { SenioritySelector } from '@/components/SenioritySelector'
import { PaymentButton } from '@/components/PaymentButton'
import { useAgents } from '@/hooks/useAgentCatalog'
import { useCreateOnboarding } from '@/hooks/useOnboarding'
import { activateAgent } from '@/lib/api'
import type { Agent, SeniorityLevel, PaymentRequest, AgentCategory } from '@/types'

const SENIORITY_PRICES: Record<SeniorityLevel, number> = {
  junior: 0.50,
  mid: 1.00,
  senior: 1.00,
  staff: 2.00,
  lead: 2.00,
}

type CategoryFilter = 'all' | AgentCategory

const CATEGORY_TABS: { label: string; value: CategoryFilter }[] = [
  { label: 'All', value: 'all' },
  { label: 'Dev', value: 'dev' },
  { label: 'Ops', value: 'ops' },
  { label: 'QA', value: 'qa' },
  { label: 'AI', value: 'ai' },
  { label: 'Data', value: 'data' },
]

interface OnboardingFlowState {
  step: 'seniority' | 'payment' | 'email'
  agent: Agent
  seniority?: SeniorityLevel
  paymentRequest?: PaymentRequest
}

export function AgentCatalog() {
  const navigate = useNavigate()
  const { data: agents, isLoading, error } = useAgents()
  const createOnboarding = useCreateOnboarding()

  const [filter, setFilter] = useState<CategoryFilter>('all')
  const [flowState, setFlowState] = useState<OnboardingFlowState | null>(null)
  const [devEmail, setDevEmail] = useState('')
  const [flowError, setFlowError] = useState('')
  const [activating, setActivating] = useState(false)

  const filtered =
    filter === 'all' ? (agents ?? []) : (agents ?? []).filter((a) => a.category === filter)

  const handleAgentSelect = (agent: Agent) => {
    setFlowState({ step: 'seniority', agent })
    setFlowError('')
  }

  const handleSenioritySelect = async (level: SeniorityLevel) => {
    if (!flowState) return
    setFlowState((prev) => prev ? { ...prev, step: 'email', seniority: level } : null)
  }

  const handleEmailContinue = async () => {
    if (!flowState?.seniority || !devEmail.trim()) return
    setActivating(true)
    setFlowError('')
    try {
      const paymentReq = await activateAgent({
        agent_id: flowState.agent.id,
        seniority: flowState.seniority,
        dev_email: devEmail.trim(),
      })
      setFlowState((prev) =>
        prev ? { ...prev, step: 'payment', paymentRequest: paymentReq } : null
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error activating the agent'
      // If 402-like error, still show payment (for demo)
      if (msg.includes('402') || msg.includes('payment')) {
        const demoPayment: PaymentRequest = {
          session_id: '',
          amount_usdc: SENIORITY_PRICES[flowState.seniority ?? 'mid'],
          wallet_address: '0x742d35Cc6634C0532925a3b8D4C9a1A7c3de4F9e',
          network: 'Base',
          expires_at: new Date(Date.now() + 3600000).toISOString(),
          memo: `Onboarding ${flowState.agent.name}`,
        }
        setFlowState((prev) =>
          prev ? { ...prev, step: 'payment', paymentRequest: demoPayment } : null
        )
      } else {
        setFlowError(msg)
      }
    } finally {
      setActivating(false)
    }
  }

  const handlePaymentSuccess = async () => {
    if (!flowState?.seniority) return
    try {
      const session = await createOnboarding.mutateAsync({
        dev_email: devEmail,
        agent_id: flowState.agent.id,
        seniority: flowState.seniority,
        tx_hash: 'demo_txhash_123',
      })
      navigate(`/interview/${session.id}`)
    } catch (err) {
      setFlowError(err instanceof Error ? err.message : 'Error creating the session')
    }
  }

  const handleCloseFlow = () => {
    setFlowState(null)
    setDevEmail('')
    setFlowError('')
    setActivating(false)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Catalog</h1>
          <p className="text-gray-500 text-sm mt-1">
            Select the right agent for your new developer
          </p>
        </div>
        <button
          onClick={() => navigate('/agents/new')}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
        >
          <Plus size={16} />
          Create Agent
        </button>
      </div>

      {/* Category Filter Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        {CATEGORY_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setFilter(tab.value)}
            className={clsx(
              'px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200',
              filter === tab.value
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <div className="text-center space-y-3">
            <Loader2 size={36} className="animate-spin text-indigo-500 mx-auto" />
            <p className="text-gray-500 text-sm">Loading agents...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center justify-center py-24">
          <div className="text-center space-y-3">
            <AlertCircle size={36} className="text-red-500 mx-auto" />
            <p className="text-gray-400 text-sm">Error loading agents</p>
            <p className="text-gray-600 text-xs">{error instanceof Error ? error.message : 'Unknown error'}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && filtered.length === 0 && (
        <div className="text-center py-24">
          <div className="text-4xl mb-4">🤖</div>
          <p className="text-gray-400">No agents in this category</p>
          <button
            onClick={() => navigate('/agents/new')}
            className="mt-4 text-indigo-400 hover:text-indigo-300 text-sm underline"
          >
            Create the first one
          </button>
        </div>
      )}

      {/* Agents Grid */}
      {!isLoading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onSelect={handleAgentSelect} />
          ))}
        </div>
      )}

      {/* Onboarding Flow Modal */}
      {flowState && (
        <>
          {flowState.step === 'seniority' && (
            <SenioritySelector
              agent={flowState.agent}
              onSelect={handleSenioritySelect}
              onCancel={handleCloseFlow}
            />
          )}

          {flowState.step === 'email' && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={handleCloseFlow} />
              <div className="relative z-10 w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl p-6">
                <h2 className="text-base font-semibold text-white mb-1">
                  Developer email
                </h2>
                <p className="text-sm text-gray-500 mb-5">
                  Enter the developer's email to start onboarding with{' '}
                  <span className="text-indigo-400">{flowState.agent.name}</span>{' '}
                  ({flowState.seniority})
                </p>
                <input
                  type="email"
                  value={devEmail}
                  onChange={(e) => setDevEmail(e.target.value)}
                  placeholder="dev@company.com"
                  className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-indigo-500 mb-3 transition-colors"
                  onKeyDown={(e) => { if (e.key === 'Enter') void handleEmailContinue() }}
                />
                {flowError && (
                  <p className="text-xs text-red-400 mb-3">{flowError}</p>
                )}
                <div className="flex gap-3">
                  <button
                    onClick={handleCloseFlow}
                    className="flex-1 py-2 rounded-lg text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => void handleEmailContinue()}
                    disabled={!devEmail.trim() || activating}
                    className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                  >
                    {activating ? <Loader2 size={14} className="animate-spin" /> : null}
                    Continue
                  </button>
                </div>
              </div>
            </div>
          )}

          {flowState.step === 'payment' && flowState.paymentRequest && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={handleCloseFlow} />
              <div className="relative z-10 w-full max-w-md">
                <PaymentButton
                  paymentRequest={flowState.paymentRequest}
                  onSuccess={() => void handlePaymentSuccess()}
                  onError={(e) => setFlowError(e)}
                />
                {flowError && (
                  <p className="text-xs text-red-400 mt-2 text-center">{flowError}</p>
                )}
                <button
                  onClick={handleCloseFlow}
                  className="w-full mt-3 py-2 text-sm text-gray-500 hover:text-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
