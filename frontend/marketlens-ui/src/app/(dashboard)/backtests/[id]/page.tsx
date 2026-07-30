'use client'

import React, { useState, useMemo, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/shared/EmptyState'
import { DataTable } from '@/components/shared/DataTable'
import { useBacktestDetail } from '@/hooks/useBacktests'
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { EquityCurve } from '@/components/charts/EquityCurve'
import { DrawdownChart } from '@/components/charts/DrawdownChart'
import { PieChart } from '@/components/charts/PieChart'

const LEDGER_PAGE_SIZE = 10

function StatCard({ title, value, colored = false, formatFn }: { title: string, value: any, colored?: boolean, formatFn?: (v: number) => string }) {
    let formattedValue = value
    if (typeof value === 'number') {
        formattedValue = formatFn ? formatFn(value) : value.toLocaleString(undefined, { maximumFractionDigits: 4 })
    }

    let colorClass = "text-foreground"
    if (colored && typeof value === 'number') {
        colorClass = value > 0 ? "text-accent" : value < 0 ? "text-destructive" : "text-foreground"
    }

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardContent className="p-4 flex flex-col gap-1">
                <span className="text-xs text-center font-bold text-muted-foreground uppercase tracking-widest font-mono">{title}</span>
                <span className={`text-2xl text-center font-mono ${colorClass}`}>{formattedValue ?? '-'}</span>
            </CardContent>
        </Card>
    )
}

