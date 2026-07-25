import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export function useStrategies() {
    return useQuery({
        queryKey: ['strategies'],
        queryFn: async () => {
            const { data } = await api.get('/strategies')
            return data.data ?? []
        },
        staleTime: 30 * 1000,
    })
}

export function useStrategyDetail(strategyName: string) {
    return useQuery({
        queryKey: ['strategy', strategyName],
        queryFn: async () => {
            const { data } = await api.get(`/strategies/${strategyName}`)
            return data.data ?? data
        },
        enabled: !!strategyName,
        staleTime: 30 * 1000,
    })
}
