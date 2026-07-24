import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { DashboardStats } from '@/types/dashboard'

const MOCK_STATS: DashboardStats = {
    totalStrategies: 24,
    activeStrategies: 8,
    runningExecutions: 3,
    runningSimulations: 1,
    connectedAccounts: 2,
    trainedMlModels: 12,
    totalBacktests: 142,
    todayPnl: 5204.10,
    overallPortfolioValue: 248190.42,
    totalReturn: 24.5
}

export function useDashboardStats() {
    return useQuery({
        queryKey: ['dashboard-stats'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/dashboard')
                return data as DashboardStats
            } catch (err) {
                console.warn('Backend unavailable, using mock data for dashboard stats')
                return MOCK_STATS
            }
        }
    })
}
