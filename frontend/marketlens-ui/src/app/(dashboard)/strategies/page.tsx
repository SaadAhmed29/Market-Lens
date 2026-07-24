'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useStrategies } from '@/hooks/useStrategies'
import { Strategy } from '@/types/strategy'

export default function StrategiesPage() {
    const router = useRouter()
    const { data: strategies, isLoading } = useStrategies()
    const [search, setSearch] = useState('')

    const columns: Column<Strategy>[] = [
        { header: 'NAME', accessorKey: 'name', className: 'text-accent' },
        { header: 'SYMBOL', accessorKey: 'symbol' },
        { header: 'EXCHANGE', accessorKey: 'exchange' },
        { header: 'TIMEFRAME', accessorKey: 'timeframe' },
        { 
            header: 'STATUS', 
            cell: (row) => (
                <Badge variant={
                    row.status === 'ACTIVE' ? 'cyber-running' : 
                    row.status === 'PAUSED' ? 'cyber-paused' : 'cyber-stopped'
                }>
                    {row.status}
                </Badge>
            )
        },
        { 
            header: 'LATEST_RETURN', 
            cell: (row) => (
                <span className={row.latestReturn > 0 ? 'text-accent' : 'text-destructive'}>
                    {row.latestReturn > 0 ? '+' : ''}{row.latestReturn}%
                </span>
            ),
            className: 'text-right'
        },
        { header: 'SHARPE', accessorKey: 'sharpeRatio', className: 'text-right' },
        { 
            header: 'WIN_RATE', 
            cell: (row) => `${row.winRate}%`,
            className: 'text-right' 
        },
    ]

    const filteredStrategies = strategies?.filter(s => 
        s.name.toLowerCase().includes(search.toLowerCase()) || 
        s.symbol.toLowerCase().includes(search.toLowerCase()) ||
        s.exchange.toLowerCase().includes(search.toLowerCase())
    ) || []

    return (
        <PageWrapper 
            title="STRATEGY_DIRECTORY"
            actions={
                <Button variant="cyber-glitch">DEPLOY_NEW_STRATEGY</Button>
            }
        >
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

            <DataTable 
                data={filteredStrategies} 
                columns={columns} 
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/strategies/${row.id}`)}
                emptyMessage="NO_STRATEGIES_MATCH_CRITERIA"
            />
        </PageWrapper>
    )
}
