import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <div className="relative flex items-center w-full">
      <span className="absolute left-2 text-accent pointer-events-none select-none font-mono text-sm">&gt;</span>
      <InputPrimitive
        type={type}
        data-slot="input"
        className={cn(
          "h-9 w-full min-w-0 cyber-chamfer-sm border border-border bg-input/50 pl-7 pr-3 py-1 text-sm font-mono transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-accent focus-visible:shadow-[var(--shadow-neon-sm)] focus-visible:ring-1 focus-visible:ring-accent disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-1 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40",
          className
        )}
        {...props}
      />
    </div>
  )
}

export { Input }
