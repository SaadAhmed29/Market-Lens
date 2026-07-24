'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { DataTable, Column } from '@/components/shared/DataTable'
import { EquityCurve } from '@/components/charts/EquityCurve'
import { DrawdownChart } from '@/components/charts/DrawdownChart'
import { ReturnsHeatmap } from '@/components/charts/ReturnsHeatmap'
import { useBacktest } from '@/hooks/useBacktests'
import { Trade } from '@/types/strategy'

export default function BacktestDetailPage() {
    const params = useParams()
    const { data: backtest, isLoading } = useBacktest(params.id as string)

    if (isLoading) {
        return <PageWrapper title="LOADING_SIMULATION_DATA..."><div/></PageWrapper>
    }

    if (!backtest) {
        return <PageWrapper title="SIMULATION_NOT_FOUND"><div/></PageWrapper>
    }

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
    ]

    return (
        <PageWrapper 
            title={`BACKTEST: ${backtest.strategyName}`}
            actions={
                <div className="flex items-center gap-4">
                    <Badge variant="cyber-completed">{backtest.status}</Badge>
                    <Button variant="cyber-outline">EXPORT_REPORT_JSON</Button>
                </div>
            }
        >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4">
                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">INITIAL_CAPITAL</span>
                        <span className="text-xl font-mono text-foreground">${backtest.initialCapital.toLocaleString()}</span>
                    </CardContent>
                </Card>
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4">
                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">FINAL_CAPITAL</span>
                        <span className="text-xl font-mono text-accent">${backtest.finalCapital.toLocaleString()}</span>
                    </CardContent>
                </Card>
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4">
                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">SHARPE_RATIO</span>
                        <span className="text-xl font-mono text-foreground">{backtest.stats.sharpe}</span>
                    </CardContent>
                </Card>
                <Card className="border-border bg-card cyber-chamfer">
                    <CardContent className="p-4">
                        <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">MAX_DRAWDOWN</span>
                        <span className="text-xl font-mono text-destructive">{backtest.stats.maxDrawdown}%</span>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                
                {/* QuantStats Grid */}
                <Card className="lg:col-span-1 border-border bg-card cyber-chamfer h-fit">
                    <CardHeader className="py-3 border-b border-border bg-background/50">
                        <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent">QUANT_STATS</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="flex flex-col divide-y divide-border">
                            {Object.entries(backtest.stats).map(([key, value]) => (
                                <div key={key} className="flex items-center justify-between p-3 text-sm font-mono hover:bg-muted/30 transition-colors">
                                    <span className="text-muted-foreground uppercase tracking-wider">{key.replace(/([A-Z])/g, '_$1')}</span>
                                    <span className="text-foreground">{value}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Charts */}
                <div className="lg:col-span-3">
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
                            <Card className="border-border bg-card cyber-chamfer p-12 text-center text-muted-foreground font-mono">
                                [ TRADE_LEDGER_DATA_UNAVAILABLE ]
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </PageWrapper>
    )
}
