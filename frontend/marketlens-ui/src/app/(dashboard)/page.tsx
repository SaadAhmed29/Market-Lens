'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { StatCard } from '@/components/shared/StatCard'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { useDashboard, DashboardStrategy } from '@/hooks/useDashboard'

const STRATEGIES_PAGE_SIZE = 10

type SortKey = 'total_trades' | 'latest_return' | 'sharpe_ratio' | 'win_rate'
type SortDir = 'asc' | 'desc'

const ALL = 'ALL'

export default function DashboardPage() {
    const router = useRouter()
    const { data: dashboard, isLoading, isError } = useDashboard()
    const [page, setPage] = useState(1)

    // Sort state
    const [sortKey, setSortKey] = useState<SortKey | ''>('')
    const [sortDir, setSortDir] = useState<SortDir>('desc')

    // Filter state
    const [filterExchange, setFilterExchange] = useState(ALL)
    const [filterSymbol, setFilterSymbol] = useState(ALL)
    const [filterTimeframe, setFilterTimeframe] = useState(ALL)
    const [filterStatus, setFilterStatus] = useState(ALL)

    const rawStrategies = useMemo(() => dashboard?.strategies || [], [dashboard?.strategies])

    // Reset to page 1 whenever the underlying data, filters, or sort change
    useEffect(() => {
        setPage(1)
    }, [rawStrategies, sortKey, sortDir, filterExchange, filterSymbol, filterTimeframe, filterStatus])

    // Build unique option lists from the data itself
    const exchangeOptions = useMemo(
        () => Array.from(new Set(rawStrategies.map((s) => s.exchange))).sort(),
        [rawStrategies]
    )
    const symbolOptions = useMemo(
        () => Array.from(new Set(rawStrategies.map((s) => s.symbol))).sort(),
        [rawStrategies]
    )
    const timeframeOptions = useMemo(
        () => Array.from(new Set(rawStrategies.map((s) => s.timehorizon))).sort(),
        [rawStrategies]
    )
    const statusOptions = useMemo(
        () => Array.from(new Set(rawStrategies.map((s) => s.status.toUpperCase()))).sort(),
        [rawStrategies]
    )

    // Apply filters, then sort
    const allStrategies = useMemo(() => {
        let result = rawStrategies

        if (filterExchange !== ALL) result = result.filter((s) => s.exchange === filterExchange)
        if (filterSymbol !== ALL) result = result.filter((s) => s.symbol === filterSymbol)
        if (filterTimeframe !== ALL) result = result.filter((s) => s.timehorizon === filterTimeframe)
        if (filterStatus !== ALL) result = result.filter((s) => s.status.toUpperCase() === filterStatus)

        if (sortKey) {
            result = [...result].sort((a, b) => {
                const diff = (a[sortKey] as number) - (b[sortKey] as number)
                return sortDir === 'asc' ? diff : -diff
            })
        }

        return result
    }, [rawStrategies, filterExchange, filterSymbol, filterTimeframe, filterStatus, sortKey, sortDir])

    if (isError) {
        return (
            <PageWrapper title="DASHBOARD_OVERVIEW">
                <EmptyState message="ERROR_FETCHING_DASHBOARD_DATA" />
            </PageWrapper>
        )
    }

    const columns: Column<DashboardStrategy>[] = [
        { header: 'NAME', accessorKey: 'strategy_name', className: 'text-accent text-center' },
        { header: 'SYMBOL', accessorKey: 'symbol', className: 'text-center' },
        { header: 'EXCHANGE', accessorKey: 'exchange', className: 'text-center' },
        { header: 'TIMEFRAME', accessorKey: 'timehorizon', className: 'text-center' },
        { header: 'TOTAL_TRADES', accessorKey: 'total_trades', className: 'text-center' },
        {
            header: 'AVERAGE_RETURN',
            cell: (row) => (
                <span className={row.latest_return > 0 ? 'text-accent' : row.latest_return < 0 ? 'text-destructive' : 'text-foreground'}>
                    {row.latest_return > 0 ? '+' : ''}{row.latest_return.toFixed(5)}%
                </span>
            ),
            className: 'text-center'
        },
        {
            header: 'SHARPE',
            cell: (row) => row.sharpe_ratio.toFixed(4),
            className: 'text-center'
        },
        {
            header: 'WIN_RATE',
            cell: (row) => `${(row.win_rate * 100).toFixed(1)}%`,
            className: 'text-center'
        },
        {
            header: 'STATUS',
            cell: (row) => (
                <Badge variant={
                    row.status.toUpperCase() === 'OPEN' || row.status.toUpperCase() === 'ACTIVE' ? 'cyber-running' :
                        row.status.toUpperCase() === 'PAUSED' ? 'cyber-paused' : 'cyber-stopped'
                }>
                    {row.status.toUpperCase()}
                </Badge>
            ),
            className: 'text-center'
        },
    ]

    const totalPages = Math.max(1, Math.ceil(allStrategies.length / STRATEGIES_PAGE_SIZE))
    const currentPage = Math.min(page, totalPages)
    const paginatedStrategies = allStrategies.slice(
        (currentPage - 1) * STRATEGIES_PAGE_SIZE,
        currentPage * STRATEGIES_PAGE_SIZE
    )

    const selectClass =
        "bg-card border border-border cyber-chamfer font-mono text-xs uppercase tracking-widest text-muted-foreground px-3 py-1.5 hover:border-accent/50 hover:text-foreground focus:outline-none focus:border-accent/50 transition-colors"

    return (
        <PageWrapper title="DASHBOARD_OVERVIEW">
            {/* Top Stat Strip */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {isLoading ? (
                    Array.from({ length: 8 }).map((_, i) => (
                        <Skeleton key={i} className="h-24 w-full bg-card cyber-chamfer border border-border" />
                    ))
                ) : dashboard && (
                    <>
                        <StatCard label="TOTAL_STRATEGIES" value={dashboard.total_strategies} />
                        <StatCard label="ACTIVE_STRATEGIES" value={dashboard.active_strategies} className="border-accent/50" />
                        <StatCard label="RUNNING_EXECUTIONS" value={dashboard.running_executions} />
                        <StatCard label="TRADES_EXECUTED" value={dashboard.total_trades_executed} />
                        <StatCard label="STRATEGIES_SIMULATED" value={dashboard.running_simulations} />
                        <StatCard label="TRADES_SIMULATED" value={dashboard.total_trades_simulated} />
                        <StatCard label="CONNECTED_ACCOUNTS" value={dashboard.connected_accounts} />
                        <StatCard label="ML_MODELS" value={dashboard.trained_ml_models} />
                        <StatCard label="TOTAL_BACKTESTS" value={dashboard.total_backtests} />
                        <StatCard
                            label="TOTAL_RETURN"
                            value={`$${dashboard.total_return.toLocaleString()}`}
                            isUp={dashboard.total_return >= 0}
                        />
                    </>
                )}
            </div>

            {/* Strategy Table */}
            <div className="mt-8">
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-accent">&gt;</span>
                    <h2 className="text-2xl sm:text-3xl font-heading font-bold uppercase tracking-wider text-foreground cyber-glitch">STRATEGIES_OVERVIEW</h2>
                </div>

                {/* Filter / Sort Bar */}
                {!isLoading && rawStrategies.length > 0 && (
                    <div className="flex flex-wrap items-center justify-center gap-3 mb-4">
                        <select
                            className={selectClass}
                            value={filterExchange}
                            onChange={(e) => setFilterExchange(e.target.value)}
                        >
                            <option value={ALL}>ALL_EXCHANGES</option>
                            {exchangeOptions.map((ex) => (
                                <option key={ex} value={ex}>{ex}</option>
                            ))}
                        </select>

                        <select
                            className={selectClass}
                            value={filterSymbol}
                            onChange={(e) => setFilterSymbol(e.target.value)}
                        >
                            <option value={ALL}>ALL_SYMBOLS</option>
                            {symbolOptions.map((sym) => (
                                <option key={sym} value={sym}>{sym}</option>
                            ))}
                        </select>

                        <select
                            className={selectClass}
                            value={filterTimeframe}
                            onChange={(e) => setFilterTimeframe(e.target.value)}
                        >
                            <option value={ALL}>ALL_TIMEFRAMES</option>
                            {timeframeOptions.map((tf) => (
                                <option key={tf} value={tf}>{tf}</option>
                            ))}
                        </select>

                        <select
                            className={selectClass}
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                        >
                            <option value={ALL}>ALL_STATUSES</option>
                            {statusOptions.map((st) => (
                                <option key={st} value={st}>{st}</option>
                            ))}
                        </select>

                        <div className="w-px h-5 bg-border mx-1" />

                        <select
                            className={selectClass}
                            value={sortKey}
                            onChange={(e) => setSortKey(e.target.value as SortKey | '')}
                        >
                            <option value="">NO_SORT</option>
                            <option value="total_trades">TOTAL_TRADES</option>
                            <option value="latest_return">AVERAGE_RETURN</option>
                            <option value="sharpe_ratio">SHARPE</option>
                            <option value="win_rate">WIN_RATE</option>
                        </select>

                        <button
                            onClick={() => setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))}
                            disabled={!sortKey}
                            className={cn_button(selectClass)}
                        >
                            {sortDir === 'asc' ? 'ASC ▲' : 'DESC ▼'}
                        </button>

                        {(filterExchange !== ALL || filterSymbol !== ALL || filterTimeframe !== ALL || filterStatus !== ALL || sortKey) && (
                            <button
                                onClick={() => {
                                    setFilterExchange(ALL)
                                    setFilterSymbol(ALL)
                                    setFilterTimeframe(ALL)
                                    setFilterStatus(ALL)
                                    setSortKey('')
                                    setSortDir('desc')
                                }}
                                className="font-mono text-xs uppercase tracking-widest text-muted-foreground hover:text-accent transition-colors px-3 py-1.5"
                            >
                                RESET
                            </button>
                        )}
                    </div>
                )}

                <DataTable
                    data={paginatedStrategies}
                    columns={columns}
                    isLoading={isLoading}
                    onRowClick={(row) => router.push(`/strategies/${row.strategy_name}`)}
                    emptyMessage={rawStrategies.length > 0 ? "NO_MATCHING_STRATEGIES" : "NO_DATA_FOUND"}
                />

                {!isLoading && allStrategies.length > STRATEGIES_PAGE_SIZE && (
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
            </div>
        </PageWrapper>
    )
}

function cn_button(base: string) {
    return `${base} disabled:opacity-40 disabled:cursor-not-allowed`
}