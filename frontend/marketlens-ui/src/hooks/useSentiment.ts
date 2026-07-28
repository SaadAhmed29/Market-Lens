import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export interface SentimentPost {
    symbol: string
    title: string
    body: string
    comments: string[]
    label: 'bullish' | 'bearish' | 'neutral'
    confidence_score: number
}

export interface SentimentDistribution {
    bullish: number
    bearish: number
    neutral: number
}

export interface SentimentApiData {
    sample_posts: Record<string, SentimentPost[]>
    overall_distribution: SentimentDistribution
    per_symbol_distribution: Record<string, SentimentDistribution>
    symbol_sentiment: Record<string, 'bullish' | 'bearish' | 'neutral'>
    market_sentiment: 'bullish' | 'bearish' | 'neutral'
}

interface SentimentResponse {
    status: string
    data: SentimentApiData
}

export function useSentiment() {
    return useQuery({
        queryKey: ['sentiment'],
        queryFn: async () => {
            const response = await api.get<SentimentResponse>('/sentiment')
            return response.data.data
        },
        staleTime: 5 * 60 * 1000,
    })
}
