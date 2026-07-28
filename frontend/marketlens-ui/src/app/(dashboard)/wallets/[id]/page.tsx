'use client'

import React, { useState, useMemo, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/shared/EmptyState'
import { DataTable } from '@/components/shared/DataTable'
import { useWalletDetail } from '@/hooks/useWallets'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'

const HISTORY_PAGE_SIZE = 10

function formatCurrency(val: number) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0)
}

function formatPercent(val: number) {
    return `${(val * 100).toFixed(2)}%`
}

function StatCard({ title, value, isCurrency = false, isPercent = false, colored = false }: { title: string, value: any, isCurrency?: boolean, isPercent?: boolean, colored?: boolean }) {
    let formattedValue = value
    if (isCurrency) formattedValue = formatCurrency(value)
    else if (isPercent) formattedValue = formatPercent(value)
    else if (typeof value === 'number') formattedValue = value.toLocaleString(undefined, { maximumFractionDigits: 2 })

    let colorClass = "text-foreground"
    if (colored && typeof value === 'number') {
        colorClass = value > 0 ? "text-accent" : value < 0 ? "text-destructive" : "text-foreground"
    }

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardContent className="p-4 flex flex-col gap-1">
                <span className="text-xs font-bold text-center justify-center items-center text-muted-foreground uppercase tracking-widest">{title}</span>
                <span className={`text-2xl font-mono text-center ${colorClass}`}>{formattedValue}</span>
            </CardContent>
        </Card>
    )
}

function PnlChart({ data, title }: { data: any, title: string }) {
    // Convert object to array if needed
    let chartData = Array.isArray(data) ? data : Object.entries(data || {}).map(([name, value]) => ({ name, value }))
    // standardize names
    chartData = chartData.map(item => {
        let name = item.name || item.symbol || item.hour || item.day || Object.keys(item)[0]
        if (typeof name === 'string') {
            name = name.replace(/USDT$/i, '')
            if (title.toUpperCase().includes('DOW')) {
                name = name.slice(0, 3).toUpperCase()
            }
        }
        return {
            name,
            value: item.value ?? item.pnl ?? Object.values(item)[0]
        }
    })

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardHeader className="p-4 border-b border-border/50">
                <CardTitle className="text-sm font-mono uppercase tracking-widest text-secondary">{title}</CardTitle>
            </CardHeader>
            <CardContent className="p-4 h-48">
                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData}>
                            <XAxis dataKey="name" stroke="#888888" fontSize={10} tickLine={false} axisLine={false} interval={0} />
                            <YAxis stroke="#888888" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                            <Tooltip
                                cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                                contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '0px' }}
                                itemStyle={{ color: 'hsl(var(--foreground))', fontFamily: 'monospace' }}
                            />
                            <Bar dataKey="value" radius={[2, 2, 0, 0]}>
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={Number(entry.value) >= 0 ? "var(--accent)" : "var(--destructive)"} />
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
    )
}

