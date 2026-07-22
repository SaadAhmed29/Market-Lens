import pandas as pd
import numpy as np
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Ensure project root is on sys.path when running the script directly
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from utils.config import load_config
from utils.db import (
    run_cli, get_open_position, save_ledger, load_backtest_config, create_backtest_config_table,
    upsert_simulation_position, upsert_simulation_stats
)
from data.data_downloader import DataFetcher
from signals.main import get_signal_df, _extract_indicators_for_strategy
from backtest.backtest import (
    _calculate_entry_price, _calculate_position_size, _calculate_exit_conditions,
    _apply_commission_slippage, _calculate_pnl, _update_balance
)

def get_current_balance(strategy_name: str, initial_balance: float) -> float:
    """Helper to calculate current live balance from the ledger."""
    from utils.db import get_engine
    from sqlalchemy import text
    engine = get_engine()
    schema = 'backtest_ledgers'
    table = f"{strategy_name.lower()}"
    try:
        with engine.connect() as conn:
            # Try to get the latest balance_after_trade
            row = conn.execute(text(f"SELECT balance_after_trade FROM {schema}.{table} ORDER BY exit_time DESC LIMIT 1")).fetchone()
            if row:
                return round(row[0], 4)
    except Exception:
        pass
    return round(initial_balance, 4)

def _next_trade_id(strategy_name: str) -> int:
    """Return the next trade_id for the strategy by counting existing ledger rows."""
    from utils.db import get_engine
    from sqlalchemy import text
    engine = get_engine()
    schema = 'backtest_ledgers'
    table = f"{strategy_name.lower()}"
    try:
        with engine.connect() as conn:
            row = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}")).fetchone()
            return (row[0] or 0) + 1
    except Exception:
        return 1

def calculate_lookback_start(config: dict, indicators_config: dict) -> str:
    from utils.intervals import INTERVAL_DELTAS
    time_horizon = config.get('timehorizon', '1m')
    max_period = 0
    for ind_name, configs in indicators_config.items():
        for cfg in configs:
            for param_key, param_val in cfg.get('parameters', {}).items():
                if isinstance(param_val, (int, float)) and param_val > max_period:
                    max_period = param_val
                    
    lookback_candles = int(max_period) + 5
    delta = INTERVAL_DELTAS.get(time_horizon, pd.Timedelta(minutes=1))
    total_duration = lookback_candles * delta
    start_dt = (datetime.now(timezone.utc) - total_duration).strftime("%Y-%m-%d")
    return start_dt

def _update_simulation_stats(strategy_name: str, balance: float, sim_config: dict):
    from utils.db import get_engine
    import pandas as pd
    engine = get_engine()
    try:
        ledger = pd.read_sql(f"SELECT * FROM backtest_ledgers.{strategy_name.lower()}", engine)
        if ledger.empty:
            stats = {'final_balance': round(balance, 4), 'total_trades': 0}
            stats.update({k: 0.0 for k in _SCALAR_METRIC_KEYS})
            stats['consecutive_losses'] = 0
            stats['consecutive_wins'] = 0        
        else:
            ledger['exit_time'] = pd.to_datetime(ledger['exit_time'])
            ledger = ledger.sort_values('exit_time').set_index('exit_time')
            initial_balance = sim_config.get('initial_balance', 10000.0)
            first_time = ledger.index[0]
            initial_time = first_time - pd.Timedelta(minutes=1)
            balances = pd.concat([
                pd.Series([initial_balance], index=[initial_time]),
                ledger['balance_after_trade']
            ]).sort_index()

            returns = balances.pct_change().dropna()
            
            from stats.metrics import calculate_metrics
            metrics = calculate_metrics(returns) if not returns.empty else {}

            SCALAR_METRIC_KEYS = [
                'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'max_drawdown', 'cagr',
                'volatility', 'win_rate', 'profit_factor', 'average_win', 'average_loss',
                'best_day', 'worst_day', 'var', 'cvar', 'skewness', 'kurtosis',
                'recovery_factor', 'ulcer_index', 'avg_return', 'common_sense_ratio',
                'comp', 'conditional_value_at_risk', 'cpc_index', 'expected_return',
                'expected_shortfall', 'exposure', 'gain_to_pain_ratio', 'geometric_mean',
                'ghpr', 'outlier_loss_ratio', 'outlier_win_ratio', 'payoff_ratio',
                'profit_ratio', 'rar', 'risk_of_ruin', 'ror', 'tail_ratio',
                'ulcer_performance_index', 'upi', 'win_loss_ratio', 'kelly_criterion',
                'risk_return_ratio',
            ]

            stats = {
                'final_balance': round(balance, 4),
                'total_trades': len(ledger),
                'consecutive_losses': int(metrics.get('consecutive_losses') or 0),
                'consecutive_wins': int(metrics.get('consecutive_wins') or 0),
            }
            for key in SCALAR_METRIC_KEYS:
                decimals = 6 if key == 'max_drawdown' else 4
                stats[key] = round(metrics.get(key) or 0.0, decimals)

            upsert_simulation_stats(strategy_name, stats)
    except Exception as e:
        logger.error(f"Failed to update stats: {e}")

