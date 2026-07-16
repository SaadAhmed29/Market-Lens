import pandas as pd
from ml.data_formation import build_dataset
from ml.preprocessing.scalars import minmax_scaler, maxabs_scaler
from ml.preprocessing.stationarity import fractional_differencing
from ml.utils.logging import get_logger

logger = get_logger(__name__)

def run_preprocessing_pipeline(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Runs the full preprocessing pipeline:
    1. Builds dataset using config
    2. Drops sen_MARKET if it exists
    3. Splits into train and val
    4. Applies scaling based on model_type
    5. Applies fractional differencing
    """

    # Build dataset
    df = build_dataset(config)
    
    # Drop sen_MARKET
    if 'sen_MARKET' in df.columns:
        df = df.drop(columns=['sen_MARKET'])
        
    # Split into train and val
    train_start_date = config.get('train_start_date')
    train_end_date = config.get('train_end_date')
    val_start_date = config.get('val_start_date')
    val_end_date = config.get('val_end_date')
    
    if all([train_start_date, train_end_date, val_start_date, val_end_date]):
        if 'date_time' in df.columns:
            date_series = pd.to_datetime(df['date_time'], utc=True)
            train_mask = (date_series >= pd.to_datetime(train_start_date, utc=True)) & (date_series <= pd.to_datetime(train_end_date, utc=True))
            val_mask = (date_series >= pd.to_datetime(val_start_date, utc=True)) & (date_series <= pd.to_datetime(val_end_date, utc=True))
            train_df = df[train_mask].copy()
            val_df = df[val_mask].copy()
        else:
            index_series = pd.to_datetime(df.index, utc=True)
            train_mask = (index_series >= pd.to_datetime(train_start_date, utc=True)) & (index_series <= pd.to_datetime(train_end_date, utc=True))
            val_mask = (index_series >= pd.to_datetime(val_start_date, utc=True)) & (index_series <= pd.to_datetime(val_end_date, utc=True))
            train_df = df[train_mask].copy()
            val_df = df[val_mask].copy()
    else:
        # Fallback to an 80/20 chronological split if not explicitly provided
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx].copy()
        val_df = df.iloc[split_idx:].copy()
        
    # Apply scaling
    model_type = config.get('model_type', 'classification')
    
    logger.info(f"Selected scaling method for model_type: {model_type}")
    if model_type == 'classification':
        train_df, val_df = minmax_scaler(train_df, val_df)
        logger.debug("Fitted minmax_scaler")
    elif model_type in ['regression', 'timeseries']:
        train_df, val_df = maxabs_scaler(train_df, val_df)
        logger.debug("Fitted maxabs_scaler")
        
    # Apply fractional differencing
    logger.debug("Applying fractional differencing...")
    train_df = fractional_differencing(train_df)
    val_df = fractional_differencing(val_df)
    
    logger.info(f"Train shape: {train_df.shape}, Val shape: {val_df.shape} after preprocessing")
    return train_df, val_df


if __name__ == "__main__":
    from utils.config import load_config
    config = load_config("ml/config.yaml")
    train_df, val_df = run_preprocessing_pipeline(config)
    print(train_df.head())
    print(train_df.shape)
    print(val_df.head())
    print(val_df.shape)