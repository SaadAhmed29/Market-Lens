import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from indicators.talib_indicators import TalibIndicators
from data.data_downloader import DataFetcher
from signals.rules import generate_signals


def calculate_indicators(exchange: str, symbol: str, start, end, time_frame: str, config_path: str, selected_indicators: list[str]) -> pd.DataFrame:
    
    print("Fetching data and initializing indicators...")
    try:
        indicators = TalibIndicators(
            exchange=exchange,
            symbol=symbol,
            start=start,
            end=end,
            time_frame=time_frame,
            config_path=config_path
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
        "SMA"
    ]

    df = calculate_indicators(
        exchange="binance",
        symbol="BTC",
        start=pd.to_datetime("2025-01-01", utc=True),
        end=pd.to_datetime("2026-07-01", utc=True),
        time_frame="1h",
        config_path="indicators/config.yaml",  
        selected_indicators=selected_indicators
    )

    # generate signals

    signal = generate_signals(
        df=df,
        config_path="signals/config.yaml",
        strategy_name="my_strategy"
    )

    df = df.join(signal)
  
    # Save df in a csv file
    df.to_csv("sma_signal.csv", index=True)
    print("Saved DataFrame to btc_sma.csv")
    

main()