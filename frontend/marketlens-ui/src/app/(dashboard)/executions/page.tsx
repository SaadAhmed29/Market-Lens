'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useExecutions } from '@/hooks/useExecutions'
import { EmptyState } from '@/components/shared/EmptyState'

type ExecutionRow = {
    strategy: string
    symbol: string
    exchange: string
    wallet: string
    status: string
    position: string
    avg_return: number
    last_trade_entry: string
}

const EXECUTIONS_PAGE_SIZE = 10

export default function ExecutionsPage() {
    const router = useRouter()
    const { data: executions, isLoading, isError } = useExecutions()

    const [executionsPage, setExecutionsPage] = useState(1)

    const rawExecutions = useMemo(() => executions || [], [executions])

    useEffect(() => {
        setExecutionsPage(1)
    }, [rawExecutions])

    if (isError) {
        return (
            <PageWrapper title="LIVE_EXECUTIONS">
                <EmptyState message="ERROR: FAILED_TO_LOAD_EXECUTIONS_DATA" />
            </PageWrapper>
        )
    }

    const columns: Column<ExecutionRow>[] = [
        { header: 'STRATEGY', accessorKey: 'strategy', className: 'text-accent' },
        { header: 'SYMBOL', accessorKey: 'symbol', className: 'text-center' },
        { header: 'EXCHANGE', accessorKey: 'exchange', className: 'text-center' },
        { header: 'WALLET', accessorKey: 'wallet', className: 'text-center' },
        {
            header: 'POSITION',
            cell: (row) => (
                <Badge variant={
                    row.position?.toUpperCase() === 'LONG' ? 'cyber-active' :
                        row.position?.toUpperCase() === 'SHORT' ? 'destructive' : 'outline'
                }>
                    {row.position?.toUpperCase() || 'NONE'}
                </Badge>
            ),
            className: 'text-center'
        },
        {
            header: 'AVG_RETURN',
            cell: (row) => {
                const ret = Number(row.avg_return || 0)
                return (
                    <span className={ret > 0 ? 'text-accent' : ret < 0 ? 'text-destructive' : 'text-muted-foreground'}>
                        {ret > 0 ? '+' : ''}{(ret * 100).toFixed(2)}%
                    </span>
                )
            },
            className: 'text-center'
        },
        {
            header: 'LAST_TRADE_ENTRY',
            cell: (row) => row.last_trade_entry && row.last_trade_entry !== "N/A" ? new Date(row.last_trade_entry).toLocaleString() : 'N/A',
            className: 'text-right'
        },
        {
            header: 'STATUS',
            cell: (row) => (
                <Badge variant={
                    row.status?.toUpperCase() === 'OPEN' ? 'cyber-active' : 'outline'
                }>
                    {row.status?.toUpperCase() || 'UNKNOWN'}
                </Badge>
            )
        },
    ]

    const executionsTotalPages = Math.max(1, Math.ceil(rawExecutions.length / EXECUTIONS_PAGE_SIZE))
    const executionsCurrentPage = Math.min(executionsPage, executionsTotalPages)
    const paginatedExecutions = rawExecutions.slice(
        (executionsCurrentPage - 1) * EXECUTIONS_PAGE_SIZE,
        executionsCurrentPage * EXECUTIONS_PAGE_SIZE
    )

    return (
        <PageWrapper
            title="LIVE EXECUTIONS"
        >
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">ACTIVE TRADING STRATEGIES</h2>
            </div>
            <DataTable
                data={paginatedExecutions}
                columns={columns}
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/executions/${row.strategy}`)}
                emptyMessage="NO_LIVE_EXECUTIONS_FOUND"
            />

            {rawExecutions.length > EXECUTIONS_PAGE_SIZE && (
                <div className="flex items-center justify-between mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                    <button
                        onClick={() => setExecutionsPage((p) => Math.max(1, p - 1))}
                        disabled={executionsCurrentPage === 1}
                        className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                    >
                        &lt; PREV
                    </button>
                    <span>
                        PAGE {executionsCurrentPage} / {executionsTotalPages}
                    </span>
                    <button
                        onClick={() => setExecutionsPage((p) => Math.min(executionsTotalPages, p + 1))}
                        disabled={executionsCurrentPage === executionsTotalPages}
                        className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                    >
                        NEXT &gt;
                    </button>
                </div>
            )}
        </PageWrapper>
    )
}