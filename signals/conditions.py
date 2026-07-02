import pandas as pd
import yaml

from utils.signal_utils import (
    _apply_persist,
    _op_pattern_match,
    _resolve_operand,
    OHLC_OPERATOR_MAP,
    OPERATOR_MAP,
)

# Core: evaluate a single condition dict

def evaluate_condition(df: pd.DataFrame, condition: dict) -> pd.Series:
    """
    Evaluates a single condition block from config and returns a Boolean Series.

    Condition dict keys:
        left        : column name (str) or scalar
        operator    : one of the supported operator strings
        right       : column name (str) or scalar (not required for pat_* or OHLC operators)
        persist_bars: int (default 0)
    """
    
    left_key    = condition.get('left', '')
    operator    = condition.get('operator', '').strip()
    right_key   = condition.get('right', None)
    persist     = int(condition.get('persist_bars', 0))

    # Pattern match (pat_* prefix on operator or left column name)
    if operator == 'pattern_match' or (isinstance(left_key, str) and left_key.startswith('pat_')):
        result = _op_pattern_match(df, left_key)

    # OHLC-anchored operators (close_above, high_below, etc.)
    elif operator in OHLC_OPERATOR_MAP:
        result = OHLC_OPERATOR_MAP[operator](df, right_key)

    # Standard / cross operators
    elif operator in OPERATOR_MAP:
        left  = _resolve_operand(df, left_key)
        right = _resolve_operand(df, right_key)
        result = OPERATOR_MAP[operator](left, right)

    else:
        raise ValueError(
            f"Unsupported operator '{operator}'. "
            f"Supported: {list(OPERATOR_MAP.keys()) + list(OHLC_OPERATOR_MAP.keys()) + ['pattern_match']}"
        )

    # Fill any NaN produced by shifting (first bar of cross ops) with False
    result = result.fillna(False)

    return _apply_persist(result, persist)



# Public API: evaluate all long/short conditions from strategy config

def evaluate_all_conditions(df: pd.DataFrame, config_path: str, strategy_name: str) -> pd.DataFrame:
    """
    Evaluates all conditions for a given strategy from config.yaml
    and returns a single DataFrame of Boolean columns.

    Parameters
    ----------
    df            : merged OHLCV + indicator DataFrame from main.py
    config_path   : path to config.yaml
    strategy_name : name of the strategy to evaluate (e.g. 'my_strategy')

    Returns
    -------
    pd.DataFrame with index matching df and one Boolean column per condition.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    strategy = config.get(strategy_name)
    if strategy is None:
        raise KeyError(
            f"Strategy '{strategy_name}' not found in config. "
            f"Available strategies: {list(config.keys())}"
        )

    result_cols: dict[str, pd.Series] = {}

    for side in ('long', 'short'):
        side_cfg = strategy.get(side, {})
        conditions = side_cfg.get('conditions', [])

        for i, condition in enumerate(conditions, start=1):
            col_name = f"{side}_cond_{i}"
            try:
                result_cols[col_name] = evaluate_condition(df, condition)
            except (KeyError, ValueError) as e:
                print(f"[conditions] Warning: skipping {col_name} — {e}")
                result_cols[col_name] = pd.Series(False, index=df.index)

    df = pd.DataFrame(result_cols, index=df.index).shift(1)
    df = df.fillna(False)
    return df