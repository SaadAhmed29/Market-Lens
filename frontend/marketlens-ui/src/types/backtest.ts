export interface BacktestRequest {
    strategyId: string
    symbol: string
    exchange: string
    timeframe: string
    startDate: string
    endDate: string
    initialCapital: number
    commission: number
    slippage: number
}

export interface Backtest {
    id: string
    strategyName: string
    symbol: string
    exchange: string
    timeframe: string
    submittedAt: string
    duration: string
    status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
    initialCapital: number
    finalCapital: number
    stats: {
        sharpe: number
        sortino: number
        calmar: number
        maxDrawdown: number
        cagr: number
        winRate: number
        profitFactor: number
        expectancy: number
        var: number
        cvar: number
    }
}
