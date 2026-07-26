import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export function useExecutions() {
    return useQuery({
        queryKey: ['executions'],
        queryFn: async () => {
            const { data } = await api.get('/executions')
            return data.data
        },
        staleTime: 30000,
        refetchInterval: 60000,
    })
}

export function useExecutionDetail(strategyName: string) {
    return useQuery({
        queryKey: ['executions', strategyName],
        queryFn: async () => {
            const { data } = await api.get(`/executions/${strategyName}`)
            return data.data
        },
        enabled: !!strategyName,
        staleTime: 30000,
        refetchInterval: 60000,
    })
}
