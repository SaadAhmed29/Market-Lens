import pandas as pd
from darts import TimeSeries
from ml.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline
from ml.utils.logging import get_logger

logger = get_logger(__name__)

def prepare_timeseries(config: dict):
    """
    Runs preprocessing and converts data to darts TimeSeries objects.
    """
    logger.info("Running preprocessing pipeline")
    train_df, val_df = run_preprocessing_pipeline(config)
    
    if 'date_time' not in train_df.columns:
        train_df = train_df.reset_index(names='date_time' if train_df.index.name != 'date_time' else None)
        if 'date_time' not in train_df.columns and 'index' in train_df.columns:
            train_df.rename(columns={'index': 'date_time'}, inplace=True)
            
    if 'date_time' not in val_df.columns:
        val_df = val_df.reset_index(names='date_time' if val_df.index.name != 'date_time' else None)
        if 'date_time' not in val_df.columns and 'index' in val_df.columns:
            val_df.rename(columns={'index': 'date_time'}, inplace=True)
            
    logger.info("Converting to darts TimeSeries")
    train_ts = TimeSeries.from_dataframe(train_df, time_col='date_time')
    val_ts = TimeSeries.from_dataframe(val_df, time_col='date_time')
    
    target_col = 'target'
    covariate_cols = [c for c in train_df.columns if c not in [target_col, 'date_time']]
    
    logger.info("Separating covariates and target")
    train_series = train_ts[target_col]
    train_covariates = train_ts[covariate_cols]
    
    val_series = val_ts[target_col]
    val_covariates = val_ts[covariate_cols]
    
    return train_series, train_covariates, val_series, val_covariates


def fixed_window_forecasting(model, train_series, val_series, train_covariates, val_covariates, config):
    """
    Uses darts historical_forecasts method on the trained model to generate forecasts 
    over the validation period using a fixed input window.
    """
    logger.info("Starting fixed window forecasting")
    
    # Extract sequence_length
    sequence_length = config.get('sequence_length')
    if sequence_length is None:
        for m_type, m_list in config.get('models', {}).items():
            for m in m_list:
                if 'params' in m and 'sequence_length' in m['params']:
                    sequence_length = m['params']['sequence_length']
                    break
            if sequence_length is not None:
                break
    if sequence_length is None:
        sequence_length = 60 # Default fallback
        
    # Extract horizon
    model_type = config.get('model_type', 'timeseries')
    horizon = config.get('target', {}).get(model_type, [{}])[0].get('horizon', 1)
    
    logger.info(f"Using sequence_length={sequence_length}, horizon={horizon}")
    
    kwargs = {
        'series': val_series,
        'forecast_horizon': horizon,
        'train_length': sequence_length,
        'retrain': False,
        'stride': 1
    }
    
    if getattr(model, 'supports_past_covariates', False):
        logger.info("Model supports past covariates, passing them to historical_forecasts")
        kwargs['past_covariates'] = val_covariates
        
    predictions = model.historical_forecasts(**kwargs)
    logger.info("Forecasting completed successfully")
    
    return predictions
