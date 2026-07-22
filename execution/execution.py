import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Ensure project root is on sys.path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Load env variables for Pybit
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

from pybit.unified_trading import HTTP
from sqlalchemy import text

from utils.config import load_config
from utils.db import (
    get_engine, save_ledger, load_backtest_config, load_strategies_config,
    upsert_execution_position, upsert_execution_stats
)
from data.data_downloader import DataFetcher
from signals.main import get_signal_df, _extract_indicators_for_strategy
from backtest.backtest import (
    _calculate_position_size, _calculate_exit_conditions, _calculate_entry_price
)
from stats.main import generate_stats

# Initialize pybit client
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")
client = None
if api_key and api_secret:
    client = HTTP(testnet=False, demo=True, api_key=api_key, api_secret=api_secret)
else:
    logger.warning("BYBIT_API_KEY and BYBIT_API_SECRET not set in .env. Order placement will fail.")

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

def get_open_execution_position(strategy_name: str) -> dict | None:
    engine = get_engine()
    with engine.connect() as conn:
        try:
            row = conn.execute(
                text("SELECT * FROM execution.positions WHERE strategy_name=:name AND status='Open' LIMIT 1"),
                {"name": strategy_name}
            ).mappings().fetchone()
            if row:
                d = dict(row)
                d['take_profit'] = d.pop('tp_price', None)
                d['stop_loss'] = d.pop('sl_price', None)
                return d
        except Exception:
            pass
    return None

def update_execution_stats(strategy_name: str, balance: float):
    engine = get_engine()
    try:
        ledger = pd.read_sql(f"SELECT * FROM execution_ledgers.{strategy_name.lower()}", engine)
        if ledger.empty:
            stats = {'final_balance': round(balance, 4), 'total_trades': 0}
            upsert_execution_stats(strategy_name, stats)
            return
            
        metrics = generate_stats(ledger, strategy_name)
        if metrics:
            stats = {**metrics}
            stats['final_balance'] = round(balance, 4)
            stats['total_trades'] = len(ledger)
            upsert_execution_stats(strategy_name, stats)
    except Exception as e:
        logger.error(f"Failed to update execution stats for {strategy_name}: {e}")

def get_real_wallet_balance() -> float:
    try:
        if not client: return 0.0
        wallet_resp = client.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        if wallet_resp.get("result", {}).get("list"):
            coins = wallet_resp["result"]["list"][0].get("coin", [])
            for c in coins:
                if c["coin"] == "USDT":
                    return float(c["walletBalance"])
    except Exception as e:
        logger.error(f"Error fetching wallet balance: {e}")
    return 0.0

