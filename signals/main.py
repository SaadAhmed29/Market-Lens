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

def main():

    # calculate indicators

    selected_indicators = [
        "CDLDOJI"
    ]

    indicator_config = load_config("indicators/config.yaml")

    df = calculate_indicators(
        exchange="binance",
        symbol="BTC",
        start=pd.to_datetime("2025-01-01", utc=True),
        end=pd.to_datetime("2026-07-01", utc=True),
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

    df = df.join(signal)
  
    # Save df in a csv file
    df.to_csv("doji_signal.csv", index=True)
    print("Saved DataFrame to doji_signal.csv")
    

main()