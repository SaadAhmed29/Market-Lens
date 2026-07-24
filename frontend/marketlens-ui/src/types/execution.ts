export interface Execution {
    id: string
    strategyName: string
    symbol: string
    exchange: string
    walletName: string
    status: 'RUNNING' | 'PAUSED' | 'ERROR'
    currentPosition: 'LONG' | 'SHORT' | 'FLAT'
    currentPnl: number
    dailyReturn: number
    lastSignal: string
    lastExecutionTime: string
    livePosition: {
        direction: 'LONG' | 'SHORT'
        entryPrice: number
        currentPrice: number
        unrealizedPnl: number
        tp: number
        sl: number
    }
    riskStats: {
        currentExposure: number
        positionSize: number
        marginUsed: number
    }
}

export interface Signal {
    id: string
    dateTime: string
    value: 1 | 0 | -1
}

export interface Order {
    id: string
    dateTime: string
    type: 'LIMIT' | 'MARKET'
    side: 'BUY' | 'SELL'
    price: number
    amount: number
    status: 'FILLED' | 'OPEN' | 'CANCELED'
}
