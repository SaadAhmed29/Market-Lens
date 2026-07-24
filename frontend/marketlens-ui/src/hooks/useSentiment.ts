import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { SentimentData } from '@/types/sentiment'

const MOCK_SENTIMENT: SentimentData = {
    overview: {
        fearGreedIndex: 65,
        overallMarketSentiment: 0.42,
        newsSentiment: 0.28
    },
    symbols: [
        { symbol: 'BTC', latestLabel: 'POSITIVE', confidenceScore: 0.85, lastUpdated: '2026-07-24T09:30:00Z' },
        { symbol: 'ETH', latestLabel: 'POSITIVE', confidenceScore: 0.72, lastUpdated: '2026-07-24T09:30:00Z' },
        { symbol: 'SOL', latestLabel: 'NEUTRAL', confidenceScore: 0.55, lastUpdated: '2026-07-24T09:30:00Z' },
        { symbol: 'ADA', latestLabel: 'NEGATIVE', confidenceScore: 0.64, lastUpdated: '2026-07-24T09:30:00Z' },
        { symbol: 'XRP', latestLabel: 'NEUTRAL', confidenceScore: 0.48, lastUpdated: '2026-07-24T09:30:00Z' }
    ]
}

export function useSentiment() {
    return useQuery({
        queryKey: ['sentiment'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/sentiment')
                return data as SentimentData
            } catch (err) {
                console.warn('Backend unavailable, using mock data for sentiment')
                return MOCK_SENTIMENT
            }
        }
    })
}
