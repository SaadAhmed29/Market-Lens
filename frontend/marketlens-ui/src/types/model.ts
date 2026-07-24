export interface MLModel {
    id: string
    name: string
    type: 'CLASSIFIER' | 'REGRESSOR' | 'TIMESERIES'
    symbol: string
    timeframe: string
    trainingDate: string
    primaryMetricName: string
    score: number
    dataset: {
        exchange: string
        startDate: string
        endDate: string
        trainValSplit: string
    }
    features: string[]
    targetColumn: string
    trainingInfo: {
        algorithm: string
        hyperparameters: Record<string, any>
        preprocessing: string
        scaling: string
        stationarity: string
    }
    evaluation: {
        mlMetrics: Record<string, number>
        backtestMetrics: Record<string, number>
    }
}