export default function WalletDetailPage() {
    const params = useParams()
    const accountName = params.id as string

    const { data, isLoading, isError } = useWalletDetail(accountName)

    const [historyPage, setHistoryPage] = useState(1)

    const rawHistory = useMemo(() => data?.history || [], [data?.history])

    useEffect(() => {
        setHistoryPage(1)
    }, [rawHistory])

    if (isLoading) {
        return (
            <PageWrapper title={`WALLET_${accountName?.toUpperCase() || 'LOADING'}`}>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                    {Array.from({ length: 10 }).map((_, i) => (
                        <Card key={i} className="border-border bg-card cyber-chamfer h-24 animate-pulse" />
                    ))}
                </div>
            </PageWrapper>
        )
    }

    if (isError || !data) {
        return (
            <PageWrapper title={`WALLET_${accountName?.toUpperCase() || 'ERROR'}`}>
                <EmptyState message="FAILED_TO_LOAD_WALLET_DETAIL" />
            </PageWrapper>
        )
    }

    const { stats, history } = data

    const columns = [
        {
            header: 'TIME',
            cell: (row: any) => row.exec_time
        },
        { header: 'SYMBOL', accessorKey: 'symbol' as keyof any },
        {
            header: 'SIDE',
            cell: (row: any) => (
                <Badge variant={row.side.toUpperCase() === 'BUY' ? 'cyber-running' : 'cyber-paused'}>
                    {row.side.toUpperCase()}
                </Badge>
            )
        },
        { header: 'PRICE', cell: (row: any) => formatCurrency(row.price) },
        { header: 'QTY', accessorKey: 'qty' as keyof any },
        { header: 'FEE', cell: (row: any) => formatCurrency(row.fee) },
        { header: 'TYPE', accessorKey: 'order_type' as keyof any },
    ]

    const historyTotalPages = Math.max(1, Math.ceil(rawHistory.length / HISTORY_PAGE_SIZE))
    const historyCurrentPage = Math.min(historyPage, historyTotalPages)
    const paginatedHistory = rawHistory.slice(
        (historyCurrentPage - 1) * HISTORY_PAGE_SIZE,
        historyCurrentPage * HISTORY_PAGE_SIZE
    )

    return (
        <PageWrapper title={`WALLET_${accountName.toUpperCase()}`}>

            {/* Top Stat Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                <StatCard title="WALLET_BALANCE" value={stats.wallet_balance} isCurrency colored />
                <StatCard title="UNREALIZED_PNL" value={stats.total_unrealized_pnl} isCurrency colored />
                <StatCard title="TOTAL_REALIZED_PNL" value={stats.total_realized_pnl} isCurrency colored />
                <StatCard title="AVAILABLE_BALANCE" value={stats.available_balance} isCurrency />
                <StatCard title="TOTAL_FEES_PAID" value={stats.total_fees_paid} isCurrency colored />
                <StatCard title="TOTAL_VOLUME" value={stats.total_volume_traded} />
                <StatCard title="WIN_RATE" value={stats.win_rate} isPercent />
                <StatCard title="PROFIT_FACTOR" value={stats.profit_factor} colored />
                <StatCard title="TRADES_PER_DAY" value={stats.trades_per_day} />
                <StatCard title="FILL_RATE" value={stats.fill_rate} isPercent />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Key-Value Grid for Remaining Stats */}
                <Card className="border-border bg-card cyber-chamfer lg:col-span-1">
                    <CardHeader className="border-b border-border/50 py-4">
                        <CardTitle className="text-sm font-mono uppercase tracking-widest text-secondary">ADVANCED_METRICS</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="grid grid-cols-2 gap-x-4 gap-y-0 text-sm">
                            {[
                                ['AVG_WIN', formatCurrency(stats.avg_win)],
                                ['AVG_LOSS', formatCurrency(stats.avg_loss)],
                                ['LARGEST_WIN', formatCurrency(stats.largest_win)],
                                ['LARGEST_LOSS', formatCurrency(stats.largest_loss)],
                                ['EXPECTANCY', formatCurrency(stats.expectancy)],
                                ['MAX_WIN_STREAK', stats.max_win_streak],
                                ['MAX_LOSS_STREAK', stats.max_loss_streak],
                                ['AVG_HOLDING_TIME', `${(stats.avg_holding_time_seconds / 60).toFixed(1)}m`],
                                ['MAKER_FILL_RATIO', formatPercent(stats.maker_fill_ratio)],
                                ['TAKER_FILL_RATIO', formatPercent(stats.taker_fill_ratio)],
                                ['REAL_SLIPPAGE_AVG', stats.real_slippage_avg],
                                ['OPEN_POSITIONS', stats.open_position_count],
                                ['NOTIONAL_EXPOSURE', formatCurrency(stats.total_notional_exposure)],
                            ].map(([k, v], i) => (
                                <div key={k} className={`flex flex-col py-3 px-4 ${i % 2 === 0 ? 'bg-background/20' : ''}`}>
                                    <span className="text-xs text-muted-foreground font-mono tracking-widest">{k}</span>
                                    <span className="font-mono text-foreground">{v}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Charts */}
                <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <PnlChart title="PNL_BY_SYMBOL" data={stats.pnl_by_symbol} />
                    <PnlChart title="PNL_BY_SIDE" data={stats.pnl_by_side} />
                    <PnlChart title="PNL_BY_HOUR" data={stats.pnl_by_hour} />
                    <PnlChart title="PNL_BY_DOW" data={stats.pnl_by_dow} />
                </div>
            </div>

            {/* History Table */}
            <div className="mb-6">
                <h3 className="text-sm font-mono uppercase tracking-widest text-secondary mb-4">EXECUTION_HISTORY</h3>
                <DataTable data={paginatedHistory} columns={columns} />

                {rawHistory.length > HISTORY_PAGE_SIZE && (
                    <div className="flex items-center justify-between mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                        <button
                            onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                            disabled={historyCurrentPage === 1}
                            className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                        >
                            &lt; PREV
                        </button>
                        <span>
                            PAGE {historyCurrentPage} / {historyTotalPages}
                        </span>
                        <button
                            onClick={() => setHistoryPage((p) => Math.min(historyTotalPages, p + 1))}
                            disabled={historyCurrentPage === historyTotalPages}
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