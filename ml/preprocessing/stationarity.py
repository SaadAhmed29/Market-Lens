"""
Helper functions for stationarity analysis
"""

import pandas as pd
import numpy as np
from ml.preprocessing.stationarity import feature_cols


# Fractional Differencing

def _fracdiff_weights(d: float, threshold: float) -> np.ndarray:
    """Compute fixed-width fractional differencing weights, stopping once
    the absolute weight magnitude drops below `threshold`."""
    weights = [1.0]
    k = 1
    while True:
        w_k = -weights[-1] * (d - k + 1) / k
        if abs(w_k) < threshold:
            break
        weights.append(w_k)
        k += 1
    return np.array(weights)


def fractional_differencing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply fixed-window fractional differencing to each feature column.

    Fractional differencing removes just enough memory from a series to
    make it stationary, while preserving more of its long-term memory
    than a full first difference would (which wipes out all memory).
    d closer to 0 keeps more memory / is less stationary; d closer to 1
    behaves more like a standard first difference.

    Weights depend only on d and the threshold cutoff, not on the data
    itself, so this can be applied independently to train and val (no
    fit-on-train step needed).

    Config params (defaults):
        d (float): Differencing order, in (0, 1).  Default 0.4.
        threshold (float): Minimum absolute weight to keep -- this
            determines the effective window size.  Default 1e-4.
    """
    d: float = 0.4
    threshold: float = 1e-4

    weights = _fracdiff_weights(d, threshold)
    window = len(weights)
    reversed_weights = weights[::-1]

    df = df.copy()
    cols = feature_cols(df)

    for col in cols:
        df[col] = df[col].rolling(window=window, min_periods=window).apply(
            lambda w: np.dot(reversed_weights, w), raw=True
        )

    df.dropna(inplace=True)
    return df