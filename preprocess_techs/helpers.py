"""
Helper functions for preprocessing techniques, stationarity analysis,
and trend preservation methods.
"""

import os
import numpy as np
import pandas as pd
import yaml
from statsmodels.tsa.stattools import adfuller, kpss as kpss_test, acf


_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def _load_config() -> dict:
    """Load the preprocess_techs config YAML."""
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def _get_technique_params(technique_name: str) -> dict:
    """Return the params dict for a given technique from the config.

    Looks through 'techniques', 'stationarity_analysis', and
    'trend_preservation' sections of the config for a matching name.
    Returns an empty dict when the technique has no extra params.
    """
    cfg = _load_config()
    for section in ("techniques", "stationarity_analysis", "trend_preservation"):
        entries = cfg.get(section, [])
        if entries is None:
            continue
        for entry in entries:
            if entry.get("name") == technique_name:
                params = {k: v for k, v in entry.items() if k != "name"}
                return params
    return {}



_EXCLUDE_COLS = {"date_time", "target"}


def _feature_cols(df: pd.DataFrame) -> list[str]:
    """Return numeric columns excluding date_time and target."""
    return [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in _EXCLUDE_COLS
    ]


# Preprocessing Techniques

def raw_baseline(df: pd.DataFrame) -> pd.DataFrame:
    """Return the DataFrame as-is — serves as the no-op baseline."""
    return df.copy()


def log_returns_rolling_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Convert price columns to log returns, then apply rolling z-score.

    Config params (defaults):
        window (int): Rolling window size for the z-score.  Default 20.
    """
    params = _get_technique_params("log_returns_rolling_zscore")
    window: int = params.get("window", 20)

    df = df.copy()
    cols = _feature_cols(df)

    for col in cols:
        # Log returns: ln(x_t / x_{t-1})
        log_ret = np.log(df[col] / df[col].shift(1))

        # Rolling z-score
        roll_mean = log_ret.rolling(window=window, min_periods=1).mean()
        roll_std = log_ret.rolling(window=window, min_periods=1).std()
        # Avoid division by zero — replace 0 std with NaN then forward-fill
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
    cols = _feature_cols(df)

    for col in cols:
        roll_std = df[col].rolling(window=window, min_periods=1).std()
        roll_std = roll_std.replace(0, np.nan)
        df[col] = df[col] / roll_std

    df.dropna(inplace=True)
    return df


def winsorized_robust(df: pd.DataFrame) -> pd.DataFrame:
    """Clip outliers at percentile bounds then apply robust scaling.

    Robust scaling: (x - median) / IQR

    Config params (defaults):
        lower_percentile (float): Lower clip bound.  Default 1.0.
        upper_percentile (float): Upper clip bound.  Default 99.0.
    """
    params = _get_technique_params("winsorized_robust")
    lower_pct: float = params.get("lower_percentile", 1.0)
    upper_pct: float = params.get("upper_percentile", 99.0)

    df = df.copy()
    cols = _feature_cols(df)

    for col in cols:
        lower_bound = np.nanpercentile(df[col], lower_pct)
        upper_bound = np.nanpercentile(df[col], upper_pct)
        clipped = df[col].clip(lower=lower_bound, upper=upper_bound)

        median = clipped.median()
        q1 = clipped.quantile(0.25)
        q3 = clipped.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            iqr = 1.0  # Prevent division by zero

        df[col] = (clipped - median) / iqr

    return df


def rolling_rank_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Transform each feature into its percentile rank within a rolling window.

    Output values lie in [0, 1].

    Config params (defaults):
        window (int): Rolling window for rank calculation.  Default 20.
    """
    params = _get_technique_params("rolling_rank_transform")
    window: int = params.get("window", 20)

    df = df.copy()
    cols = _feature_cols(df)

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

    cols = _feature_cols(df)
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

    cols = _feature_cols(df)
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

    cols = _feature_cols(df)
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
            Default 0.7.
    """
    params = _get_technique_params("long_term_trend_retention")
    slow_window: int = params.get("slow_window", 100)
    corr_threshold: float = params.get("correlation_threshold", 0.7)

    cols = _feature_cols(df)
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
            Default 0.7.
    """
    params = _get_technique_params("local_trend_retention")
    fast_window: int = params.get("fast_window", 10)
    corr_threshold: float = params.get("correlation_threshold", 0.7)

    cols = _feature_cols(df)
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
