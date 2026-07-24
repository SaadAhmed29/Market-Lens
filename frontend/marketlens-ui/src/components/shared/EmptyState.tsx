import React from 'react'
import { Terminal } from 'lucide-react'

interface EmptyStateProps {
    message?: string
}

export function EmptyState({ message = "NO_DATA_FOUND" }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center p-12 border border-border bg-card cyber-chamfer w-full min-h-[200px]">
            <div className="p-4 rounded-full bg-background mb-4 border border-border">
                <Terminal className="size-6 text-muted-foreground" strokeWidth={1.5} />
            </div>
            <div className="flex items-center gap-2 font-mono text-sm uppercase tracking-widest text-muted-foreground">
                <span className="text-accent">&gt;</span>
                <span className="typewriter-text">{message}</span>
                <span className="inline-block w-2 h-4 bg-accent animate-pulse" />
            </div>
        </div>
    )
}
