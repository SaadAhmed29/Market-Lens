'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DataTable, Column } from '@/components/shared/DataTable'
import { EquityCurve } from '@/components/charts/EquityCurve'
import { DrawdownChart } from '@/components/charts/DrawdownChart'
import { ReturnsHeatmap } from '@/components/charts/ReturnsHeatmap'
import { PieChart } from '@/components/charts/PieChart'
import { useStrategyDetail } from '@/hooks/useStrategies'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/shared/EmptyState'


type MetricFormat = 'percent' | 'ratio' | 'currency' | 'integer' | 'raw'

interface MetricConfig {
    key: string
    label: string
    format: MetricFormat
}

const METRICS: MetricConfig[] = [
    { key: 'sharpe_ratio', label: 'SHARPE', format: 'ratio' },
    { key: 'sortino_ratio', label: 'SORTINO', format: 'ratio' },
    { key: 'calmar_ratio', label: 'CALMAR', format: 'ratio' },
    { key: 'max_drawdown', label: 'MAX DD', format: 'percent' },
    { key: 'cagr', label: 'CAGR', format: 'percent' },
    { key: 'volatility', label: 'VOLATILITY', format: 'percent' },
    { key: 'win_rate', label: 'WIN RATE', format: 'percent' },
    { key: 'profit_factor', label: 'PROFIT FACTOR', format: 'ratio' },
    { key: 'average_win', label: 'AVG WIN', format: 'percent' },
    { key: 'average_loss', label: 'AVG LOSS', format: 'percent' },
    { key: 'best_day', label: 'BEST DAY', format: 'percent' },
    { key: 'worst_day', label: 'WORST DAY', format: 'percent' },
    { key: 'var', label: 'VAR', format: 'percent' },
    { key: 'cvar', label: 'CVAR', format: 'percent' },
    { key: 'skewness', label: 'SKEWNESS', format: 'raw' },
    { key: 'kurtosis', label: 'KURTOSIS', format: 'raw' },
    { key: 'recovery_factor', label: 'RECOVERY FACTOR', format: 'ratio' },
    { key: 'ulcer_index', label: 'ULCER INDEX', format: 'raw' },
    { key: 'avg_return', label: 'AVG RET', format: 'percent' },
    { key: 'common_sense_ratio', label: 'COMMON SENSE RATIO', format: 'ratio' },
    { key: 'comp', label: 'COMP', format: 'percent' },
    { key: 'conditional_value_at_risk', label: 'CONDITIONAL VAR', format: 'percent' },
    { key: 'consecutive_losses', label: 'CONSEC LOSSES', format: 'integer' },
    { key: 'consecutive_wins', label: 'CONSEC WINS', format: 'integer' },
    { key: 'cpc_index', label: 'CPC INDEX', format: 'ratio' },
    { key: 'expected_return', label: 'EXPECTED RETURN', format: 'percent' },
    { key: 'expected_shortfall', label: 'EXPECTED SHORTFALL', format: 'percent' },
    { key: 'exposure', label: 'EXPOSURE', format: 'percent' },
    { key: 'gain_to_pain_ratio', label: 'GAIN TO PAIN', format: 'ratio' },
    { key: 'geometric_mean', label: 'GEOMETRIC MEAN', format: 'percent' },
    { key: 'ghpr', label: 'GHPR', format: 'percent' },
    { key: 'outlier_loss_ratio', label: 'OUTLIER LOSS RATIO', format: 'ratio' },
    { key: 'outlier_win_ratio', label: 'OUTLIER WIN RATIO', format: 'ratio' },
    { key: 'payoff_ratio', label: 'PAYOFF RATIO', format: 'ratio' },
    { key: 'profit_ratio', label: 'PROFIT RATIO', format: 'ratio' },
    { key: 'rar', label: 'RAR', format: 'percent' },
    { key: 'risk_of_ruin', label: 'RISK OF RUIN', format: 'percent' },
    { key: 'ror', label: 'ROR', format: 'percent' },
    { key: 'tail_ratio', label: 'TAIL RATIO', format: 'ratio' },
    { key: 'ulcer_performance_index', label: 'ULCER PERF INDEX', format: 'ratio' },
    { key: 'upi', label: 'UPI', format: 'ratio' },
    { key: 'win_loss_ratio', label: 'WIN-LOSS RATIO', format: 'ratio' },
    { key: 'kelly_criterion', label: 'KELLY CRITERION', format: 'percent' },
    { key: 'risk_return_ratio', label: 'RISK-RETURN RATIO', format: 'ratio' },
]

