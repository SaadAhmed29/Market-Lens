'use client'

import React, { useState, useEffect } from 'react'
import { Bell, Search, Terminal } from 'lucide-react'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'

export function Topbar() {
    const [time, setTime] = useState<Date | null>(null)

    useEffect(() => {
        setTime(new Date())
        const timer = setInterval(() => setTime(new Date()), 1000)
        return () => clearInterval(timer)
    }, [])

    return (
        <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-card/80 backdrop-blur px-4 sticky top-0 z-50">
            <SidebarTrigger className="text-muted-foreground hover:text-accent transition-colors" />
            <Separator orientation="vertical" className="h-5" />
            <div className="flex items-center gap-2 text-accent">
                <Terminal className="size-4" strokeWidth={1.5} />
                <span className="text-xs font-mono uppercase tracking-widest hidden sm:inline-block">SYS.STATUS: <span className="animate-pulse">ONLINE</span></span>
            </div>

            <div className="ml-auto flex items-center gap-6">
                <div className="hidden sm:flex items-center text-sm font-mono text-muted-foreground tabular-nums">
                    {time ? time.toISOString().replace('T', ' ').substring(0, 19) + ' UTC' : '...'}
                </div>



                <button
                    type="button"
                    className="relative flex size-8 items-center justify-center border border-border bg-background text-muted-foreground transition-colors hover:text-accent hover:border-accent cyber-chamfer-sm"
                    aria-label="Notifications"
                >
                    <Bell className="size-4" strokeWidth={1.5} />
                    <span className="absolute -top-1 -right-1 size-2 rounded-full bg-destructive animate-pulse" />
                </button>
            </div>
        </header>
    )
}
