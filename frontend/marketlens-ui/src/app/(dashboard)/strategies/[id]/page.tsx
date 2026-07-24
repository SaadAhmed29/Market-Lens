'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DataTable, Column } from '@/components/shared/DataTable'
import { EquityCurve } from '@/components/charts/EquityCurve'
import { DrawdownChart } from '@/components/charts/DrawdownChart'
import { ReturnsHeatmap } from '@/components/charts/ReturnsHeatmap'
import { useStrategy } from '@/hooks/useStrategies'
import { Trade } from '@/types/strategy'

export default function StrategyDetailPage() {
    const params = useParams()
    const { data, isLoading } = useStrategy(params.id as string)

    if (isLoading) {
        return <PageWrapper title="LOADING_STRATEGY_DATA..."><div/></PageWrapper>
    }

    if (!data) {
        return <PageWrapper title="STRATEGY_NOT_FOUND"><div/></PageWrapper>
    }

    const { strategy, performance, recentTrades } = data

    const tradeColumns: Column<Trade>[] = [
        { header: 'ENTRY_TIME', cell: (row) => new Date(row.entryTime).toLocaleString() },
        { header: 'EXIT_TIME', cell: (row) => new Date(row.exitTime).toLocaleString() },
        { 
            header: 'DIR', 
            cell: (row) => <span className={row.direction === 'LONG' ? 'text-accent' : 'text-destructive'}>{row.direction}</span>
        },
        { header: 'ENTRY_PRICE', cell: (row) => `$${row.entryPrice.toLocaleString()}` },
        { header: 'EXIT_PRICE', cell: (row) => `$${row.exitPrice.toLocaleString()}` },
        { 
            header: 'PNL', 
            cell: (row) => (
                <span className={row.pnl > 0 ? 'text-accent' : 'text-destructive'}>
                    {row.pnl > 0 ? '+' : ''}${row.pnl.toLocaleString()}
                </span>
            ),
            className: 'text-right'
        },
    ]

    // Mock chart data
    const mockCurve = Array.from({ length: 50 }).map((_, i) => ({
        date: `Day ${i}`,
        value: 100000 + (Math.sin(i / 5) * 5000) + (i * 500)
    }))
    
    const mockDrawdown = Array.from({ length: 50 }).map((_, i) => ({
        date: `Day ${i}`,
        value: -(Math.random() * 5 + (Math.cos(i / 5) * 5 + 5))
    }))
    
    const mockHeatmap = [
        { year: 2026, months: [2.1, -1.5, 4.2, 0.5, -2.1, 8.4, 3.1, null, null, null, null, null], ytd: 15.3 },
        { year: 2025, months: [-5.4, 2.1, 1.2, 3.4, -1.2, -4.5, 2.1, 6.7, 8.1, -2.3, 1.1, 4.5], ytd: 15.8 },
        { year: 2024, months: [1.1, 2.2, 3.3, -4.4, -5.5, 6.6, 7.7, -8.8, 9.9, 1.2, -2.1, 3.4], ytd: 14.6 }
    ]

    return (
        <PageWrapper 
            title={strategy.name}
            actions={
                <Badge variant={
                    strategy.status === 'ACTIVE' ? 'cyber-running' : 
                    strategy.status === 'PAUSED' ? 'cyber-paused' : 'cyber-stopped'
                }>
                    {strategy.status}
                </Badge>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Info Panel */}
                <div className="flex flex-col gap-6">
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent">STRATEGY_CONFIG</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 flex flex-col gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">SYMBOL</span>
                                    <span className="text-sm font-mono text-foreground">{strategy.symbol}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">EXCHANGE</span>
                                    <span className="text-sm font-mono text-foreground">{strategy.exchange}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TIMEFRAME</span>
                                    <span className="text-sm font-mono text-foreground">{strategy.timeframe}</span>
                                </div>
                            </div>
                            
                            <div className="border-t border-border pt-4">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest mb-2 block">INDICATORS</span>
                                <div className="flex flex-wrap gap-2">
                                    {strategy.indicators.map((ind, i) => (
                                        <span key={i} className="px-2 py-1 bg-muted text-xs font-mono border border-border cyber-chamfer-sm text-foreground/80">{ind}</span>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-xs font-mono uppercase tracking-widest text-secondary">PERFORMANCE_SUMMARY</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">SHARPE</span>
                                <span className="text-lg font-mono text-foreground">{performance.sharpe}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">WIN_RATE</span>
                                <span className="text-lg font-mono text-foreground">{performance.winRate}%</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">MAX_DD</span>
                                <span className="text-lg font-mono text-destructive">{performance.maxDrawdown}%</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TOTAL_RET</span>
                                <span className="text-lg font-mono text-accent">{performance.totalReturn}%</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <Tabs defaultValue="charts" className="w-full">
                        <TabsList>
                            <TabsTrigger value="charts">PERFORMANCE_CHARTS</TabsTrigger>
                            <TabsTrigger value="trades">TRADE_LEDGER</TabsTrigger>
                        </TabsList>
                        <TabsContent value="charts" className="flex flex-col gap-6 mt-4">
                            <EquityCurve data={mockCurve} />
                            <DrawdownChart data={mockDrawdown} />
                            <ReturnsHeatmap data={mockHeatmap} />
                        </TabsContent>
                        <TabsContent value="trades" className="mt-4">
                            <DataTable data={recentTrades} columns={tradeColumns} />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </PageWrapper>
    )
}
