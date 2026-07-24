"""
MarketLens — Dashboard Module
Aggregates all data required by the /api/dashboard endpoint.
"""

import sys
import yaml
import json
from pathlib import Path

from sqlalchemy import text

# Path setup: allow imports from project root regardless of how this module
# is imported (e.g. when FastAPI is launched from backend/).
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.db import get_engine  # noqa: E402

# Path to the ML config relative to project root
ML_CONFIG_PATH = ROOT / "ml" / "config.yaml"


# Individual data-fetching helpers

def count_rows(conn, query: str, params: dict | None = None) -> int:
    """Execute a COUNT query and return the scalar result, defaulting to 0."""
    try:
        result = conn.execute(text(query), params or {})
        return result.scalar() or 0
    except Exception:
        return 0


def fetch_ml_models() -> int:
    """
    Parse ml/config.yaml and return the count of all models from the classification,
    regression, and timeseries blocks.
    """
    try:
        with open(ML_CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"ML config not found at expected path: {ML_CONFIG_PATH}")
        return 0

    models: list[dict] = []
    model_blocks = config.get("models", {})

    for model_type, entries in model_blocks.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            name = entry.get("name") if isinstance(entry, dict) else str(entry)
            if name:
                models.append({"name": name, "type": model_type})

    count = len(models)

    return count


def fetch_strategy_table(conn) -> list[dict]:
    """
    Return one row per strategy from meta_data.strategies, enriched with
    live status (simulation.positions) and latest performance metrics
    (simulation.stats).
    """
    try:
        strategy_rows = conn.execute(
            text("SELECT strategy_name, config FROM meta_data.strategies")
        ).mappings().fetchall()
    except Exception:
        return []

    if not strategy_rows:
        return []

    # Pull all relevant positions and stats in two bulk queries to avoid N+1.
    try:
        pos_rows = conn.execute(
            text("SELECT strategy_name, status FROM simulation.positions")
        ).mappings().fetchall()
        position_status: dict[str, str] = {
            r["strategy_name"]: r["status"] for r in pos_rows
        }
    except Exception:
        position_status = {}

    try:
        stats_rows = conn.execute(
            text(
                "SELECT strategy_name, total_trades, avg_return, sharpe_ratio, win_rate "
                "FROM simulation.stats"
            )
        ).mappings().fetchall()
        stats_map: dict[str, dict] = {r["strategy_name"]: dict(r) for r in stats_rows}
    except Exception:
        stats_map = {}

    strategies: list[dict] = []
    for row in strategy_rows:
        name = row["strategy_name"]
        cfg = row["config"] or {}

        # config may already be a dict (JSONB auto-decoded) or a raw JSON string
        if isinstance(cfg, str):
            import json
            try:
                cfg = json.loads(cfg)
            except Exception:
                cfg = {}

        stats = stats_map.get(name, {})

        strategies.append(
            {
                "strategy_name": name,
                "symbol": cfg.get("symbol", "N/A"),
                "exchange": cfg.get("exchange", "N/A"),
                "timehorizon": cfg.get("timehorizon", "N/A"),
                "total_trades": stats.get("total_trades") or 0,
                "status": position_status.get(name, "inactive"),
                "latest_return": stats.get("avg_return") or 0,
                "sharpe_ratio": stats.get("sharpe_ratio") or 0,
                "win_rate": stats.get("win_rate") or 0,
            }
        )

    return strategies


# Main entry point

def get_dashboard_data() -> dict:
    """
    Aggregate all dashboard widgets and return a single dict.
    Uses the shared SQLAlchemy engine from utils/db.py for all DB queries.
    Falls back to sensible defaults (0 / empty list / "N/A") on any failure.
    """
    engine = get_engine()

    with engine.connect() as conn:
        # Scalar counters 

        total_strategies = count_rows(
            conn, "SELECT COUNT(*) FROM meta_data.strategies"
        )

        active_strategies = count_rows(
            conn,
            "SELECT COUNT(DISTINCT strategy_name) FROM simulation.positions "
            "WHERE LOWER(status) = 'open'",
        )

        running_executions = count_rows(
            conn,
            "SELECT COUNT(DISTINCT strategy_name) FROM execution.positions "
            "WHERE LOWER(status) = 'open'",
        )

        total_trades_executed = count_rows(conn, "SELECT SUM(total_trades) FROM execution.stats", )

        running_simulations = count_rows(
            conn,
            "SELECT COUNT(DISTINCT strategy_name) FROM simulation.positions",
        )

        total_trades_simulated = count_rows(conn, "SELECT SUM(total_trades) FROM simulation.stats", )

        connected_accounts = count_rows(
            conn, "SELECT COUNT(*) FROM accounts.api"
        )

        total_backtests = count_rows(
            conn,
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'backtest_ledgers'
            """,
        )

        # Portfolio stats from accounts.main_stats
        total_return: float = 0.0
        try:
            stats_row = conn.execute(
                text(
                    "SELECT total_realized_pnl "
                    "FROM accounts.main_stats "
                    "LIMIT 1"
                )
            ).mappings().fetchone()
            if stats_row:
                total_return = float(stats_row["total_realized_pnl"] or 0)
        except Exception:
            pass  # table may not exist yet; defaults are already set

        # Strategy table 
        strategy_table = fetch_strategy_table(conn)

    # ML models (file-based, no DB)
    ml_models = fetch_ml_models()

    return {
        "total_strategies": total_strategies,
        "active_strategies": active_strategies,
        "running_executions": running_executions,
        "total_trades_executed": total_trades_executed,
        "running_simulations": running_simulations,
        "total_trades_simulated": total_trades_simulated,
        "connected_accounts": connected_accounts,
        "total_backtests": total_backtests,
        "total_return": total_return,
        "trained_ml_models": ml_models,
        "strategies": strategy_table,
    }
