import pandas as pd
import numpy as np

from utils.config import load_config
from data.data_downloader import DataFetcher
from signals.main import get_signal_df

class BacktestEngine:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.ohlcv_df = None
        self.signal_df = None

    def load_data(self):
        # get_updated_df returns (df, df_1m). We want the df.
        df, _ = DataFetcher.get_updated_df(
            exchange=self.config.get('exchange', 'binance'),
            symbol=self.config.get('symbol', 'BTC'),
            start=self.config.get('start_date'),
            end=self.config.get('end_date'),
            time_frame="1m",
            resample_1m=False
        )
        self.ohlcv_df = df

    def load_signals(self):
        # get_signal_df is called with the loaded OHLCV dataframe
        try:
            self.signal_df = get_signal_df(
                save_csv=False,
                exchange=self.config.get('exchange', 'binance'),
                symbol=self.config.get('symbol', 'BTC'),
                start=self.config.get('start_date'),
                end=self.config.get('end_date')
            )
        except TypeError:
            # Fallback if get_signal_df hasn't been updated to accept df yet
            self.signal_df = get_signal_df()

    def prepare(self):
        self.load_data()
        self.load_signals()
        return self.ohlcv_df, self.signal_df
