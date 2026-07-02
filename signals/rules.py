import yaml
import numpy as np
import pandas as pd
from signals.conditions import evaluate_all_conditions
from utils.signal_utils import _apply_rule

# Public API

def generate_signals(df: pd.DataFrame, config_path: str, strategy_name: str) -> pd.Series:
    """
    Full pipeline: evaluates conditions then applies the configured rule
    to produce a final signal series.

    Parameters
    ----------
    df            : merged OHLCV + indicator DataFrame from main.py
    config_path   : path to config.yaml
    strategy_name : name of the strategy to run (must exist in config.yaml)

    Returns
    -------
    pd.Series with values:
         1  → Buy
        -1  → Sell
         0  → No Signal
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    strategy = config.get(strategy_name)
    if strategy is None:
        raise KeyError(
            f"Strategy '{strategy_name}' not found in config. "
            f"Available strategies: {list(config.keys())}"
        )

    # evaluate all conditions
    condition_df = evaluate_all_conditions(df, config_path, strategy_name)

    # apply rule per side
    long_signal  = _apply_rule(condition_df, strategy.get('long',  {}), side='long')
    short_signal = _apply_rule(condition_df, strategy.get('short', {}), side='short')

    # combine into final signal — long takes priority if both fire on same bar
    signal = pd.Series(0, index=df.index, name='signal')
    signal[short_signal] = -1
    signal[long_signal]  = 1

    condition_df = condition_df.join(signal)
    
    return condition_df