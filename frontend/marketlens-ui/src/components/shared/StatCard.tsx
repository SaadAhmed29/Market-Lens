import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
    label: string
    value: string | number
    change?: string
    isUp?: boolean
    icon?: React.ReactNode
    className?: string
}

export function StatCard({ label, value, change, isUp, icon, className }: StatCardProps) {
    return (
        <Card className={cn("relative overflow-hidden group/stat border-border", className)}>
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover/stat:opacity-30 group-hover/stat:text-accent transition-all duration-300">
                {icon}
            </div>

            <CardContent className="p-4 flex flex-col justify-between h-full relative z-10">
                <div className="flex flex-col gap-1">
                    <span className="text-sm font-bold font-mono uppercase tracking-[0.2em] text-muted-foreground flex items-center justify-center gap-1">
                        <span className="text-accent">&gt;</span> {label}
                    </span>
                    <span className="text-2xl font-mono tracking-tight text-center mt-1">
                        {value}
                    </span>
                </div>

                {change && (
                    <div className="mt-4 text-center flex items-center justify-between">
                        <span
                            className={cn(
                                "flex items-center gap-1 text-[0.65rem] font-mono tracking-widest uppercase",
                                isUp ? "text-accent drop-shadow-[var(--shadow-neon-sm)]" : "text-destructive"
                            )}
                        >
                            {isUp ? (
                                <ArrowUpRight className="size-3" strokeWidth={2} />
                            ) : (
                                <ArrowDownRight className="size-3" strokeWidth={2} />
                            )}
                            {change}
                        </span>

                        {/* Decorative bar */}
                        <div className="h-0.5 w-12 bg-muted overflow-hidden flex">
                            <div
                                className={cn("h-full", isUp ? "bg-accent" : "bg-destructive")}
                                style={{ width: `${Math.random() * 60 + 20}%` }}
                            />
                        </div>
                    </div>
                )}
            </CardContent>

            {/* Hover effect gradient */}
            <div className="absolute -inset-px opacity-0 group-hover/stat:opacity-100 transition-opacity duration-300 pointer-events-none rounded-[inherit]"
                style={{
                    background: 'radial-gradient(circle at top right, rgba(0, 255, 136, 0.1), transparent 70%)'
                }}
            />
        </Card>
    )
}
