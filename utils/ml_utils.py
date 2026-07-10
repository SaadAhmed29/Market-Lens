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
