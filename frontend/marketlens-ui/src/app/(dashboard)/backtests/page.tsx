'use client'

import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useBacktests, useSubmitBacktest } from '@/hooks/useBacktests'
import { Backtest } from '@/types/backtest'

export default function BacktestsPage() {
    const router = useRouter()
    const { data: backtests, isLoading } = useBacktests()
    const submitBacktest = useSubmitBacktest()

    const columns: Column<Backtest>[] = [
        { header: 'STRATEGY', accessorKey: 'strategyName', className: 'text-accent' },
        { header: 'SYMBOL', accessorKey: 'symbol' },
        { header: 'EXCHANGE', accessorKey: 'exchange' },
        { header: 'TIMEFRAME', accessorKey: 'timeframe' },
        { header: 'SUBMITTED', cell: (row) => new Date(row.submittedAt).toLocaleString() },
        { header: 'DURATION', accessorKey: 'duration' },
        { 
            header: 'STATUS', 
            cell: (row) => (
                <Badge variant={
                    row.status === 'COMPLETED' ? 'cyber-completed' : 
                    row.status === 'RUNNING' ? 'cyber-running' : 
                    row.status === 'FAILED' ? 'cyber-error' : 'cyber-pending'
                }>
                    {row.status}
                </Badge>
            )
        }
    ]

    const handleRunBacktest = (e: React.FormEvent) => {
        e.preventDefault()
        submitBacktest.mutate({
            strategyId: 'strat-1',
            symbol: 'BTC-USD',
            exchange: 'BINANCE',
            timeframe: '1H',
            startDate: '2025-01-01',
            endDate: '2026-01-01',
            initialCapital: 100000,
            commission: 0.05,
            slippage: 0.1
        })
    }

    return (
        <PageWrapper title="BACKTEST_ENGINE">
            
            {/* Request Form */}
            <Card className="border-border bg-card cyber-chamfer mb-6">
                <CardHeader className="py-3 border-b border-border bg-background/50">
                    <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                        <span className="animate-pulse">&gt;</span> NEW_SIMULATION_REQUEST
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-6">
                    <form onSubmit={handleRunBacktest} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] text-muted-foreground uppercase tracking-widest">STRATEGY</label>
                            <Input placeholder="SELECT STRATEGY..." />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] text-muted-foreground uppercase tracking-widest">SYMBOL</label>
                            <Input placeholder="e.g. BTC-USD" />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] text-muted-foreground uppercase tracking-widest">TIMEFRAME</label>
                            <Input placeholder="e.g. 1H" />
                        </div>
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] text-muted-foreground uppercase tracking-widest">CAPITAL</label>
                            <Input type="number" placeholder="100000" />
                        </div>
                        <div className="lg:col-span-4 flex justify-end mt-2">
                            <Button type="submit" variant="cyber-glitch" disabled={submitBacktest.isPending}>
                                {submitBacktest.isPending ? 'INITIALIZING...' : 'EXECUTE_BACKTEST'}
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* List */}
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">SIMULATION_HISTORY</h2>
            </div>
            <DataTable 
                data={backtests || []} 
                columns={columns} 
                isLoading={isLoading}
                onRowClick={(row) => row.status === 'COMPLETED' && router.push(`/backtests/${row.id}`)}
                emptyMessage="NO_BACKTESTS_FOUND"
            />
        </PageWrapper>
    )
}
