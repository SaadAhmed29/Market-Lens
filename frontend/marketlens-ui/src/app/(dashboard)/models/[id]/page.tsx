'use client'

import { useParams } from 'next/navigation'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useModel } from '@/hooks/useModels'
import { BrainCircuit, Activity } from 'lucide-react'

export default function ModelDetailPage() {
    const params = useParams()
    const { data: model, isLoading } = useModel(params.id as string)

    if (isLoading) {
        return <PageWrapper title="LOADING_MODEL_DATA..."><div/></PageWrapper>
    }

    if (!model) {
        return <PageWrapper title="MODEL_NOT_FOUND"><div/></PageWrapper>
    }

    return (
        <PageWrapper 
            title={`MODEL: ${model.name}`}
            actions={
                <div className="flex gap-2">
                    <Button variant="cyber-outline">RETRAIN_MODEL</Button>
                    <Button variant="cyber-glitch">GENERATE_SIGNALS</Button>
                </div>
            }
        >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Meta Panel */}
                <div className="flex flex-col gap-6">
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-xs font-mono uppercase tracking-widest text-accent flex items-center gap-2">
                                <BrainCircuit className="size-4" /> MODEL_METADATA
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 flex flex-col gap-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TYPE</span>
                                    <Badge variant="outline" className="w-fit">{model.type}</Badge>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TARGET</span>
                                    <span className="text-sm font-mono text-foreground">{model.targetColumn}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">SYMBOL</span>
                                    <span className="text-sm font-mono text-foreground">{model.symbol} ({model.timeframe})</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest">TRAINED_ON</span>
                                    <span className="text-sm font-mono text-foreground">{new Date(model.trainingDate).toLocaleDateString()}</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-xs font-mono uppercase tracking-widest text-secondary flex items-center gap-2">
                                <Activity className="size-4" /> EVALUATION_METRICS
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="flex flex-col divide-y divide-border">
                                {Object.entries(model.evaluation.mlMetrics).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between p-3 text-sm font-mono hover:bg-muted/30 transition-colors">
                                        <span className="text-muted-foreground">{key}</span>
                                        <span className={key === model.primaryMetricName ? 'text-accent font-bold' : 'text-foreground'}>{value}</span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <Card className="border-border bg-card cyber-chamfer">
                        <CardHeader className="py-3 border-b border-border bg-background/50">
                            <CardTitle className="text-xs font-mono uppercase tracking-widest text-foreground">TRAINING_PIPELINE</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 grid grid-cols-2 gap-6">
                            
                            <div className="flex flex-col gap-4 border-r border-border/50 pr-4">
                                <h3 className="text-sm font-mono text-muted-foreground border-b border-border pb-2">ALGORITHM & PARAMS</h3>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">ALGORITHM</span>
                                    <span className="text-sm font-mono text-accent">{model.trainingInfo.algorithm}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">HYPERPARAMETERS</span>
                                    <pre className="text-xs font-mono text-foreground bg-background p-2 border border-border cyber-chamfer-sm overflow-x-auto">
                                        {JSON.stringify(model.trainingInfo.hyperparameters, null, 2)}
                                    </pre>
                                </div>
                            </div>
                            
                            <div className="flex flex-col gap-4">
                                <h3 className="text-sm font-mono text-muted-foreground border-b border-border pb-2">PREPROCESSING</h3>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">SCALING</span>
                                    <span className="text-sm font-mono text-foreground">{model.trainingInfo.scaling}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">STATIONARITY</span>
                                    <span className="text-sm font-mono text-foreground">{model.trainingInfo.stationarity}</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-widest block mb-1">FEATURES ({model.features.length})</span>
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {model.features.map(f => (
                                            <span key={f} className="text-[10px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 cyber-chamfer-sm border border-border">{f}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                            
                        </CardContent>
                    </Card>
                    
                    <Card className="border-border bg-card cyber-chamfer" variant="holographic">
                        <CardContent className="p-12 text-center flex flex-col items-center justify-center gap-4">
                            <BrainCircuit className="size-12 text-accent/50 animate-pulse" />
                            <div className="text-sm font-mono text-muted-foreground">
                                FEATURE_IMPORTANCE_CHART_PENDING
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </PageWrapper>
    )
}
