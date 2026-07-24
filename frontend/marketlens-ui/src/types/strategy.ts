export interface Strategy {
    id: string
    name: string
    symbol: string
    exchange: string
    timeframe: string
    status: 'ACTIVE' | 'PAUSED' | 'STOPPED'
    latestReturn: number
    sharpeRatio: number
    winRate: number
    indicators: string[]
    longConditions: string[]
    shortConditions: string[]
    riskParams: {
        maxDrawdown: number
        stopLoss: number
        takeProfit: number
    }
}

export interface StrategyPerformance {
    sharpe: number
    sortino: number
    maxDrawdown: number
    winRate: number
    profitFactor: number
    totalReturn: number
}

export interface Trade {
    id: string
    entryTime: string
    exitTime: string
    direction: 'LONG' | 'SHORT'
    entryPrice: number
    exitPrice: number
    pnl: number
    balanceAfter: number
}
