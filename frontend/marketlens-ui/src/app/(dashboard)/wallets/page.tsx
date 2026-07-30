'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { useWallets, useUpdateWalletKeys, useUnassignedStrategies, useAssignStrategy } from '@/hooks/useWallets'
import { Wallet as WalletIcon } from 'lucide-react'
import { EmptyState } from '@/components/shared/EmptyState'

function WalletCard({ wallet }: { wallet: any }) {
    const router = useRouter()
    const { mutate, isPending } = useUpdateWalletKeys()
    const [open, setOpen] = useState(false)
    const [apiKey, setApiKey] = useState('')
    const [apiSecret, setApiSecret] = useState('')

    const handleSave = () => {
        mutate({ accountName: wallet.account_name, api_key: apiKey, api_secret: apiSecret }, {
            onSuccess: () => {
                setOpen(false)
                setApiKey('')
                setApiSecret('')
            }
        })
    }

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val || 0)
    }

    return (
        <Card
            className="border-border bg-card cyber-chamfer flex flex-col group/wallet cursor-pointer hover:border-accent transition-colors"
            onClick={() => router.push(`/wallets/${wallet.account_name}`)}
        >
            <CardHeader className="py-4 border-b border-border bg-background/50 flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-muted cyber-chamfer-sm border border-border group-hover/wallet:border-accent transition-colors">
                        <WalletIcon className="size-5 text-accent" strokeWidth={1.5} />
                    </div>
                    <div className="flex flex-col">
                        <CardTitle className="text-sm font-mono uppercase tracking-widest text-foreground">
                            {wallet.exchange}
                        </CardTitle>
                        <span className="text-sm text-muted-foreground font-mono tracking-widest">{wallet.account_type}</span>
                    </div>
                </div>
                <div className="text-sm font-mono font-bold text-muted-foreground">{wallet.account_name}</div>
            </CardHeader>

            <CardContent className="p-4 flex-1 flex flex-col gap-4">
                <div className="flex flex-col gap-1">
                    <span className="text-xs text-muted-foreground uppercase tracking-widest">CURRENT_BALANCE</span>
                    <span className="text-2xl font-mono text-foreground">{formatCurrency(wallet.wallet_balance)}</span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col gap-1">
                        <span className="text-xs text-muted-foreground uppercase tracking-widest">UNREALIZED_PNL</span>
                        <span className={wallet.unrealized_pnl >= 0 ? "text-accent font-mono" : "text-destructive font-mono"}>
                            {wallet.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(wallet.unrealized_pnl)}
                        </span>
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs text-muted-foreground uppercase tracking-widest">TOTAL_PNL</span>
                        <span className={wallet.total_realized_pnl >= 0 ? "text-accent font-mono" : "text-destructive font-mono"}>
                            {wallet.total_realized_pnl >= 0 ? '+' : ''}{formatCurrency(wallet.total_realized_pnl)}
                        </span>
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-4 border-t border-border/50">
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-sm font-mono text-foreground">{wallet.total_strategies}</span>
                        <span className="text-xs text-muted-foreground uppercase tracking-wider text-center">STRATEGIES</span>
                    </div>
                    <div className="flex flex-col items-center gap-1 border-x border-border/50">
                        <span className="text-sm font-mono text-foreground">{wallet.active_positions}</span>
                        <span className="text-xs text-muted-foreground uppercase tracking-wider text-center">POSITIONS</span>
                    </div>
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-sm font-mono text-foreground">{wallet.open_orders}</span>
                        <span className="text-xs text-muted-foreground uppercase tracking-wider text-center">ORDERS</span>
                    </div>
                </div>
            </CardContent>

            <CardFooter className="p-4 border-t border-border bg-background/30 flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger render={<Button variant="cyber-outline" size="sm" />}>
                        EDIT_KEYS
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>EDIT_API_KEYS</DialogTitle>
                        </DialogHeader>
                        <div className="flex flex-col gap-4 py-4">
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">API_KEY</label>
                                <Input
                                    placeholder="••••••••"
                                    value={apiKey}
                                    onChange={(e) => setApiKey(e.target.value)}
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">API_SECRET</label>
                                <Input
                                    placeholder="••••••••"
                                    type="password"
                                    value={apiSecret}
                                    onChange={(e) => setApiSecret(e.target.value)}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button
                                variant="cyber-glitch"
                                onClick={handleSave}
                                disabled={isPending || !apiKey || !apiSecret}
                            >
                                {isPending ? 'SAVING...' : 'SAVE'}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </CardFooter>
        </Card>
    )
}

