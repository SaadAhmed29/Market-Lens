'use client'

import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useExecutions } from '@/hooks/useExecutions'
import { Execution } from '@/types/execution'

export default function ExecutionsPage() {
    const router = useRouter()
    const { data: executions, isLoading } = useExecutions()

    const columns: Column<Execution>[] = [
        { header: 'STRATEGY', accessorKey: 'strategyName', className: 'text-accent' },
        { header: 'SYMBOL', accessorKey: 'symbol' },
        { header: 'WALLET', accessorKey: 'walletName' },
        { 
            header: 'STATUS', 
            cell: (row) => (
                <Badge variant={
                    row.status === 'RUNNING' ? 'cyber-running' : 
                    row.status === 'PAUSED' ? 'cyber-paused' : 'cyber-error'
                }>
                    {row.status}
                </Badge>
            )
        },
        { 
            header: 'POSITION', 
            cell: (row) => (
                <Badge variant={
                    row.currentPosition === 'LONG' ? 'cyber-active' : 
                    row.currentPosition === 'SHORT' ? 'destructive' : 'outline'
                }>
                    {row.currentPosition}
                </Badge>
            )
        },
        { 
            header: 'CURRENT_PNL', 
            cell: (row) => (
                <span className={row.currentPnl > 0 ? 'text-accent' : row.currentPnl < 0 ? 'text-destructive' : 'text-muted-foreground'}>
                    {row.currentPnl > 0 ? '+' : ''}${row.currentPnl.toLocaleString()}
                </span>
            ),
            className: 'text-right'
        },
        { 
            header: 'DAILY_RET', 
            cell: (row) => (
                <span className={row.dailyReturn > 0 ? 'text-accent' : row.dailyReturn < 0 ? 'text-destructive' : 'text-muted-foreground'}>
                    {row.dailyReturn > 0 ? '+' : ''}{row.dailyReturn}%
                </span>
            ),
            className: 'text-right'
        },
        { header: 'LAST_EXECUTION', cell: (row) => new Date(row.lastExecutionTime).toLocaleString(), className: 'text-right' },
    ]

    return (
        <PageWrapper 
            title="LIVE_EXECUTIONS"
            actions={
                <Button variant="cyber-glitch">LAUNCH_STRATEGY</Button>
            }
        >
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">ACTIVE_TRADING_BOTS</h2>
            </div>
            <DataTable 
                data={executions || []} 
                columns={columns} 
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/executions/${row.id}`)}
                emptyMessage="NO_LIVE_EXECUTIONS_FOUND"
            />
        </PageWrapper>
    )
}
