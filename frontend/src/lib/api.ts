import axios from 'axios'
import type {
  Agent,
  OnboardingSession,
  Plan,
  PaymentRequest,
  DashboardData,
  AuditLogPage,
  CreateAgentPayload,
  CreateOnboardingPayload,
} from '@/types'

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : import.meta.env.PROD
  ? 'https://techonboardia-production.up.railway.app/api/v1'
  : '/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error)) {
      const message =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        'An unexpected error occurred'
      return Promise.reject(new Error(message))
    }
    return Promise.reject(error)
  }
)

// Agents
export async function getAgents(): Promise<Agent[]> {
  const { data } = await apiClient.get<Agent[]>('/agents')
  return data
}

export async function getAgent(id: string): Promise<Agent> {
  const { data } = await apiClient.get<Agent>(`/agents/${id}`)
  return data
}

export async function createAgent(payload: CreateAgentPayload): Promise<Agent> {
  const { data } = await apiClient.post<Agent>('/agents', payload)
  return data
}

// Onboarding Sessions
export async function createOnboarding(payload: CreateOnboardingPayload): Promise<OnboardingSession> {
  const { data } = await apiClient.post<OnboardingSession>('/onboarding', payload)
  return data
}

export async function getOnboarding(id: string): Promise<OnboardingSession> {
  const { data } = await apiClient.get<OnboardingSession>(`/onboarding/${id}`)
  return data
}

export async function getOnboardingPlan(id: string): Promise<Plan> {
  const { data } = await apiClient.get<Plan>(`/onboarding/${id}/plan`)
  return data
}

// Payments
export async function activateAgent(payload: {
  agent_id: string
  seniority: string
  dev_email: string
}): Promise<PaymentRequest> {
  const { data } = await apiClient.post<PaymentRequest>('/payments/activate', payload)
  return data
}

export async function verifyPayment(txHash: string): Promise<boolean> {
  const { data } = await apiClient.post<{ verified: boolean }>('/payments/verify', {
    tx_hash: txHash,
  })
  return data.verified
}

export async function cancelOnboarding(id: string): Promise<OnboardingSession> {
  const { data } = await apiClient.patch<OnboardingSession>(`/onboarding/${id}/cancel`)
  return data
}

export async function deleteOnboarding(id: string): Promise<void> {
  await apiClient.delete(`/onboarding/${id}`)
}

// Dashboard
export async function getDashboard(): Promise<DashboardData> {
  const { data } = await apiClient.get<DashboardData>('/dashboard/manager')
  return data
}

// Audit Log
export async function getAuditLog(page = 1, size = 10): Promise<AuditLogPage> {
  const { data } = await apiClient.get<AuditLogPage>('/audit-log', {
    params: { page, size },
  })
  return data
}
