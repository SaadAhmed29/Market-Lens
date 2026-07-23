"""
MarketLens — Account-level Stats
Fetches raw execution / order / PnL history from Bybit per account,
computes comprehensive stats, and upserts them into accounts.{name}_stats.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import pandas as pd
from pybit.unified_trading import HTTP
from sqlalchemy import text

# Ensure project root is on sys.path
root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from ml.utils.logging import get_logger
from utils.db import (
    get_engine,
    create_accounts_schema,
    create_account_history_table,
    create_account_stats_table,
    load_api_credentials,
)

logger = get_logger("account_stats")

# helpers

def paginate(api_call, category="linear", **extra) -> list[dict]:
    """Generic paginator for Bybit v5 list endpoints (cursor-based)."""
    all_rows: list[dict] = []
    cursor = ""
    while True:
        kwargs = {"category": category, "limit": 100, **extra}
        if cursor:
            kwargs["cursor"] = cursor
        resp = api_call(**kwargs)
        result = resp.get("result", {})
        rows = result.get("list", [])
        if not rows:
            break
        all_rows.extend(rows)
        cursor = result.get("nextPageCursor", "")
        if not cursor:
            break
    return all_rows


# History Fetch & Store

def fetch_and_store_history(client: HTTP, account_name: str) -> None:
    """Paginate get_executions and upsert into accounts.{account_name}_history."""
    create_account_history_table(account_name)
    table = f"{account_name.lower()}_history"
    engine = get_engine()

    rows = paginate(client.get_executions, category="linear")
    logger.info(f"[{account_name}] Fetched {len(rows)} execution records from Bybit.")

    if not rows:
        return

    insert_sql = text(f"""
        INSERT INTO accounts.{table}
            (exec_id, order_id, symbol, side, price, qty, fee, fee_rate,
             exec_time, order_type, is_maker)
        VALUES
            (:exec_id, :order_id, :symbol, :side, :price, :qty, :fee, :fee_rate,
             :exec_time, :order_type, :is_maker)
        ON CONFLICT (exec_id) DO UPDATE SET
            price      = EXCLUDED.price,
            qty        = EXCLUDED.qty,
            fee        = EXCLUDED.fee,
            fee_rate   = EXCLUDED.fee_rate,
            exec_time  = EXCLUDED.exec_time,
            order_type = EXCLUDED.order_type,
            is_maker   = EXCLUDED.is_maker
    """)

    records = []
    for r in rows:
        exec_time_ms = r.get("execTime")
        exec_time = (
            pd.to_datetime(int(exec_time_ms), unit="ms", utc=True)
            if exec_time_ms
            else None
        )
        records.append({
            "exec_id":    r.get("execId"),
            "order_id":   r.get("orderId"),
            "symbol":     r.get("symbol"),
            "side":       r.get("side"),
            "price":      float(r.get("execPrice", 0)),
            "qty":        float(r.get("execQty", 0)),
            "fee":        float(r.get("execFee", 0)),
            "fee_rate":   float(r.get("feeRate", 0)),
            "exec_time":  exec_time,
            "order_type": r.get("orderType"),
            "is_maker":   r.get("isMaker", "false").lower() == "true" if isinstance(r.get("isMaker"), str) else bool(r.get("isMaker", False)),
        })

    with engine.begin() as conn:
        conn.execute(insert_sql, records)

    logger.info(f"[{account_name}] Upserted {len(records)} rows into accounts.{table}.")


# Stats: closed PnL

def calc_closed_pnl_stats(client: HTTP) -> dict:
    """Compute stats from get_closed_pnl (trade-level P&L records)."""
    rows = paginate(client.get_closed_pnl, category="linear")
    if not rows:
        return {}

    pnls = []
    symbols_pnl = defaultdict(float)
    side_pnl = defaultdict(float)
    hour_pnl = defaultdict(float)
    dow_pnl = defaultdict(float)
    holding_times = []

    for r in rows:
        pnl = float(r.get("closedPnl", 0))
        pnls.append(pnl)
        sym = r.get("symbol", "")
        side = r.get("side", "")
        symbols_pnl[sym] += pnl
        side_pnl[side] += pnl

        created_ms = r.get("createdTime")
        updated_ms = r.get("updatedTime")
        if created_ms and updated_ms:
            t_open = pd.to_datetime(int(created_ms), unit="ms", utc=True)
            t_close = pd.to_datetime(int(updated_ms), unit="ms", utc=True)
            holding_times.append((t_close - t_open).total_seconds())
            hour_pnl[str(t_close.hour)] += pnl
            dow_pnl[str(t_close.day_name())] += pnl

    total_pnl = sum(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    n = len(pnls)

    win_rate = len(wins) / n if n else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    largest_win = max(wins) if wins else 0.0
    largest_loss = min(losses) if losses else 0.0
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
    expectancy = total_pnl / n if n else 0.0

    # Streaks
    max_w, max_l, cur_w, cur_l = 0, 0, 0, 0
    for p in pnls:
        if p > 0:
            cur_w += 1
            cur_l = 0
        else:
            cur_l += 1
            cur_w = 0
        max_w = max(max_w, cur_w)
        max_l = max(max_l, cur_l)

    avg_hold = sum(holding_times) / len(holding_times) if holding_times else 0.0

    # Trades per day
    if len(rows) >= 2:
        first_ms = min(int(r.get("createdTime", 0)) for r in rows if r.get("createdTime"))
        last_ms = max(int(r.get("updatedTime", 0)) for r in rows if r.get("updatedTime"))
        span_days = max((last_ms - first_ms) / 86_400_000, 1)
        tpd = n / span_days
    else:
        tpd = float(n)

    return {
        "total_realized_pnl": round(total_pnl, 4),
        "win_rate":           round(win_rate, 4),
        "avg_win":            round(avg_win, 4),
        "avg_loss":           round(avg_loss, 4),
        "largest_win":        round(largest_win, 4),
        "largest_loss":       round(largest_loss, 4),
        "profit_factor":      round(profit_factor, 4),
        "expectancy":         round(expectancy, 4),
        "max_win_streak":     max_w,
        "max_loss_streak":    max_l,
        "avg_holding_time_seconds": round(avg_hold, 2),
        "trades_per_day":     round(tpd, 4),
        "pnl_by_symbol":      json.dumps(dict(symbols_pnl)),
        "pnl_by_side":        json.dumps(dict(side_pnl)),
        "pnl_by_hour":        json.dumps(dict(hour_pnl)),
        "pnl_by_dow":         json.dumps(dict(dow_pnl)),
    }


# Stats: execution fills

def calc_execution_stats(client: HTTP, account_name: str) -> dict:
    """Compute fee / volume / slippage stats from the stored history table."""
    engine = get_engine()
    table = f"{account_name.lower()}_history"

    try:
        df = pd.read_sql(f"SELECT * FROM accounts.{table}", engine)
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        return {}

    total_fees = float(df["fee"].sum())
    total_volume = float((df["price"] * df["qty"]).sum())
    fees_pct = (total_fees / total_volume * 100) if total_volume else 0.0
    avg_size = float((df["price"] * df["qty"]).mean())

    maker_count = int(df["is_maker"].sum())
    n = len(df)
    maker_ratio = maker_count / n if n else 0.0
    taker_ratio = 1.0 - maker_ratio

    # Real slippage: compare exec price in history to predicted entry_price
    # stored in execution_ledgers by matching order_id → trade_id.
    slippage_avg = 0.0
    try:
        ledger_tables = pd.read_sql(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'execution_ledgers'",
            engine,
        )
        if not ledger_tables.empty:
            all_ledger = []
            for tbl in ledger_tables["tablename"]:
                try:
                    chunk = pd.read_sql(f"SELECT trade_id, entry_price FROM execution_ledgers.{tbl}", engine)
                    all_ledger.append(chunk)
                except Exception:
                    pass
            if all_ledger:
                ledger = pd.concat(all_ledger, ignore_index=True)
                merged = df.merge(ledger, left_on="order_id", right_on="trade_id", how="inner")
                if not merged.empty:
                    merged["slip"] = (merged["price"] - merged["entry_price"]).abs()
                    slippage_avg = float(merged["slip"].mean())
    except Exception as e:
        logger.debug(f"Slippage calc skipped: {e}")

    return {
        "total_fees_paid":     round(total_fees, 4),
        "total_volume_traded": round(total_volume, 4),
        "fees_pct_of_volume":  round(fees_pct, 4),
        "avg_trade_size":      round(avg_size, 4),
        "maker_fill_ratio":    round(maker_ratio, 4),
        "taker_fill_ratio":    round(taker_ratio, 4),
        "real_slippage_avg":   round(slippage_avg, 6),
    }


# Stats: order history

def calc_order_stats(client: HTTP) -> dict:
    """Compute fill / status / type breakdowns from get_order_history."""
    rows = paginate(client.get_order_history, category="linear")
    if not rows:
        return {}

    n = len(rows)
    status_counts = defaultdict(int)
    type_counts = defaultdict(int)

    for r in rows:
        status_counts[r.get("orderStatus", "Unknown")] += 1
        type_counts[r.get("orderType", "Unknown")] += 1

    filled = status_counts.get("Filled", 0)
    fill_rate = filled / n if n else 0.0

    return {
        "fill_rate":               round(fill_rate, 4),
        "order_status_breakdown":  json.dumps(dict(status_counts)),
        "order_type_breakdown":    json.dumps(dict(type_counts)),
    }


# Live Snapshot

def calc_live_snapshot(client: HTTP) -> dict:
    """Current positions + wallet balance snapshot."""
    # Positions
    pos_count = 0
    notional = 0.0
    unrealized = 0.0
    try:
        resp = client.get_positions(category="linear", settleCoin="USDT")
        for p in resp.get("result", {}).get("list", []):
            size = float(p.get("size", 0))
            if size > 0:
                pos_count += 1
                notional += float(p.get("positionValue", 0))
                unrealized += float(p.get("unrealisedPnl", 0))
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")

    # Wallet
    wallet_bal = 0.0
    avail_bal = 0.0
    try:
        w = client.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        for acct in w.get("result", {}).get("list", []):
            avail_bal = float(acct.get("totalAvailableBalance") or 0)
            for c in acct.get("coin", []):
                if c["coin"] == "USDT":
                    wallet_bal = float(c.get("walletBalance") or 0.0)
    except Exception as e:
        logger.error(f"Error fetching wallet balance: {e}")

    return {
        "open_position_count":     pos_count,
        "total_notional_exposure": round(notional, 4),
        "total_unrealized_pnl":    round(unrealized, 4),
        "wallet_balance":          round(wallet_bal, 4),
        "available_balance":       round(avail_bal, 4),
    }


# Sanitize for SQL

def sanitize_for_sql(stats: dict) -> dict:
    """Convert any numpy scalar types to native Python types before
    they're passed as SQL bind parameters."""
    clean = {}
    for k, v in stats.items():
        if hasattr(v, "item") and not isinstance(v, (dict, list)):
            clean[k] = v.item()
        else:
            clean[k] = v
    return clean


