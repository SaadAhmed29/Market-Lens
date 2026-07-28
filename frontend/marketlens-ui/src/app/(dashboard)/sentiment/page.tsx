'use client'

import React, { useState } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/shared/EmptyState'
import { useSentiment, SentimentPost } from '@/hooks/useSentiment'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, Legend } from 'recharts'
import { ChevronDown, ChevronUp, MessageSquare } from 'lucide-react'

// Sentiment color helpers
function sentimentColor(label: string): string {
    if (label === 'bullish') return 'text-accent'
    if (label === 'bearish') return 'text-destructive'
    return 'text-muted-foreground'
}

function sentimentBadgeVariant(label: string): "cyber-active" | "cyber-error" | "cyber-stopped" {
    if (label === 'bullish') return 'cyber-active'
    if (label === 'bearish') return 'cyber-error'
    return 'cyber-stopped'
}

function sentimentBgGlow(label: string): string {
    if (label === 'bullish') return 'shadow-[var(--shadow-neon-lg)]'
    if (label === 'bearish') return 'shadow-[0_0_10px_rgba(255,51,102,0.5),0_0_20px_rgba(255,51,102,0.3)]'
    return ''
}

// Post card with expand/collapse for body and comments
function titleColorForSentiment(label: string) {
    const normalized = label?.toLowerCase()
    if (normalized === 'bearish' || normalized === 'negative') return 'text-destructive'
    if (normalized === 'bullish' || normalized === 'positive') return 'text-accent'
    return 'text-foreground'
}

