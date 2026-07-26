import sys
import json
import math
from pathlib import Path
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.db import get_engine

def get_all_executions() -> list[dict]:
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            query = """
            SELECT p.strategy_name, p.status, p.direction, p.entry_time, s.config 
            FROM execution.positions p
            LEFT JOIN meta_data.strategies s ON p.strategy_name = s.strategy_name
            """
            rows = conn.execute(text(query)).mappings().fetchall()
        except Exception:
            return []
            
        try:
            account_row = conn.execute(text("SELECT account_name FROM accounts.api LIMIT 1")).mappings().fetchone()
            wallet = account_row["account_name"] if account_row else "N/A"
        except Exception:
            wallet = "N/A"
            
        try:
            stats_rows = conn.execute(text("SELECT strategy_name, comp, avg_return FROM execution.stats")).mappings().fetchall()
            stats_map = {r["strategy_name"]: dict(r) for r in stats_rows}
        except Exception:
            stats_map = {}
            
        result = []
        for row in rows:
            name = row["strategy_name"]
            cfg = row["config"] or {}
            if isinstance(cfg, str):
                try:
                    cfg = json.loads(cfg)
                except Exception:
                    cfg = {}
                    
            stats = stats_map.get(name, {})
            avg_return = stats.get("avg_return") or 0
            
            try:
                # signal.{strategy_name}_signal
                signal_query = f"SELECT signal FROM signal.\"{name}_signal\" ORDER BY timestamp DESC LIMIT 1"
                signal_row = conn.execute(text(signal_query)).mappings().fetchone()
                last_signal = signal_row["signal"] if signal_row else "N/A"
            except Exception:
                last_signal = "N/A"
                
            entry_time = row["entry_time"]
            if entry_time:
                if hasattr(entry_time, "isoformat"):
                    entry_time = entry_time.isoformat()
                else:
                    entry_time = str(entry_time)
            else:
                entry_time = "N/A"
                
            result.append({
                "strategy": name,
                "symbol": cfg.get("symbol", "N/A"),
                "exchange": cfg.get("exchange", "N/A"),
                "wallet": wallet,
                "status": row["status"],
                "position": row["direction"] or "none",
                "avg_return": avg_return,
                "last_trade_entry": entry_time
            })
            
    return result


