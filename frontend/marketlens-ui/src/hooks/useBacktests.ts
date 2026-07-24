import { useQuery, useMutation } from '@tanstack/react-query'
import api from '@/lib/api'
import { Backtest, BacktestRequest } from '@/types/backtest'
import { queryClient } from '@/lib/queryClient'

const MOCK_BACKTESTS: Backtest[] = [
    {
        id: 'bt-1',
        strategyName: 'MEAN_REVERSION_ALPHA',
        symbol: 'BTC-USD',
        exchange: 'BINANCE',
        timeframe: '1H',
        submittedAt: '2026-07-24T08:00:00Z',
        duration: '45s',
        status: 'COMPLETED',
        initialCapital: 100000,
        finalCapital: 124500,
        stats: {
            sharpe: 1.85,
            sortino: 2.4,
            calmar: 1.2,
            maxDrawdown: -12.4,
            cagr: 24.5,
            winRate: 64.2,
            profitFactor: 1.6,
            expectancy: 45.2,
            var: -2.5,
            cvar: -3.8
        }
    },
    {
        id: 'bt-2',
        strategyName: 'TREND_FOLLOWING_OMEGA',
        symbol: 'ETH-USD',
        exchange: 'KRAKEN',
        timeframe: '4H',
        submittedAt: '2026-07-24T09:15:00Z',
        duration: '...',
        status: 'RUNNING',
        initialCapital: 50000,
        finalCapital: 50000,
        stats: {
            sharpe: 0, sortino: 0, calmar: 0, maxDrawdown: 0, cagr: 0, winRate: 0, profitFactor: 0, expectancy: 0, var: 0, cvar: 0
        }
    }
]

export function useBacktests() {
    return useQuery({
        queryKey: ['backtests'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/backtests')
                return data as Backtest[]
            } catch (err) {
                console.warn('Backend unavailable, using mock data for backtests')
                return MOCK_BACKTESTS
            }
        }
    })
}

export function useBacktest(id: string) {
    return useQuery({
        queryKey: ['backtest', id],
        queryFn: async () => {
            try {
                const { data } = await api.get(`/backtests/${id}`)
                return data as Backtest
            } catch (err) {
                console.warn(`Backend unavailable, using mock data for backtest ${id}`)
                return MOCK_BACKTESTS.find(b => b.id === id) || MOCK_BACKTESTS[0]
            }
        },
        enabled: !!id,
    })
}

export function useSubmitBacktest() {
    return useMutation({
        mutationFn: async (req: BacktestRequest) => {
            try {
                const { data } = await api.post('/backtests', req)
                return data
            } catch (err) {
                console.warn('Backend unavailable, simulating backtest submission')
                return { status: 'ok', id: `bt-${Date.now()}` }
            }
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['backtests'] })
        }
    })
}
