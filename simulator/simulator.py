import pandas as pd
import numpy as np
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when running the script directly
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from utils.config import load_config
from utils.db import run_cli, get_open_position, upsert_position, save_ledger, load_backtest_config, create_backtest_config_table
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
                return row[0]
    except Exception:
        pass
    return initial_balance

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

    end_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_dt = (datetime.now(timezone.utc) - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\n--- Running Simulator for {symbol} on {exchange} ({time_horizon}) using {strategy_name} ---")
    
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
    fetcher.download(symbol)
    
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
        print(f"No data available for {strategy_name}.")
        return
        
    current_candle_1m = df_1m.iloc[-1]
    current_price = current_candle_1m['close']
    current_time = df_1m.index[-1]
    
    pos = get_open_position(strategy_name)
    balance = get_current_balance(strategy_name, config.get('initial_balance', 10000.0))
    
    if pos:
        high = current_candle_1m['high']
        low = current_candle_1m['low']
        direction_num = 1 if pos['direction'] == 'long' else -1
        
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
                'entry_time': pos['entry_time'],
                'exit_time': current_time,
                'direction': pos['direction'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': qty,
                'gross_pnl': gross,
                'commission': comm,
                'slippage': slip,
                'net_pnl': net,
                'balance_after_trade': balance,
                'exit_reason': reason,
                'forced_exit': False
            }])
            save_ledger(ledger_row, strategy_name, if_exists='append')
            
            pos['status'] = 'Closed'
            upsert_position(pos, strategy_name)
            print(f"[{strategy_name}] Position closed due to {reason}. Net PnL: {net:.2f}")
            pos = None
        else:
            qty = pos['quantity']
            entry_price = pos['entry_price']
            if direction_num == 1:
                unrealized = (current_price - entry_price) * qty
            else:
                unrealized = (entry_price - current_price) * qty
            
            pos['current_price'] = float(current_price)
            pos['unrealized_pnl'] = float(unrealized)
            upsert_position(pos, strategy_name)
            print(f"[{strategy_name}] Position updated. Unrealized PnL: {unrealized:.2f}")
            
    # Call get_signals
    indicator_config = load_config("indicators/config.yaml")
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
        print(f"[{strategy_name}] No signals generated.")
        return
        
    last_signal_row = signals.iloc[-1]
    sig_val = last_signal_row['signal']
    sig_time = signals.index[-1]
    
    print(f"[{strategy_name}] Latest signal at {sig_time}: {sig_val}")
    
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
                'entry_time': pos['entry_time'],
                'exit_time': current_time,
                'direction': pos['direction'],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': qty,
                'gross_pnl': gross,
                'commission': comm,
                'slippage': slip,
                'net_pnl': net,
                'balance_after_trade': balance,
                'exit_reason': 'opposite signal',
                'forced_exit': False
            }])
            save_ledger(ledger_row, strategy_name, if_exists='append')
            pos['status'] = 'Closed'
            upsert_position(pos, strategy_name)
            pos = None
            print(f"[{strategy_name}] Position closed due to opposite signal. Net PnL: {net:.2f}")
            
    if not pos:
        def open_pos(direction):
            entry_price = _calculate_entry_price(config, current_price)
            qty = _calculate_position_size(config, balance, entry_price)
            tp, sl = _calculate_exit_conditions(config, direction, entry_price)
            
            new_pos = {
                'direction': 'long' if direction == 1 else 'short',
                'entry_time': current_time,
                'entry_price': float(entry_price),
                'quantity': float(qty),
                'take_profit': float(tp) if not np.isnan(tp) else None,
                'stop_loss': float(sl) if not np.isnan(sl) else None,
                'current_price': float(current_price),
                'unrealized_pnl': 0.0,
                'status': 'Open'
            }
            upsert_position(new_pos, strategy_name)
            print(f"[{strategy_name}] Opened {'long' if direction == 1 else 'short'} position at {entry_price}")

        if sig_val == 1 and allow_long:
            open_pos(1)
        elif sig_val == -1 and allow_short:
            open_pos(-1)
