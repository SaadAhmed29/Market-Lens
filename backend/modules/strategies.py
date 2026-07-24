"""
MarketLens — Strategies Module
Data fetchers for /api/strategies endpoints.
"""

import sys
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.db import get_engine

def get_all_strategies() -> list[dict]:
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            strategy_rows = conn.execute(
                text("SELECT strategy_name, config FROM meta_data.strategies")
            ).mappings().fetchall()
        except Exception:
            return []

        if not strategy_rows:
            return []
            
        try:
            pos_rows = conn.execute(
                text("SELECT strategy_name, status FROM simulation.positions")
            ).mappings().fetchall()
            position_status = {r["strategy_name"]: r["status"] for r in pos_rows}
        except Exception:
            position_status = {}

        try:
            stats_rows = conn.execute(
                text(
                    "SELECT strategy_name, avg_return, sharpe_ratio, win_rate "
                    "FROM simulation.stats"
                )
            ).mappings().fetchall()
            stats_map = {r["strategy_name"]: dict(r) for r in stats_rows}
        except Exception:
            stats_map = {}

    strategies = []
    for row in strategy_rows:
        name = row["strategy_name"]
        cfg = row["config"] or {}
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except Exception:
                cfg = {}

        stats = stats_map.get(name, {})
        strategies.append({
            "strategy_name": name,
            "symbol": cfg.get("symbol", "N/A"),
            "exchange": cfg.get("exchange", "N/A"),
            "timehorizon": cfg.get("timehorizon", "N/A"),
            "status": position_status.get(name, "inactive"),
            "latest_return": stats.get("avg_return") or 0.0,
            "sharpe_ratio": stats.get("sharpe_ratio") or 0.0,
            "win_rate": stats.get("win_rate") or 0.0,
        })

    return strategies


def parse_indicators(config: dict) -> list[dict]:
    """Parse conditions blocks and extract indicator/pattern names and periods."""
    indicators = []
    seen = set()

    def process_cond(cond):
        for side in ["left", "right"]:
            val = str(cond.get(side, ""))
            if val.startswith("ind_") or val.startswith("pat_"):
                if val in seen:
                    continue
                seen.add(val)
                parts = val.split("_")
                prefix = parts[0]
                name = parts[1] if len(parts) > 1 else ""
                
                if prefix == "ind":
                    period = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                    indicators.append({"name": name, "period": period})
                elif prefix == "pat":
                    indicators.append({"name": name, "type": "pattern"})

    for block in ["long", "short"]:
        conditions = config.get(block, {}).get("conditions", [])
        for c in conditions:
            process_cond(c)

    return indicators


def get_strategy_detail(strategy_name: str) -> dict:
    engine = get_engine()
    
    with engine.connect() as conn:
        try:
            row = conn.execute(
                text("SELECT config FROM meta_data.strategies WHERE strategy_name = :name"),
                {"name": strategy_name}
            ).mappings().fetchone()
        except Exception:
            row = None
            
        if not row:
            return {}

        config = row["config"] or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except Exception:
                config = {}

        # Indicators
        indicators = parse_indicators(config)

        # Performance Summary
        try:
            stats_row = conn.execute(
                text("SELECT * FROM simulation.stats WHERE strategy_name = :name"),
                {"name": strategy_name}
            ).mappings().fetchone()
            perf_summary = dict(stats_row) if stats_row else {}
        except Exception:
            perf_summary = {}

        # Fallback missing numeric fields to 0 if totally empty
        if not perf_summary:
            pass

        # Ledger tables
        # The user requested simulation_ledgers.{strategy_name}_ledger in their prompt,
        # but in previous requests we noted the simulator creates the table without "_ledger".
        # We will use the literal name to be safe since they already corrected this for backtests.
        table_name = strategy_name.lower()
        recent_trades = []
        equity_curve = []
        drawdown_data = []
        monthly_returns = []

        try:
            # Load full ledger via pandas
            df = pd.read_sql_query(
                text(f"SELECT * FROM simulation_ledgers.\"{table_name}\" ORDER BY exit_time ASC"), 
                conn
            )
            
            if not df.empty:
                # Format dates to ISO
                if "exit_time" in df.columns:
                    df["exit_time_str"] = pd.to_datetime(df["exit_time"]).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                if "entry_time" in df.columns:
                    df["entry_time_str"] = pd.to_datetime(df["entry_time"]).dt.strftime('%Y-%m-%dT%H:%M:%SZ')

                # Recent trades
                recent_df = df.sort_values("exit_time", ascending=False).head(3)
                for _, r in recent_df.iterrows():
                    recent_trades.append({
                        "entry_time": r.get("entry_time_str", ""),
                        "exit_time": r.get("exit_time_str", ""),
                        "direction": r.get("direction", ""),
                        "entry_price": r.get("entry_price", 0),
                        "exit_price": r.get("exit_price", 0),
                        "quantity": r.get("quantity", 0),
                        "net_pnl": r.get("net_pnl", 0),
                        "balance_after_trade": r.get("balance_after_trade", 0),
                    })
                
                # Chart Data
                running_max = 0
                for _, r in df.iterrows():
                    bal = float(r.get("balance_after_trade", 0))
                    dt = r.get("exit_time_str", "")
                    
                    equity_curve.append({"date": dt, "value": bal})
                    
                    if bal > running_max:
                        running_max = bal
                    
                    dd = ((bal - running_max) / running_max * 100) if running_max > 0 else 0
                    drawdown_data.append({"date": dt, "value": dd})

                # Monthly Returns
                if "exit_time" in df.columns:
                    df["month"] = pd.to_datetime(df["exit_time"]).dt.strftime('%Y-%m')
                    monthly_df = df.groupby("month")["net_pnl"].sum().reset_index()
                    for _, r in monthly_df.iterrows():
                        monthly_returns.append({
                            "month": r["month"],
                            "return": r["net_pnl"]
                        })

        except Exception as e:
            # Table probably doesn't exist
            pass

    return {
        "configuration": {
            "exchange": config.get("exchange"),
            "symbol": config.get("symbol"),
            "timehorizon": config.get("timehorizon"),
            "long": config.get("long", {}),
            "short": config.get("short", {}),
        },
        "indicators": indicators,
        "performance": perf_summary,
        "recent_trades": recent_trades,
        "chart_data": {
            "equity_curve": equity_curve,
            "drawdown": drawdown_data,
            "monthly_returns": monthly_returns,
        }
    }