def simulate_strategy(strategy_name: str, strategy_config: dict, exchange: str, symbol: str, time_horizon: str, sim_config: dict, all_bt_configs: dict):
    from utils.db import get_engine
    from sqlalchemy import text
    
    # Fetch backtest config for this strategy from DB
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM meta_data.strategies WHERE strategy_name = :name"), {"name": strategy_name}).fetchone()
        strategy_id = row[0] if row else None
        
    bt_config = all_bt_configs.get(strategy_id, {}) if strategy_id else {}
    if isinstance(bt_config, str):
        bt_config = json.loads(bt_config)
        
    config = {**sim_config, **bt_config, 'symbol': symbol, 'exchange': exchange}

    indicator_config = load_config("indicators/config.yaml")
    end_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_dt = calculate_lookback_start(strategy_config, indicator_config)
    
    logger.info(f"--- Running Simulator for {symbol} on {exchange} ({time_horizon}) using {strategy_name} ---")
    
    fetcher_cfg = {
        "exchange": exchange,
        "time_horizon": "1m",
        "start_date": start_dt,
        "end_date": end_dt,
        "fill_missing_data": "interpolation",
        "retries": 3,
        "retry_delay": 5
    }
    fetcher = DataFetcher(fetcher_cfg)
    
    df_1m, _ = DataFetcher.get_updated_df(
        exchange=exchange,
        symbol=symbol,
        start=start_dt,
        end=end_dt,
        time_frame='1m',
        resample_1m=False
    )
    
    df_resampled, _ = DataFetcher.get_resampled_df(df_1m, time_horizon)
    
    if df_resampled is None or df_resampled.empty or df_1m is None or df_1m.empty:
        logger.info(f"No data available for {strategy_name}.")
        return
        
    current_candle_1m = df_1m.iloc[-1]
    current_price = current_candle_1m['close']
    current_time = df_1m.index[-1]
    
    pos = get_open_position(strategy_name)
    balance = get_current_balance(strategy_name, config.get('initial_balance', 10000.0))
    
    if pos:
        high = current_candle_1m['high']
        low = current_candle_1m['low']
        direction_num = 1 if pos['direction'].lower() == 'long' else -1
        
        tp = pos.get('take_profit')
        sl = pos.get('stop_loss')
        
        tp_hit = False
        sl_hit = False
        
        if direction_num == 1:
            if tp is not None and not np.isnan(tp) and high >= tp: tp_hit = True
            if sl is not None and not np.isnan(sl) and low <= sl: sl_hit = True
        else:
            if tp is not None and not np.isnan(tp) and low <= tp: tp_hit = True
            if sl is not None and not np.isnan(sl) and high >= sl: sl_hit = True
            
        closed = False
        exit_price = None
        reason = ""
        
        if sl_hit:
            closed = True
            exit_price = sl
            reason = 'SL'
        elif tp_hit:
            closed = True
            exit_price = tp
            reason = 'TP'
            
        if closed:
            qty = pos['quantity']
            entry_price = pos['entry_price']
            comm, slip = _apply_commission_slippage(config, entry_price, exit_price, qty)
            gross, net = _calculate_pnl(direction_num, entry_price, exit_price, qty, comm, slip)
            balance = _update_balance(balance, net)
            
            ledger_row = pd.DataFrame([{
                'trade_id': pos.get('trade_id'),
                'entry_time': pos['entry_time'],
                'exit_time': current_time,
                'direction': pos['direction'],
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'quantity': round(qty, 4),
                'gross_pnl': round(gross, 4),
                'commission': round(comm, 4),
                'slippage': round(slip, 4),
                'net_pnl': round(net, 4),
                'balance_after_trade': round(balance, 4),
                'exit_reason': reason,
                'forced_exit': False
            }])
            save_ledger(ledger_row, strategy_name, if_exists='append', schema='backtest_ledgers', table_suffix='')
            
            pos['status'] = 'Closed'
            sim_pos = {
                'trade_id': pos.get('trade_id'),
                'entry_time': pos['entry_time'],
                'direction': pos['direction'],
                'entry_price': round(pos['entry_price'], 4),
                'quantity': round(pos['quantity'], 4),
                'tp_price': round(pos.get('take_profit'), 4) if pos.get('take_profit') is not None else None,
                'sl_price': round(pos.get('stop_loss'), 4) if pos.get('stop_loss') is not None else None,
                'current_price': round(float(exit_price), 4),
                'unrealized_pnl': 0.0,
                'status': pos['status']
            }
            upsert_simulation_position(strategy_name, sim_pos)
            logger.info(f"[{strategy_name}] Position closed due to {reason}. Net PnL: {net:.2f}")
            pos = None
        else:
            qty = pos['quantity']
            entry_price = pos['entry_price']
            if direction_num == 1:
                unrealized = (current_price - entry_price) * qty
            else:
                unrealized = (entry_price - current_price) * qty
            
            pos['current_price'] = round(float(current_price), 4)
            pos['unrealized_pnl'] = round(float(unrealized), 4)
            sim_pos = {
                'trade_id': pos.get('trade_id'),
                'entry_time': pos['entry_time'],
                'direction': pos['direction'],
                'entry_price': round(pos['entry_price'], 4),
                'quantity': round(pos['quantity'], 4),
                'tp_price': round(pos.get('take_profit'), 4) if pos.get('take_profit') is not None else None,
                'sl_price': round(pos.get('stop_loss'), 4) if pos.get('stop_loss') is not None else None,
                'current_price': pos['current_price'],
                'unrealized_pnl': pos['unrealized_pnl'],
                'status': pos['status']
            }
            upsert_simulation_position(strategy_name, sim_pos)
            logger.info(f"[{strategy_name}] Position updated. Unrealized PnL: {unrealized:.2f}")
            
    # Call get_signals
    selected_indicators = _extract_indicators_for_strategy(strategy_config, indicator_config)
    
    signals = get_signal_df(
        save_csv=False,
        exchange=exchange,
        symbol=symbol,
        start=start_dt,
        end=end_dt,
        strategy_name=strategy_name,
        selected_indicators=selected_indicators,
        strategy_config=strategy_config
    )
    
    if signals is None or signals.empty:
        logger.info(f"[{strategy_name}] No signals generated.")
        return
        
    last_signal_row = signals.iloc[-1]
    sig_val = last_signal_row['signal']
    sig_time = signals.index[-1]
    
    logger.info(f"[{strategy_name}] Latest signal at {sig_time}: {sig_val}")
    
    allow_long = config.get('allow_long', True)
    allow_short = config.get('allow_short', True)
    
    if pos:
        exit_on_opp = config.get('exit_on_opposite_signal', False)
        direction_num = 1 if pos['direction'] == 'long' else -1
        if exit_on_opp and sig_val != 0 and sig_val != direction_num:
            exit_price = current_price
            qty = pos['quantity']
            entry_price = pos['entry_price']
            comm, slip = _apply_commission_slippage(config, entry_price, exit_price, qty)
            gross, net = _calculate_pnl(direction_num, entry_price, exit_price, qty, comm, slip)
            balance = _update_balance(balance, net)
            
            ledger_row = pd.DataFrame([{
                'trade_id': pos.get('trade_id'),
                'entry_time': pos['entry_time'],
                'exit_time': current_time,
                'direction': pos['direction'],
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'quantity': round(qty, 4),
                'gross_pnl': round(gross, 4),
                'commission': round(comm, 4),
                'slippage': round(slip, 4),
                'net_pnl': round(net, 4),
                'balance_after_trade': round(balance, 4),
                'exit_reason': 'opposite signal',
                'forced_exit': False
            }])
            save_ledger(ledger_row, strategy_name, if_exists='append', schema='backtest_ledgers', table_suffix='')
            pos['status'] = 'Closed'
            sim_pos = {
                'trade_id': pos.get('trade_id'),
                'entry_time': pos['entry_time'],
                'direction': pos['direction'],
                'entry_price': round(pos['entry_price'], 4),
                'quantity': round(pos['quantity'], 4),
                'tp_price': round(pos.get('take_profit'), 4) if pos.get('take_profit') is not None else None,
                'sl_price': round(pos.get('stop_loss'), 4) if pos.get('stop_loss') is not None else None,
                'current_price': round(float(exit_price), 4),
                'unrealized_pnl': 0.0,
                'status': pos['status']
            }
            upsert_simulation_position(strategy_name, sim_pos)
            pos = None
            logger.info(f"[{strategy_name}] Position closed due to opposite signal. Net PnL: {net:.2f}")
            
    if not pos:
        def open_pos(direction):
            trade_id = _next_trade_id(strategy_name)
            entry_price = _calculate_entry_price(config, current_price)
            qty = _calculate_position_size(config, balance, entry_price)
            tp, sl = _calculate_exit_conditions(config, direction, entry_price)
            
            new_pos = {
                'trade_id': trade_id,
                'direction': 'long' if direction == 1 else 'short',
                'entry_time': current_time,
                'entry_price': round(float(entry_price), 4),
                'quantity': round(float(qty), 4),
                'take_profit': round(float(tp), 4) if not np.isnan(tp) else None,
                'stop_loss': round(float(sl), 4) if not np.isnan(sl) else None,
                'current_price': round(float(current_price), 4),
                'unrealized_pnl': 0.0,
                'status': 'Open'
            }
            sim_pos = {
                'trade_id': new_pos['trade_id'],
                'entry_time': new_pos['entry_time'],
                'direction': new_pos['direction'],
                'entry_price': new_pos['entry_price'],
                'quantity': new_pos['quantity'],
                'tp_price': new_pos['take_profit'],
                'sl_price': new_pos['stop_loss'],
                'current_price': new_pos['current_price'],
                'unrealized_pnl': new_pos['unrealized_pnl'],
                'status': new_pos['status']
            }
            upsert_simulation_position(strategy_name, sim_pos)
            logger.info(f"[{strategy_name}] Opened {'long' if direction == 1 else 'short'} position at {entry_price}")

        if sig_val == 1 and allow_long:
            open_pos(1)
        elif sig_val == -1 and allow_short:
            open_pos(-1)
            
    # Update Stats
    _update_simulation_stats(strategy_name, balance, sim_config)