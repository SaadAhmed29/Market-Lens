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
    
    exchange="binance",
    symbol="ADA",
    start=pd.to_datetime("2026-06-28", utc=True),
    end=pd.to_datetime("2026-06-29", utc=True),
    time_frame="1m",
    config_path="indicators/config.yaml"
    selected_indicators=[
        "EMA",
        "RSI",
        "MACD",
        "CDLDOJI",
        "CDLENGULFING"
    ]

    # calculate indicators

    df = calculate_indicators(
        exchange="binance",
        symbol="ADA",
        start=pd.to_datetime("2026-06-28", utc=True),
        end=pd.to_datetime("2026-06-29", utc=True),
        time_frame="1m",
        config_path="indicators/config.yaml",  
        selected_indicators=selected_indicators
    )

    # generate signals

    signal = generate_signals(
        df=df,
        config_path="signals/config.yaml",
        strategy_name="sample_strategy"
    )

    print(signal)
    

main()