def get_execution_detail(strategy_name: str) -> dict:
    engine = get_engine()
    
    with engine.connect() as conn:
        # Strategy Information
        try:
            row = conn.execute(
                text("SELECT config FROM meta_data.strategies WHERE strategy_name = :name"),
                {"name": strategy_name}
            ).mappings().fetchone()
            config = row["config"] or {} if row else {}
            if isinstance(config, str):
                config = json.loads(config)
        except Exception:
            config = {}
            
        strategy_info = {
            "symbol": config.get("symbol", "N/A"),
            "exchange": config.get("exchange", "N/A"),
            "timehorizon": config.get("timehorizon", "N/A"),
            "long": config.get("long", {}),
            "short": config.get("short", {})
        }
        
        # Wallet Information
        try:
            account_row = conn.execute(text("SELECT account_name FROM accounts.api LIMIT 1")).mappings().fetchone()
            wallet_name = account_row["account_name"] if account_row else "N/A"
        except Exception:
            wallet_name = "N/A"
            
        wallet_info = {
            "account_name": wallet_name,
            "wallet_balance": 0,
        }
        if wallet_name != "N/A":
            try:
                w_stats_row = conn.execute(text(f"SELECT wallet_balance FROM accounts.\"{wallet_name}_stats\" LIMIT 1")).mappings().fetchone()
                if w_stats_row:
                    wallet_info["wallet_balance"] = float(w_stats_row["wallet_balance"] or 0)
            except Exception:
                pass
                
        # Position History & Chart Data
        try:
            df = pd.read_sql_query(
                text(f"SELECT * FROM execution_ledgers.\"{strategy_name}\" ORDER BY exit_time DESC"),
                conn
            )
        except Exception:
            df = pd.DataFrame()
            
        position_history = []
        equity_curve = []
        position_size = []
        returns = []
        pie_chart = [{"name": "LONG", "value": 0}, {"name": "SHORT", "value": 0}]
        
        if not df.empty:
            if "exit_time" in df.columns:
                df["exit_time_str"] = pd.to_datetime(df["exit_time"]).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                df["exit_time_str"] = ""
            if "entry_time" in df.columns:
                df["entry_time_str"] = pd.to_datetime(df["entry_time"]).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                df["entry_time_str"] = ""
                
            for _, r in df.iterrows():
                position_history.append({
                    "entry_time": r.get("entry_time_str", ""),
                    "exit_time": r.get("exit_time_str", ""),
                    "direction": r.get("direction", ""),
                    "entry_price": float(r.get("entry_price") or 0) if pd.notnull(r.get("entry_price")) else 0,
                    "exit_price": float(r.get("exit_price") or 0) if pd.notnull(r.get("exit_price")) else 0,
                    "quantity": float(r.get("quantity") or 0) if pd.notnull(r.get("quantity")) else 0,
                    "net_pnl": float(r.get("net_pnl") or 0) if pd.notnull(r.get("net_pnl")) else 0,
                    "balance_after_trade": float(r.get("balance_after_trade") or 0) if pd.notnull(r.get("balance_after_trade")) else 0
                })
                
            df_asc = df.sort_values("exit_time", ascending=True) if "exit_time" in df.columns else df
            for _, r in df_asc.iterrows():
                if r.get("exit_time_str"):
                    equity_curve.append({
                        "date": r["exit_time_str"], 
                        "value": float(r.get("balance_after_trade") or 0) if pd.notnull(r.get("balance_after_trade")) else 0
                    })
                    returns.append({
                        "date": r["exit_time_str"], 
                        "value": float(r.get("net_pnl") or 0) if pd.notnull(r.get("net_pnl")) else 0
                    })
            
            df_entry_asc = df.sort_values("entry_time", ascending=True) if "entry_time" in df.columns else df
            for _, r in df_entry_asc.iterrows():
                if r.get("entry_time_str"):
                    position_size.append({
                        "date": r["entry_time_str"], 
                        "value": float(r.get("quantity") or 0) if pd.notnull(r.get("quantity")) else 0
                    })
                    
            long_count = int((df["direction"].str.upper() == "LONG").sum()) if "direction" in df.columns else 0
            short_count = int((df["direction"].str.upper() == "SHORT").sum()) if "direction" in df.columns else 0
            pie_chart = [{"name": "LONG", "value": long_count}, {"name": "SHORT", "value": short_count}]
            
        # Current Position
        try:
            curr_pos_row = conn.execute(
                text("SELECT direction, entry_price, quantity, tp_price, sl_price, status FROM execution.positions WHERE strategy_name = :name"),
                {"name": strategy_name}
            ).mappings().fetchone()
            if curr_pos_row:
                current_position = dict(curr_pos_row)
                for k in ["entry_price", "quantity", "tp_price", "sl_price"]:
                    if k in current_position and current_position[k] is not None:
                        current_position[k] = float(current_position[k])
            else:
                current_position = {}
        except Exception:
            current_position = {}
            
        # Statistics
        try:
            stats_row = conn.execute(
                text("SELECT * FROM execution.stats WHERE strategy_name = :name"),
                {"name": strategy_name}
            ).mappings().fetchone()
            
            if stats_row:
                statistics = dict(stats_row)
                for k, v in statistics.items():
                    if v is None:
                        statistics[k] = 0
                    elif isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
                        statistics[k] = 0
            else:
                # Need to fallback to 0 for all fields
                cols = conn.execute(
                    text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'execution' AND table_name = 'stats'")
                ).fetchall()
                statistics = {r[0]: 0 for r in cols if r[0] != 'strategy_name'}
                if not statistics:
                    statistics = {}
        except Exception:
            statistics = {}

    return {
        "strategy_information": strategy_info,
        "wallet_information": wallet_info,
        "position_history": position_history,
        "current_position": current_position,
        "statistics": statistics,
        "chart_data": {
            "equity_curve": equity_curve,
            "position_size": position_size,
            "returns": returns,
            "pie_chart": pie_chart
        }
    }
