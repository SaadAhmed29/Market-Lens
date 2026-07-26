'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useStrategies } from '@/hooks/useStrategies'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/shared/EmptyState'

export default function StrategiesPage() {
    const router = useRouter()
    const { data: strategies, isLoading, isError } = useStrategies()
    const [search, setSearch] = useState('')

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

    const filteredStrategies = strategies?.filter((s: any) =>
        (s.strategy_name || '').toLowerCase().includes(search.toLowerCase()) ||
        (s.symbol || '').toLowerCase().includes(search.toLowerCase()) ||
        (s.exchange || '').toLowerCase().includes(search.toLowerCase())
    ) || []

    return (
        <PageWrapper title="STRATEGY DIRECTORY">
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-card p-4 border border-border cyber-chamfer">
                <div className="w-full sm:w-96">
                    <Input
                        placeholder="SEARCH BY NAME, SYMBOL, OR EXCHANGE..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="cyber-outline">FILTER: ACTIVE</Button>
                    <Button variant="cyber-outline">FILTER: ALL</Button>
                </div>
            </div>

            {isLoading ? (
                <div className="flex flex-col gap-2 mt-4">
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                </div>
            ) : isError ? (
                <div className="mt-4">
                    <EmptyState
                        message="ERROR_LOADING_STRATEGIES"
                    />
                </div>
            ) : (
                <DataTable
                    data={filteredStrategies}
                    columns={columns}
                    isLoading={isLoading}
                    onRowClick={(row) => router.push(`/strategies/${row.strategy_name}`)}
                    emptyMessage="NO_STRATEGIES_MATCH_CRITERIA"
                />
            )}
        </PageWrapper>
    )
}
