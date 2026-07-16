import pandas as pd

def regression_to_signals(predictions: pd.Series, threshold: float = 0.3) -> pd.Series:
    """
    Converts continuous regression output into 1, 0, -1 signals.
    Positive return above threshold -> 1
    Negative return below -threshold -> -1
    Within range -> 0
    Returns a Series with date_time as index.
    """
    signals = pd.Series(0, index=predictions.index, name="signal")
    signals[predictions > threshold] = 1
    signals[predictions < -threshold] = -1
    return signals
