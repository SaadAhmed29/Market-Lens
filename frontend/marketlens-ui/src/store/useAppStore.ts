import { create } from 'zustand'

interface AppState {
    globalTimeframe: string
    setGlobalTimeframe: (timeframe: string) => void
    
    isBacktestEngineRunning: boolean
    setBacktestEngineRunning: (isRunning: boolean) => void
    
    isLiveExecutionRunning: boolean
    setLiveExecutionRunning: (isRunning: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
    globalTimeframe: '1H',
    setGlobalTimeframe: (timeframe) => set({ globalTimeframe: timeframe }),
    
    isBacktestEngineRunning: true,
    setBacktestEngineRunning: (isRunning) => set({ isBacktestEngineRunning: isRunning }),
    
    isLiveExecutionRunning: true,
    setLiveExecutionRunning: (isRunning) => set({ isLiveExecutionRunning: isRunning })
}))
