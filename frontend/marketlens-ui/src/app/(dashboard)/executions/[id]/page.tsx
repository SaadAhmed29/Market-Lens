'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { DataTable, Column } from '@/components/shared/DataTable'
import { useExecution } from '@/hooks/useExecutions'
import { Signal, Order } from '@/types/execution'
import { Pause, Square, Terminal } from 'lucide-react'

export default function ExecutionDetailPage() {
    const params = useParams()
    const { data, isLoading } = useExecution(params.id as string)

    if (isLoading) {
        return <PageWrapper title="LOADING_EXECUTION_DATA..."><div/></PageWrapper>
    }

    if (!data) {
        return <PageWrapper title="EXECUTION_NOT_FOUND"><div/></PageWrapper>
    }

    const { execution, signals, orders } = data

    const signalColumns: Column<Signal>[] = [
        { header: 'DATE_TIME', cell: (row) => new Date(row.dateTime).toLocaleString() },
        { 
            header: 'SIGNAL_VALUE', 
            cell: (row) => (
                <span className={row.value === 1 ? 'text-accent' : row.value === -1 ? 'text-destructive' : 'text-muted-foreground'}>
                    {row.value === 1 ? 'LONG (1)' : row.value === -1 ? 'SHORT (-1)' : 'FLAT (0)'}
                </span>
            )
        },
    ]

    const orderColumns: Column<Order>[] = [
        { header: 'DATE_TIME', cell: (row) => new Date(row.dateTime).toLocaleString() },
        { header: 'TYPE', accessorKey: 'type' },
        { 
            header: 'SIDE', 
            cell: (row) => (
                <span className={row.side === 'BUY' ? 'text-accent' : 'text-destructive'}>
                    {row.side}
                </span>
            )
        },
        { header: 'PRICE', cell: (row) => `$${row.price.toLocaleString()}` },
        { header: 'AMOUNT', accessorKey: 'amount' },
        { 
            header: 'STATUS', 
            cell: (row) => (
                <Badge variant={row.status === 'FILLED' ? 'cyber-completed' : row.status === 'OPEN' ? 'cyber-pending' : 'cyber-stopped'}>
                    {row.status}
                </Badge>
            )
        }
    ]

    return (
        <PageWrapper 
            title={`EXEC_NODE: ${execution.strategyName}`}
            actions={
                <div className="flex items-center gap-4">
                    <Badge variant={execution.status === 'RUNNING' ? 'cyber-running' : 'cyber-paused'}>{execution.status}</Badge>
                    <div className="flex gap-2">
                        <Button variant="cyber-outline" size="sm"><Pause className="size-4 mr-2" /> PAUSE</Button>
                        <Button variant="cyber-destructive" size="sm"><Square className="size-4 mr-2" /> STOP</Button>
                    </div>
                </div>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Live Position */}
                <Card className="lg:col-span-1 border-border bg-card cyber-chamfer">
                    <CardHeader className="py-3 border-b border-border bg-background/50">
                        <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                            <span className="animate-pulse">&gt;</span> LIVE_POSITION
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 flex flex-col gap-4">
                        <div className="flex justify-between items-center border-b border-border pb-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">DIRECTION</span>
                                <Badge variant={execution.livePosition.direction === 'LONG' ? 'cyber-active' : execution.livePosition.direction === 'SHORT' ? 'destructive' : 'outline'} className="w-fit">
                                    {execution.livePosition.direction}
                                </Badge>
                            </div>
                            <div className="flex flex-col gap-1 text-right">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">UNREALIZED_PNL</span>
                                <span className={`text-xl font-mono ${execution.livePosition.unrealizedPnl > 0 ? 'text-accent' : 'text-destructive'}`}>
                                    {execution.livePosition.unrealizedPnl > 0 ? '+' : ''}${execution.livePosition.unrealizedPnl.toLocaleString()}
                                </span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 border-b border-border pb-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">ENTRY_PRICE</span>
                                <span className="text-sm font-mono">${execution.livePosition.entryPrice.toLocaleString()}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">CURRENT_PRICE</span>
                                <span className="text-sm font-mono text-accent animate-pulse">${execution.livePosition.currentPrice.toLocaleString()}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TAKE_PROFIT</span>
                                <span className="text-sm font-mono text-accent">${execution.livePosition.tp.toLocaleString()}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">STOP_LOSS</span>
                                <span className="text-sm font-mono text-destructive">${execution.livePosition.sl.toLocaleString()}</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">POSITION_SIZE</span>
                                <span className="text-sm font-mono">{execution.riskStats.positionSize} {execution.symbol.split('-')[0]}</span>
                            </div>
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">EXPOSURE</span>
                                <span className="text-sm font-mono">${execution.riskStats.currentExposure.toLocaleString()}</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Log & Tables */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    {/* Fake Terminal Log */}
                    <Card className="border-border bg-card cyber-chamfer" variant="terminal">
                        <CardHeader className="py-2 border-b border-border/50 bg-background flex flex-row items-center gap-2">
                            <Terminal className="size-4 text-accent" />
                            <CardTitle className="text-xs font-mono uppercase tracking-widest text-muted-foreground">SYSTEM_LOG</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 h-32 overflow-y-auto font-mono text-xs text-muted-foreground flex flex-col gap-1">
                            <div><span className="text-secondary">[SYS]</span> 2026-07-24 09:35:10 - Processing new candle for BTC-USD...</div>
                            <div><span className="text-secondary">[SYS]</span> 2026-07-24 09:35:11 - Signal generated: LONG (1.0)</div>
                            <div><span className="text-accent">[EXEC]</span> 2026-07-24 09:35:12 - Order placed: BUY 2.4 BTC @ MKT</div>
                            <div><span className="text-accent">[EXEC]</span> 2026-07-24 09:35:12 - Order filled: 2.4 BTC @ 62450.0</div>
                            <div><span className="text-secondary">[SYS]</span> 2026-07-24 09:35:13 - Setting SL/TP brackets...</div>
                            <div className="text-foreground animate-pulse mt-2">&gt;_</div>
                        </CardContent>
                    </Card>

                    <Tabs defaultValue="orders" className="w-full">
                        <TabsList>
                            <TabsTrigger value="orders">ORDER_BOOK</TabsTrigger>
                            <TabsTrigger value="signals">SIGNAL_HISTORY</TabsTrigger>
                        </TabsList>
                        <TabsContent value="orders" className="mt-4">
                            <DataTable data={orders} columns={orderColumns} />
                        </TabsContent>
                        <TabsContent value="signals" className="mt-4">
                            <DataTable data={signals} columns={signalColumns} />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </PageWrapper>
    )
}
