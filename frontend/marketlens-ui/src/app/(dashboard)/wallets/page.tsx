'use client'

import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useWallets } from '@/hooks/useWallets'
import { Wallet } from 'lucide-react'

export default function WalletsPage() {
    const { data: wallets, isLoading } = useWallets()

    return (
        <PageWrapper 
            title="EXCHANGE_WALLETS"
            actions={
                <Button variant="cyber-glitch">CONNECT_NEW_EXCHANGE</Button>
            }
        >
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {isLoading ? (
                    Array.from({ length: 3 }).map((_, i) => (
                        <Card key={i} className="border-border bg-card cyber-chamfer h-64 animate-pulse" />
                    ))
                ) : wallets?.map(wallet => (
                    <Card key={wallet.id} className="border-border bg-card cyber-chamfer flex flex-col group/wallet">
                        <CardHeader className="py-4 border-b border-border bg-background/50 flex flex-row items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-muted cyber-chamfer-sm border border-border group-hover/wallet:border-accent transition-colors">
                                    <Wallet className="size-5 text-accent" strokeWidth={1.5} />
                                </div>
                                <div className="flex flex-col">
                                    <CardTitle className="text-sm font-mono uppercase tracking-widest text-foreground">
                                        {wallet.exchangeName}
                                    </CardTitle>
                                    <span className="text-[10px] text-muted-foreground font-mono tracking-widest">{wallet.accountType}</span>
                                </div>
                            </div>
                            <Badge variant={wallet.apiStatus === 'CONNECTED' ? 'cyber-active' : 'cyber-error'}>
                                {wallet.apiStatus}
                            </Badge>
                        </CardHeader>
                        
                        <CardContent className="p-4 flex-1 flex flex-col gap-4">
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-muted-foreground uppercase tracking-widest">CURRENT_BALANCE</span>
                                <span className="text-2xl font-mono text-foreground">${wallet.currentBalance.toLocaleString()}</span>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">UNREALIZED_PNL</span>
                                    <span className={wallet.unrealizedPnl >= 0 ? "text-accent font-mono" : "text-destructive font-mono"}>
                                        {wallet.unrealizedPnl >= 0 ? '+' : ''}${wallet.unrealizedPnl.toLocaleString()}
                                    </span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TOTAL_PNL</span>
                                    <span className={wallet.totalPnl >= 0 ? "text-accent font-mono" : "text-destructive font-mono"}>
                                        {wallet.totalPnl >= 0 ? '+' : ''}${wallet.totalPnl.toLocaleString()}
                                    </span>
                                </div>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-2 pt-4 border-t border-border/50">
                                <div className="flex flex-col items-center gap-1">
                                    <span className="text-sm font-mono text-foreground">{wallet.strategiesAssigned}</span>
                                    <span className="text-[9px] text-muted-foreground uppercase tracking-wider text-center">STRATS</span>
                                </div>
                                <div className="flex flex-col items-center gap-1 border-x border-border/50">
                                    <span className="text-sm font-mono text-foreground">{wallet.activePositionsCount}</span>
                                    <span className="text-[9px] text-muted-foreground uppercase tracking-wider text-center">POSITIONS</span>
                                </div>
                                <div className="flex flex-col items-center gap-1">
                                    <span className="text-sm font-mono text-foreground">{wallet.openOrdersCount}</span>
                                    <span className="text-[9px] text-muted-foreground uppercase tracking-wider text-center">ORDERS</span>
                                </div>
                            </div>
                        </CardContent>
                        
                        <CardFooter className="p-4 border-t border-border bg-background/30 flex gap-2 justify-end">
                            <Button variant="cyber-outline" size="sm">EDIT_KEYS</Button>
                            <Button variant="cyber-destructive" size="sm">REMOVE</Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>
        </PageWrapper>
    )
}