function PostCard({ post }: { post: SentimentPost }) {
    const [expanded, setExpanded] = useState(false)
    const [commentsOpen, setCommentsOpen] = useState(false)

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardContent className="p-4 flex flex-col gap-3">
                {/* Header row */}
                <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                        <Badge variant="outline">{post.symbol}</Badge>
                        <Badge variant={sentimentBadgeVariant(post.label)}>
                            {post.label.toUpperCase()}
                        </Badge>
                    </div>
                    <span className="text-sm font-mono text-muted-foreground">
                        {(post.confidence_score * 100).toFixed(0)}%
                    </span>
                </div>

                {/* Title */}
                <h3 className={`text-lg font-heading font-bold uppercase tracking-wider ${titleColorForSentiment(post.label)}`}>
                    {post.title}
                </h3>

                {/* Body */}
                <div className="text-sm text-muted-foreground leading-relaxed">
                    <p className={!expanded ? 'line-clamp-3' : ''}>
                        {post.body}
                    </p>
                    {post.body.length > 150 && (
                        <button
                            onClick={() => setExpanded(!expanded)}
                            className="text-sm font-mono uppercase tracking-widest mt-1 hover:underline h-12"
                            style={{ color: 'var(--accent-tertiary)' }}
                        >
                            {expanded ? '< COLLAPSE' : '> read more'}
                        </button>
                    )}
                </div>

                {/* Comments toggle */}
                {post.comments && post.comments.length > 0 && (
                    <div className="border-t border-border pt-2">
                        <button
                            onClick={() => setCommentsOpen(!commentsOpen)}
                            className="flex items-center gap-2 text-sm font-mono uppercase tracking-widest text-muted-foreground hover:text-accent transition-colors"
                        >
                            <MessageSquare className="size-3" />
                            <span>{post.comments.length} COMMENT{post.comments.length !== 1 ? 'S' : ''}</span>
                            {commentsOpen ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                        </button>
                        {commentsOpen && (
                            <div className="mt-2 flex flex-col gap-1 pl-2 border-l border-border">
                                {post.comments.map((comment, i) => (
                                    <p key={i} className="text-sm font-mono text-muted-foreground">
                                        <span className="text-accent">&gt;</span> {comment}
                                    </p>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

export default function SentimentPage() {
    const { data, isLoading, isError } = useSentiment()

    if (isLoading) {
        return (
            <PageWrapper title="MARKET SENTIMENT">
                {/* Skeleton: top strip */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {Array.from({ length: 4 }).map((_, i) => (
                        <Skeleton key={i} className="h-24 w-full bg-card cyber-chamfer border border-border" />
                    ))}
                </div>
                {/* Skeleton: symbol row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-3">
                    {Array.from({ length: 8 }).map((_, i) => (
                        <Skeleton key={i} className="h-16 w-full bg-card cyber-chamfer border border-border" />
                    ))}
                </div>
                {/* Skeleton: charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Skeleton className="h-64 w-full bg-card cyber-chamfer border border-border" />
                    <Skeleton className="h-64 w-full bg-card cyber-chamfer border border-border" />
                </div>
                {/* Skeleton: posts */}
                <Skeleton className="h-96 w-full bg-card cyber-chamfer border border-border" />
            </PageWrapper>
        )
    }

    if (isError || !data) {
        return (
            <PageWrapper title="MARKET SENTIMENT">
                <EmptyState message="FAILED_TO_LOAD_SENTIMENT_DATA" />
            </PageWrapper>
        )
    }

    const { sample_posts, overall_distribution, per_symbol_distribution, symbol_sentiment, market_sentiment } = data

    // Chart data for overall distribution
    const overallChartData = [
        { name: 'Bullish', value: overall_distribution.bullish },
        { name: 'Bearish', value: overall_distribution.bearish },
        { name: 'Neutral', value: overall_distribution.neutral },
    ]
    const overallColors = ['var(--accent)', 'var(--destructive)', 'var(--accent-tertiary)']

    // Chart data for per-symbol distribution
    const symbolKeys = Object.keys(per_symbol_distribution)
    const perSymbolChartData = symbolKeys.map((sym) => ({
        name: sym,
        bullish: per_symbol_distribution[sym]?.bullish || 0,
        bearish: per_symbol_distribution[sym]?.bearish || 0,
        neutral: per_symbol_distribution[sym]?.neutral || 0,
    }))

    // Tab symbols from sample_posts
    const postSymbols = Object.keys(sample_posts)

    return (
        <PageWrapper title="MARKET SENTIMENT">

            {/* Top Strip */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Market Sentiment Badge */}
                <Card className={`border-border bg-card cyber-chamfer flex flex-col justify-center items-center py-6 ${sentimentBgGlow(market_sentiment)}`}>
                    <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">MARKET SENTIMENT</span>
                    <Badge
                        variant={sentimentBadgeVariant(market_sentiment)}
                        className="text-lg px-4 py-1"
                    >
                        {market_sentiment.toUpperCase()}
                    </Badge>
                </Card>

                {/* Stat cards */}
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4 flex flex-col gap-1">
                        <span className="text-xs font-bold text-center text-muted-foreground uppercase tracking-widest">TOTAL BULLISH</span>
                        <span className="text-2xl font-mono text-center text-accent">{overall_distribution.bullish.toLocaleString()}</span>
                    </CardContent>
                </Card>
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4 flex flex-col gap-1">
                        <span className="text-xs font-bold text-center text-muted-foreground uppercase tracking-widest">TOTAL BEARISH</span>
                        <span className="text-2xl font-mono text-center text-destructive">{overall_distribution.bearish.toLocaleString()}</span>
                    </CardContent>
                </Card>
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4 flex flex-col gap-1">
                        <span className="text-xs font-bold text-center text-muted-foreground uppercase tracking-widest">TOTAL NEUTRAL</span>
                        <span className="text-2xl font-mono text-center text-muted-foreground">{overall_distribution.neutral.toLocaleString()}</span>
                    </CardContent>
                </Card>
            </div>

            {/* Per Symbol Sentiment Row */}
            <div>
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-accent">&gt;</span>
                    <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">SYMBOL SENTIMENT</h2>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-7 gap-5 justify-center">
                    {Object.entries(symbol_sentiment).map(([symbol, label]) => (
                        <Card key={symbol} className="border-border bg-card cyber-chamfer">
                            <CardContent className="p-4 flex flex-col items-center gap-1.5">
                                <span className="text-sm font-mono font-bold text-foreground">{symbol}</span>
                                <Badge variant={sentimentBadgeVariant(label)} className="text-xs">
                                    {label.toUpperCase()}
                                </Badge>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>

            {/*  Distribution Charts  */}
            <div>
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-accent">&gt;</span>
                    <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">DISTRIBUTION ANALYSIS</h2>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-1 gap-6">
                    {/* Overall Distribution */}
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="p-4 border-b border-border/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-secondary">OVERALL DISTRIBUTION</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 h-80">
                            {overallChartData.some(d => d.value > 0) ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={overallChartData}>
                                        <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} interval={0} />
                                        <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                        <Tooltip
                                            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '0px' }}
                                            itemStyle={{ color: 'hsl(var(--foreground))', fontFamily: 'monospace' }}
                                        />
                                        <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                                            {overallChartData.map((_, index) => (
                                                <Cell key={`cell-${index}`} fill={overallColors[index]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex items-center justify-center">
                                    <span className="text-xs text-muted-foreground font-mono uppercase">NO_DATA</span>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Per Symbol Distribution (grouped bar) */}
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="p-4 border-b border-border/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-secondary">PER-SYMBOL DISTRIBUTION</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 h-80">
                            {perSymbolChartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={perSymbolChartData}>
                                        <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} interval={0} />
                                        <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                        <Tooltip
                                            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '0px' }}
                                            itemStyle={{ color: 'hsl(var(--foreground))', fontFamily: 'monospace' }}
                                        />
                                        <Legend
                                            wrapperStyle={{ fontSize: '14px', fontFamily: 'monospace' }}
                                        />
                                        <Bar dataKey="bullish" fill="var(--accent)" radius={[2, 2, 0, 0]} />
                                        <Bar dataKey="bearish" fill="var(--destructive)" radius={[2, 2, 0, 0]} />
                                        <Bar dataKey="neutral" fill="var(--accent-tertiary)" radius={[2, 2, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex items-center justify-center">
                                    <span className="text-xs text-muted-foreground font-mono uppercase">NO DATA</span>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/*  Sample Posts Section */}
            <div>
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-accent">&gt;</span>
                    <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">REDDIT POSTS</h2>
                </div>

                {postSymbols.length > 0 ? (
                    <Tabs defaultValue={postSymbols[0]} className="w-full">
                        <TabsList>
                            {postSymbols.map((sym) => (
                                <TabsTrigger key={sym} value={sym}>{sym}</TabsTrigger>
                            ))}
                        </TabsList>
                        {postSymbols.map((sym) => (
                            <TabsContent key={sym} value={sym} className="mt-4">
                                <div className="grid grid-cols-1 gap-4">
                                    {(sample_posts[sym] || []).map((post, idx) => (
                                        <PostCard key={`${sym}-${idx}`} post={post} />
                                    ))}
                                </div>
                            </TabsContent>
                        ))}
                    </Tabs>
                ) : (
                    <EmptyState message="NO_SAMPLE_POSTS_AVAILABLE" />
                )}
            </div>

        </PageWrapper>
    )
}