# Combine & Upsert

def compute_and_store(account_name: str, client: HTTP) -> None:
    """Run the full stats pipeline for one account and upsert results."""
    create_account_stats_table(account_name)
    table = f"{account_name.lower()}_stats"
    engine = get_engine()

    logger.info(f"[{account_name}] Fetching execution history...")
    fetch_and_store_history(client, account_name)

    logger.info(f"[{account_name}] Computing closed PnL stats...")
    stats = calc_closed_pnl_stats(client)

    logger.info(f"[{account_name}] Computing execution stats...")
    stats.update(calc_execution_stats(client, account_name))

    logger.info(f"[{account_name}] Computing order stats...")
    stats.update(calc_order_stats(client))

    logger.info(f"[{account_name}] Taking live snapshot...")
    stats.update(calc_live_snapshot(client))

    stats["last_updated"] = datetime.now(timezone.utc)
    stats = sanitize_for_sql(stats)

    # Build dynamic upsert
    cols = list(stats.keys())
    placeholders = ", ".join([f":{c}" for c in cols])
    col_names = ", ".join(cols)
    update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols])

    upsert_sql = text(f"""
        INSERT INTO accounts.{table} (id, {col_names})
        VALUES (1, {placeholders})
        ON CONFLICT (id) DO UPDATE SET {update_clause}
    """)

    with engine.begin() as conn:
        conn.execute(upsert_sql, stats)

    logger.info(f"[{account_name}] Stats upserted into accounts.{table}.")


# Entry Point

def run_account_stats() -> None:
    """Load all accounts, init a client per account, compute & store stats."""
    create_accounts_schema()
    creds = load_api_credentials()

    if not creds:
        logger.warning("No API credentials found in accounts.api. Nothing to do.")
        return

    for acct in creds:
        name = acct["account_name"]
        logger.info(f"Processing account: {name}")
        try:
            client = HTTP(
                testnet=False,
                demo=True,
                api_key=acct["bybit_api_key"],
                api_secret=acct["bybit_api_secret"],
                timeout=10,
            )
            compute_and_store(name, client)
        except Exception as e:
            logger.error(f"[{name}] Failed: {e}", exc_info=True)

    logger.info("All accounts processed.")


if __name__ == "__main__":
    run_account_stats()
