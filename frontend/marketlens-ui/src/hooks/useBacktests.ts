import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export function useBacktests() {
    return useQuery({
        queryKey: ['backtests'],
        queryFn: async () => {
            const { data } = await api.get('/backtests')
            return data.data ?? []
        },
        staleTime: 0,
        refetchInterval: 10000,
    })
}

export function useBacktestOptions() {
    return useQuery({
        queryKey: ['backtests', 'options'],
        queryFn: async () => {
            const { data } = await api.get('/backtests/options')
            return data.data ?? []
        },
        staleTime: 30000,
    })
}

export function useBacktestDetail(requestId: string) {
    return useQuery({
        queryKey: ['backtests', requestId],
        queryFn: async () => {
            const { data } = await api.get(`/backtests/${requestId}`)
            return data.data ?? data
        },
        staleTime: 30000,
        enabled: !!requestId,
    })
}

export function useSubmitBacktest() {
    const queryClient = useQueryClient()
    return useMutation({
        mutationFn: async (config: any) => {
            const { data } = await api.post('/backtests', config)
            return data.data ?? data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['backtests'] })
        }
    })
}
