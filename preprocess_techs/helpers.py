"""
Helper functions for preprocessing techniques, stationarity analysis,
and trend preservation methods.
"""

import os
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss as kpss_test, acf
from utils.config import load_config
from preprocess_techs.data_utils import print_table


_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def _get_technique_params(technique_name: str) -> dict:
    """Return the params dict for a given technique from the config.

    Looks through 'techniques', 'stationarity_analysis', and
    'trend_preservation' sections of the config for a matching name.
    Returns an empty dict when the technique has no extra params.
    """
    cfg = load_config(_CONFIG_PATH)
    for section in ("techniques", "stationarity_analysis", "trend_preservation"):
        entries = cfg.get(section, [])
        if entries is None:
            continue
        for entry in entries:
            if entry.get("name") == technique_name:
                params = {k: v for k, v in entry.items() if k != "name"}
                return params
    return {}


EXCLUDE_COLS = {"date_time", "target", "sen_MARKET"}


def feature_cols(df: pd.DataFrame) -> list[str]:
    """Return numeric columns excluding date_time and target."""
    return [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in EXCLUDE_COLS
    ]


# Preprocessing Techniques

def raw_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """Return the DataFrame as-is — serves as the no-op baseline."""
    return df.copy()


def log_returns_rolling_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Convert price columns to log returns, then apply rolling z-score.

    Columns that contain zero or negative values (e.g. oscillators like
    RSI/MACD, or binary pattern flags) can't take a meaningful log return
    — dividing by/into zero or a negative value produces -inf/inf/NaN,
    which then contaminates the whole frame via the rolling window and
    the final dropna(). For those columns, fall back to a plain rolling
    z-score of the raw values instead.

    Config params (defaults):
        window (int): Rolling window size for the z-score.  Default 20.
    """
    params = _get_technique_params("log_returns_rolling_zscore")
    window: int = params.get("window", 20)

    df = df.copy()
    cols = feature_cols(df)

    for col in cols:
        series = df[col]

        if (series <= 0).any():
            # Not eligible for log returns — plain rolling z-score instead.
            roll_mean = series.rolling(window=window, min_periods=1).mean()
            roll_std = series.rolling(window=window, min_periods=1).std()
            roll_std = roll_std.replace(0, np.nan)
            df[col] = (series - roll_mean) / roll_std
            continue

        # Log returns: ln(x_t / x_{t-1})
        log_ret = np.log(series / series.shift(1))

        # Rolling z-score
        roll_mean = log_ret.rolling(window=window, min_periods=1).mean()
        roll_std = log_ret.rolling(window=window, min_periods=1).std()
        roll_std = roll_std.replace(0, np.nan)

        df[col] = (log_ret - roll_mean) / roll_std

    df.dropna(inplace=True)
    return df


def volatility_scaled(df: pd.DataFrame) -> pd.DataFrame:
    """Scale each feature by its rolling volatility (rolling std).

    Config params (defaults):
        window (int): Rolling window for std calculation.  Default 20.
    """
    params = _get_technique_params("volatility_scaled")
    window: int = params.get("window", 20)

    df = df.copy()
    cols = feature_cols(df)

    for col in cols:
        roll_std = df[col].rolling(window=window, min_periods=1).std()
        roll_std = roll_std.replace(0, np.nan)
        df[col] = df[col] / roll_std

    df.dropna(inplace=True)
    return df


# Winsorized Robust (fit on train, apply on val)

def winsorized_robust(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit winsorized_robust on train, apply the same stats to val."""
    params = _get_technique_params("winsorized_robust")
    lower_pct: float = params.get("lower_percentile", 1.0)
    upper_pct: float = params.get("upper_percentile", 99.0)

    train_out = train_df.copy()
    val_out = val_df.copy()

    feat_cols = feature_cols(train_df)

    for col in feat_cols:
        # Compute bounds on train
        lower_bound = np.nanpercentile(train_df[col], lower_pct)
        upper_bound = np.nanpercentile(train_df[col], upper_pct)

        # Clip both
        train_clipped = train_out[col].clip(lower=lower_bound, upper=upper_bound)
        val_clipped = val_out[col].clip(lower=lower_bound, upper=upper_bound)

        # Compute median / IQR on train clipped
        median = train_clipped.median()
        q1 = train_clipped.quantile(0.25)
        q3 = train_clipped.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            iqr = 1.0

        train_out[col] = (train_clipped - median) / iqr
        val_out[col] = (val_clipped - median) / iqr

    return train_out, val_out


def rolling_rank_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform each feature into its percentile rank within a rolling window.

    Output values lie in [0, 1].

    Config params (defaults):
        window (int): Rolling window for rank calculation.  Default 20.
    """
    params = _get_technique_params("rolling_rank_transform")
    window: int = params.get("window", 20)

    df = df.copy()
    cols = feature_cols(df)

    for col in cols:
        series = df[col]
        # For each point, compute the fraction of values in the window that
        # are less than or equal to the current value  →  percentile rank.
        df[col] = series.rolling(window=window, min_periods=1).apply(
            lambda w: pd.Series(w).rank(pct=True).iloc[-1],
            raw=False,
        )

    df.dropna(inplace=True)
    return df


# Sklearn-based Scalers (fit on train, apply on val)

def standard_scaler(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Standardize features by removing the mean and scaling to unit variance.

    (x - mean) / std, computed on train and applied to both.
    """
    from sklearn.preprocessing import StandardScaler

    train_out = train_df.copy()
    val_out = val_df.copy()
    cols = feature_cols(train_df)

    scaler = StandardScaler()
    train_out[cols] = scaler.fit_transform(train_df[cols])
    val_out[cols] = scaler.transform(val_df[cols])

    return train_out, val_out


