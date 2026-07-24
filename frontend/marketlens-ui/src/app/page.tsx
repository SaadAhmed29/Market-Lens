import { ArrowDownRight, ArrowUpRight, Bell, Search } from 'lucide-react'

import { AppSidebar } from '@/components/ui/layout/Sidebar'
import { Separator } from '@/components/ui/separator'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'

const stats = [
  { label: 'Portfolio Value', value: '$248,190.42', change: '+4.21%', up: true },
  { label: 'Daily P&L', value: '+$5,204.10', change: '+2.14%', up: true },
  { label: 'Open Positions', value: '18', change: '-3.02%', up: false },
  { label: 'Win Rate', value: '67.4%', change: '+1.08%', up: true },
]

const positions = [
  { symbol: 'BTC-USD', side: 'Long', size: '2.40', pnl: '+$8,412', up: true },
  { symbol: 'ETH-USD', side: 'Long', size: '31.5', pnl: '+$2,190', up: true },
  { symbol: 'SOL-USD', side: 'Short', size: '480', pnl: '-$640', up: false },
  { symbol: 'AAPL', side: 'Long', size: '150', pnl: '+$1,024', up: true },
  { symbol: 'NVDA', side: 'Short', size: '90', pnl: '-$318', up: false },
]

export default function Page() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border px-4">
          <SidebarTrigger className="text-muted-foreground" />
          <Separator orientation="vertical" className="h-5" />
          <div className="flex flex-col leading-none">
            <h1 className="text-sm font-semibold">Dashboard</h1>
            <p className="text-xs text-muted-foreground">
              Live market overview
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5 text-sm text-muted-foreground sm:flex">
              <Search className="size-4" />
              <span>Search markets</span>
            </div>
            <button
              type="button"
              className="flex size-9 items-center justify-center rounded-md border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
              aria-label="Notifications"
            >
              <Bell className="size-4" />
            </button>
          </div>
        </header>

        <main className="flex flex-1 flex-col gap-6 p-4 md:p-6">
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4"
              >
                <span className="text-xs font-medium text-muted-foreground">
                  {stat.label}
                </span>
                <span className="text-2xl font-semibold tracking-tight">
                  {stat.value}
                </span>
                <span
                  className={`flex items-center gap-1 text-xs font-medium ${stat.up ? 'text-primary' : 'text-destructive'
                    }`}
                >
                  {stat.up ? (
                    <ArrowUpRight className="size-3.5" />
                  ) : (
                    <ArrowDownRight className="size-3.5" />
                  )}
                  {stat.change}
                </span>
              </div>
            ))}
          </section>

          <section className="rounded-lg border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold">Open Positions</h2>
              <span className="text-xs text-muted-foreground">
                Updated just now
              </span>
            </div>
            <div className="divide-y divide-border">
              <div className="grid grid-cols-4 px-4 py-2 text-xs font-medium text-muted-foreground">
                <span>Symbol</span>
                <span>Side</span>
                <span>Size</span>
                <span className="text-right">Unrealized P&L</span>
              </div>
              {positions.map((pos) => (
                <div
                  key={pos.symbol}
                  className="grid grid-cols-4 items-center px-4 py-3 text-sm"
                >
                  <span className="font-medium font-mono">{pos.symbol}</span>
                  <span
                    className={
                      pos.side === 'Long' ? 'text-primary' : 'text-muted-foreground'
                    }
                  >
                    {pos.side}
                  </span>
                  <span className="font-mono text-muted-foreground">
                    {pos.size}
                  </span>
                  <span
                    className={`text-right font-mono font-medium ${pos.up ? 'text-primary' : 'text-destructive'
                      }`}
                  >
                    {pos.pnl}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
