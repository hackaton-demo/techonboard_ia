import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getOnboarding,
  createOnboarding,
  getOnboardingPlan,
} from '@/lib/api'
import type { CreateOnboardingPayload } from '@/types'

export function useOnboarding(id: string | undefined) {
  return useQuery({
    queryKey: ['onboarding', id],
    queryFn: () => getOnboarding(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data?.status === 'provisioning' || data?.status === 'interviewing') {
        return 5000
      }
      return false
    },
  })
}

export function useCreateOnboarding() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateOnboardingPayload) => createOnboarding(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(['onboarding', data.id], data)
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useOnboardingPlan(id: string | undefined) {
  return useQuery({
    queryKey: ['onboarding-plan', id],
    queryFn: () => getOnboardingPlan(id!),
    enabled: !!id,
  })
}
