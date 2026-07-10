import pandas as pd
from utils.ml_utils import merge_ohlcv_indicators, fetch_sentiment_data, map_sentiment_to_ohlcv
from utils.db import get_engine
from data.data_downloader import DataFetcher
from indicators.talib_indicators import TalibIndicators

def build_dataset(config: dict) -> pd.DataFrame:
    """Builds the ML dataset by merging OHLCV data with technical indicators."""
    
    data_cfg = config.get('data', {})
    features_cfg = config.get('features', {})
    
    # OHLCV Data
    ohlcv_df = None
    if data_cfg.get('enabled', False):
        # Fetch the 1m raw data from the DB first
        raw_df, _ = DataFetcher.get_updated_df(
            exchange=data_cfg['exchange'],
            symbol=data_cfg['symbol'],
            start=data_cfg['start_date'],
            end=data_cfg['end_date'],
            time_frame="1m"
        )
        
        # Resample it to the timeframe specified in config (e.g., 1h)
        ohlcv_df, _ = DataFetcher.get_resampled_df(raw_df, data_cfg['timeframe'])
        
        if ohlcv_df is None or ohlcv_df.empty:
            print("Warning: OHLCV DataFrame is empty.")
            return pd.DataFrame()
    else:
        print("Data fetching is disabled in config.")
        return pd.DataFrame()

    # Indicators
    if not features_cfg.get('enabled', False) or 'indicators' not in features_cfg:
        return ohlcv_df

    # Prepare talib config and indicator list according to the TalibIndicators format
    talib_config = {}
    indicator_list = []
    
    for ind_group, items in features_cfg['indicators'].items():
        if ind_group == 'PATTERNS':
            for pat_name, pat_cfg in items.items():
                talib_name = f"CDL{pat_name}"
                # Default inputs for candlestick patterns if not provided
                pat_cfg['inputs'] = pat_cfg.get('inputs', ['open', 'high', 'low', 'close'])
                talib_config[talib_name] = [pat_cfg]
                indicator_list.append(talib_name)
        else:
            for cfg in items:
                # Default inputs for standard indicators if not provided
                cfg['inputs'] = cfg.get('inputs', ['close'])
            talib_config[ind_group] = items
            indicator_list.append(ind_group)

    # Initialize TalibIndicators using __new__ to bypass the internal __init__ data fetch
    indicators = TalibIndicators.__new__(TalibIndicators)
    indicators.df = ohlcv_df
    indicators.config = talib_config
    
    # get_indicators_df returns ohlcv + indicators
    combined_ind = indicators.get_indicators_df(indicator_list)
    
    # Extract only the newly added indicator columns for the indicator_df
    new_cols = [c for c in combined_ind.columns if c not in ohlcv_df.columns]
    indicator_df = combined_ind[new_cols]
    
    # Combine OHLCV + indicators
    final_df = merge_ohlcv_indicators(ohlcv_df, indicator_df)

    # Sentiment
    sentiment_cfg = features_cfg.get('sentiment', {})
    if sentiment_cfg.get('enabled', False):
        start_date = data_cfg['start_date']
        end_date = data_cfg['end_date']
        alias = list(sentiment_cfg.get('aliases', {}).values())[0]

        engine = get_engine()
        sentiment_df = fetch_sentiment_data(start_date, end_date, engine)
        final_df = map_sentiment_to_ohlcv(final_df, sentiment_df, alias)

    return final_df
