import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export function useStrategyBuilder() {
    return useQuery({
        queryKey: ['strategy-builder'],
        queryFn: async () => {
            const { data } = await api.get('/strategy-builder')
            return data.data ?? []
        },
        staleTime: 0,
        refetchInterval: 10000,
    })
}

export function useStrategyBuilderOptions() {
    return useQuery({
        queryKey: ['strategy-builder', 'options'],
        queryFn: async () => {
            const { data } = await api.get('/strategy-builder/options')
            return data.data ?? []
        },
        staleTime: 30000,
    })
}

export function useStrategyBuilderDetail(requestId: string) {
    return useQuery({
        queryKey: ['strategy-builder', requestId],
        queryFn: async () => {
            const { data } = await api.get(`/strategy-builder/${requestId}`)
            return data.data ?? data
        },
        staleTime: 30000,
        enabled: !!requestId,
    })
}

export function useSubmitStrategyBuilder() {
    const queryClient = useQueryClient()
    return useMutation({
        mutationFn: async (config: any) => {
            const { data } = await api.post('/strategy-builder', config)
            return data.data ?? data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['strategy-builder'] })
        }
    })
}

export function useSaveStrategy() {
    return useMutation({
        mutationFn: async (config: any) => {
            const { data } = await api.post('/strategy-builder/save', config)
            return data
        }
    })
}
