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
        
        # Pre-calculate vectorized trade parameters
        if self.signal_df is not None and not self.signal_df.empty:
            self._calculate_entry_price()
            self._calculate_position_size()
            self._calculate_exit_conditions()
            
        return self.ohlcv_df, self.signal_df

    def _calculate_entry_price(self):
        # Shift the open price by 1 to get next candle open as entry price
        self.entry_prices = self.ohlcv_df['open'].shift(-1)

    def _calculate_position_size(self):
        # Read position_size type and value from config
        pos_type = self.config['position_size']['type']
        val = self.config['position_size']['value']
        
        # Support fixed_percentage only for now
        if pos_type == 'fixed_percentage':
            # Initialize with initial balance. Dynamic updates to balance (after each trade)
            # are applied during the trade filtering and execution phase.
            initial_balance = self.config.get('initial_balance', 10000)
            balances = pd.Series(initial_balance, index=self.ohlcv_df.index)
            
            position_values = balances * (val / 100)
            self.quantities = position_values / self.entry_prices

    def _calculate_exit_conditions(self):
        tp_enabled = self.config['take_profit'].get('enabled', True)
        sl_enabled = self.config['stop_loss'].get('enabled', True)
        tp_pct = self.config['take_profit']['value'] / 100
        sl_pct = self.config['stop_loss']['value'] / 100

        self.take_profit_prices = pd.Series(np.nan, index=self.ohlcv_df.index)
        self.stop_loss_prices = pd.Series(np.nan, index=self.ohlcv_df.index)
        self.exit_prices = pd.Series(np.nan, index=self.ohlcv_df.index)
        
        # Determine the signal column name
        signal_col = 'signal' if 'signal' in self.signal_df.columns else self.signal_df.columns[0]
        long_signals = self.signal_df[signal_col] == 1
        short_signals = self.signal_df[signal_col] == -1

        # Calculate TP and SL prices
        if tp_enabled:
            self.take_profit_prices[long_signals] = self.entry_prices[long_signals] * (1 + tp_pct)
            self.take_profit_prices[short_signals] = self.entry_prices[short_signals] * (1 - tp_pct)
        if sl_enabled:
            self.stop_loss_prices[long_signals] = self.entry_prices[long_signals] * (1 - sl_pct)
            self.stop_loss_prices[short_signals] = self.entry_prices[short_signals] * (1 + sl_pct)

        # Vectorized forward scan across all signals simultaneously
        signal_indices = np.where(long_signals | short_signals)[0]
        if len(signal_indices) == 0:
            return

        tps = self.take_profit_prices.values[signal_indices]
        sls = self.stop_loss_prices.values[signal_indices]
        sigs = self.signal_df[signal_col].values[signal_indices]

        N = len(self.ohlcv_df)
        M = len(signal_indices)
        highs = self.ohlcv_df['high'].values
        lows = self.ohlcv_df['low'].values

        # M x N matrix for finding first hit
        tp_hits = np.zeros((M, N), dtype=bool)
        sl_hits = np.zeros((M, N), dtype=bool)

        long_mask = sigs == 1
        short_mask = sigs == -1

        if np.any(long_mask):
            tp_hits[long_mask] = highs >= tps[long_mask, None]
            sl_hits[long_mask] = lows <= sls[long_mask, None]

        if np.any(short_mask):
            tp_hits[short_mask] = lows <= tps[short_mask, None]
            sl_hits[short_mask] = highs >= sls[short_mask, None]

        # Ignore hits on or before the signal candle (exit must be AFTER signal)
        past_mask = np.arange(N) <= signal_indices[:, None]
        tp_hits[past_mask] = False
        sl_hits[past_mask] = False

        # Find first index where TP or SL is hit
        tp_first = np.argmax(tp_hits, axis=1)
        sl_first = np.argmax(sl_hits, axis=1)

        # argmax returns 0 if no True is found, so remap to N
        tp_first[~tp_hits.any(axis=1)] = N
        sl_first[~sl_hits.any(axis=1)] = N

        # Determine which was hit first
        tp_first_mask = tp_first < sl_first
        sl_first_mask = sl_first < tp_first
        both_same = (tp_first == sl_first) & (tp_first != N)
        
        # If both hit on the same bar, assume SL to be conservative
        sl_first_mask |= both_same

        # Populate exit prices
        exit_prices = np.full(M, np.nan)
        exit_prices[tp_first_mask] = tps[tp_first_mask]
        exit_prices[sl_first_mask] = sls[sl_first_mask]

        self.exit_prices.iloc[signal_indices] = exit_prices
