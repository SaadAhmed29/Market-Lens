import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Strategy, StrategyPerformance, Trade } from '@/types/strategy'

// Mock Data
const MOCK_STRATEGIES: Strategy[] = [
    {
        id: 'strat-1',
        name: 'MEAN_REVERSION_ALPHA',
        symbol: 'BTC-USD',
        exchange: 'BINANCE',
        timeframe: '1H',
        status: 'ACTIVE',
        latestReturn: 2.45,
        sharpeRatio: 1.85,
        winRate: 64.2,
        indicators: ['RSI', 'Bollinger Bands', 'MACD'],
        longConditions: ['RSI < 30', 'Close < Lower BB'],
        shortConditions: ['RSI > 70', 'Close > Upper BB'],
        riskParams: {
            maxDrawdown: 15,
            stopLoss: 2.5,
            takeProfit: 5.0
        }
    },
    {
        id: 'strat-2',
        name: 'TREND_FOLLOWING_OMEGA',
        symbol: 'ETH-USD',
        exchange: 'KRAKEN',
        timeframe: '4H',
        status: 'PAUSED',
        latestReturn: -1.2,
        sharpeRatio: 1.2,
        winRate: 45.8,
        indicators: ['EMA 50', 'EMA 200', 'ATR'],
        longConditions: ['EMA 50 > EMA 200', 'Close > EMA 50'],
        shortConditions: ['EMA 50 < EMA 200', 'Close < EMA 50'],
        riskParams: {
            maxDrawdown: 25,
            stopLoss: 4.0,
            takeProfit: 12.0
        }
    }
]

const MOCK_PERFORMANCE: StrategyPerformance = {
    sharpe: 1.85,
    sortino: 2.4,
    maxDrawdown: 12.4,
    winRate: 64.2,
    profitFactor: 1.6,
    totalReturn: 145.2
}

const MOCK_TRADES: Trade[] = [
    { id: 't-1', entryTime: '2026-07-20T14:30:00Z', exitTime: '2026-07-21T09:15:00Z', direction: 'LONG', entryPrice: 64200.5, exitPrice: 65100.0, pnl: 899.5, balanceAfter: 100899.5 },
    { id: 't-2', entryTime: '2026-07-21T11:00:00Z', exitTime: '2026-07-21T15:45:00Z', direction: 'SHORT', entryPrice: 65200.0, exitPrice: 64800.0, pnl: 400.0, balanceAfter: 101299.5 },
    { id: 't-3', entryTime: '2026-07-22T08:10:00Z', exitTime: '2026-07-22T09:00:00Z', direction: 'LONG', entryPrice: 64500.0, exitPrice: 64100.0, pnl: -400.0, balanceAfter: 100899.5 },
]

export function useStrategies() {
    return useQuery({
        queryKey: ['strategies'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/strategies')
                return data as Strategy[]
            } catch (err) {
                console.warn('Backend unavailable, using mock data for strategies')
                return MOCK_STRATEGIES
            }
        },
    })
}

export function useStrategy(id: string) {
    return useQuery({
        queryKey: ['strategy', id],
        queryFn: async () => {
            try {
                const { data } = await api.get(`/strategies/${id}`)
                return data as { strategy: Strategy, performance: StrategyPerformance, recentTrades: Trade[] }
            } catch (err) {
                console.warn(`Backend unavailable, using mock data for strategy ${id}`)
                const strategy = MOCK_STRATEGIES.find(s => s.id === id) || MOCK_STRATEGIES[0]
                return { strategy, performance: MOCK_PERFORMANCE, recentTrades: MOCK_TRADES }
            }
        },
        enabled: !!id,
    })
}
