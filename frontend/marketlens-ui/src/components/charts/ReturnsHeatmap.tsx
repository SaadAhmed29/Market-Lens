'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface ReturnsHeatmapProps {
    data: {
        year: number
        months: (number | null)[] // 0 = Jan, 11 = Dec
        ytd: number
    }[]
    title?: string
}

const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

export function ReturnsHeatmap({ data, title = "MONTHLY-RETURNS HEATMAP" }: ReturnsHeatmapProps) {

    // Helper to determine color based on return value
    const getColorClass = (val: number | null) => {
        if (val === null) return 'bg-muted/20 text-muted-foreground/30'
        if (val === 0) return 'bg-muted text-muted-foreground'
        if (val > 5) return 'bg-accent/40 text-accent font-bold shadow-[0_0_5px_rgba(0,255,136,0.3)]'
        if (val > 0) return 'bg-accent/20 text-accent'
        if (val < -5) return 'bg-destructive/40 text-destructive font-bold shadow-[0_0_5px_rgba(255,51,102,0.3)]'
        if (val < 0) return 'bg-destructive/20 text-destructive'
        return 'bg-muted text-muted-foreground'
    }

    return (
        <Card className="border-border bg-card cyber-chamfer">
            <CardHeader className="py-3 px-4 border-b border-border bg-background/50">
                <CardTitle className="text-xs font-mono uppercase tracking-widest text-[#00d4ff] flex items-center gap-2">
                    <span>&gt;</span> {title}
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 overflow-x-auto">
                <div className="min-w-[700px]">
                    <div className="grid grid-cols-14 gap-1 mb-1">
                        <div className="text-[10px] font-mono text-muted-foreground text-center py-1">YEAR</div>
                        {MONTHS.map(m => (
                            <div key={m} className="text-[10px] font-mono text-muted-foreground text-center py-1">{m}</div>
                        ))}
                        <div className="text-[10px] font-mono text-muted-foreground text-center py-1 border-l border-border pl-1">YTD</div>
                    </div>

                    <div className="flex flex-col gap-1">
                        {data.map((row, i) => (
                            <div key={i} className="grid grid-cols-14 gap-1">
                                <div className="text-xs font-mono text-foreground flex items-center justify-center bg-muted/30">
                                    {row.year}
                                </div>
                                {row.months.map((val, j) => (
                                    <div
                                        key={j}
                                        className={cn(
                                            "text-xs font-mono flex items-center justify-center py-2 transition-colors cursor-default hover:text-[#00d4ff] border border-border/50",
                                            getColorClass(val)
                                        )}
                                        title={val !== null ? `$${val.toFixed(2)}` : 'No data'}
                                    >
                                        {val !== null ? val > 0 ? `+$${val.toFixed(1)}` : `$${val.toFixed(1)}` : '-'}
                                    </div>
                                ))}
                                <div className={cn(
                                    "text-xs font-mono flex items-center justify-center border-l border-border pl-1 font-bold",
                                    row.ytd > 0 ? "text-accent" : row.ytd < 0 ? "text-destructive" : "text-muted-foreground"
                                )}>
                                    {row.ytd > 0 ? `+$${row.ytd.toFixed(1)}` : `$${row.ytd.toFixed(1)}`}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
