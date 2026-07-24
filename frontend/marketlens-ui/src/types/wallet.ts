export interface Wallet {
    id: string
    exchangeName: string
    accountType: string
    apiStatus: 'CONNECTED' | 'ERROR'
    currentBalance: number
    unrealizedPnl: number
    totalPnl: number
    strategiesAssigned: number
    activePositionsCount: number
    openOrdersCount: number
}
