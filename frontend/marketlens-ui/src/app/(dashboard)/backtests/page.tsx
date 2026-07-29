'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/shared/EmptyState'
import { useBacktests, useBacktestOptions, useSubmitBacktest } from '@/hooks/useBacktests'

const BACKTESTS_PAGE_SIZE = 10

export default function BacktestsPage() {
    const router = useRouter()
    const { data: backtests, isLoading: isBacktestsLoading, isError } = useBacktests()
    const { data: optionsData } = useBacktestOptions()
    const submitBacktest = useSubmitBacktest()

    const [strategyName, setStrategyName] = useState('')
    const [symbol, setSymbol] = useState('')
    const [exchange, setExchange] = useState('')
    const [timeframe, setTimeframe] = useState('')
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [initialBalance, setInitialBalance] = useState(10000)
    const [exitOnOppositeSignal, setExitOnOppositeSignal] = useState(true)
    const [positionSizeType, setPositionSizeType] = useState('fixed_percentage')
    const [positionSizeValue, setPositionSizeValue] = useState(10)
    const [commission, setCommission] = useState(0.05)
    const [slippage, setSlippage] = useState(0.02)
    const [allowLong, setAllowLong] = useState(true)
    const [allowShort, setAllowShort] = useState(true)
    const [tpEnabled, setTpEnabled] = useState(false)
    const [tpType, setTpType] = useState('percentage')
    const [tpValue, setTpValue] = useState(2.0)
    const [slEnabled, setSlEnabled] = useState(false)
    const [slType, setSlType] = useState('percentage')
    const [slValue, setSlValue] = useState(1.0)

    const [page, setPage] = useState(1)

    const rawBacktests = useMemo(() => backtests || [], [backtests])

    useEffect(() => {
        setPage(1)
    }, [rawBacktests])

    // Autofill when strategy changes
    useEffect(() => {
        if (strategyName && optionsData) {
            const opt = optionsData.find((o: any) => o.strategy_name === strategyName)
            if (opt) {
                if (opt.symbol) setSymbol(opt.symbol)
                if (opt.exchange) setExchange(opt.exchange)
                if (opt.timehorizon) setTimeframe(opt.timehorizon)
            }
        }
    }, [strategyName, optionsData])

    const handleRunBacktest = (e: React.FormEvent) => {
        e.preventDefault()
        submitBacktest.mutate({
            strategy_name: strategyName,
            symbol,
            exchange,
            timehorizon: timeframe,
            start_date: startDate,
            end_date: endDate,
            initial_balance: initialBalance,
            exit_on_opposite_signal: exitOnOppositeSignal,
            position_size: { type: positionSizeType, value: positionSizeValue },
            commission,
            slippage,
            allow_long: allowLong,
            allow_short: allowShort,
            take_profit: { enabled: tpEnabled, type: tpType, value: tpValue },
            stop_loss: { enabled: slEnabled, type: slType, value: slValue }
        })
    }

    const uniqueStrategies = Array.from(new Set(optionsData?.map((o: any) => o.strategy_name).filter(Boolean))) as string[]
    const uniqueSymbols = Array.from(new Set(optionsData?.map((o: any) => o.symbol).filter(Boolean))) as string[]
    const TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']
    const columns: Column<any>[] = [
        { header: 'STRATEGY', accessorKey: 'strategy_name', className: 'text-accent font-bold' },
        {
            header: 'STATUS',
            cell: (row) => {
                const s = row.status || ''
                let v = 'cyber-pending'
                if (s === 'Completed') v = 'cyber-completed'
                else if (s === 'Running') v = 'cyber-running'
                else if (s === 'Failed') v = 'cyber-error'
                return (
                    <Badge variant={v as any}>
                        {s.toUpperCase()}
                    </Badge>
                )
            }
        },
        { header: 'CREATED AT', cell: (row) => row.created_at ? new Date(row.created_at).toLocaleString() : '-' },
        { header: 'COMPLETED AT', cell: (row) => row.completed_at ? new Date(row.completed_at).toLocaleString() : '-' },
        {
            header: 'SHARPE',
            cell: (row) => {
                try {
                    const res = typeof row.result_summary === 'string' ? JSON.parse(row.result_summary) : row.result_summary
                    return res?.sharpe != null ? Number(res.sharpe).toFixed(2) : '-'
                } catch { return '-' }
            }
        },
        {
            header: 'WIN RATE',
            cell: (row) => {
                try {
                    const res = typeof row.result_summary === 'string' ? JSON.parse(row.result_summary) : row.result_summary
                    return res?.win_rate != null ? `${(Number(res.win_rate)).toFixed(1)}%` : '-'
                } catch { return '-' }
            }
        },
        {
            header: 'FINAL BALANCE',
            cell: (row) => {
                try {
                    const res = typeof row.result_summary === 'string' ? JSON.parse(row.result_summary) : row.result_summary
                    return res?.final_balance != null ? `$${Number(res.final_balance).toLocaleString()}` : '-'
                } catch { return '-' }
            }
        }
    ]

    const totalPages = Math.max(1, Math.ceil(rawBacktests.length / BACKTESTS_PAGE_SIZE))
    const currentPage = Math.min(page, totalPages)
    const paginatedBacktests = rawBacktests.slice(
        (currentPage - 1) * BACKTESTS_PAGE_SIZE,
        currentPage * BACKTESTS_PAGE_SIZE
    )

    return (
        <PageWrapper title="BACKTEST ENGINE">
            <Card className="border-border bg-card cyber-chamfer mb-6">
                <CardHeader className="py-3 border-b border-border bg-background/50">
                    <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                        <span className="animate-pulse">&gt;</span> NEW_BACKTEST_REQUEST
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-6">
                    <form onSubmit={handleRunBacktest} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm font-mono">

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">STRATEGY</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={strategyName}
                                onChange={e => setStrategyName(e.target.value)}
                                required
                            >
                                <option value="">SELECT STRATEGY...</option>
                                {uniqueStrategies.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">SYMBOL</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={symbol}
                                onChange={e => setSymbol(e.target.value)}
                                required
                            >
                                <option value="">SELECT SYMBOL...</option>
                                {uniqueSymbols.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">TIMEFRAME</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={timeframe}
                                onChange={e => setTimeframe(e.target.value)}
                                required
                            >
                                <option value="">SELECT TIMEFRAME...</option>
                                {TIMEFRAMES.map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">EXCHANGE</label>
                            <Input placeholder="e.g. BINANCE" value={exchange} onChange={e => setExchange(e.target.value)} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">START DATE</label>
                            <Input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">END DATE</label>
                            <Input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">INITIAL BALANCE</label>
                            <Input type="number" value={initialBalance} onChange={e => setInitialBalance(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2 justify-center pt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-xs">
                                <input type="checkbox" checked={exitOnOppositeSignal} onChange={e => setExitOnOppositeSignal(e.target.checked)} className="accent-accent" />
                                EXIT ON OPPOSITE SIGNAL
                            </label>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">POS SIZE TYPE</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={positionSizeType}
                                onChange={e => setPositionSizeType(e.target.value)}
                            >
                                <option value="fixed_percentage">FIXED PERCENTAGE</option>
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">POS SIZE VALUE</label>
                            <Input type="number" step="0.1" value={positionSizeValue} onChange={e => setPositionSizeValue(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">COMMISSION (%)</label>
                            <Input type="number" step="0.01" value={commission} onChange={e => setCommission(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">SLIPPAGE (%)</label>
                            <Input type="number" step="0.01" value={slippage} onChange={e => setSlippage(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2 justify-center pt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-xs">
                                <input type="checkbox" checked={allowLong} onChange={e => setAllowLong(e.target.checked)} className="accent-accent" />
                                ALLOW LONG
                            </label>
                        </div>

                        <div className="flex flex-col gap-2 justify-center pt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-xs">
                                <input type="checkbox" checked={allowShort} onChange={e => setAllowShort(e.target.checked)} className="accent-accent" />
                                ALLOW SHORT
                            </label>
                        </div>

                        {/* TP Settings */}
                        <div className="flex flex-col gap-2 border border-border/50 p-2 pt-1 cyber-chamfer-sm bg-background/20 lg:col-span-2">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-accent uppercase tracking-widest">TAKE PROFIT</span>
                                <label className="flex items-center gap-2 cursor-pointer text-xs">
                                    <input type="checkbox" checked={tpEnabled} onChange={e => setTpEnabled(e.target.checked)} className="accent-accent" />
                                    ENABLED
                                </label>
                            </div>
                            <div className="flex gap-2">
                                <select
                                    className="h-9 flex-1 cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none disabled:opacity-50"
                                    value={tpType}
                                    onChange={e => setTpType(e.target.value)}
                                    disabled={!tpEnabled}
                                >
                                    <option value="percentage">PERCENTAGE</option>
                                </select>
                                <Input type="number" step="0.1" value={tpValue} onChange={e => setTpValue(Number(e.target.value))} disabled={!tpEnabled} className="flex-1" />
                            </div>
                        </div>

                        {/* SL Settings */}
                        <div className="flex flex-col gap-2 border border-border/50 p-2 pt-1 cyber-chamfer-sm bg-background/20 lg:col-span-2">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-destructive uppercase tracking-widest">STOP LOSS</span>
                                <label className="flex items-center gap-2 cursor-pointer text-xs">
                                    <input type="checkbox" checked={slEnabled} onChange={e => setSlEnabled(e.target.checked)} className="accent-destructive" />
                                    ENABLED
                                </label>
                            </div>
                            <div className="flex gap-2">
                                <select
                                    className="h-9 flex-1 cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none disabled:opacity-50"
                                    value={slType}
                                    onChange={e => setSlType(e.target.value)}
                                    disabled={!slEnabled}
                                >
                                    <option value="percentage">PERCENTAGE</option>
                                </select>
                                <Input type="number" step="0.1" value={slValue} onChange={e => setSlValue(Number(e.target.value))} disabled={!slEnabled} className="flex-1" />
                            </div>
                        </div>

                        <div className="lg:col-span-4 flex justify-end mt-2 pt-4 border-t border-border/50">
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

            {isError ? (
                <EmptyState message="FAILED_TO_LOAD_BACKTESTS" />
            ) : (
                <>
                    <DataTable
                        data={paginatedBacktests}
                        columns={columns}
                        isLoading={isBacktestsLoading}
                        onRowClick={(row) => row.status === 'Completed' && router.push(`/backtests/${row.request_id}`)}
                        emptyMessage="NO_BACKTESTS_FOUND"
                    />

                    {!isBacktestsLoading && rawBacktests.length > BACKTESTS_PAGE_SIZE && (
                        <div className="flex items-center justify-between mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                            <button
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                            >
                                &lt; PREV
                            </button>
                            <span>
                                PAGE {currentPage} / {totalPages}
                            </span>
                            <button
                                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                            >
                                NEXT &gt;
                            </button>
                        </div>
                    )}
                </>
            )}
        </PageWrapper>
    )
}