export default function BacktestDetailPage() {
    const params = useParams()
    const requestId = params.id as string

    const { data, isLoading, isError } = useBacktestDetail(requestId)

    const [ledgerPage, setLedgerPage] = useState(1)

    const rawLedger = useMemo(() => data?.ledger || [], [data?.ledger])

    useEffect(() => {
        setLedgerPage(1)
    }, [rawLedger])

    if (isLoading) {
        return (
            <PageWrapper title={`BACKTEST_${requestId?.substring(0, 8) || 'LOADING'}`}>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
                    {Array.from({ length: 12 }).map((_, i) => (
                        <Card key={i} className="border-border bg-card cyber-chamfer h-24 animate-pulse" />
                    ))}
                </div>
            </PageWrapper>
        )
    }

    if (isError || !data || !data.request) {
        return (
            <PageWrapper title="BACKTEST_ERROR">
                <EmptyState message="FAILED_TO_LOAD_BACKTEST_DETAIL" />
            </PageWrapper>
        )
    }

    const { request, equity_curve, drawdown, monthly_returns, win_loss, ledger } = data
    const summary = typeof request.result_summary === 'string' ? JSON.parse(request.result_summary) : (request.result_summary || {})
    const config = typeof request.request_config === 'string' ? JSON.parse(request.request_config) : (request.request_config || {})
    const strategyName = request.strategy_name || 'UNKNOWN'

    // PieChart component expects a fraction (0–1), so derive it from win_loss data
    const winEntry = (win_loss || []).find((e: any) => e.name === 'WIN')
    const totalWL = (win_loss || []).reduce((acc: number, e: any) => acc + (Number(e.value) || 0), 0)
    const winRate = winEntry && totalWL > 0 ? Number(winEntry.value) / totalWL : 0

    let statusVariant = 'cyber-pending'
    if (request.status === 'Completed') statusVariant = 'cyber-completed'
    else if (request.status === 'Running') statusVariant = 'cyber-running'
    else if (request.status === 'Failed') statusVariant = 'cyber-error'

    const handleExport = () => {
        const json = JSON.stringify(ledger, null, 2)
        const blob = new Blob([json], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${strategyName}_ledger.json`
        a.click()
        URL.revokeObjectURL(url)
    }

    const ledgerColumns = [
        { header: 'ENTRY TIME', cell: (r: any) => r.entry_time ? new Date(r.entry_time).toLocaleString() : '-' },
        { header: 'EXIT TIME', cell: (r: any) => r.exit_time ? new Date(r.exit_time).toLocaleString() : '-' },
        {
            header: 'DIRECTION',
            cell: (r: any) => (
                <Badge variant={r.direction?.toUpperCase() === 'LONG' ? 'cyber-running' : 'cyber-paused'}>
                    {r.direction?.toUpperCase() || '-'}
                </Badge>
            )
        },
        { header: 'ENTRY PRICE', cell: (r: any) => r.entry_price != null ? `$${Number(r.entry_price).toFixed(2)}` : '-' },
        { header: 'EXIT PRICE', cell: (r: any) => r.exit_price != null ? `$${Number(r.exit_price).toFixed(2)}` : '-' },
        { header: 'QTY', cell: (r: any) => r.quantity != null ? Number(r.quantity).toFixed(4) : '-' },
        { header: 'GROSS PNL', cell: (r: any) => r.gross_pnl != null ? `$${Number(r.gross_pnl).toFixed(2)}` : '-' },
        { header: 'COMMISSION', cell: (r: any) => r.commission != null ? `$${Number(r.commission).toFixed(2)}` : '-' },
        { header: 'SLIPPAGE', cell: (r: any) => r.slippage != null ? `$${Number(r.slippage).toFixed(2)}` : '-' },
        {
            header: 'NET PNL',
            cell: (r: any) => (
                <span className={r.net_pnl > 0 ? "text-accent font-bold" : r.net_pnl < 0 ? "text-destructive font-bold" : ""}>
                    {r.net_pnl != null ? `$${Number(r.net_pnl).toFixed(2)}` : '-'}
                </span>
            )
        },
        { header: 'BALANCE', cell: (r: any) => r.balance_after_trade != null ? `$${Number(r.balance_after_trade).toFixed(2)}` : '-' }
    ]

    const ledgerTotalPages = Math.max(1, Math.ceil(rawLedger.length / LEDGER_PAGE_SIZE))
    const ledgerCurrentPage = Math.min(ledgerPage, ledgerTotalPages)
    const paginatedLedger = rawLedger.slice(
        (ledgerCurrentPage - 1) * LEDGER_PAGE_SIZE,
        ledgerCurrentPage * LEDGER_PAGE_SIZE
    )

    return (
        <PageWrapper title={`BT_${strategyName.substring(0, 18)}.....`} actions={
            <Button variant="cyber-outline" size="sm" onClick={handleExport}>
                EXPORT_LEDGER
            </Button>
        }>
            {/* Header info */}
            <div className="flex flex-wrap items-center gap-4 mb-6">
                <Badge variant={statusVariant as any} className={request.status === 'Running' ? 'animate-pulse' : ''}>
                    {request.status.toUpperCase()}
                </Badge>
                <div className="flex flex-col">
                    <span className="text-xs text-muted-foreground font-bold tracking-widest uppercase">STRATEGY</span>
                    <span className="text-sm font-mono text-accent">{strategyName}</span>
                </div>
                <div className="w-[1px] h-6 bg-border mx-2" />
                <div className="flex flex-col">
                    <span className="text-xs text-muted-foreground font-bold tracking-widest uppercase">DATE RANGE</span>
                    <span className="text-sm font-mono text-foreground">{config.start_date || '-'} to {config.end_date || '-'}</span>
                </div>
                <div className="w-[1px] h-6 bg-border mx-2" />
                <div className="flex flex-col">
                    <span className="text-xs text-muted-foreground font-bold tracking-widest uppercase">INITIAL / FINAL BAL</span>
                    <span className="text-sm font-mono text-foreground">
                        ${config.initial_balance || 0} &rarr; ${summary.final_balance != null ? Number(summary.final_balance).toLocaleString() : '---'}
                    </span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
                {Object.entries(summary).map(([k, v]) => (
                    <StatCard
                        key={k}
                        title={k.replace(/_/g, ' ')}
                        value={v}
                        colored={k.includes('sharpe') || k.includes('drawdown') || k.includes('pnl') || k.includes('win_rate') || k === 'total_net_profit' || k === 'cagr'}
                        formatFn={k === 'win_rate' ? (val) => `${val.toFixed(1)}%` : undefined}
                    />
                ))}
            </div>

            {/* Charts Tabbed */}
            <div className="mb-8">
                <Tabs defaultValue="equity">
                    <TabsList className="mb-4">
                        <TabsTrigger value="equity">EQUITY CURVE</TabsTrigger>
                        <TabsTrigger value="drawdown">DRAWDOWN</TabsTrigger>
                        <TabsTrigger value="monthly">MONTHLY RETURNS</TabsTrigger>
                        <TabsTrigger value="winloss">WIN/LOSS</TabsTrigger>
                    </TabsList>

                    <TabsContent value="equity">
                        <EquityCurve data={equity_curve || []} height={320} />
                    </TabsContent>

                    <TabsContent value="drawdown">
                        <DrawdownChart data={drawdown || []} height={320} />
                    </TabsContent>

                    <TabsContent value="monthly">
                        <Card className="border-border bg-card cyber-chamfer">
                            <CardContent className="p-4 h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={monthly_returns || []}>
                                        <XAxis dataKey="month" stroke="#888888" fontSize={10} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#888888" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val) => `${val.toFixed(2)}%`} />
                                        <Tooltip
                                            cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                                            contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '0' }}
                                            itemStyle={{ color: '#ffffff' }}
                                            labelStyle={{ color: '#ffffff' }}
                                            formatter={(val: any) => `${Number(val).toFixed(4)}%`}
                                        />
                                        <Bar dataKey="return" radius={[2, 2, 0, 0]}>
                                            {(monthly_returns || []).map((entry: any, index: number) => (
                                                <Cell key={`cell-${index}`} fill={Number(entry.return) >= 0 ? "var(--accent)" : "var(--destructive)"} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="winloss">
                        <PieChart winRate={(summary.win_rate ?? 0) / 100} height={320} />
                    </TabsContent>
                </Tabs>
            </div>

            {/* Ledger Table */}
            <div className="mb-6">
                <h3 className="text-sm font-mono uppercase tracking-widest text-muted-foreground mb-4">TRADE LEDGER</h3>
                <DataTable data={paginatedLedger} columns={ledgerColumns} emptyMessage="NO_TRADES_EXECUTED" />

                {rawLedger.length > LEDGER_PAGE_SIZE && (
                    <div className="flex items-center justify-between mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                        <button
                            onClick={() => setLedgerPage((p) => Math.max(1, p - 1))}
                            disabled={ledgerCurrentPage === 1}
                            className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                        >
                            &lt; PREV
                        </button>
                        <span>
                            PAGE {ledgerCurrentPage} / {ledgerTotalPages}
                        </span>
                        <button
                            onClick={() => setLedgerPage((p) => Math.min(ledgerTotalPages, p + 1))}
                            disabled={ledgerCurrentPage === ledgerTotalPages}
                            className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                        >
                            NEXT &gt;
                        </button>
                    </div>
                )}
            </div>
        </PageWrapper>
    )
}