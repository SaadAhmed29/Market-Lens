import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from indicators.talib_indicators import TalibIndicators
from data.data_downloader import DataFetcher
from signals.rules import generate_signals
from utils.config import load_config


def calculate_indicators(exchange: str, symbol: str, start, end, time_frame: str,
                        config: dict, selected_indicators: list[str]) -> pd.DataFrame:
    
    print("Fetching data and initializing indicators...")
    try:
        indicators = TalibIndicators(
            exchange=exchange,
            symbol=symbol,
            start=start,
            end=end,
            time_frame=time_frame,
            config=config
        )
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
    
    print(f"Applying indicators: {selected_indicators}")
    
    # Calling get_indicators_df with selected indicators
    final_df = indicators.get_indicators_df(selected_indicators)

    return final_df


def _extract_indicators_for_strategy(strategy_config: dict, indicator_config: dict) -> list[str]:
    """Find which top-level indicators are needed based on the aliases used in the strategy."""
    vals = set()
    for side in ['long', 'short']:
        if side in strategy_config:
            for cond in strategy_config[side].get('conditions', []):
                vals.add(str(cond.get('left', '')))
                vals.add(str(cond.get('right', '')))
    
    selected = set()
    for ind_name, configs in indicator_config.items():
        for cfg in configs:
            for alias in cfg.get('aliases', {}).values():
                if alias in vals:
                    selected.add(ind_name)
    return list(selected)


# Generate main signals
def get_signal_df(save_csv: bool = False, exchange: str = "binance", symbol: str = "BTC",
                  start: str = "2026-04-01", end: str = "2026-06-01", strategy_name: str = "",
                  selected_indicators: list[str] = [], strategy_config: dict = None):

    # Calculate indicators
    indicator_config = load_config("indicators/config.yaml")

    df = calculate_indicators(
        exchange=exchange,
        symbol=symbol,
        start=start,
        end=end,
        time_frame=strategy_config["timehorizon"],
        config=indicator_config,  
        selected_indicators=selected_indicators
    )

    if df is None or df.empty:
        print("No data available to generate signals.")
        return None

    # Generate signals
    signal_config = {strategy_name: strategy_config}

    signal = generate_signals(
        df=df,
        config=signal_config,
        strategy_name=strategy_name
    )

    if save_csv:
        df = df.join(signal)
        df.to_csv(f"{strategy_name}_signal.csv", index=True)
        print(f"Saved DataFrame to {strategy_name}_signal.csv")
        return df

    signal = signal[["signal"]]
    return signal

def main():
    from utils.db import seed_strategies, run_cli

    # Ensure strategies are seeded
    seed_strategies()

    # Prompt user
    options = ['strategy', 'exchange', 'symbols', 'start_date', 'end_date']
    config = run_cli(options)

    strategy_name = config['strategy_name']
    strategy_config = config['strategy_config']
    exchange = config['exchange']
    # run_cli with 'strategy' conditionally forces symbols to be single-select, returning a list with one item or string.
    # We'll take the first element (or string) as the single symbol.
    sym_val = config['symbols']
    symbol = sym_val[0] if isinstance(sym_val, list) else sym_val
    start = config['start_date']
    end = config['end_date']

    indicator_config = load_config("indicators/config.yaml")
    selected_indicators = _extract_indicators_for_strategy(strategy_config, indicator_config)

    print(f"Starting signal calculation for {symbol} on {exchange} using {strategy_name}...")
    
    get_signal_df(
        save_csv=False, 
        exchange=exchange, 
        symbol=symbol, 
        start=start, 
        end=end, 
        strategy_name=strategy_name, 
        selected_indicators=selected_indicators,
        strategy_config=strategy_config
    )

if __name__ == "__main__":
    main()