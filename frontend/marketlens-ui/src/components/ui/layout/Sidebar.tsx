'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
    Boxes,
    BrainCircuit,
    LayoutDashboard,
    LineChart,
    TerminalSquare,
    Wallet,
    Activity,
    Wrench,
} from 'lucide-react'

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    useSidebar,
} from '@/components/ui/sidebar'

const navItems = [
    { title: 'Dashboard', url: '/', icon: LayoutDashboard },
    { title: 'Strategies', url: '/strategies', icon: LineChart },
    { title: 'Backtests', url: '/backtests', icon: Boxes },
    { title: 'Strategy Builder', url: '/strategy-builder', icon: Wrench },
    { title: 'Wallets', url: '/wallets', icon: Wallet },
    { title: 'Executions', url: '/executions', icon: TerminalSquare },
    { title: 'ML Models', url: '/models', icon: BrainCircuit },
    { title: 'Sentiment', url: '/sentiment', icon: Activity },
]

export function AppSidebar() {
    const pathname = usePathname()
    const { state } = useSidebar()
    const isCollapsed = state === 'collapsed'

    return (
        <Sidebar collapsible="icon" className="border-sidebar-border bg-card">
            <SidebarHeader className="border-b border-sidebar-border py-4">
                <div className="flex items-center gap-3 px-2">
                    <div className="flex size-8 shrink-0 items-center justify-center bg-transparent text-accent" style={{ filter: 'drop-shadow(var(--shadow-neon-sm))' }}>
                        <LineChart className="size-6" strokeWidth={1.5} />
                    </div>
                    {!isCollapsed && (
                        <div className="flex min-w-0 flex-col leading-none">
                            <span className="truncate text-lg font-heading font-bold tracking-widest text-accent cyber-glitch">
                                MARKETLENS
                            </span>
                            <span className="truncate text-xs uppercase tracking-[0.3em] text-muted-foreground mt-1">
                                Trading Terminal
                            </span>
                        </div>
                    )}
                </div>
            </SidebarHeader>

            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel className="text-sm font-mono uppercase tracking-[0.2em] text-muted-foreground mb-2 mt-4">
                        SYSTEMS_NAV
                    </SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu className="gap-1">
                            {navItems.map((item) => {
                                const isActive =
                                    item.url === '/'
                                        ? pathname === '/'
                                        : pathname === item.url ||
                                        pathname.startsWith(`${item.url}/`)

                                return (
                                    <SidebarMenuItem key={item.title}>
                                        <SidebarMenuButton
                                            isActive={isActive}
                                            tooltip={item.title}
                                            className={`h-9 py-2 transition-all duration-200 uppercase font-mono tracking-wider text-xs rounded-none ${isActive ? 'bg-accent/10 text-accent border-l-2 border-accent shadow-[inset_2px_0_0_0_var(--accent)]' : 'text-muted-foreground hover:bg-muted hover:text-foreground border-l-2 border-transparent'}`}
                                            render={
                                                <Link href={item.url} className="flex items-center gap-1">
                                                    <item.icon className={`size-3 ${isActive ? 'drop-shadow-[0_0_5px_currentColor]' : ''}`} strokeWidth={1.5} />
                                                    <span className="flex-1">
                                                        {isActive && !isCollapsed && <span className="mr-2 text-accent">&gt;</span>}
                                                        {item.title}
                                                    </span>
                                                </Link>
                                            }
                                        />
                                    </SidebarMenuItem>
                                )
                            })}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>

            <SidebarFooter className="border-t border-sidebar-border p-4">
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            size="lg"
                            tooltip="SYS_ADMIN"
                            className="cursor-default hover:bg-transparent rounded-none border border-border bg-background cyber-chamfer-sm p-1"
                        >
                            <div className="flex size-8 shrink-0 items-center justify-center bg-muted text-xs font-mono text-accent">
                                AM
                            </div>
                            <div className="flex min-w-0 flex-col leading-tight ml-2">
                                <span className="truncate text-xs font-mono font-bold text-foreground tracking-wide">
                                    main
                                </span>
                                <span className="truncate text-[0.6rem] uppercase font-mono tracking-widest text-accent mt-1">
                                    [ ROOT_ACCESS ]
                                </span>
                            </div>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarFooter>
        </Sidebar>
    )
}