function AssignStrategiesDialog() {
    const [open, setOpen] = useState(false)
    const { data: unassignedStrategies, isLoading: isLoadingStrategies } = useUnassignedStrategies()
    const { mutate: assignStrategy, isPending: isAssigning, isSuccess, isError, reset } = useAssignStrategy()

    const [selectedStrategyName, setSelectedStrategyName] = useState<string>('')
    const [allowExecution, setAllowExecution] = useState(false)
    const [allowSimulation, setAllowSimulation] = useState(false)

    const handleStrategyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const name = e.target.value
        setSelectedStrategyName(name)
        reset()
        const strategy = unassignedStrategies?.find((s: any) => s.strategy_name === name)
        if (strategy) {
            setAllowExecution(strategy.allow_execution)
            setAllowSimulation(strategy.allow_simulation)
        } else {
            setAllowExecution(false)
            setAllowSimulation(false)
        }
    }

    const handleAssign = () => {
        if (!selectedStrategyName) return
        assignStrategy({
            strategy_name: selectedStrategyName,
            allow_execution: allowExecution,
            allow_simulation: allowSimulation
        }, {
            onSuccess: () => {
                setSelectedStrategyName('')
            }
        })
    }

    return (
        <Dialog open={open} onOpenChange={(newOpen) => {
            setOpen(newOpen)
            if (!newOpen) {
                setSelectedStrategyName('')
                reset()
            }
        }}>
            <DialogTrigger render={<Button variant="cyber-glitch" size="sm" />}>
                ASSIGN_STRATEGIES
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>ASSIGN_STRATEGIES</DialogTitle>
                </DialogHeader>
                <div className="flex flex-col gap-4 py-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">SELECT_STRATEGY</label>
                        <select
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 font-mono"
                            value={selectedStrategyName}
                            onChange={handleStrategyChange}
                            disabled={isLoadingStrategies || isAssigning}
                        >
                            <option value="">-- Select Strategy --</option>
                            {unassignedStrategies?.map((s: any) => (
                                <option key={s.strategy_name} value={s.strategy_name}>
                                    {s.strategy_name} ({s.symbol} - {s.exchange})
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedStrategyName && (
                        <>
                            <div className="flex items-center justify-between">
                                <label className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">ALLOW_EXECUTION</label>
                                <input
                                    type="checkbox"
                                    className="w-5 h-5 accent-accent"
                                    checked={allowExecution}
                                    onChange={(e) => setAllowExecution(e.target.checked)}
                                    disabled={isAssigning}
                                />
                            </div>
                            <div className="flex items-center justify-between">
                                <label className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">ALLOW_SIMULATION</label>
                                <input
                                    type="checkbox"
                                    className="w-5 h-5 accent-accent"
                                    checked={allowSimulation}
                                    onChange={(e) => setAllowSimulation(e.target.checked)}
                                    disabled={isAssigning}
                                />
                            </div>
                        </>
                    )}

                    {isSuccess && <div className="text-accent text-xs tracking-widest uppercase font-mono mt-2 text-center">STRATEGY_ASSIGNED_SUCCESSFULLY</div>}
                    {isError && <div className="text-destructive text-xs tracking-widest uppercase font-mono mt-2 text-center">FAILED_TO_ASSIGN_STRATEGY</div>}
                </div>
                <DialogFooter>
                    <Button
                        variant="cyber-glitch"
                        onClick={handleAssign}
                        disabled={isAssigning || !selectedStrategyName}
                    >
                        {isAssigning ? 'ASSIGNING...' : 'ASSIGN'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default function WalletsPage() {
    const { data: wallets, isLoading, isError } = useWallets()

    return (
        <PageWrapper
            title="EXCHANGE WALLETS"
            actions={<AssignStrategiesDialog />}
        >
            {isError ? (
                <EmptyState message="FAILED_TO_LOAD_WALLETS" />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {isLoading ? (
                        Array.from({ length: 3 }).map((_, i) => (
                            <Card key={i} className="border-border bg-card cyber-chamfer h-64 animate-pulse" />
                        ))
                    ) : wallets?.map((wallet: any) => (
                        <WalletCard key={wallet.account_name} wallet={wallet} />
                    ))}
                </div>
            )}
        </PageWrapper>
    )
}
