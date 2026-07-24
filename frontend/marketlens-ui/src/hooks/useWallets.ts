import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Wallet } from '@/types/wallet'

const MOCK_WALLETS: Wallet[] = [
    {
        id: 'w-1',
        exchangeName: 'BINANCE',
        accountType: 'FUTURES',
        apiStatus: 'CONNECTED',
        currentBalance: 245190.42,
        unrealizedPnl: 8412.50,
        totalPnl: 45190.42,
        strategiesAssigned: 3,
        activePositionsCount: 2,
        openOrdersCount: 5
    },
    {
        id: 'w-2',
        exchangeName: 'KRAKEN',
        accountType: 'SPOT',
        apiStatus: 'CONNECTED',
        currentBalance: 52400.00,
        unrealizedPnl: -640.00,
        totalPnl: 2400.00,
        strategiesAssigned: 1,
        activePositionsCount: 1,
        openOrdersCount: 1
    },
    {
        id: 'w-3',
        exchangeName: 'BYBIT',
        accountType: 'FUTURES',
        apiStatus: 'ERROR',
        currentBalance: 0,
        unrealizedPnl: 0,
        totalPnl: 0,
        strategiesAssigned: 0,
        activePositionsCount: 0,
        openOrdersCount: 0
    }
]

export function useWallets() {
    return useQuery({
        queryKey: ['wallets'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/wallets')
                return data as Wallet[]
            } catch (err) {
                console.warn('Backend unavailable, using mock data for wallets')
                return MOCK_WALLETS
            }
        }
    })
}
