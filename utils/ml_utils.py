import yaml
import pandas as pd

def load_ml_config(config_path: str) -> dict:
    """Load and return the ML config YAML as a dict."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def merge_ohlcv_indicators(ohlcv_df: pd.DataFrame, indicator_df: pd.DataFrame) -> pd.DataFrame:
    """Merge OHLCV and indicator dataframes on date_time, dropping NaNs."""
    if ohlcv_df is None or ohlcv_df.empty:
        return indicator_df
    if indicator_df is None or indicator_df.empty:
        return ohlcv_df
        
    combined_df = pd.merge(ohlcv_df, indicator_df, left_index=True, right_index=True, how="inner")
    combined_df.dropna(inplace=True)
    return combined_df

def fetch_sentiment_data(start_date, end_date, engine) -> pd.DataFrame:
    """Queries sentiment_data.cleaned_data for rows where date_time is within range."""
    from sqlalchemy import text
    query = text("""
        SELECT date_time, label 
        FROM sentiment_data.cleaned_data 
        WHERE date_time >= :start_date AND date_time <= :end_date
        ORDER BY date_time ASC
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
    if not df.empty:
        df['date_time'] = pd.to_datetime(df['date_time'], utc=True)
    return df

def map_sentiment_to_ohlcv(ohlcv_df: pd.DataFrame, sentiment_df: pd.DataFrame, alias: str) -> pd.DataFrame:
    """Maps sentiment labels to OHLCV data using nearest date_time matching."""
    if sentiment_df.empty:
        ohlcv_df = ohlcv_df.copy()
        ohlcv_df[alias] = pd.NA
        return ohlcv_df

    sentiment_df = sentiment_df.sort_values('date_time').rename(columns={'label': alias})
    temp_ohlcv = ohlcv_df.reset_index().sort_values('date_time')

    merged = pd.merge_asof(
        temp_ohlcv,
        sentiment_df[['date_time', alias]],
        on='date_time',
        direction='nearest'
    )
    
    merged.set_index('date_time', inplace=True)
    
    # Forward fill any gaps
    merged[alias] = merged[alias].ffill()
    
    # Fill with NULL any rows before the first available sentiment record or after the last one
    first_sentiment_time = sentiment_df['date_time'].min()
    last_sentiment_time = sentiment_df['date_time'].max()
    
    merged.loc[merged.index < first_sentiment_time, alias] = pd.NA
    merged.loc[merged.index > last_sentiment_time, alias] = pd.NA
    
    return merged

