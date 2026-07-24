import React from 'react'
import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
    className?: string
    text?: string
}

export function LoadingSpinner({ className, text = "INITIALIZING..." }: LoadingSpinnerProps) {
    return (
        <div className={cn("flex flex-col items-center justify-center gap-4", className)}>
            <div className="relative size-12">
                <div className="absolute inset-0 rounded-full border-t-2 border-accent animate-spin" style={{ animationDuration: '1s' }} />
                <div className="absolute inset-2 rounded-full border-r-2 border-secondary animate-spin" style={{ animationDuration: '0.7s', animationDirection: 'reverse' }} />
                <div className="absolute inset-4 rounded-full border-b-2 border-primary animate-spin" style={{ animationDuration: '1.2s' }} />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="size-1 bg-accent rounded-full animate-pulse shadow-[var(--shadow-neon-sm)]" />
                </div>
            </div>
            {text && (
                <div className="text-xs font-mono tracking-widest text-accent cyber-glitch">
                    {text}
                </div>
            )}
        </div>
    )
}
