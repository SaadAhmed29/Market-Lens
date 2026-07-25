import React from 'react'
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table'
import { EmptyState } from '@/components/shared/EmptyState'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { cn } from '@/lib/utils'

export interface Column<T> {
    header: string
    accessorKey?: keyof T
    cell?: (item: T) => React.ReactNode
    className?: string
    headerClassName?: string
}

interface DataTableProps<T> {
    data: T[]
    columns: Column<T>[]
    isLoading?: boolean
    emptyMessage?: string
    onRowClick?: (item: T) => void
    className?: string
}

export function DataTable<T>({
    data,
    columns,
    isLoading,
    emptyMessage = "NO_DATA_FOUND",
    onRowClick,
    className
}: DataTableProps<T>) {
    if (isLoading) {
        return (
            <div className="flex justify-center items-center p-12 w-full border border-border cyber-chamfer bg-card">
                <LoadingSpinner />
            </div>
        )
    }

    if (!data || data.length === 0) {
        return <EmptyState message={emptyMessage} />
    }

    return (
        <div className={cn("rounded-none border border-border bg-card cyber-chamfer overflow-hidden", className)}>
            <div className="overflow-x-auto">
                <Table>
                    <TableHeader className="bg-background/80">
                        <TableRow className="border-b-border hover:bg-transparent">
                            {columns.map((col, i) => (
                                <TableHead
                                    key={i}
                                    className={cn(
                                        "px-4 font-bold text-sm uppercase tracking-widest text-muted-foreground",
                                        col.headerClassName ?? col.className
                                    )}
                                >
                                    {col.header}
                                </TableHead>
                            ))}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.map((row, rowIndex) => (
                            <TableRow
                                key={rowIndex}
                                onClick={() => onRowClick?.(row)}
                                className={cn(
                                    "border-b-border group transition-all duration-200",
                                    onRowClick ? "cursor-pointer hover:bg-accent/5 hover:border-l-2 hover:border-l-accent" : ""
                                )}
                            >
                                {columns.map((col, colIndex) => (
                                    <TableCell
                                        key={colIndex}
                                        className={cn(
                                            "px-4 py-3 font-mono text-sm group-hover:text-foreground transition-colors",
                                            col.className
                                        )}
                                    >
                                        {col.cell ? col.cell(row) : col.accessorKey ? String(row[col.accessorKey]) : null}
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}