'use client'

import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useModels } from '@/hooks/useModels'
import { EmptyState } from '@/components/shared/EmptyState'

const MODELS_PAGE_SIZE = 10

export default function ModelsPage() {
    const router = useRouter()
    const { data: models, isLoading, isError } = useModels()

    const [modelsPage, setModelsPage] = useState(1)

    const rawModels = useMemo(() => models || [], [models])

    useEffect(() => {
        setModelsPage(1)
    }, [rawModels])

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
                    ? `${(0.00).toFixed(2)}%`
                    : `${(score * 100).toFixed(2)}%`

                return (
                    <span className="text-secondary text-center">
                        {row.primary_metric}: {displayScore}
                    </span>
                )
            }
        },
    ]

    const modelsTotalPages = Math.max(1, Math.ceil(rawModels.length / MODELS_PAGE_SIZE))
    const modelsCurrentPage = Math.min(modelsPage, modelsTotalPages)
    const paginatedModels = rawModels.slice(
        (modelsCurrentPage - 1) * MODELS_PAGE_SIZE,
        modelsCurrentPage * MODELS_PAGE_SIZE
    )

    return (
        <PageWrapper
            title="ML MODEL REGISTRY"
        >
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">AVAILABLE PREDICTORS</h2>
            </div>
            <DataTable
                data={paginatedModels}
                columns={columns}
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/models/${row.model_name}`)}
                emptyMessage="NO_MODELS_FOUND"
            />

            {rawModels.length > MODELS_PAGE_SIZE && (
                <div className="flex items-center justify-between mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                    <button
                        onClick={() => setModelsPage((p) => Math.max(1, p - 1))}
                        disabled={modelsCurrentPage === 1}
                        className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                    >
                        &lt; PREV
                    </button>
                    <span>
                        PAGE {modelsCurrentPage} / {modelsTotalPages}
                    </span>
                    <button
                        onClick={() => setModelsPage((p) => Math.min(modelsTotalPages, p + 1))}
                        disabled={modelsCurrentPage === modelsTotalPages}
                        className="px-3 py-1.5 border border-border cyber-chamfer disabled:opacity-40 disabled:cursor-not-allowed hover:text-accent hover:border-accent/50 transition-colors"
                    >
                        NEXT &gt;
                    </button>
                </div>
            )}
        </PageWrapper>
    )
}