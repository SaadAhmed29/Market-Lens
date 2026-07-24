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

interface DrawdownChartProps {
    data: any[]
    title?: string
    height?: number
}

export function DrawdownChart({ data, title = "DRAWDOWN", height = 200 }: DrawdownChartProps) {
    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardHeader className="py-3 px-4 border-b border-border bg-background/50">
                <CardTitle className="text-xs font-mono uppercase tracking-widest text-destructive flex items-center gap-2">
                    <span>&gt;</span> {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-6">
                <div style={{ height }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--destructive)" stopOpacity={0} />
                                    <stop offset="95%" stopColor="var(--destructive)" stopOpacity={0.3} />
                                </linearGradient>
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
                                tick={{ fill: 'var(--muted-foreground)', fontSize: 10, fontFamily: 'monospace' }}
                                tickLine={false}
                                axisLine={{ stroke: 'var(--border)' }}
                                tickFormatter={(val) => `${val}%`}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'var(--background)',
                                    borderColor: 'var(--border)',
                                    borderRadius: '0',
                                    borderWidth: '1px',
                                    fontFamily: 'monospace',
                                    fontSize: '12px',
                                    boxShadow: '0 0 10px rgba(255, 51, 102, 0.2)'
                                }}
                                itemStyle={{ color: 'var(--destructive)' }}
                                labelStyle={{ color: 'var(--muted-foreground)', marginBottom: '5px' }}
                            />
                            <Area
                                type="step"
                                dataKey="value"
                                stroke="var(--destructive)"
                                strokeWidth={1.5}
                                fillOpacity={1}
                                fill="url(#colorDrawdown)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
