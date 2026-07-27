'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useExecutionDetail } from '@/hooks/useExecutions'
import { EmptyState } from '@/components/shared/EmptyState'
import { DataTable, Column } from '@/components/shared/DataTable'
import { EquityCurve } from '@/components/charts/EquityCurve'
import { PieChart } from '@/components/charts/PieChart'

type MetricFormat = 'percent' | 'ratio' | 'currency' | 'integer' | 'raw'

interface MetricConfig {
    key: string
    label: string
    format: MetricFormat
}

const METRICS: MetricConfig[] = [
    { key: 'final_balance', label: 'FINAL BALANCE', format: 'currency' },
    { key: 'total_trades', label: 'TOTAL TRADES', format: 'integer' },
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

export default function ExecutionDetailPage() {
    const params = useParams()
    const strategyName = params.id as string
    const { data, isLoading, isError } = useExecutionDetail(strategyName)

    if (isLoading) {
        return (
            <PageWrapper title="LOADING_EXECUTION_DATA...">
                <div className="h-96 animate-pulse bg-card/50 rounded-lg border border-border" />
            </PageWrapper>
        )
    }

    if (isError || !data) {
        return (
            <PageWrapper title="EXECUTION_ERROR">
                <EmptyState message="EXECUTION_ERROR: FAILED_TO_LOAD_EXECUTION_DETAILS_OR_DATA_IS_EMPTY." />
            </PageWrapper>
        )
    }

    const {
        strategy_information: stratInfo,
        wallet_information: walletInfo,
        current_position: currentPos,
        position_history: posHistory,
        statistics: stats,
        chart_data: chartData
    } = data

    // Position history columns
    const historyColumns: Column<any>[] = [
        { header: 'ENTRY_TIME', cell: (row) => row.entry_time ? new Date(row.entry_time).toLocaleString() : 'N/A' },
        { header: 'EXIT_TIME', cell: (row) => row.exit_time ? new Date(row.exit_time).toLocaleString() : 'N/A' },
        {
            header: 'DIRECTION',
            cell: (row) => (
                <span className={row.direction?.toUpperCase() === 'LONG' ? 'text-accent' : 'text-destructive'}>
                    {row.direction?.toUpperCase() || 'N/A'}
                </span>
            )
        },
        { header: 'ENTRY_PRICE', cell: (row) => `$${Number(row.entry_price || 0).toLocaleString()}` },
        { header: 'EXIT_PRICE', cell: (row) => `$${Number(row.exit_price || 0).toLocaleString()}` },
        { header: 'QUANTITY', cell: (row) => Number(row.quantity || 0).toLocaleString() },
        {
            header: 'NET_PNL',
            cell: (row) => {
                const pnl = Number(row.net_pnl || 0)
                return (
                    <span className={pnl > 0 ? 'text-accent' : pnl < 0 ? 'text-destructive' : 'text-muted-foreground'}>
                        {pnl > 0 ? '+' : ''}${pnl.toLocaleString()}
                    </span>
                )
            }
        },
        { header: 'BALANCE', cell: (row) => `$${Number(row.balance_after_trade || 0).toLocaleString()}` }
    ]

    // Statistics layout logic
    const mainStatKeys = ['final_balance', 'total_trades', 'sharpe_ratio', 'win_rate', 'max_drawdown', 'profit_factor', 'avg_return', 'comp']
    const otherStats = Object.entries(stats || {}).filter(([k]) => !mainStatKeys.includes(k) && k !== 'strategy_name')

    const mainMetricsMap = new Map(METRICS.map((m) => [m.key, m]))

    return (
        <PageWrapper title={`EXEC_NODE: ${strategyName}`}>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                <div className="lg:col-span-1 flex flex-col gap-6">
                    {/* Strategy Information */}
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                                <span>&gt;</span> STRATEGY INFO
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 flex flex-col gap-4">
                            <div className="grid grid-cols-3 gap-2">
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">SYMBOL</span>
                                    <span className="text-sm font-mono">{stratInfo?.symbol || 'N/A'}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">EXCHANGE</span>
                                    <span className="text-sm font-mono">{stratInfo?.exchange || 'N/A'}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">HORIZON</span>
                                    <span className="text-sm font-mono">{stratInfo?.timehorizon || 'N/A'}</span>
                                </div>
                            </div>

                            {/* Conditions */}
                            {['long', 'short'].map(side => (
                                stratInfo?.[side]?.conditions && stratInfo[side].conditions.length > 0 && (
                                    <div key={side} className="mt-2">
                                        <div className="text-xs text-muted-foreground uppercase tracking-widest mb-2 border-b border-border/50 pb-1">{side}_CONDITIONS</div>
                                        <div className="flex flex-col gap-2">
                                            {stratInfo[side].conditions.map((cond: any, idx: number) => (
                                                <div key={idx} className="bg-background/50 p-2 rounded text-xs font-mono grid grid-cols-12 gap-2 items-center">
                                                    <div className="col-span-4 break-words text-foreground">{cond.left}</div>
                                                    <div className="col-span-4 break-words text-accent">{cond.operator}</div>
                                                    <div className="col-span-4 break-words text-foreground">{cond.right}</div>
                                                    <div className="col-span-2 break-words text-right text-muted-foreground">x{cond.persist_bars}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )
                            ))}
                        </CardContent>
                    </Card>

                    {/* Wallet Information */}
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                                <span>&gt;</span> WALLET INFO
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-xs text-muted-foreground uppercase tracking-widest">ACCOUNT</span>
                                <span className="text-sm font-mono truncate">{walletInfo?.account_name || 'N/A'}</span>
                            </div>
                            <div className="flex flex-col gap-1 text-right">
                                <span className="text-xs text-muted-foreground uppercase tracking-widest">BALANCE</span>
                                <span className="text-lg font-mono text-accent">
                                    ${Number(walletInfo?.wallet_balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </span>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Current Position */}
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                                <span className="animate-pulse">&gt;</span> CURRENT POSITION
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 flex flex-col gap-4">
                            <div className="flex justify-between items-center border-b border-border pb-4">
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-left text-muted-foreground uppercase tracking-widest">DIRECTION</span>
                                    <Badge variant={currentPos?.direction?.toUpperCase() === 'LONG' ? 'cyber-active' : currentPos?.direction?.toUpperCase() === 'SHORT' ? 'destructive' : 'outline'} className="w-fit">
                                        {currentPos?.direction?.toUpperCase() || 'NONE'}
                                    </Badge>
                                </div>
                                <div className="flex flex-col gap-1 text-right">
                                    <span className="text-xs text-left text-muted-foreground uppercase tracking-widest">STATUS</span>
                                    <Badge variant={
                                        currentPos?.status?.toUpperCase() === 'OPEN' ? 'cyber-active' : 'outline'
                                    }>
                                        {currentPos?.status?.toUpperCase() || 'UNKNOWN'}
                                    </Badge>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">ENTRY_PRICE</span>
                                    <span className="text-sm font-mono">${Number(currentPos?.entry_price || 0).toLocaleString()}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">QUANTITY</span>
                                    <span className="text-sm font-mono">{Number(currentPos?.quantity || 0).toLocaleString()}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">TAKE_PROFIT</span>
                                    <span className="text-sm font-mono text-accent">${Number(currentPos?.tp_price || 0).toLocaleString()}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs text-muted-foreground uppercase tracking-widest">STOP_LOSS</span>
                                    <span className="text-sm font-mono text-destructive">${Number(currentPos?.sl_price || 0).toLocaleString()}</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                </div>

                <div className="lg:col-span-2 flex flex-col gap-6">

                    {/* Key Statistics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {mainStatKeys.map(k => {
                            const config = mainMetricsMap.get(k)
                            const rawValue = stats?.[k]
                            const numValue = rawValue === undefined || rawValue === null ? undefined : Number(rawValue)
                            const format: MetricFormat = config?.format || 'raw'
                            const displayValue = formatMetric(numValue, format)
                            const isColorable = format === 'percent' || format === 'ratio' || format === 'raw'
                            const colorClass = isColorable
                                ? numValue !== undefined && numValue > 0
                                    ? 'text-accent'
                                    : numValue !== undefined && numValue < 0
                                        ? 'text-destructive'
                                        : 'text-foreground'
                                : 'text-foreground'

                            return (
                                <Card key={k} className="border-border bg-card cyber-chamfer">
                                    <CardContent className="p-4 flex flex-col gap-1">
                                        <span className="text-sm text-muted-foreground uppercase tracking-widest text-center">{k.replace(/_/g, ' ')}</span>
                                        <span className={`text-lg font-mono ${colorClass} text-center`}>{displayValue}</span>
                                    </CardContent>
                                </Card>
                            )
                        })}
                    </div>

                    <Tabs defaultValue="charts" className="w-full">
                        <TabsList>
                            <TabsTrigger value="charts">CHARTS</TabsTrigger>
                            <TabsTrigger value="history">HISTORY</TabsTrigger>
                            <TabsTrigger value="stats">ALL_STATS</TabsTrigger>
                        </TabsList>

                        <TabsContent value="charts" className="flex flex-col gap-6 mt-4">
                            {/* Equity Curve */}
                            <EquityCurve data={chartData?.equity_curve || []} title="EQUITY CURVE" height={300} />

                            {/* Position Size */}
                            <EquityCurve data={chartData?.position_size || []} title="POSITION SIZE" height={240} />

                            {/* Returns */}
                            <EquityCurve data={chartData?.returns || []} title="RETURNS" height={240} />

                            {/* Pie Chart */}
                            <PieChart winRate={stats?.win_rate || 0} title="WIN / LOSS" height={240} />
                        </TabsContent>

                        <TabsContent value="history" className="mt-4">
                            <DataTable data={posHistory || []} columns={historyColumns} emptyMessage="NO_POSITION_HISTORY_FOUND" />
                        </TabsContent>

                        <TabsContent value="stats" className="mt-4">
                            <Card className="border-border bg-card cyber-chamfer">
                                <CardContent className="p-4 grid grid-cols-2 gap-x-8 gap-y-2">
                                    {otherStats.map(([k, v]) => {
                                        const config = mainMetricsMap.get(k)
                                        const numValue = v === undefined || v === null ? undefined : Number(v)
                                        const format: MetricFormat = config?.format || 'raw'
                                        const displayValue = formatMetric(numValue, format)
                                        const isColorable = format === 'percent' || format === 'ratio' || format === 'raw'
                                        const colorClass = isColorable
                                            ? numValue !== undefined && numValue > 0
                                                ? 'text-accent'
                                                : numValue !== undefined && numValue < 0
                                                    ? 'text-destructive'
                                                    : 'text-foreground'
                                            : 'text-foreground'

                                        return (
                                            <div key={k} className="flex justify-between items-center border-b border-border/50 py-1">
                                                <span className="text-sm font-mono text-muted-foreground uppercase">{(config?.label || k.replace(/_/g, ' ')).toUpperCase()}</span>
                                                <span className={`text-sm font-mono ${colorClass}`}>{displayValue}</span>
                                            </div>
                                        )
                                    })}
                                </CardContent>
                            </Card>
                        </TabsContent>

                    </Tabs>
                </div>

            </div>
        </PageWrapper>
    )
}