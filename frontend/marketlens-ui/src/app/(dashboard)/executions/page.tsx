'use client'

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

export default function ExecutionsPage() {
    const router = useRouter()
    const { data: executions, isLoading, isError } = useExecutions()

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

    return (
        <PageWrapper
            title="LIVE EXECUTIONS"
        >
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">ACTIVE TRADING STRATEGIES</h2>
            </div>
            <DataTable
                data={executions || []}
                columns={columns}
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/executions/${row.strategy}`)}
                emptyMessage="NO_LIVE_EXECUTIONS_FOUND"
            />
        </PageWrapper>
    )
}
