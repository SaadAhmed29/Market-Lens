'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useStrategies } from '@/hooks/useStrategies'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/shared/EmptyState'

const STRATEGIES_PAGE_SIZE = 10

type SortKey = 'total_trades' | 'latest_return' | 'sharpe_ratio' | 'win_rate'
type SortDir = 'asc' | 'desc'

const ALL = 'ALL'

function cn_button(base: string) {
    return `${base} disabled:opacity-40 disabled:cursor-not-allowed`
}

export default function StrategiesPage() {
    const router = useRouter()
    const { data: strategies, isLoading, isError } = useStrategies()
    const [search, setSearch] = useState('')
    const [page, setPage] = useState(1)

    // Sort state
    const [sortKey, setSortKey] = useState<SortKey | ''>('')
    const [sortDir, setSortDir] = useState<SortDir>('desc')

    // Filter state
    const [filterExchange, setFilterExchange] = useState(ALL)
    const [filterSymbol, setFilterSymbol] = useState(ALL)
    const [filterTimeframe, setFilterTimeframe] = useState(ALL)
    const [filterStatus, setFilterStatus] = useState(ALL)

    const rawStrategies = useMemo(() => strategies || [], [strategies])

    // Reset to page 1 whenever the underlying data, search, filters, or sort change
    useEffect(() => {
        setPage(1)
    }, [rawStrategies, search, sortKey, sortDir, filterExchange, filterSymbol, filterTimeframe, filterStatus])

    // Build unique option lists from the data itself
    const exchangeOptions: string[] = Array.from(
        new Set(rawStrategies.map((s: any) => String(s.exchange)))
    ) as string[]

    const symbolOptions: string[] = Array.from(
        new Set(rawStrategies.map((s: any) => String(s.symbol)))
    ) as string[]

    const timeframeOptions: string[] = Array.from(
        new Set(rawStrategies.map((s: any) => String(s.timehorizon)))
    ) as string[]

    const statusOptions: string[] = Array.from(
        new Set(rawStrategies.map((s: any) => String(s.status || '').toUpperCase()))
    ) as string[]

    // Apply search, then filters, then sort
    const allStrategies = useMemo(() => {
        let result = rawStrategies

        if (search) {
            result = result.filter((s: any) =>
                (s.strategy_name || '').toLowerCase().includes(search.toLowerCase()) ||
                (s.symbol || '').toLowerCase().includes(search.toLowerCase()) ||
                (s.exchange || '').toLowerCase().includes(search.toLowerCase())
            )
        }

        if (filterExchange !== ALL) result = result.filter((s: any) => s.exchange === filterExchange)
        if (filterSymbol !== ALL) result = result.filter((s: any) => s.symbol === filterSymbol)
        if (filterTimeframe !== ALL) result = result.filter((s: any) => s.timehorizon === filterTimeframe)
        if (filterStatus !== ALL) result = result.filter((s: any) => (s.status || '').toUpperCase() === filterStatus)

        if (sortKey) {
            result = [...result].sort((a: any, b: any) => {
                const diff = (a[sortKey] as number) - (b[sortKey] as number)
                return sortDir === 'asc' ? diff : -diff
            })
        }

        return result
    }, [rawStrategies, search, filterExchange, filterSymbol, filterTimeframe, filterStatus, sortKey, sortDir])

    const columns: Column<any>[] = [
        { header: 'NAME', accessorKey: 'strategy_name', className: 'text-accent text-center' },
        { header: 'SYMBOL', accessorKey: 'symbol', className: 'text-center' },
        { header: 'EXCHANGE', accessorKey: 'exchange', className: 'text-center' },
        { header: 'TIMEHORIZON', accessorKey: 'timehorizon', className: 'text-center' },
        { header: 'TRADES', accessorKey: 'total_trades', className: 'text-center' },
        {
            header: 'AVG RETURN',
            cell: (row) => {
                const ret = row.latest_return || 0;
                return (
                    <span className={ret > 0 ? 'text-accent' : ret < 0 ? 'text-destructive' : ''}>
                        {ret > 0 ? '+' : ''}{(ret * 100).toFixed(2)}%
                    </span>
                )
            },
            className: 'text-center'
        },
        {
            header: 'SHARPE',
            cell: (row) => (
                <span className={row.sharpe_ratio > 0 ? 'text-accent' : row.sharpe_ratio < 0 ? 'text-destructive' : 'text-foreground'}>
                    {row.sharpe_ratio > 0 ? '+' : ''}{(row.sharpe_ratio || 0).toFixed(4)}
                </span>
            ),
            className: 'text-center'
        },
        {
            header: 'WIN RATE',
            cell: (row) => `${((row.win_rate || 0) * 100).toFixed(2)}%`,
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
        "bg-card border border-border cyber-chamfer font-mono text-[12px] uppercase tracking-widest text-muted-foreground px-2 py-0.5 hover:border-accent/50 hover:text-foreground focus:outline-none focus:border-accent/50 transition-colors"

    if (isError) {
        return (
            <PageWrapper title="STRATEGY DIRECTORY">
                <div className="mt-4">
                    <EmptyState message="ERROR_LOADING_STRATEGIES" />
                </div>
            </PageWrapper>
        )
    }

    return (
        <PageWrapper title="STRATEGY DIRECTORY">
            <div className="flex flex-col sm:flex-row gap-6 items-center justify-between bg-card p-4 border border-border cyber-chamfer">
                <div className="w-full sm:w-108">
                    <Input
                        placeholder="SEARCH BY NAME, SYMBOL, OR EXCHANGE..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                {/* Filter / Sort Bar */}
                {!isLoading && rawStrategies.length > 0 && (

                    <div className="flex flex-wrap items-center gap-4 mt-4">
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
                            <option value="total_trades">TRADES</option>
                            <option value="latest_return">AVG_RETURN</option>
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

                        {(filterExchange !== ALL || filterSymbol !== ALL || filterTimeframe !== ALL || filterStatus !== ALL || sortKey || search) && (
                            <button
                                onClick={() => {
                                    setSearch('')
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
            </div>

            {isLoading ? (
                <div className="flex flex-col gap-2 mt-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                </div>
            ) : (
                <>
                    <div className="mt-4">
                        <DataTable
                            data={paginatedStrategies}
                            columns={columns}
                            isLoading={isLoading}
                            onRowClick={(row) => router.push(`/strategies/${row.strategy_name}`)}
                            emptyMessage={rawStrategies.length > 0 ? "NO_MATCHING_STRATEGIES" : "NO_STRATEGIES_FOUND"}
                        />
                    </div>

                    {allStrategies.length > STRATEGIES_PAGE_SIZE && (
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