def minmax_scaler(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scale features to a fixed [feature_range] interval (default [0, 1]).

    Config params (defaults):
        feature_min (float): Lower bound of output range.  Default 0.0.
        feature_max (float): Upper bound of output range.  Default 1.0.
    """
    from sklearn.preprocessing import MinMaxScaler

    params = _get_technique_params("minmax_scaler")
    feature_min: float = params.get("feature_min", 0.0)
    feature_max: float = params.get("feature_max", 1.0)

    train_out = train_df.copy()
    val_out = val_df.copy()
    cols = feature_cols(train_df)

    scaler = MinMaxScaler(feature_range=(feature_min, feature_max))
    train_out[cols] = scaler.fit_transform(train_df[cols])
    val_out[cols] = scaler.transform(val_df[cols])

    return train_out, val_out


def robust_scaler(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Scale features using statistics robust to outliers: (x - median) / IQR.

    Config params (defaults):
        quantile_min (float): Lower quantile for IQR.  Default 25.0.
        quantile_max (float): Upper quantile for IQR.  Default 75.0.
    """
    from sklearn.preprocessing import RobustScaler

    params = _get_technique_params("robust_scaler")
    quantile_min: float = params.get("quantile_min", 25.0)
    quantile_max: float = params.get("quantile_max", 75.0)

    train_out = train_df.copy()
    val_out = val_df.copy()
    cols = feature_cols(train_df)

    scaler = RobustScaler(quantile_range=(quantile_min, quantile_max))
    train_out[cols] = scaler.fit_transform(train_df[cols])
    val_out[cols] = scaler.transform(val_df[cols])

    return train_out, val_out


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

    return train_out, val_out


def quantile_transformer(train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map features to a uniform (or normal) distribution using quantiles.

    Non-linear — this can spread out the most frequent values and
    reduces the impact of outliers, at the cost of distorting linear
    relationships between features that were previously correlated.

    Config params (defaults):
        n_quantiles (int): Number of quantiles to compute.  Default 1000
            (automatically capped at the train set size if smaller).
        output_distribution (str): 'uniform' or 'normal'.  Default 'uniform'.
    """
    from sklearn.preprocessing import QuantileTransformer as SkQuantileTransformer

    params = _get_technique_params("quantile_transformer")
    n_quantiles: int = params.get("n_quantiles", 1000)
    output_distribution: str = params.get("output_distribution", "uniform")

    train_out = train_df.copy()
    val_out = val_df.copy()
    cols = feature_cols(train_df)

    # n_quantiles can't exceed the number of train samples
    effective_n_quantiles = min(n_quantiles, len(train_df))

    scaler = SkQuantileTransformer(
        n_quantiles=effective_n_quantiles,
        output_distribution=output_distribution,
        random_state=42,
    )
    train_out[cols] = scaler.fit_transform(train_df[cols])
    val_out[cols] = scaler.transform(val_df[cols])

    return train_out, val_out


# Stationarity Analysis

def adf(df: pd.DataFrame) -> pd.DataFrame:
    """Run the Augmented Dickey-Fuller test on each numeric column.

    Returns a summary DataFrame with columns:
        column, adf_statistic, p_value, result (Stationary / Non-Stationary)

    Config params (defaults):
        significance_level (float): Threshold for p-value.  Default 0.05.
    """
    params = _get_technique_params("adf")
    sig_level: float = params.get("significance_level", 0.05)

    cols = feature_cols(df)
    records: list[dict] = []

    for col in cols:
        series = df[col].dropna()
        if series.empty or series.nunique() < 2:
            records.append({
                "column": col,
                "adf_statistic": np.nan,
                "p_value": np.nan,
                "result": "Insufficient Data",
            })
            continue
        stat, p_value, *_ = adfuller(series, autolag="AIC")
        records.append({
            "column": col,
            "adf_statistic": stat,
            "p_value": p_value,
            "result": "Stationary" if p_value < sig_level else "Non-Stationary",
        })

    return pd.DataFrame(records)


def kpss(df: pd.DataFrame) -> pd.DataFrame:
    """Run the KPSS test on each numeric column.

    Returns a summary DataFrame with columns:
        column, kpss_statistic, p_value, result (Stationary / Non-Stationary)

    Config params (defaults):
        significance_level (float): Threshold for p-value.  Default 0.05.
        regression (str): 'c' (constant) or 'ct' (constant + trend).  Default 'c'.
    """
    params = _get_technique_params("kpss")
    sig_level: float = params.get("significance_level", 0.05)
    regression: str = params.get("regression", "c")

    cols = feature_cols(df)
    records: list[dict] = []

    for col in cols:
        series = df[col].dropna()
        if series.empty or series.nunique() < 2:
            records.append({
                "column": col,
                "kpss_statistic": np.nan,
                "p_value": np.nan,
                "result": "Insufficient Data",
            })
            continue
        stat, p_value, _lags, _crit = kpss_test(series, regression=regression, nlags="auto")
        # KPSS null hypothesis is stationarity — reject (p < α) means
        # the series is *not* stationary.
        records.append({
            "column": col,
            "kpss_statistic": stat,
            "p_value": p_value,
            "result": "Non-Stationary" if p_value < sig_level else "Stationary",
        })

    return pd.DataFrame(records)


def autocorrelation(df: pd.DataFrame) -> pd.DataFrame:
    """Compute autocorrelation for each numeric column up to *nlags* lags.

    Returns a summary DataFrame where each row is a (column, lag) pair
    with its autocorrelation value.

    Config params (defaults):
        nlags (int): Maximum number of lags.  Default 20.
    """
    params = _get_technique_params("autocorrelation")
    nlags: int = params.get("nlags", 20)

    cols = feature_cols(df)
    records: list[dict] = []

    for col in cols:
        series = df[col].dropna()
        if series.empty or series.nunique() < 2:
            continue
        # Ensure nlags does not exceed series length - 1
        effective_lags = min(nlags, len(series) - 1)
        acf_values = acf(series, nlags=effective_lags, fft=True)
        for lag, value in enumerate(acf_values):
            records.append({
                "column": col,
                "lag": lag,
                "autocorrelation": value,
            })

    return pd.DataFrame(records)


# Trend Preservation

def long_term_trend_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Verify that the long-term trend is preserved after transformation.

    Computes a slow rolling mean per column and returns a summary
    DataFrame with the correlation between the original trend component
    and the column values, plus a pass/fail flag.

    Config params (defaults):
        slow_window (int): Window for the slow rolling mean.  Default 100.
        correlation_threshold (float): Minimum acceptable correlation.
            Default 0.5.
    """
    params = _get_technique_params("long_term_trend_retention")
    slow_window: int = params.get("slow_window", 100)
    corr_threshold: float = params.get("correlation_threshold", 0.5)

    cols = feature_cols(df)
    records: list[dict] = []

    for col in cols:
        series = df[col].dropna()
        if len(series) < slow_window:
            records.append({
                "column": col,
                "slow_window": slow_window,
                "trend_correlation": np.nan,
                "result": "Insufficient Data",
            })
            continue

        trend = series.rolling(window=slow_window, min_periods=slow_window).mean().dropna()
        aligned_series = series.loc[trend.index]
        corr = aligned_series.corr(trend)

        records.append({
            "column": col,
            "slow_window": slow_window,
            "trend_correlation": corr,
            "result": "Preserved" if abs(corr) >= corr_threshold else "Not Preserved",
        })

    return pd.DataFrame(records)


def local_trend_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Verify that the short-term (local) trend is preserved after transformation.

    Computes a fast rolling mean per column and returns a summary
    DataFrame with the correlation between the local trend component
    and the column values, plus a pass/fail flag.

    Config params (defaults):
        fast_window (int): Window for the fast rolling mean.  Default 10.
        correlation_threshold (float): Minimum acceptable correlation.
            Default 0.5.
    """
    params = _get_technique_params("local_trend_retention")
    fast_window: int = params.get("fast_window", 10)
    corr_threshold: float = params.get("correlation_threshold", 0.5)

    cols = feature_cols(df)
    records: list[dict] = []

    for col in cols:
        series = df[col].dropna()
        if len(series) < fast_window:
            records.append({
                "column": col,
                "fast_window": fast_window,
                "trend_correlation": np.nan,
                "result": "Insufficient Data",
            })
            continue

        trend = series.rolling(window=fast_window, min_periods=fast_window).mean().dropna()
        aligned_series = series.loc[trend.index]
        corr = aligned_series.corr(trend)

        records.append({
            "column": col,
            "fast_window": fast_window,
            "trend_correlation": corr,
            "result": "Preserved" if abs(corr) >= corr_threshold else "Not Preserved",
        })

    return pd.DataFrame(records)


# Runner Functions

def run_stationarity(train_df: pd.DataFrame, methods: list[str]) -> None:
    for method_name in methods:
        func = globals()[method_name]
        summary = func(train_df)
        print_table(f"Stationarity — {method_name.upper()}", summary)


def run_trend_preservation(train_df: pd.DataFrame, methods: list[str]) -> None:
    for method_name in methods:
        func = globals()[method_name]
        summary = func(train_df)
        # Normalise the result column for display
        if "result" in summary.columns:
            summary["trend_retained"] = summary["result"].apply(
                lambda r: "Yes" if r == "Preserved" else "No"
            )
            display_cols = ["column", "trend_retained"]
            extra = [c for c in summary.columns if c not in ("column", "result", "trend_retained")]
            display_cols = ["column"] + extra + ["trend_retained"]
            summary = summary[display_cols]
        print_table(f"Trend Preservation — {method_name}", summary)
