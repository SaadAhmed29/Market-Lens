'use client'

import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useModels } from '@/hooks/useModels'
import { EmptyState } from '@/components/shared/EmptyState'

export default function ModelsPage() {
    const router = useRouter()
    const { data: models, isLoading, isError } = useModels()

    if (isError) {
        return (
            <PageWrapper title="ML MODEL REGISTRY">
                <EmptyState message="ERROR: Failed to load models" />
            </PageWrapper>
        )
    }

    const columns: Column<any>[] = [
        { header: 'MODEL_NAME', accessorKey: 'model_name' },
        { header: 'SYMBOL', accessorKey: 'symbol', className: 'text-center' },
        { header: 'TIMEFRAME', accessorKey: 'timeframe', className: 'text-center' },
        {
            header: 'TYPE',
            cell: (row) => (
                <Badge variant="outline" className='text-center'>
                    {row.model_type}
                </Badge>
            )
        },
        {
            header: 'PRIMARY_METRIC',
            cell: (row) => {
                const isRegression = row.model_type === 'regression'
                const score = row.score !== null && row.score !== undefined ? Number(row.score) : null
                const displayScore = score === null || Number.isNaN(score)
                    ? 'N/A'
                    : isRegression
                        ? score.toFixed(4)
                        : `${(score * 100).toFixed(2)}%`

                return (
                    <span className="text-secondary text-center">
                        {row.primary_metric}: {displayScore}
                    </span>
                )
            }
        },
    ]

    return (
        <PageWrapper
            title="ML MODEL REGISTRY"
        >
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">AVAILABLE PREDICTORS</h2>
            </div>
            <DataTable
                data={models || []}
                columns={columns}
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/models/${row.model_name}`)}
                emptyMessage="NO_MODELS_FOUND"
            />
        </PageWrapper>
    )
}
