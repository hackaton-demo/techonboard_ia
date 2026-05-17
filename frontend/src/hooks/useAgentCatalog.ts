import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAgents, getAgent, createAgent } from '@/lib/api'
import type { CreateAgentPayload } from '@/types'

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: getAgents,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useAgent(id: string | undefined) {
  return useQuery({
    queryKey: ['agent', id],
    queryFn: () => getAgent(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCreateAgent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateAgentPayload) => createAgent(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['agents'] })
    },
  })
}
