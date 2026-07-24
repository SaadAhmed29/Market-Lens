import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { MLModel } from '@/types/model'

const MOCK_MODELS: MLModel[] = [
    {
        id: 'ml-1',
        name: 'BTC_PRICE_PREDICTOR_V4',
        type: 'TIMESERIES',
        symbol: 'BTC-USD',
        timeframe: '1H',
        trainingDate: '2026-07-20T10:00:00Z',
        primaryMetricName: 'RMSE',
        score: 124.5,
        dataset: {
            exchange: 'BINANCE',
            startDate: '2024-01-01',
            endDate: '2026-01-01',
            trainValSplit: '80/20'
        },
        features: ['close', 'volume', 'rsi_14', 'macd', 'bollinger_w'],
        targetColumn: 'target_return_1h',
        trainingInfo: {
            algorithm: 'LightGBM',
            hyperparameters: { learning_rate: 0.05, num_leaves: 31 },
            preprocessing: 'StandardScaler',
            scaling: 'MinMax',
            stationarity: 'Fractional Differentiation'
        },
        evaluation: {
            mlMetrics: { RMSE: 124.5, MAE: 89.2, R2: 0.84 },
            backtestMetrics: { Sharpe: 2.1, MaxDD: 14.2, WinRate: 58.5 }
        }
    },
    {
        id: 'ml-2',
        name: 'ETH_DIRECTION_CLASSIFIER',
        type: 'CLASSIFIER',
        symbol: 'ETH-USD',
        timeframe: '4H',
        trainingDate: '2026-07-22T14:30:00Z',
        primaryMetricName: 'F1_SCORE',
        score: 0.68,
        dataset: {
            exchange: 'KRAKEN',
            startDate: '2023-01-01',
            endDate: '2025-12-31',
            trainValSplit: '75/25'
        },
        features: ['returns_1', 'returns_2', 'returns_3', 'volatility_20'],
        targetColumn: 'direction_up',
        trainingInfo: {
            algorithm: 'RandomForest',
            hyperparameters: { n_estimators: 200, max_depth: 10 },
            preprocessing: 'RobustScaler',
            scaling: 'None',
            stationarity: 'Log Returns'
        },
        evaluation: {
            mlMetrics: { F1_SCORE: 0.68, ACCURACY: 0.65, PRECISION: 0.69 },
            backtestMetrics: { Sharpe: 1.4, MaxDD: 22.1, WinRate: 55.0 }
        }
    }
]

export function useModels() {
    return useQuery({
        queryKey: ['models'],
        queryFn: async () => {
            try {
                const { data } = await api.get('/models')
                return data as MLModel[]
            } catch (err) {
                console.warn('Backend unavailable, using mock data for ML models')
                return MOCK_MODELS
            }
        }
    })
}

export function useModel(id: string) {
    return useQuery({
        queryKey: ['model', id],
        queryFn: async () => {
            try {
                const { data } = await api.get(`/models/${id}`)
                return data as MLModel
            } catch (err) {
                console.warn(`Backend unavailable, using mock data for ML model ${id}`)
                return MOCK_MODELS.find(m => m.id === id) || MOCK_MODELS[0]
            }
        },
        enabled: !!id,
    })
}
