'use client'

import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable, Column } from '@/components/shared/DataTable'
import { useSentiment } from '@/hooks/useSentiment'
import { SymbolSentiment } from '@/types/sentiment'

export default function SentimentPage() {
    const { data: sentiment, isLoading } = useSentiment()

    const columns: Column<SymbolSentiment>[] = [
        { header: 'SYMBOL', accessorKey: 'symbol', className: 'text-accent' },
        { 
            header: 'LATEST_SIGNAL', 
            cell: (row) => (
                <span className={
                    row.latestLabel === 'POSITIVE' ? 'text-accent font-bold' : 
                    row.latestLabel === 'NEGATIVE' ? 'text-destructive font-bold' : 'text-muted-foreground'
                }>
                    {row.latestLabel}
                </span>
            )
        },
        { 
            header: 'CONFIDENCE', 
            cell: (row) => (
                <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 bg-muted overflow-hidden flex">
                        <div 
                            className={`h-full ${row.latestLabel === 'POSITIVE' ? 'bg-accent' : row.latestLabel === 'NEGATIVE' ? 'bg-destructive' : 'bg-foreground'}`} 
                            style={{ width: `${row.confidenceScore * 100}%` }} 
                        />
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground">
                        {(row.confidenceScore * 100).toFixed(1)}%
                    </span>
                </div>
            )
        },
        { header: 'LAST_UPDATED', cell: (row) => new Date(row.lastUpdated).toLocaleTimeString(), className: 'text-right' },
    ]

    return (
        <PageWrapper title="MARKET_SENTIMENT">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                
                {/* Fear & Greed */}
                <Card className="border-border bg-card cyber-chamfer flex flex-col justify-center items-center py-8">
                    <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-4">FEAR_GREED_INDEX</span>
                    <div className="relative size-32 flex items-center justify-center mb-2">
                        <svg viewBox="0 0 100 50" className="w-full h-full absolute top-0 left-0">
                            <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="var(--muted)" strokeWidth="10" />
                            {sentiment && (
                                <path 
                                    d="M 10 50 A 40 40 0 0 1 90 50" 
                                    fill="none" 
                                    stroke="var(--accent)" 
                                    strokeWidth="10" 
                                    strokeDasharray={`${(sentiment.overview.fearGreedIndex / 100) * 125.6} 125.6`} 
                                />
                            )}
                        </svg>
                        <span className="text-3xl font-mono font-bold mt-8">{isLoading ? '...' : sentiment?.overview.fearGreedIndex}</span>
                    </div>
                    <span className="text-xs font-mono text-accent">
                        {sentiment?.overview.fearGreedIndex && sentiment.overview.fearGreedIndex > 60 ? 'GREED' : 
                         sentiment?.overview.fearGreedIndex && sentiment.overview.fearGreedIndex < 40 ? 'FEAR' : 'NEUTRAL'}
                    </span>
                </Card>

                {/* Social Sentiment */}
                <Card className="border-border bg-card cyber-chamfer">
                    <CardHeader className="py-3 border-b border-border bg-background/50 text-center">
                        <CardTitle className="text-xs font-mono uppercase tracking-widest text-foreground">SOCIAL_SENTIMENT</CardTitle>
                    </CardHeader>
                    <CardContent className="p-8 flex flex-col items-center justify-center gap-4 h-[calc(100%-41px)]">
                        <span className={`text-4xl font-mono ${sentiment?.overview.overallMarketSentiment && sentiment.overview.overallMarketSentiment > 0 ? 'text-accent' : 'text-destructive'}`}>
                            {isLoading ? '...' : (sentiment?.overview.overallMarketSentiment || 0).toFixed(2)}
                        </span>
                        <span className="text-[10px] text-muted-foreground text-center">AGGREGATED TWITTER & REDDIT SCORE (-1.0 TO 1.0)</span>
                    </CardContent>
                </Card>

                {/* News Sentiment */}
                <Card className="border-border bg-card cyber-chamfer">
                    <CardHeader className="py-3 border-b border-border bg-background/50 text-center">
                        <CardTitle className="text-xs font-mono uppercase tracking-widest text-foreground">NEWS_SENTIMENT</CardTitle>
                    </CardHeader>
                    <CardContent className="p-8 flex flex-col items-center justify-center gap-4 h-[calc(100%-41px)]">
                        <span className={`text-4xl font-mono ${sentiment?.overview.newsSentiment && sentiment.overview.newsSentiment > 0 ? 'text-accent' : 'text-destructive'}`}>
                            {isLoading ? '...' : (sentiment?.overview.newsSentiment || 0).toFixed(2)}
                        </span>
                        <span className="text-[10px] text-muted-foreground text-center">FINANCIAL NEWS NLP SCORE (-1.0 TO 1.0)</span>
                    </CardContent>
                </Card>
            </div>

            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">ASSET_SENTIMENT_MONITOR</h2>
            </div>
            
            <DataTable 
                data={sentiment?.symbols || []} 
                columns={columns} 
                isLoading={isLoading}
            />
        </PageWrapper>
    )
}
