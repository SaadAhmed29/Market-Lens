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
            
            <div className="ml-auto flex items-center gap-4">
                <div className="hidden sm:flex items-center text-xs font-mono text-muted-foreground tabular-nums">
                    {time ? time.toISOString().replace('T', ' ').substring(0, 19) + ' UTC' : '...'}
                </div>
                
                <div className="relative group hidden md:block">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within:text-accent transition-colors" strokeWidth={1.5} />
                    <input 
                        type="text" 
                        placeholder="Search markets..." 
                        className="h-8 w-64 rounded-none border border-border bg-background/50 pl-9 pr-3 text-xs font-mono uppercase tracking-wider text-foreground placeholder:text-muted-foreground/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent cyber-chamfer-sm transition-all"
                    />
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
