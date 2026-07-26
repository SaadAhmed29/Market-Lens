import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export function useModels() {
    return useQuery({
        queryKey: ['models'],
        queryFn: async () => {
            const { data } = await api.get('/models')
            return data.data
        },
        staleTime: 60 * 1000
    })
}

export function useModelDetail(modelName: string) {
    return useQuery({
        queryKey: ['model', modelName],
        queryFn: async () => {
            const { data } = await api.get(`/models/${modelName}`)
            return data.data
        },
        enabled: !!modelName,
        staleTime: 60 * 1000
    })
}
