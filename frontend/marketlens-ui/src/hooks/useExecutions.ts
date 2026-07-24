import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Execution, Signal, Order } from '@/types/execution'

const MOCK_EXECUTIONS: Execution[] = [
    {
        id: 'exec-1',
        strategyName: 'MEAN_REVERSION_ALPHA',
        symbol: 'BTC-USD',
        exchange: 'BINANCE',
        walletName: 'BINANCE_MAIN',
        status: 'RUNNING',
        currentPosition: 'LONG',
        currentPnl: 8412.50,
        dailyReturn: 2.14,
        lastSignal: 'BUY',
        lastExecutionTime: '2026-07-24T09:35:12Z',
        livePosition: {
            direction: 'LONG',
            entryPrice: 62450.0,
            currentPrice: 63200.5,
            unrealizedPnl: 8412.50,
            tp: 65000.0,
            sl: 61500.0
        },
        riskStats: {
            currentExposure: 150000.0,
            positionSize: 2.4,
            marginUsed: 15000.0
        }
    },
    {
        id: 'exec-2',
        strategyName: 'TREND_FOLLOWING_OMEGA',
        symbol: 'ETH-USD',
        exchange: 'KRAKEN',
        walletName: 'KRAKEN_ALT',
        status: 'PAUSED',
        currentPosition: 'FLAT',
        currentPnl: 0,
        dailyReturn: 0,
        lastSignal: 'FLAT',
        lastExecutionTime: '2026-07-23T15:20:00Z',
        livePosition: { direction: 'LONG', entryPrice: 0, currentPrice: 0, unrealizedPnl: 0, tp: 0, sl: 0 },
        riskStats: { currentExposure: 0, positionSize: 0, marginUsed: 0 }
    }
]

const MOCK_SIGNALS: Signal[] = [
    { id: 'sig-1', dateTime: '2026-07-24T09:35:10Z', value: 1 },
    { id: 'sig-2', dateTime: '2026-07-23T14:20:00Z', value: -1 },
    { id: 'sig-3', dateTime: '2026-07-22T10:15:00Z', value: 0 },
]

const MOCK_ORDERS: Order[] = [
    { id: 'ord-1', dateTime: '2026-07-24T09:35:12Z', type: 'MARKET', side: 'BUY', price: 62450.0, amount: 2.4, status: 'FILLED' },
    { id: 'ord-2', dateTime: '2026-07-24T09:35:13Z', type: 'LIMIT', side: 'SELL', price: 65000.0, amount: 2.4, status: 'OPEN' },
    { id: 'ord-3', dateTime: '2026-07-24T09:35:13Z', type: 'LIMIT', side: 'SELL', price: 61500.0, amount: 2.4, status: 'OPEN' },
]

export function useExecutions() {
    return useQuery({
        queryKey: ['executions'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/executions')
                return data as Execution[]
            } catch (err) {
                console.warn('Backend unavailable, using mock data for executions')
                return MOCK_EXECUTIONS
            }
        }
    })
}

export function useExecution(id: string) {
    return useQuery({
        queryKey: ['execution', id],
        queryFn: async () => {
            try {
                const { data } = await api.get(`/executions/${id}`)
                return data as { execution: Execution, signals: Signal[], orders: Order[] }
            } catch (err) {
                console.warn(`Backend unavailable, using mock data for execution ${id}`)
                const execution = MOCK_EXECUTIONS.find(e => e.id === id) || MOCK_EXECUTIONS[0]
                return { execution, signals: MOCK_SIGNALS, orders: MOCK_ORDERS }
            }
        },
        enabled: !!id,
    })
}
