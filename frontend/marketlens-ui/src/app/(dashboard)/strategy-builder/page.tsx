'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/shared/EmptyState'
import { useStrategyBuilder, useStrategyBuilderOptions, useSubmitStrategyBuilder, useSaveStrategy } from '@/hooks/useStrategyBuilder'
import api from '@/lib/api'

const REQUESTS_PAGE_SIZE = 10

type Mode = 'strategy' | 'model' | 'strategy_combination' | 'strategy_model_combination'

export default function StrategyBuilderPage() {
    const router = useRouter()
    const { data: requests, isLoading: isRequestsLoading, isError } = useStrategyBuilder()
    const { data: optionsData } = useStrategyBuilderOptions()
    const submitRequest = useSubmitStrategyBuilder()
    const saveStrategy = useSaveStrategy()

    const [mode, setMode] = useState<Mode>('strategy')
    const [selectedStrategies, setSelectedStrategies] = useState<string[]>([])
    const [selectedModels, setSelectedModels] = useState<string[]>([])
    const [combinationRule, setCombinationRule] = useState<'AND' | 'OR'>('AND')
    const [showSaveNameInput, setShowSaveNameInput] = useState(false)
    const [placeholderName, setPlaceholderName] = useState('')
    const [saveStrategyName, setSaveStrategyName] = useState('')
    const [saveError, setSaveError] = useState<string | null>(null)
    const [saveSuccess, setSaveSuccess] = useState(false)

    const [symbol, setSymbol] = useState('')
    const [exchange, setExchange] = useState('')
    const [timeframe, setTimeframe] = useState('')
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [initialBalance, setInitialBalance] = useState(10000)
    const [exitOnOppositeSignal, setExitOnOppositeSignal] = useState(true)
    const [positionSizeType, setPositionSizeType] = useState('fixed_percentage')
    const [positionSizeValue, setPositionSizeValue] = useState(10)
    const [commission, setCommission] = useState(0.05)
    const [slippage, setSlippage] = useState(0.02)
    const [allowLong, setAllowLong] = useState(true)
    const [allowShort, setAllowShort] = useState(true)
    const [tpEnabled, setTpEnabled] = useState(false)
    const [tpType, setTpType] = useState('percentage')
    const [tpValue, setTpValue] = useState(2.0)
    const [slEnabled, setSlEnabled] = useState(false)
    const [slType, setSlType] = useState('percentage')
    const [slValue, setSlValue] = useState(1.0)

    const [page, setPage] = useState(1)

    const rawRequests = useMemo(() => requests || [], [requests])

    useEffect(() => {
        setPage(1)
    }, [rawRequests])

    // Autofill when single strategy changes
    useEffect(() => {
        if (mode === 'strategy' && selectedStrategies.length > 0 && optionsData?.strategies) {
            const opt = optionsData.strategies.find((o: any) => o.strategy_name === selectedStrategies[0])
            if (opt) {
                if (opt.symbol) setSymbol(opt.symbol)
                if (opt.exchange) setExchange(opt.exchange)
                if (opt.timehorizon) setTimeframe(opt.timehorizon)
            }
        }
    }, [mode, selectedStrategies, optionsData])

    // Autofill when single model changes
    useEffect(() => {
        if (mode === 'model' && selectedModels.length > 0 && optionsData?.models) {
            const opt = optionsData.models.find((o: any) => o.model_file === selectedModels[0])
            if (opt) {
                if (opt.symbol) setSymbol(opt.symbol)
                if (opt.timeframe) setTimeframe(opt.timeframe)
            }
        }
    }, [mode, selectedModels, optionsData])

    const handleRunBacktest = (e: React.FormEvent) => {
        e.preventDefault()
        submitRequest.mutate({
            mode,
            selected_strategies: selectedStrategies,
            selected_models: selectedModels.map(m => optionsData?.models?.find((opt: any) => opt.model_file === m)).filter(Boolean),
            combination_rule: combinationRule,
            symbol,
            exchange,
            timehorizon: timeframe,
            start_date: startDate,
            end_date: endDate,
            initial_balance: initialBalance,
            exit_on_opposite_signal: exitOnOppositeSignal,
            position_size: { type: positionSizeType, value: positionSizeValue },
            commission,
            slippage,
            allow_long: allowLong,
            allow_short: allowShort,
            take_profit: { enabled: tpEnabled, type: tpType, value: tpValue },
            stop_loss: { enabled: slEnabled, type: slType, value: slValue }
        })
    }

    const handleSaveStrategy = async () => {
        setSaveError(null)
        setSaveSuccess(false)
        const isCombination = mode.includes('combination')

        if (!showSaveNameInput) {
            try {
                const modelNames = selectedModels.map(m => {
                    const opt = optionsData?.models?.find((opt: any) => opt.model_file === m)
                    return opt ? opt.model_name || opt.model_file : m
                })
                const queryParams = new URLSearchParams({
                    mode,
                    exchange,
                    symbol,
                    timehorizon: timeframe,
                    strategies: selectedStrategies.join(','),
                    models: modelNames.join(',')
                }).toString()

                const { data } = await api.get(`/strategy-builder/preview-name?${queryParams}`)
                if (data.status === 'success' && data.data?.name) {
                    setPlaceholderName(data.data.name)
                }
            } catch (err) {
                console.error("Failed to fetch preview name")
            }
            setShowSaveNameInput(true)
            return
        }

        const config = {
            mode,
            is_combination: isCombination,
            strategy_name_override: saveStrategyName.trim() || undefined,
            selected_strategies: selectedStrategies,
            selected_models: selectedModels.map(m => optionsData?.models?.find((opt: any) => opt.model_file === m)).filter(Boolean),
            combination_rule: combinationRule,
            symbol,
            exchange,
            timehorizon: timeframe,
            allow_execution: true,
            allow_simulation: true,
        }

        saveStrategy.mutate(config, {
            onSuccess: (res) => {
                if (res.status === 'error') {
                    setSaveError(res.message || "Failed to save strategy")
                } else {
                    setSaveSuccess(true)
                    setShowSaveNameInput(false)
                    setSaveStrategyName('')
                    setTimeout(() => setSaveSuccess(false), 3000)
                }
            },
            onError: (err: any) => {
                setSaveError(err.message || "An unexpected error occurred")
            }
        })
    }

    const uniqueSymbols = Array.from(new Set([
        ...(optionsData?.strategies?.map((o: any) => o.symbol) || []),
        ...(optionsData?.models?.map((o: any) => o.symbol) || [])
    ].filter(Boolean))) as string[]

    const TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h']
    const columns: Column<any>[] = [
        { header: 'STRATEGY', accessorKey: 'strategy_name', className: 'text-accent font-bold' },
        {
            header: 'STATUS',
            cell: (row) => {
                const s = row.status || ''
                let v = 'cyber-pending'
                if (s === 'Completed') v = 'cyber-completed'
                else if (s === 'Running') v = 'cyber-running'
                else if (s === 'Failed') v = 'cyber-error'
                return (
                    <Badge variant={v as any}>
                        {s.toUpperCase()}
                    </Badge>
                )
            }
        },
        { header: 'CREATED AT', cell: (row) => row.created_at ? new Date(row.created_at).toLocaleString() : '-' },
        { header: 'COMPLETED AT', cell: (row) => row.completed_at ? new Date(row.completed_at).toLocaleString() : '-' },
        {
            header: 'SHARPE',
            cell: (row) => {
                try {
                    const res = typeof row.result_summary === 'string' ? JSON.parse(row.result_summary) : row.result_summary
                    return res?.sharpe != null ? Number(res.sharpe).toFixed(2) : '-'
                } catch { return '-' }
            }
        },
        {
            header: 'WIN RATE',
            cell: (row) => {
                try {
                    const res = typeof row.result_summary === 'string' ? JSON.parse(row.result_summary) : row.result_summary
                    return res?.win_rate != null ? `${(Number(res.win_rate)).toFixed(1)}%` : '-'
                } catch { return '-' }
            }
        },
        {
            header: 'FINAL BALANCE',
            cell: (row) => {
                try {
                    const res = typeof row.result_summary === 'string' ? JSON.parse(row.result_summary) : row.result_summary
                    return res?.final_balance != null ? `$${Number(res.final_balance).toLocaleString()}` : '-'
                } catch { return '-' }
            }
        }
    ]

    const totalPages = Math.max(1, Math.ceil(rawRequests.length / REQUESTS_PAGE_SIZE))
    const currentPage = Math.min(page, totalPages)
    const paginatedRequests = rawRequests.slice(
        (currentPage - 1) * REQUESTS_PAGE_SIZE,
        currentPage * REQUESTS_PAGE_SIZE
    )

    const isStrategyVisible = mode === 'strategy' || mode.includes('strategy_combination') || mode === 'strategy_model_combination'
    const isModelVisible = mode === 'model' || mode === 'strategy_model_combination'
    const isCombinationRuleVisible = mode.includes('combination')

    return (
        <PageWrapper title="STRATEGY BUILDER">
            <Card className="border-border bg-card cyber-chamfer mb-6">
                <CardHeader className="py-3 border-b border-border bg-background/50">
                    <CardTitle className="text-sm font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                        <span className="animate-pulse">&gt;</span> CONFIGURE_STRATEGY
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-6">
                    <form onSubmit={handleRunBacktest} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm font-mono">

                        {/* Mode Selection */}
                        <div className="lg:col-span-4 flex flex-col gap-2 mb-4 border-b border-border/50 pb-6">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">MODE SELECTION</label>
                            <div className="flex flex-wrap gap-2">
                                {[
                                    { id: 'strategy', label: 'STRATEGY' },
                                    { id: 'model', label: 'MODEL' },
                                    { id: 'strategy_combination', label: 'STRATEGY COMBINATION' },
                                    { id: 'strategy_model_combination', label: 'STRATEGY + MODEL COMBINATION' }
                                ].map(m => (
                                    <button
                                        key={m.id}
                                        type="button"
                                        onClick={() => {
                                            setMode(m.id as Mode)
                                            setSelectedStrategies([])
                                            setSelectedModels([])
                                            setShowSaveNameInput(false)
                                        }}
                                        className={`px-4 py-2 cyber-chamfer-sm border text-xs font-bold tracking-wider transition-colors ${mode === m.id
                                            ? 'bg-accent/20 border-accent text-accent shadow-[inset_0_0_10px_rgba(var(--accent-rgb),0.3)]'
                                            : 'bg-input/50 border-border text-muted-foreground hover:bg-input hover:text-foreground'
                                            }`}
                                    >
                                        {m.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Strategy Fields */}
                        {isStrategyVisible && (
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-muted-foreground uppercase tracking-widest">STRATEGIES</label>
                                {mode === 'strategy' ? (
                                    <select
                                        className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 py-2 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                        value={selectedStrategies[0] || ''}
                                        onChange={e => setSelectedStrategies([e.target.value])}
                                        required={isStrategyVisible}
                                    >
                                        <option value="">SELECT STRATEGY...</option>
                                        {optionsData?.strategies?.map((s: any) => (
                                            <option key={s.strategy_name} value={s.strategy_name}>{s.strategy_name}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <div className="w-full h-32 overflow-y-auto cyber-chamfer-sm border border-border bg-input/50 px-3 py-2 text-sm font-mono flex flex-col gap-1.5">
                                        {optionsData?.strategies?.length ? optionsData.strategies.map((s: any) => {
                                            const checked = selectedStrategies.includes(s.strategy_name)
                                            return (
                                                <label key={s.strategy_name} className="flex items-center gap-2 cursor-pointer text-xs hover:text-accent transition-colors">
                                                    <input
                                                        type="checkbox"
                                                        className="accent-accent"
                                                        checked={checked}
                                                        onChange={e => {
                                                            if (e.target.checked) {
                                                                setSelectedStrategies([...selectedStrategies, s.strategy_name])
                                                            } else {
                                                                setSelectedStrategies(selectedStrategies.filter(name => name !== s.strategy_name))
                                                            }
                                                        }}
                                                    />
                                                    {s.strategy_name}
                                                </label>
                                            )
                                        }) : (
                                            <span className="text-xs text-muted-foreground">NO_STRATEGIES_AVAILABLE</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Model Fields */}
                        {isModelVisible && (
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-muted-foreground uppercase tracking-widest">MODELS</label>
                                <select
                                    multiple={mode !== 'model'}
                                    className={`w-full cyber-chamfer-sm border border-border bg-input/50 px-3 py-2 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none ${mode !== 'model' ? 'h-32' : 'h-9'}`}
                                    value={mode === 'model' ? selectedModels[0] || '' : selectedModels}
                                    onChange={e => {
                                        if (mode === 'model') {
                                            setSelectedModels([e.target.value])
                                        } else {
                                            const values = Array.from(e.target.selectedOptions, option => option.value)
                                            setSelectedModels(values)
                                        }
                                    }}
                                    required={isModelVisible && mode !== 'strategy_model_combination'}
                                >
                                    {mode === 'model' && <option value="">SELECT MODEL...</option>}
                                    {optionsData?.models?.map((m: any) => (
                                        <option key={m.model_file} value={m.model_file}>{m.model_name}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* Combination Rule */}
                        {isCombinationRuleVisible && (
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-muted-foreground uppercase tracking-widest">COMBINATION RULE</label>
                                <div className="flex gap-2 h-9">
                                    <button
                                        type="button"
                                        onClick={() => setCombinationRule('AND')}
                                        className={`flex-1 cyber-chamfer-sm border text-xs font-bold transition-colors ${combinationRule === 'AND'
                                            ? 'bg-accent/20 border-accent text-accent'
                                            : 'bg-input/50 border-border text-muted-foreground hover:bg-input hover:text-foreground'
                                            }`}
                                        title="All signals must agree"
                                    >
                                        AND
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setCombinationRule('OR')}
                                        className={`flex-1 cyber-chamfer-sm border text-xs font-bold transition-colors ${combinationRule === 'OR'
                                            ? 'bg-accent/20 border-accent text-accent'
                                            : 'bg-input/50 border-border text-muted-foreground hover:bg-input hover:text-foreground'
                                            }`}
                                        title="Any signal triggers"
                                    >
                                        OR
                                    </button>
                                </div>
                                <span className="text-[10px] text-muted-foreground mt-1">
                                    {combinationRule === 'AND' ? 'All must agree' : 'Any signal triggers'}
                                </span>
                            </div>
                        )}

                        {/* Spacer if needed to align the next row nicely depending on what is shown */}
                        <div className="col-span-full border-b border-border/50 my-2" />

                        {/* Standard Fields */}
                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">SYMBOL</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={symbol}
                                onChange={e => setSymbol(e.target.value)}
                                required
                            >
                                <option value="">SELECT SYMBOL...</option>
                                {uniqueSymbols.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">TIMEFRAME</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={timeframe}
                                onChange={e => setTimeframe(e.target.value)}
                                required
                            >
                                <option value="">SELECT TIMEFRAME...</option>
                                {TIMEFRAMES.map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">EXCHANGE</label>
                            <Input placeholder="e.g. BINANCE" value={exchange} onChange={e => setExchange(e.target.value)} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">START DATE</label>
                            <Input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">END DATE</label>
                            <Input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">INITIAL BALANCE</label>
                            <Input type="number" value={initialBalance} onChange={e => setInitialBalance(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2 justify-center pt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-xs">
                                <input type="checkbox" checked={exitOnOppositeSignal} onChange={e => setExitOnOppositeSignal(e.target.checked)} className="accent-accent" />
                                EXIT ON OPPOSITE SIGNAL
                            </label>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">POS SIZE TYPE</label>
                            <select
                                className="h-9 w-full cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none"
                                value={positionSizeType}
                                onChange={e => setPositionSizeType(e.target.value)}
                            >
                                <option value="fixed_percentage">FIXED PERCENTAGE</option>
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">POS SIZE VALUE</label>
                            <Input type="number" step="0.1" value={positionSizeValue} onChange={e => setPositionSizeValue(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">COMMISSION (%)</label>
                            <Input type="number" step="0.01" value={commission} onChange={e => setCommission(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="text-xs text-muted-foreground uppercase tracking-widest">SLIPPAGE (%)</label>
                            <Input type="number" step="0.01" value={slippage} onChange={e => setSlippage(Number(e.target.value))} required />
                        </div>

                        <div className="flex flex-col gap-2 justify-center pt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-xs">
                                <input type="checkbox" checked={allowLong} onChange={e => setAllowLong(e.target.checked)} className="accent-accent" />
                                ALLOW LONG
                            </label>
                        </div>

                        <div className="flex flex-col gap-2 justify-center pt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-xs">
                                <input type="checkbox" checked={allowShort} onChange={e => setAllowShort(e.target.checked)} className="accent-accent" />
                                ALLOW SHORT
                            </label>
                        </div>

                        {/* TP Settings */}
                        <div className="flex flex-col gap-2 border border-border/50 p-2 pt-1 cyber-chamfer-sm bg-background/20 lg:col-span-2">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-accent uppercase tracking-widest">TAKE PROFIT</span>
                                <label className="flex items-center gap-2 cursor-pointer text-xs">
                                    <input type="checkbox" checked={tpEnabled} onChange={e => setTpEnabled(e.target.checked)} className="accent-accent" />
                                    ENABLED
                                </label>
                            </div>
                            <div className="flex gap-2">
                                <select
                                    className="h-9 flex-1 cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none disabled:opacity-50"
                                    value={tpType}
                                    onChange={e => setTpType(e.target.value)}
                                    disabled={!tpEnabled}
                                >
                                    <option value="percentage">PERCENTAGE</option>
                                </select>
                                <Input type="number" step="0.1" value={tpValue} onChange={e => setTpValue(Number(e.target.value))} disabled={!tpEnabled} className="flex-1" />
                            </div>
                        </div>

                        {/* SL Settings */}
                        <div className="flex flex-col gap-2 border border-border/50 p-2 pt-1 cyber-chamfer-sm bg-background/20 lg:col-span-2">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-destructive uppercase tracking-widest">STOP LOSS</span>
                                <label className="flex items-center gap-2 cursor-pointer text-xs">
                                    <input type="checkbox" checked={slEnabled} onChange={e => setSlEnabled(e.target.checked)} className="accent-destructive" />
                                    ENABLED
                                </label>
                            </div>
                            <div className="flex gap-2">
                                <select
                                    className="h-9 flex-1 cyber-chamfer-sm border border-border bg-input/50 px-3 text-sm font-mono focus:border-accent focus:ring-1 focus:ring-accent outline-none disabled:opacity-50"
                                    value={slType}
                                    onChange={e => setSlType(e.target.value)}
                                    disabled={!slEnabled}
                                >
                                    <option value="percentage">PERCENTAGE</option>
                                </select>
                                <Input type="number" step="0.1" value={slValue} onChange={e => setSlValue(Number(e.target.value))} disabled={!slEnabled} className="flex-1" />
                            </div>
                        </div>

                        <div className="lg:col-span-4 flex flex-col md:flex-row justify-end mt-2 pt-4 border-t border-border/50 gap-4">
                            <div className="flex-1 flex items-center justify-end gap-2">
                                {showSaveNameInput && (
                                    <div className="flex flex-col">
                                        <Input
                                            placeholder={placeholderName || "Strategy Name"}
                                            value={saveStrategyName}
                                            onChange={e => setSaveStrategyName(e.target.value)}
                                            className="w-64 border-accent focus-visible:ring-accent placeholder:text-muted-foreground/50"
                                            disabled={saveStrategy.isPending}
                                        />
                                        {saveError && <span className="text-[10px] text-destructive mt-1">{saveError}</span>}
                                        {saveSuccess && <span className="text-[10px] text-accent mt-1">Saved successfully!</span>}
                                    </div>
                                )}
                                <Button
                                    type="button"
                                    variant="cyber-glitch"
                                    onClick={handleSaveStrategy}
                                    disabled={saveStrategy.isPending}
                                >
                                    {saveStrategy.isPending ? 'SAVING...' : 'SAVE_STRATEGY'}
                                </Button>
                            </div>

                            <Button type="submit" variant="cyber-glitch" disabled={submitRequest.isPending}>
                                {submitRequest.isPending ? 'INITIALIZING...' : 'EXECUTE_BACKTEST'}
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* List */}
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">SIMULATION_HISTORY</h2>
            </div>

            {isError ? (
                <EmptyState message="FAILED_TO_LOAD_BACKTESTS" />
            ) : (
                <>
                    <DataTable
                        data={paginatedRequests}
                        columns={columns}
                        isLoading={isRequestsLoading}
                        onRowClick={(row) => row.status === 'Completed' && router.push(`/strategy-builder/${row.request_id}`)}
                        emptyMessage="NO_BACKTESTS_FOUND"
                    />

                    {!isRequestsLoading && rawRequests.length > REQUESTS_PAGE_SIZE && (
                        <div className="flex items-center justify-between mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                            <button
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                            >
                                &lt; PREV
                            </button>
                            <span>
                                PAGE {currentPage} / {totalPages}
                            </span>
                            <button
                                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                            >
                                NEXT &gt;
                            </button>
                        </div>
                    )}
                </>
            )}
        </PageWrapper>
    )
}