function formatMetric(value: number | undefined, format: MetricFormat): string {
    if (value === undefined || value === null || Number.isNaN(value)) return 'N/A'

    switch (format) {
        case 'percent':
            return `${value > 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
        case 'currency':
            return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        case 'integer':
            return value.toLocaleString()
        case 'ratio':
        case 'raw':
        default:
            return `${value > 0 ? '+' : ''}${value.toFixed(4)}`
    }
}


function buildHeatmapData(monthlyReturns: { month: string; return: number }[]) {
    const byYear: Record<number, (number | null)[]> = {}

    for (const entry of monthlyReturns) {
        const [yearStr, monthStr] = entry.month.split('-')
        const year = parseInt(yearStr, 10)
        const monthIndex = parseInt(monthStr, 10) - 1  // "07" -> index 6

        if (!byYear[year]) {
            byYear[year] = Array(12).fill(null)
        }
        byYear[year][monthIndex] = entry.return
    }

    return Object.entries(byYear)
        .map(([year, months]) => ({
            year: parseInt(year, 10),
            months,
            ytd: months.reduce((sum: number, v) => sum + (v ?? 0), 0),
        }))
        .sort((a, b) => a.year - b.year)
}

export default function StrategyDetailPage() {
    const params = useParams()
    const strategyName = params.id as string
    const { data, isLoading, isError } = useStrategyDetail(strategyName)

    if (isLoading) {
        return (
            <PageWrapper title="LOADING_STRATEGY_DATA...">
                <div className="flex flex-col gap-6 p-4">
                    <Skeleton className="h-[200px] w-full cyber-chamfer" />
                    <Skeleton className="h-[400px] w-full cyber-chamfer" />
                </div>
            </PageWrapper>
        )
    }

    if (isError || !data) {
        return (
            <PageWrapper title="STRATEGY_NOT_FOUND">
                <div className="mt-4">
                    <EmptyState
                        message="ERROR_LOADING_STRATEGY"
                    />
                </div>
            </PageWrapper>
        )
    }

    const { configuration, indicators, performance, recent_trades, chart_data } = data

    const tradeColumns: Column<any>[] = [
        {
            header: 'ENTRY_TIME',
            cell: (row) => row.entry_time ? new Date(row.entry_time).toLocaleString() : '-',
            headerClassName: 'text-center',
        },
        {
            header: 'EXIT_TIME',
            cell: (row) => row.exit_time ? new Date(row.exit_time).toLocaleString() : '-',
            headerClassName: 'text-center',
        },
        {
            header: 'DIR',
            cell: (row) => (
                <span className={row.direction?.toUpperCase() === 'LONG' ? 'text-accent' : 'text-destructive'}>
                    {row.direction?.toUpperCase()}
                </span>
            ),
            headerClassName: 'text-center',
        },
        {
            header: 'ENTRY_PRICE',
            cell: (row) => `$${(row.entry_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`,
            className: 'text-center',
            headerClassName: 'text-center',
        },
        {
            header: 'EXIT_PRICE',
            cell: (row) => `$${(row.exit_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`,
            className: 'text-center',
            headerClassName: 'text-center',
        },
        {
            header: 'QUANTITY',
            cell: (row) => {
                const quantity = row.quantity || 0;
                return (
                    <span>
                        {quantity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                )
            },
            className: 'text-center',
            headerClassName: 'text-center',
        },
        {
            header: 'PNL',
            cell: (row) => {
                const pnl = row.net_pnl || 0;
                return (
                    <span className={pnl > 0 ? 'text-accent' : pnl < 0 ? 'text-destructive' : ''}>
                        {pnl > 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                )
            },
            className: 'text-right',
            headerClassName: 'text-center',
        },
        {
            header: 'BALANCE_AFTER_TRADE',
            cell: (row) => {
                const balance = row.balance_after_trade || 0;
                return (
                    <span>
                        ${balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                )
            },
            className: 'text-center',
            headerClassName: 'text-center',
        },
        {
            header: 'EXIT_REASON',
            cell: (row) => {
                const exitReason = row.exit_reason || 'Unknown';
                return (
                    <span>
                        {exitReason}
                    </span>
                )
            },
            className: 'text-center',
            headerClassName: 'text-center',
        },
    ]

    return (
        <PageWrapper
            title={strategyName}
            actions={
                <Badge variant={
                    data.performance.status.toUpperCase() === 'OPEN' || data.performance.status.toUpperCase() === 'ACTIVE' ? 'cyber-running' :
                        data.performance.status.toUpperCase() === 'PAUSED' ? 'cyber-paused' : 'cyber-stopped'
                }>
                    {data.performance.status.toUpperCase()}
                </Badge>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Info Panel */}
                <div className="flex flex-col gap-6">
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent">STRATEGY CONFIG</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 flex flex-col gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-1">
                                    <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest">SYMBOL</span>
                                    <span className="text-sm font-mono text-foreground">{configuration?.symbol || 'N/A'}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest">EXCHANGE</span>
                                    <span className="text-sm font-mono text-foreground">{configuration?.exchange || 'N/A'}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest">TIMEFRAME</span>
                                    <span className="text-sm font-mono text-foreground">{configuration?.timehorizon || 'N/A'}</span>
                                </div>
                            </div>

                            <div className="border-t border-border pt-4">
                                <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest mb-2 block">LONG CONDITIONS</span>
                                {configuration?.long?.rule && (
                                    <div className="text-xs mb-2 text-foreground/80 font-mono">Rule: {configuration.long.rule}</div>
                                )}
                                <div className="flex flex-col gap-1">
                                    {configuration?.long?.conditions?.map((c: any, i: number) => (
                                        <span key={i} className="text-xs font-mono text-foreground/60">
                                            {c.left} {c.operator} {c.right}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="border-t border-border pt-4">
                                <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest mb-2 block">SHORT CONDITIONS</span>
                                {configuration?.short?.rule && (
                                    <div className="text-xs mb-2 text-foreground/80 font-mono">Rule: {configuration.short.rule}</div>
                                )}
                                <div className="flex flex-col gap-1">
                                    {configuration?.short?.conditions?.map((c: any, i: number) => (
                                        <span key={i} className="text-xs font-mono text-foreground/60">
                                            {c.left} {c.operator} {c.right}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div className="border-t border-border pt-4">
                                <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest mb-2 block">INDICATORS</span>
                                <div className="flex flex-wrap gap-2">
                                    {indicators?.map((ind: any, i: number) => (
                                        <span key={i} className="px-2 py-1 bg-muted text-xs font-mono border border-border cyber-chamfer-sm text-foreground/80">
                                            {ind.name} {ind.period ? `(${ind.period})` : ''}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-secondary">PERFORMANCE SUMMARY</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 grid grid-cols-2 gap-4">
                            {METRICS.map(({ key, label, format }) => {
                                const value = (performance as Record<string, number | undefined>)?.[key]
                                const isColorable = format === 'percent' || format === 'ratio' || format === 'raw'
                                const colorClass = isColorable
                                    ? value !== undefined && value > 0
                                        ? 'text-accent'
                                        : value !== undefined && value < 0
                                            ? 'text-destructive'
                                            : ''
                                    : ''

                                return (
                                    <div key={String(key)} className="flex flex-col gap-1">
                                        <span className="text-sm font-bold text-muted-foreground uppercase tracking-widest">
                                            {label}
                                        </span>
                                        <span className={colorClass}>
                                            {formatMetric(value, format)}
                                        </span>
                                    </div>
                                )
                            })}
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <Tabs defaultValue="charts" className="w-full">
                        <TabsList>
                            <TabsTrigger value="charts">PERFORMANCE CHARTS</TabsTrigger>
                            <TabsTrigger value="trades">TRADE LEDGER</TabsTrigger>
                        </TabsList>
                        <TabsContent value="charts" className="flex flex-col gap-6 mt-4">
                            <EquityCurve data={chart_data?.equity_curve || []} />
                            <DrawdownChart data={chart_data?.drawdown || []} />
                            <ReturnsHeatmap data={buildHeatmapData(chart_data?.monthly_returns || [])} />
                            <PieChart winRate={performance?.win_rate || 0} />
                        </TabsContent>
                        <TabsContent value="trades" className="mt-4">
                            <DataTable data={recent_trades || []} columns={tradeColumns} emptyMessage="NO_RECENT_TRADES_FOUND" />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </PageWrapper>
    )
}