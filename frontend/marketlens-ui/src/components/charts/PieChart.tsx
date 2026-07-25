'use client'

import React from 'react'
import {
    Cell,
    Pie,
    PieChart as RechartsPieChart,
    ResponsiveContainer,
    Tooltip
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface PieChartProps {
    winRate: number // expects a fraction, e.g. 0.36 for 36%
    title?: string
    height?: number
}

export function PieChart({ winRate, title = "WIN / LOSS", height = 240 }: PieChartProps) {
    const safeWinRate = typeof winRate === 'number' && !isNaN(winRate) ? winRate : 0
    const winPct = Math.max(0, Math.min(1, safeWinRate)) * 100
    const lossPct = 100 - winPct

    const data = [
        { name: 'WIN', value: winPct },
        { name: 'LOSS', value: lossPct },
    ]

    const COLORS = ['var(--accent)', 'var(--destructive)']

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardHeader className="py-3 px-4 border-b border-border bg-background/50">
                <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                    <span>&gt;</span> {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6">
                <div style={{ height }} className="relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <RechartsPieChart>
                            <defs>
                                <filter id="pie-neon-glow" x="-20%" y="-20%" width="140%" height="140%">
                                    <feGaussianBlur stdDeviation="2" result="blur" />
                                    <feMerge>
                                        <feMergeNode in="blur" />
                                        <feMergeNode in="SourceGraphic" />
                                    </feMerge>
                                </filter>
                            </defs>
                            <Pie
                                data={data}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                innerRadius="60%"
                                outerRadius="85%"
                                startAngle={90}
                                endAngle={-270}
                                paddingAngle={2}
                                stroke="var(--background)"
                                strokeWidth={2}
                                filter="url(#pie-neon-glow)"
                            >
                                {data.map((entry, index) => (
                                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'var(--background)',
                                    borderColor: 'var(--border)',
                                    borderRadius: '0',
                                    borderWidth: '1px',
                                    fontFamily: 'monospace',
                                    fontSize: '12px',
                                    boxShadow: 'var(--shadow-neon-sm)'
                                }}
                                itemStyle={{ color: 'var(--foreground)' }}
                                labelStyle={{ color: 'var(--muted-foreground)', marginBottom: '5px' }}
                            />
                        </RechartsPieChart>
                    </ResponsiveContainer>

                    {/* Center label */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                        <span className="text-2xl font-mono font-bold text-accent tracking-tight">
                            {winPct.toFixed(1)}%
                        </span>
                        <span className="text-[0.6rem] font-mono uppercase tracking-widest text-muted-foreground mt-1">
                            WIN RATE
                        </span>
                    </div>
                </div>

                {/* Legend */}
                <div className="flex items-center justify-center gap-6 mt-4 font-mono text-xs uppercase tracking-widest">
                    <div className="flex items-center gap-2">
                        <span className="size-2 bg-accent shadow-[0_0_6px_var(--accent)]" />
                        <span className="text-muted-foreground">WIN</span>
                        <span className="text-accent">{winPct.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="size-2 bg-destructive shadow-[0_0_6px_var(--destructive)]" />
                        <span className="text-muted-foreground">LOSS</span>
                        <span className="text-destructive">{lossPct.toFixed(1)}%</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}