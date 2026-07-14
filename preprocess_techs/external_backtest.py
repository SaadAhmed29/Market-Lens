"""
Runs a backtest using externally-supplied model predictions (e.g. the
predictions_df produced by preprocess_techs/runner.py) instead of letting
BacktestEngine compute signals from a strategy config.
"""

import os
import pandas as pd
from backtest.backtest import BacktestEngine


def _predictions_to_signal_df(predictions_df: pd.DataFrame, prediction_col: str = "predictions",
                              label_to_signal: dict = None,) -> pd.DataFrame:
    """
    Convert a predictions DataFrame (indexed by date_time, as produced by
    preprocess_techs/runner.py) into the signal_df format
    BacktestEngine._map_signals_to_1m() expects: indexed by the action
    timestamp, with a 'signal' column of 1 (long), -1 (short), or 0 (flat).

    label_to_signal: optional mapping from a raw predicted class label to
        a signal value. Leave as None if your model already predicts
        -1/0/1 directly. Example for a 3-class classifier with classes
        0/1/2 meaning down/flat/up:
            {0: -1, 1: 0, 2: 1}
    """
    signal_df = predictions_df[[prediction_col]].copy()
    signal_df.rename(columns={prediction_col: "signal"}, inplace=True)

    if label_to_signal is not None:
        signal_df["signal"] = signal_df["signal"].map(label_to_signal)

    signal_df["signal"] = signal_df["signal"].fillna(0).astype(int)
    return signal_df


def run_backtest_from_predictions(config: dict, predictions_df: pd.DataFrame, technique_name: str,
                                  model_name: str, prediction_col: str = "predictions",
                                  label_to_signal: dict = None, persist_signals: bool = False, 
                                  output_dir: str = "backtest_results") -> dict:
    """
    Run a backtest using model-predicted signals instead of a
    strategy-computed signal_df, then save the trade ledger to a CSV
    named after the preprocessing technique and model used.

    Mirrors BacktestEngine.prepare() / run(), but skips load_signals()
    (which would otherwise recompute signals from the strategy config)
    and substitutes the model's predictions instead. Only public/internal
    methods already defined on BacktestEngine are called -- the class
    itself is untouched.

    Args:
        config: same config dict you'd normally pass to BacktestEngine
            (take_profit/stop_loss/position_size/etc).
        predictions_df: DataFrame indexed by date_time with a prediction
            column (e.g. the output of preprocess_techs/runner.py's
            _train_and_evaluate).
        technique_name: name of the preprocessing technique used (e.g.
            "log_returns_rolling_zscore") -- used in the output filename.
        model_name: name of the model used (e.g. "logistic_regression")
            -- used in the output filename.
        prediction_col: name of the column in predictions_df holding the
            predicted class/direction.
        label_to_signal: optional mapping from predicted label -> signal
            value (1/-1/0). See _predictions_to_signal_df for details.
        persist_signals: if True, also save the derived signal_df via
            save_signals() the way BacktestEngine.load_signals() normally
            would. Off by default since these are model predictions, not
            a named strategy's signals.
        output_dir: directory the result CSV is written to. Created if
            it doesn't already exist.
    """
    engine = BacktestEngine(config)

    # Load OHLCV data, still needed for trade execution / TP-SL scanning.
    engine.load_data()

    # Build signal_df from predictions instead of engine.load_signals().
    engine.signal_df = _predictions_to_signal_df(
        predictions_df, prediction_col=prediction_col, label_to_signal=label_to_signal
    )

    if persist_signals and not engine.signal_df.empty:
        from utils.db import save_signals
        strategy_name = config.get("strategy_name", "model_predictions")
        save_signals(engine.signal_df, strategy_name)

    # Map signals onto the 1m timeline and build trades -- same steps
    # BacktestEngine.prepare() runs after load_signals().
    if engine.signal_df is not None and not engine.signal_df.empty:
        engine._map_signals_to_1m()
        if not engine.mapped_signals.empty:
            engine._build_trades()

    # Execute (sizing, commission/slippage, PnL, equity curve) -- same
    # as BacktestEngine.run() would do.
    results = engine.execute()

    strategy_name = config.get("strategy_name", "model_predictions")
    if engine.trade_ledger is not None and not engine.trade_ledger.empty:
        engine.trade_ledger = engine.trade_ledger.sort_values("entry_time").reset_index(drop=True)
        results["trade_ledger"] = engine.trade_ledger

    # Save the trade ledger to CSV, named after the technique + model.
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"backtest_{technique_name}_{model_name}.csv")

    ledger_to_save = results.get("trade_ledger")
    if ledger_to_save is not None and not ledger_to_save.empty:
        ledger_to_save.to_csv(csv_path, index=False)
    else:
        # No trades -- still write an empty file with headers so the run
        # is visible/traceable, rather than silently producing nothing.
        pd.DataFrame(columns=[
            "entry_time", "exit_time", "direction", "entry_price", "exit_price",
            "quantity", "gross_pnl", "commission", "slippage", "net_pnl",
            "balance_after_trade", "exit_reason", "forced_exit",
        ]).to_csv(csv_path, index=False)

    results["csv_path"] = csv_path
    return results