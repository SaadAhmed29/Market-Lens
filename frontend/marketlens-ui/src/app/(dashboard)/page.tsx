'use client'

import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { StatCard } from '@/components/shared/StatCard'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { useDashboardStats } from '@/hooks/useDashboard'
import { useStrategies } from '@/hooks/useStrategies'
import { Strategy } from '@/types/strategy'

export default function DashboardPage() {
    const router = useRouter()
    const { data: stats, isLoading: statsLoading } = useDashboardStats()
    const { data: strategies, isLoading: strategiesLoading } = useStrategies()

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

    return (
        <PageWrapper title="DASHBOARD_OVERVIEW">
            {/* Top Stat Strip */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <StatCard 
                    label="TOTAL_STRATEGIES" 
                    value={statsLoading ? '...' : stats?.totalStrategies || 0} 
                />
                <StatCard 
                    label="ACTIVE_STRATEGIES" 
                    value={statsLoading ? '...' : stats?.activeStrategies || 0} 
                    className="border-accent/50"
                />
                <StatCard 
                    label="RUNNING_EXECUTIONS" 
                    value={statsLoading ? '...' : stats?.runningExecutions || 0} 
                />
                <StatCard 
                    label="ML_MODELS" 
                    value={statsLoading ? '...' : stats?.trainedMlModels || 0} 
                />
                <StatCard 
                    label="TOTAL_BACKTESTS" 
                    value={statsLoading ? '...' : stats?.totalBacktests || 0} 
                />
                <StatCard 
                    label="CONNECTED_ACCOUNTS" 
                    value={statsLoading ? '...' : stats?.connectedAccounts || 0} 
                />
                <StatCard 
                    label="SIMULATIONS" 
                    value={statsLoading ? '...' : stats?.runningSimulations || 0} 
                />
                <StatCard 
                    label="PORTFOLIO_VALUE" 
                    value={statsLoading ? '...' : `$${stats?.overallPortfolioValue.toLocaleString() || 0}`} 
                />
                <StatCard 
                    label="TODAY_PNL" 
                    value={statsLoading ? '...' : `$${stats?.todayPnl.toLocaleString() || 0}`} 
                    isUp={stats?.todayPnl && stats.todayPnl >= 0 ? true : false}
                    change={stats?.todayPnl ? `${(stats.todayPnl / (stats.overallPortfolioValue - stats.todayPnl) * 100).toFixed(2)}%` : '0.00%'}
                />
                <StatCard 
                    label="TOTAL_RETURN" 
                    value={statsLoading ? '...' : `${stats?.totalReturn || 0}%`} 
                    isUp={stats?.totalReturn && stats.totalReturn >= 0 ? true : false}
                />
            </div>

            {/* Strategy Table */}
            <div className="mt-8">
                <div className="flex items-center gap-2 mb-4">
                    <span className="text-accent">&gt;</span>
                    <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">ACTIVE_STRATEGIES_OVERVIEW</h2>
                </div>
                <DataTable 
                    data={strategies || []} 
                    columns={columns} 
                    isLoading={strategiesLoading}
                    onRowClick={(row) => router.push(`/strategies/${row.id}`)}
                />
            </div>
        </PageWrapper>
    )
}
