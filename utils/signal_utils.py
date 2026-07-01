import pandas as pd
import numpy as np


# Conditions Helpers

def _resolve_operand(df: pd.DataFrame, operand) -> pd.Series | float | int:
    """
    Resolves a condition operand to either a Series (if it's a column name)
    or a scalar (if it's a literal number).
    """
    if isinstance(operand, str):
        if operand not in df.columns:
            raise KeyError(f"Operand '{operand}' not found in DataFrame columns: {list(df.columns)}")
        return df[operand]
    # Literal scalar (int or float)
    return float(operand)


def _apply_persist(boolean_series: pd.Series, persist_bars: int) -> pd.Series:
    """
    If a condition is True at bar N, it stays True for the next `persist_bars` bars.
    Uses a rolling max over a window of (persist_bars + 1) so the original True bar
    plus the N following bars are all True.
    """
    if persist_bars <= 0:
        return boolean_series
    return (
        boolean_series.astype(int)
        .rolling(window=persist_bars + 1, min_periods=1)
        .max()
        .astype(bool)
    )


# Operator implementations

def _op_gt(left, right) -> pd.Series:
    return left > right

def _op_gte(left, right) -> pd.Series:
    return left >= right

def _op_lt(left, right) -> pd.Series:
    return left < right

def _op_lte(left, right) -> pd.Series:
    return left <= right

def _op_eq(left, right) -> pd.Series:
    return left == right

def _op_neq(left, right) -> pd.Series:
    return left != right

def _op_cross_above(left: pd.Series, right) -> pd.Series:
    """
    True on the bar where left crosses above right:
    previous bar left <= right AND current bar left > right.
    """
    right_series = right if isinstance(right, pd.Series) else pd.Series(right, index=left.index)
    prev_below_or_equal = (left.shift(1) <= right_series.shift(1))
    now_above = (left > right_series)
    return prev_below_or_equal & now_above

def _op_cross_below(left: pd.Series, right) -> pd.Series:
    """
    True on the bar where left crosses below right:
    previous bar left >= right AND current bar left < right.
    """
    right_series = right if isinstance(right, pd.Series) else pd.Series(right, index=left.index)
    prev_above_or_equal = (left.shift(1) >= right_series.shift(1))
    now_below = (left < right_series)
    return prev_above_or_equal & now_below

def _op_close_above(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['close']) > _resolve_operand(df, right)

def _op_close_below(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['close']) < _resolve_operand(df, right)

def _op_open_above(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['open']) > _resolve_operand(df, right)

def _op_open_below(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['open']) < _resolve_operand(df, right)

def _op_high_above(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['high']) > _resolve_operand(df, right)

def _op_high_below(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['high']) < _resolve_operand(df, right)

def _op_low_above(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['low']) > _resolve_operand(df, right)

def _op_low_below(df: pd.DataFrame, right) -> pd.Series:
    return _resolve_operand(df, df['low']) < _resolve_operand(df, right)

def _op_pattern_match(df: pd.DataFrame, left: str) -> pd.Series:
    """
    Pattern recognition columns contain talib output: 100 (bullish), -100 (bearish), 0 (none).
    A pat_* condition is True wherever the column is non-zero.
    """
    col = _resolve_operand(df, left)
    return col != 0


# Operator dispatch table

OPERATOR_MAP = {
    ">":           _op_gt,
    ">=":          _op_gte,
    "<":           _op_lt,
    "<=":          _op_lte,
    "==":          _op_eq,
    "!=":          _op_neq,
    "cross_above": _op_cross_above,
    "cross_below": _op_cross_below,
}

# OHLC-anchored operators: these don't use the generic left/right resolution
OHLC_OPERATOR_MAP = {
    "close_above": _op_close_above,
    "close_below": _op_close_below,
    "open_above":  _op_open_above,
    "open_below":  _op_open_below,
    "high_above":  _op_high_above,
    "high_below":  _op_high_below,
    "low_above":   _op_low_above,
    "low_below":   _op_low_below,
}


# Rule implementations

def _rule_and(condition_df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """All conditions must be True."""
    return condition_df[cols].all(axis=1)


def _rule_or(condition_df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """At least one condition must be True."""
    return condition_df[cols].any(axis=1)


def _rule_majority(condition_df: pd.DataFrame, cols: list[str]) -> pd.Series:
    """More than half of the conditions must be True."""
    total = len(cols)
    return condition_df[cols].sum(axis=1) > (total / 2)


def _rule_weighted(condition_df: pd.DataFrame, cols: list[str], weights: list[float]) -> pd.Series:
    """
    Weighted sum of conditions must exceed the total possible weight / 2.
    Weights are defined per condition in config under 'weight' key.
    Falls back to equal weights if not provided.
    """
    if not weights or len(weights) != len(cols):
        weights = [1.0] * len(cols)

    weight_series = [
        condition_df[col].astype(float) * w
        for col, w in zip(cols, weights)
    ]
    weighted_sum = pd.concat(weight_series, axis=1).sum(axis=1)
    threshold = sum(weights) / 2
    return weighted_sum > threshold


RULE_MAP = {
    "AND":      _rule_and,
    "OR":       _rule_or,
    "MAJORITY": _rule_majority,
    "WEIGHTED": _rule_weighted,
}


# Helper: apply rule to one side (long or short)

def _apply_rule(condition_df: pd.DataFrame, side_cfg: dict, side: str) -> pd.Series:
    """
    Applies the configured rule to the condition columns for one side (long/short).
    Returns a Boolean Series.
    """
    rule = side_cfg.get('rule', 'AND').upper()
    conditions = side_cfg.get('conditions', [])

    cols = [f"{side}_cond_{i}" for i in range(1, len(conditions) + 1)]

    # Filter to only cols that actually exist (some may have been skipped with warning)
    cols = [c for c in cols if c in condition_df.columns]

    if not cols:
        return pd.Series(False, index=condition_df.index)

    if rule not in RULE_MAP:
        raise ValueError(
            f"Unsupported rule '{rule}' for side '{side}'. "
            f"Supported rules: {list(RULE_MAP.keys())}"
        )

    if rule == "WEIGHTED":
        weights = [float(c.get('weight', 1.0)) for c in conditions]
        return _rule_weighted(condition_df, cols, weights)

    return RULE_MAP[rule](condition_df, cols)