def execute_strategy(strategy_name: str, strategy_config: dict, exchange: str, symbol: str, time_horizon: str, all_bt_configs: dict):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM meta_data.strategies WHERE strategy_name = :name"), {"name": strategy_name}).fetchone()
        strategy_id = row[0] if row else None
        
    bt_config = all_bt_configs.get(strategy_id, {}) if strategy_id else {}
    if isinstance(bt_config, str):
        bt_config = json.loads(bt_config)
        
    config = {**bt_config, 'symbol': symbol, 'exchange': exchange}

    indicator_config = load_config("indicators/config.yaml")
    end_dt = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_dt = calculate_lookback_start(strategy_config, indicator_config)
    
    logger.info(f"--- Running Execution for {symbol} on {exchange} ({time_horizon}) using {strategy_name} ---")
    
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
        logger.info(f"No data available for {strategy_name}.")
        return
        
    current_candle_1m = df_1m.iloc[-1]
    current_price = current_candle_1m['close']
    current_time = df_1m.index[-1]
    
    pos = get_open_execution_position(strategy_name)
    balance = get_real_wallet_balance()
    
    retries = fetcher_cfg.get('retries', 3)
    
    if pos:
        for i in range(retries):
            try:
                if not client:
                    raise ValueError("Bybit client not initialized")
                    
                resp = client.get_positions(category="linear", symbol=symbol)
                pos_list = resp.get("result", {}).get("list", [])
                
                api_pos = None
                for p in pos_list:
                    if p['symbol'] == symbol and float(p['size']) > 0:
                        api_pos = p
                        break
                
                closed = False
                if api_pos is None or float(api_pos['size']) == 0:
                    closed = True
                    
                if closed:
                    closed_resp = client.get_closed_pnl(category="linear", symbol=symbol, limit=1)
                    closed_list = closed_resp.get("result", {}).get("list", [])
                    
                    realized_pnl = 0.0
                    fee = 0.0
                    exit_price = current_price
                    reason = "API Close"
                    
                    if closed_list:
                        latest_close = closed_list[0]
                        realized_pnl = float(latest_close.get("closedPnl", 0))
                        entry_val = float(latest_close.get("cumEntryValue", 0))
                        exit_val = float(latest_close.get("cumExitValue", 0))
                        fee = (entry_val + exit_val) * config.get('commission', 0.0005)
                        exit_price = float(latest_close.get("avgExitPrice", current_price))
                    
                    balance = get_real_wallet_balance()
                    qty = pos['quantity']
                    entry_price = pos['entry_price']
                    
                    ledger_row = pd.DataFrame([{
                        'trade_id': pos.get('order_id'),
                        'entry_time': pos['entry_time'],
                        'exit_time': current_time,
                        'direction': pos['direction'],
                        'entry_price': round(entry_price, 4),
                        'exit_price': round(exit_price, 4),
                        'quantity': round(qty, 4),
                        'gross_pnl': round(realized_pnl + fee, 4),
                        'commission': round(fee, 4),
                        'slippage': 0.0,
                        'net_pnl': round(realized_pnl, 4),
                        'balance_after_trade': round(balance, 4),
                        'exit_reason': reason,
                        'forced_exit': False
                    }])
                    
                    save_ledger(ledger_row, strategy_name, if_exists='append', schema='execution_ledgers', table_suffix='')
                    
                    pos['status'] = 'Closed'
                    exec_pos = {
                        'order_id': pos.get('order_id'),
                        'entry_time': pos['entry_time'],
                        'direction': pos['direction'],
                        'entry_price': round(pos['entry_price'], 4),
                        'quantity': round(pos['quantity'], 4),
                        'tp_price': round(pos.get('take_profit'), 4) if pos.get('take_profit') is not None else None,
                        'sl_price': round(pos.get('stop_loss'), 4) if pos.get('stop_loss') is not None else None,
                        'status': pos['status']
                    }
                    upsert_execution_position(strategy_name, exec_pos)
                    logger.info(f"[{strategy_name}] Position closed. Net PnL: {realized_pnl:.2f}")
                    pos = None
                break
            except Exception as e:
                logger.error(f"Error monitoring position on Bybit: {e}")
                if i == retries - 1:
                    logger.error(f"[{strategy_name}] Max retries reached for position monitoring. Skipping.")
                time.sleep(fetcher_cfg.get('retry_delay', 5))

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
    
    if not pos:
        def place_live_order(direction):
            entry_price = _calculate_entry_price(config, current_price)
            qty = _calculate_position_size(config, balance, entry_price)
            tp, sl = _calculate_exit_conditions(config, direction, entry_price)
            
            side = "Buy" if direction == 1 else "Sell"
            
            try:
                if not client:
                    raise ValueError("Bybit client not initialized")
                    
                order_resp = client.place_order(
                    category="linear",
                    symbol=symbol,
                    side=side,
                    orderType="Market",
                    qty=str(round(qty, 4))
                )
                order_id = order_resp.get("result", {}).get("orderId")
                
                if order_id:
                    if not np.isnan(tp) or not np.isnan(sl):
                        client.set_trading_stop(
                            category="linear",
                            symbol=symbol,
                            takeProfit=str(round(tp, 4)) if not np.isnan(tp) else "0",
                            stopLoss=str(round(sl, 4)) if not np.isnan(sl) else "0",
                            tpslMode="Full",
                            positionIdx=0
                        )
                    
                    new_pos = {
                        'order_id': order_id,
                        'direction': 'long' if direction == 1 else 'short',
                        'entry_time': current_time,
                        'entry_price': round(float(entry_price), 4),
                        'quantity': round(float(qty), 4),
                        'tp_price': round(float(tp), 4) if not np.isnan(tp) else None,
                        'sl_price': round(float(sl), 4) if not np.isnan(sl) else None,
                        'status': 'Open'
                    }
                    upsert_execution_position(strategy_name, new_pos)
                    logger.info(f"[{strategy_name}] Opened {side} position via Market Order (ID: {order_id})")
            except Exception as e:
                logger.error(f"[{strategy_name}] Order placement failed: {e}")
                
        if sig_val == 1 and allow_long:
            place_live_order(1)
        elif sig_val == -1 and allow_short:
            place_live_order(-1)
            
    # Update Stats
    update_execution_stats(strategy_name, balance)
