"""
Helper functions for preprocessing scalers
"""
import pandas as pd
from ml.preprocessing.stationarity import feature_cols

# MinMax Scaler

def minmax_scaler(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scale features to a fixed [feature_range] interval (default [0, 1]).

    Config params (defaults):
        feature_min (float): Lower bound of output range.  Default 0.0.
        feature_max (float): Upper bound of output range.  Default 1.0.
    """
    from sklearn.preprocessing import MinMaxScaler

    feature_min: float = 0.0
    feature_max: float = 1.0

    train_out = train_df.copy()
    val_out = val_df.copy()
    cols = feature_cols(train_df)

    scaler = MinMaxScaler(feature_range=(feature_min, feature_max))
    train_out[cols] = scaler.fit_transform(train_df[cols])
    val_out[cols] = scaler.transform(val_df[cols])

    import os
    import joblib
    os.makedirs('ml/models/', exist_ok=True)
    joblib.dump(scaler, 'ml/models/minmax_scaler.pkl')

    return train_out, val_out


# MaxAbs Scaler

def maxabs_scaler(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scale each feature by its maximum absolute value, into [-1, 1].

    Preserves sparsity/sign — does not center the data, so it's a good
    fit for already-signed features (e.g. MACD, returns).
    """
    from sklearn.preprocessing import MaxAbsScaler

    train_out = train_df.copy()
    val_out = val_df.copy()
    cols = feature_cols(train_df)

    scaler = MaxAbsScaler()
    train_out[cols] = scaler.fit_transform(train_df[cols])
    val_out[cols] = scaler.transform(val_df[cols])

    import os
    import joblib
    os.makedirs('ml/models/', exist_ok=True)
    joblib.dump(scaler, 'ml/models/maxabs_scaler.pkl')

    return train_out, val_out