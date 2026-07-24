import React from 'react'

interface PageWrapperProps {
    title: string
    children: React.ReactNode
    actions?: React.ReactNode
}

export function PageWrapper({ title, children, actions }: PageWrapperProps) {
    return (
        <main className="flex-1 flex flex-col circuit-bg min-h-0 relative">
            <div className="absolute inset-0 bg-background/80 pointer-events-none" />
            
            <div className="relative z-10 flex-1 flex flex-col h-full overflow-auto">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 md:p-6 border-b border-border bg-background/50 backdrop-blur">
                    <div className="flex flex-col">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-accent text-sm">&gt;</span>
                            <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
                                ROOT / {title.replace(/\s+/g, '_').toUpperCase()}
                            </span>
                        </div>
                        <h1 className="text-2xl sm:text-3xl font-heading font-bold uppercase tracking-wider text-foreground cyber-glitch">
                            {title}
                        </h1>
                    </div>
                    
                    {actions && (
                        <div className="flex items-center gap-3">
                            {actions}
                        </div>
                    )}
                </div>
                
                <div className="flex-1 p-4 md:p-6">
                    <div className="mx-auto w-full max-w-7xl h-full flex flex-col gap-6">
                        {children}
                    </div>
                </div>
            </div>
        </main>
    )
}
