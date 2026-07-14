"""
Helper Functions for model training and evaluation.
"""

import pandas as pd
import numpy as np
from preprocess_techs import helpers


# Train / Val Split

def split_train_val(df: pd.DataFrame, train_start: str, train_end: str, val_start: str, val_end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df by date ranges.  Index must be datetime-like."""
    train_df = df.loc[train_start:train_end].copy()
    val_df = df.loc[val_start:val_end].copy()
    return train_df, val_df


# Model training & evaluation

def get_model(model_name: str, model_type: str):
    """Return an untrained sklearn/lightgbm estimator."""

    is_classifier = model_type in ("classification", "timeseries")

    if model_name == "lightgbm":
        from lightgbm import LGBMClassifier, LGBMRegressor
        if is_classifier:
            return LGBMClassifier(verbosity=-1, random_state=42)
        return LGBMRegressor(verbosity=-1, random_state=42)

    if model_name == "svm":
        from sklearn.svm import SVC, SVR
        if is_classifier:
            return SVC(random_state=42)
        return SVR()

    if model_name == "logistic_regression":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(max_iter=1000, random_state=42)

    if model_name == "linear_regression":
        from sklearn.linear_model import LinearRegression
        return LinearRegression()

    raise ValueError(f"Unknown model: {model_name}")


def train_and_evaluate(model_name: str, model_type: str, train_df: pd.DataFrame, val_df: pd.DataFrame, regression_signal_threshold: float = 0.25) -> tuple[object, pd.DataFrame]:
    """Train model, evaluate, return (fitted model, predictions_df).

    For regression models, the continuous output is additionally
    converted into a -1/0/1 signal (based on regression_signal_threshold)
    before being placed into predictions_df, since downstream consumers
    (e.g. the backtest) expect discrete signals rather than raw
    regression output.
    """

    feat_cols = helpers.feature_cols(train_df)

    X_train = train_df[feat_cols]
    y_train = train_df["target"]
    X_val = val_df[feat_cols]
    y_val = val_df["target"]

    model = get_model(model_name, model_type)
    model.fit(X_train, y_train)

    preds = model.predict(X_val)

    # Metrics
    is_classifier = model_type in ("classification", "timeseries")

    print(f"\n{'=' * 60}")
    print(f"  Model: {model_name}  |  Type: {model_type}")
    print(f"{'=' * 60}")

    if is_classifier:
        from sklearn.metrics import accuracy_score, precision_score
        acc = accuracy_score(y_val, preds)
        # Use weighted average for multi-class safety
        prec = precision_score(y_val, preds, average="weighted", zero_division=0)
        print(f"  Accuracy  : {acc:.4f}")
        print(f"  Precision : {prec:.4f}")
    else:
        from sklearn.metrics import mean_absolute_error, root_mean_squared_error
        mae = mean_absolute_error(y_val, preds)
        rmse = root_mean_squared_error(y_val, preds)
        print(f"  MAE  : {mae:.4f}")
        print(f"  RMSE : {rmse:.4f}")
    print()

    # Convert regression output into a -1/0/1 signal based on threshold
    if not is_classifier:
        signal_preds = np.where(
            preds > regression_signal_threshold, 1,
            np.where(preds < -regression_signal_threshold, -1, 0)
        )
    else:
        signal_preds = preds

    # Build predictions df
    predictions_df = pd.DataFrame(
        {"predictions": signal_preds},
        index=val_df.index,
    )
    predictions_df.index.name = "date_time"

    return model, predictions_df
