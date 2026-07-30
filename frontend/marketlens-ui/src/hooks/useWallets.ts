import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export function useWallets() {
    return useQuery({
        queryKey: ['wallets'],
        queryFn: async () => {
            const { data } = await api.get('/wallets')
            return data.data ?? []
        },
        staleTime: 60000,
    })
}

export function useWalletDetail(accountName: string) {
    return useQuery({
        queryKey: ['wallets', accountName],
        queryFn: async () => {
            const { data } = await api.get(`/wallets/${accountName}`)
            return data.data ?? data
        },
        staleTime: 60000,
        enabled: !!accountName,
    })
}

export function useUpdateWalletKeys() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async ({ accountName, api_key, api_secret }: { accountName: string, api_key: string, api_secret: string }) => {
            const { data } = await api.put(`/wallets/${accountName}/keys`, { api_key, api_secret })
            return data
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['wallets'] })
            queryClient.invalidateQueries({ queryKey: ['wallets', variables.accountName] })
        }
    })
}

export function useUnassignedStrategies() {
    return useQuery({
        queryKey: ['unassigned_strategies'],
        queryFn: async () => {
            const { data } = await api.get('/wallets/strategies/unassigned')
            return data.data ?? []
        },
        staleTime: 60000,
    })
}

export function useAssignStrategy() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: async ({ strategy_name, allow_execution, allow_simulation }: { strategy_name: string, allow_execution: boolean, allow_simulation: boolean }) => {
            const { data } = await api.put('/wallets/strategies/assign', { strategy_name, allow_execution, allow_simulation })
            return data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unassigned_strategies'] })
        }
    })
}
