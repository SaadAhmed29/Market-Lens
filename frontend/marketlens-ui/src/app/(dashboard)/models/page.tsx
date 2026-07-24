'use client'

import { useRouter } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { DataTable, Column } from '@/components/shared/DataTable'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useModels } from '@/hooks/useModels'
import { MLModel } from '@/types/model'

export default function ModelsPage() {
    const router = useRouter()
    const { data: models, isLoading } = useModels()

    const columns: Column<MLModel>[] = [
        { header: 'MODEL_NAME', accessorKey: 'name', className: 'text-accent' },
        { header: 'SYMBOL', accessorKey: 'symbol' },
        { header: 'TIMEFRAME', accessorKey: 'timeframe' },
        { 
            header: 'TYPE', 
            cell: (row) => (
                <Badge variant="outline">
                    {row.type}
                </Badge>
            )
        },
        { 
            header: 'PRIMARY_METRIC', 
            cell: (row) => (
                <span className="text-secondary">
                    {row.primaryMetricName}: {row.score.toFixed(3)}
                </span>
            )
        },
        { header: 'TRAINED_ON', cell: (row) => new Date(row.trainingDate).toLocaleDateString(), className: 'text-right' },
    ]

    return (
        <PageWrapper 
            title="ML_MODEL_REGISTRY"
            actions={
                <Button variant="cyber-glitch">TRAIN_NEW_MODEL</Button>
            }
        >
            <div className="flex items-center gap-2 mb-4">
                <span className="text-accent">&gt;</span>
                <h2 className="text-sm font-mono uppercase tracking-widest text-muted-foreground">AVAILABLE_PREDICTORS</h2>
            </div>
            <DataTable 
                data={models || []} 
                columns={columns} 
                isLoading={isLoading}
                onRowClick={(row) => router.push(`/models/${row.id}`)}
                emptyMessage="NO_MODELS_FOUND"
            />
        </PageWrapper>
    )
}
