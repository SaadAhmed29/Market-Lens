'use client'

import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { StatCard } from '@/components/shared/StatCard'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/shared/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { useDashboard, DashboardStrategy } from '@/hooks/useDashboard'

export default function DashboardPage() {
    const router = useRouter()
    const { data: dashboard, isLoading, isError } = useDashboard()

    if (isError) {
        return (
            <PageWrapper title="DASHBOARD_OVERVIEW">
                <EmptyState message="ERROR_FETCHING_DASHBOARD_DATA" />
            </PageWrapper>
        )
    }

    const columns: Column<DashboardStrategy>[] = [
        { header: 'NAME', accessorKey: 'strategy_name', className: 'text-accent' },
        { header: 'SYMBOL', accessorKey: 'symbol' },
        { header: 'EXCHANGE', accessorKey: 'exchange' },
        { header: 'TIMEFRAME', accessorKey: 'timehorizon', className: 'text-center' },
        { header: 'TOTAL_TRADES', accessorKey: 'total_trades', className: 'text-center' },
        {
            header: 'STATUS',
            cell: (row) => (
                <Badge variant={
                    row.status.toUpperCase() === 'OPEN' || row.status.toUpperCase() === 'ACTIVE' ? 'cyber-running' :
                        row.status.toUpperCase() === 'PAUSED' ? 'cyber-paused' : 'cyber-stopped'
                }>
                    {row.status.toUpperCase()}
                </Badge>
            )
        },
        {
            header: 'LATEST_RETURN',
            cell: (row) => (
                <span className={row.latest_return > 0 ? 'text-accent' : row.latest_return < 0 ? 'text-destructive' : 'text-foreground'}>
                    {row.latest_return > 0 ? '+' : ''}{row.latest_return.toFixed(5)}%
                </span>
            ),
            className: 'text-center'
        },
        {
            header: 'SHARPE',
            cell: (row) => row.sharpe_ratio.toFixed(2),
            className: 'text-right'
        },
        {
            header: 'WIN_RATE',
            cell: (row) => `${(row.win_rate * 100).toFixed(1)}%`,
            className: 'text-right'
        },
    ]

    return (
        <PageWrapper title="DASHBOARD_OVERVIEW">
            {/* Top Stat Strip */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {isLoading ? (
                    Array.from({ length: 9 }).map((_, i) => (
                        <Skeleton key={i} className="h-24 w-full bg-card cyber-chamfer border border-border" />
                    ))
                ) : dashboard && (
                    <>
                        <StatCard
                            label="TOTAL_STRATEGIES"
                            value={dashboard.total_strategies}
                        />
                        <StatCard
                            label="ACTIVE_STRATEGIES"
                            value={dashboard.active_strategies}
                            className="border-accent/50"
                        />
                        <StatCard
                            label="RUNNING_EXECUTIONS"
                            value={dashboard.running_executions}
                        />
                        <StatCard
                            label="SIMULATIONS"
                            value={dashboard.running_simulations}
                        />
                        <StatCard
                            label="CONNECTED_ACCOUNTS"
                            value={dashboard.connected_accounts}
                        />
                        <StatCard
                            label="ML_MODELS"
                            value={dashboard.trained_ml_models}
                        />
                        <StatCard
                            label="TOTAL_BACKTESTS"
                            value={dashboard.total_backtests}
                        />
                        <StatCard
                            label="PORTFOLIO_VALUE"
                            value={`$${dashboard.portfolio_value.toLocaleString()}`}
                        />
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
                    <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">ACTIVE_STRATEGIES_OVERVIEW</h2>
                </div>
                <DataTable
                    data={dashboard?.strategies || []}
                    columns={columns}
                    isLoading={isLoading}
                    onRowClick={(row) => router.push(`/strategies/${row.strategy_name}`)}
                />
            </div>
        </PageWrapper>
    )
}
