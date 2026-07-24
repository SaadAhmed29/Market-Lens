import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export interface DashboardStrategy {
    strategy_name: string
    symbol: string
    exchange: string
    timehorizon: string
    total_trades: number
    status: string
    latest_return: number
    sharpe_ratio: number
    win_rate: number
}


export interface DashboardData {
    total_strategies: number
    active_strategies: number
    running_executions: number
    total_trades_executed: number
    running_simulations: number
    total_trades_simulated: number
    connected_accounts: number
    total_backtests: number
    total_return: number
    trained_ml_models: number
    strategies: DashboardStrategy[]
}

export interface DashboardResponse {
    status: string
    data: DashboardData
}

export const useDashboard = () => {
    return useQuery({
        queryKey: ['dashboard'],
        queryFn: async () => {
            const response = await api.get<DashboardResponse>('/dashboard')
            return response.data.data
        },
        staleTime: 30 * 1000,
        refetchInterval: 60 * 1000,
    })
}
