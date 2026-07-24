export interface SentimentOverview {
    fearGreedIndex: number // 0-100
    overallMarketSentiment: number // -1 to 1
    newsSentiment: number // -1 to 1
}

export interface SymbolSentiment {
    symbol: string
    latestLabel: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'
    confidenceScore: number
    lastUpdated: string
}

export interface SentimentData {
    overview: SentimentOverview
    symbols: SymbolSentiment[]
}
