'use client'

import React from 'react'
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface EquityCurveProps {
    data: any[]
    title?: string
    height?: number
}

export function EquityCurve({ data, title = "EQUITY CURVE", height = 300 }: EquityCurveProps) {
    const values = data.map((d) => d.value).filter((v) => typeof v === 'number' && !isNaN(v))
    const dataMin = values.length ? Math.min(...values) : 0
    const dataMax = values.length ? Math.max(...values) : 0
    const range = dataMax - dataMin
    const padding = range * 0.1 || 50 // fallback if flat/no data
    const yDomain: [number, number] = [dataMin - padding, dataMax + padding]

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardHeader className="py-3 px-4 border-b border-border bg-background/50">
                <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                    <span>&gt;</span> {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6">
                <div style={{ height }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                                </linearGradient>
                                <filter id="neon-glow" x="-20%" y="-20%" width="140%" height="140%">
                                    <feGaussianBlur stdDeviation="2" result="blur" />
                                    <feMerge>
                                        <feMergeNode in="blur" />
                                        <feMergeNode in="SourceGraphic" />
                                    </feMerge>
                                </filter>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                            <XAxis
                                dataKey="date"
                                tick={{ fill: 'var(--muted-foreground)', fontSize: 10, fontFamily: 'monospace' }}
                                tickLine={false}
                                axisLine={{ stroke: 'var(--border)' }}
                                minTickGap={30}
                            />
                            <YAxis
                                domain={yDomain}
                                tick={{ fill: 'var(--muted-foreground)', fontSize: 10, fontFamily: 'monospace' }}
                                tickLine={false}
                                axisLine={{ stroke: 'var(--border)' }}
                                tickFormatter={(val) => `$${Math.round(val).toLocaleString()}`}
                                allowDecimals={false}
                                tickCount={6}
                            />
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
                                itemStyle={{ color: 'var(--accent)' }}
                                labelStyle={{ color: 'var(--muted-foreground)', marginBottom: '5px' }}
                            />
                            <Area
                                type="step"
                                dataKey="value"
                                stroke="var(--accent)"
                                strokeWidth={1.5}
                                fillOpacity={1}
                                fill="url(#colorValue)"
                                filter="url(#neon-glow)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
