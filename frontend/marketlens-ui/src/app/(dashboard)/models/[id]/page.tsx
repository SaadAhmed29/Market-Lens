'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useModelDetail } from '@/hooks/useModels'
import { BrainCircuit, Activity } from 'lucide-react'
import { EmptyState } from '@/components/shared/EmptyState'

export default function ModelDetailPage() {
    const params = useParams()
    const { data, isLoading, isError } = useModelDetail(params.id as string)

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

    if (isLoading) {
        return <PageWrapper title="LOADING_MODEL_DATA..."><div /></PageWrapper>
    }

    if (isError || !data) {
        return (
            <PageWrapper title="MODEL_NOT_FOUND">
                <EmptyState message="ERROR: Model data could not be found." />
            </PageWrapper>
        )
    }

    const { dataset_information, training_information, evaluation } = data

    return (
        <PageWrapper
            title={`MODEL: ${params.id as string}`}
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Meta Panel */}
                <div className="flex flex-col gap-6">
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                                <BrainCircuit className="size-4" /> DATASET INFORMATION
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 flex flex-col gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-1 col-span-2">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">DATASET</span>
                                    <span className="text-sm font-mono text-foreground">{dataset_information.dataset}</span>
                                </div>
                                <div className="flex flex-col gap-1 col-span-2">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TARGET</span>
                                    <span className="text-sm font-mono text-foreground">{dataset_information.target}</span>
                                </div>
                                <div className="flex flex-col gap-1 col-span-2">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">DATE_RANGE</span>
                                    <span className="text-sm font-mono text-foreground">{dataset_information.date_range}</span>
                                </div>
                                <div className="flex flex-col gap-1 col-span-2">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TRAIN_SPLIT</span>
                                    <span className="text-sm font-mono text-foreground">{dataset_information.train_test_split.train}</span>
                                </div>
                                <div className="flex flex-col gap-1 col-span-2">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">VAL_SPLIT</span>
                                    <span className="text-sm font-mono text-foreground">{dataset_information.train_test_split.val}</span>
                                </div>
                                <div className="flex flex-col gap-1 col-span-2">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">FEATURES ({dataset_information.features.length})</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {dataset_information.features.map((f: string) => (
                                            <span key={f} className="text-[10px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 cyber-chamfer-sm border border-border">{f}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-secondary flex items-center gap-2">
                                <Activity className="size-4" /> ML METRICS
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 grid grid-cols-3 gap-2">
                            {Object.entries(evaluation.ml_metrics).map(([key, value]) => {
                                const isRegression = training_information.model_type === 'regression'
                                const numValue = value !== null && value !== undefined ? Number(value) : null
                                const displayValue = numValue === null || Number.isNaN(numValue)
                                    ? 'N/A'
                                    : isRegression
                                        ? numValue.toFixed(4)
                                        : `${(numValue * 100).toFixed(2)}%`

                                return (
                                    <div key={key} className="flex flex-col items-center justify-center p-3 border border-border cyber-chamfer-sm bg-background">
                                        <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">{key}</span>
                                        <span className="text-lg font-bold text-accent">
                                            {displayValue}
                                        </span>
                                    </div>
                                )
                            })}
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-foreground">TRAINING INFORMATION</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 grid grid-cols-2 gap-6">

                            <div className="flex flex-col gap-4 border-r border-border/50 pr-4">
                                <h3 className="text-sm font-mono text-muted-foreground border-b border-border pb-2">HYPERPARAMETERS</h3>
                                <div>
                                    <pre className="text-xs font-mono text-foreground bg-background p-2 border border-border cyber-chamfer-sm overflow-x-auto whitespace-pre-wrap">
                                        {JSON.stringify(training_information.hyperparameters, null, 2)}
                                    </pre>
                                </div>
                            </div>

                            <div className="flex flex-col gap-4">
                                <h3 className="text-sm font-mono text-muted-foreground border-b border-border pb-2">PIPELINE</h3>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">PREPROCESSING</span>
                                    <span className="text-sm font-mono text-foreground">{training_information.preprocessing || 'None'}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">SCALING</span>
                                    <span className="text-sm font-mono text-foreground">{training_information.scaling || 'None'}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">STATIONARITY</span>
                                    <span className="text-sm font-mono text-foreground">{training_information.stationarity || 'None'}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">FEATURE ENGINEERING ({training_information.feature_engineering.length})</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {training_information.feature_engineering.map((f: string) => (
                                            <span key={f} className="text-[10px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 cyber-chamfer-sm border border-border">{f}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                        </CardContent>
                    </Card>

                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-sm font-mono uppercase tracking-widest text-foreground">BACKTEST METRICS</CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="grid grid-cols-2 divide-x divide-y divide-border">
                                {Object.entries(evaluation.backtest_metrics).map(([key, value]) => {
                                    const metricConfig = METRICS.find((m) => m.key === key)
                                    const numValue = Number(value)
                                    const isNumber = !isNaN(numValue) && value !== null && value !== ''
                                    let textColorClass = 'text-foreground'

                                    if (isNumber) {
                                        if (numValue > 0) textColorClass = 'text-accent font-bold'
                                        if (numValue < 0) textColorClass = 'text-destructive font-bold'
                                    }

                                    const displayLabel = metricConfig?.label || key
                                    const displayValue = metricConfig
                                        ? formatMetric(isNumber ? numValue : undefined, metricConfig.format)
                                        : (isNumber ? numValue.toFixed(4) : String(value))

                                    return (
                                        <div key={key} className="flex items-center justify-between p-3 text-sm font-mono hover:bg-muted/30 transition-colors border-t-0">
                                            <span className="text-muted-foreground">{displayLabel}</span>
                                            <span className={textColorClass}>
                                                {displayValue}
                                            </span>
                                        </div>
                                    )
                                })}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </PageWrapper>
    )
}
