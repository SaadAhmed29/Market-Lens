import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from indicators.talib_indicators import TalibIndicators
from data.data_downloader import DataFetcher
from signals.rules import generate_signals
from utils.config import load_config


def calculate_indicators(exchange: str, symbol: str, start, end, time_frame: str, config: dict, selected_indicators: list[str]) -> pd.DataFrame:
    
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


# generate main signals

def get_signal_df(save_csv: bool = False, exchange: str = "binance", symbol: str = "BTC", start: str = "2025-01-01", end: str = "2025-01-31"):

    # calculate indicators

    selected_indicators = [
        "CDLDOJI"
    ]

    indicator_config = load_config("indicators/config.yaml")

    df = calculate_indicators(
        exchange=exchange,
        symbol=symbol,
        start=start,
        end=end,
        time_frame="1h",
        config=indicator_config,  
        selected_indicators=selected_indicators
    )

    # generate signals

    signal_config = load_config("signals/config.yaml")

    signal = generate_signals(
        df=df,
        config=signal_config,
        strategy_name="doji_strategy"
    )

    if save_csv:
        df = df.join(signal)
        df.to_csv("doji_signal.csv", index=True)
        print("Saved DataFrame to doji_signal.csv")
    
    signal = signal.drop(columns=["long_cond_1", "long_cond_2", "short_cond_1", "short_cond_2"])
    print(signal)
    return signal

get_signal_df()