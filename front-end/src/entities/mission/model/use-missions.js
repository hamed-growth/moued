import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiRequest } from '../../../shared/api'

export function useMissions(userId, month) {
  const client = useQueryClient()
  const calendar = useQuery({
    queryKey: ['missions', userId, month.firstISO],
    queryFn: ({ signal }) => apiRequest(`missions/calendar/?start=${month.firstISO}&end=${month.dates.at(-1)}`, { signal }),
    enabled: Boolean(userId),
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: false,
  })
  const submit = useMutation({
    mutationFn: async ({ id, note = '' }) => {
      await apiRequest('auth/csrf/')
      return apiRequest(`missions/${id}/requests/`, { method: 'POST', body: { note } })
    },
    onSuccess: () => Promise.all([
      client.invalidateQueries({ queryKey: ['missions', userId] }),
      client.invalidateQueries({ queryKey: ['session'] }),
    ]),
    onError: () => client.invalidateQueries({ queryKey: ['missions', userId] }),
  })
  return { calendar, submit }
}
