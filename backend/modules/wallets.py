from sqlalchemy import text
from utils.db import get_engine
import json

def get_all_wallets():
    engine = get_engine()
    wallets = []
    
    with engine.connect() as conn:
        try:
            accounts_res = conn.execute(text("SELECT account_name FROM accounts.api")).mappings().fetchall()
        except Exception:
            accounts_res = []
            
        for account in accounts_res:
            acc_name = account["account_name"]
            
            wallet_balance = 0.0
            unrealized_pnl = 0.0
            total_realized_pnl = 0.0
            
            try:
                stats_res = conn.execute(
                    text(f"SELECT wallet_balance, total_unrealized_pnl, total_realized_pnl FROM accounts.{acc_name}_stats LIMIT 1")
                ).mappings().fetchone()
                if stats_res:
                    wallet_balance = float(stats_res.get("wallet_balance") or 0.0)
                    unrealized_pnl = float(stats_res.get("total_unrealized_pnl") or 0.0)
                    total_realized_pnl = float(stats_res.get("total_realized_pnl") or 0.0)
            except Exception:
                pass
                
            total_strategies = 0
            try:
                strat_res = conn.execute(
                    text("SELECT COUNT(*) FROM meta_data.strategies WHERE config->>'exchange' = 'bybit'")
                ).scalar()
                total_strategies = int(strat_res) if strat_res else 0
            except Exception:
                pass
                
            active_positions = 0
            try:
                pos_res = conn.execute(
                    text("SELECT COUNT(*) FROM execution.positions")
                ).scalar()
                active_positions = int(pos_res) if pos_res else 0
            except Exception:
                pass
                
            open_orders = 0
            try:
                orders_res = conn.execute(
                    text("SELECT COUNT(*) FROM execution.positions WHERE status = 'Open'")
                ).scalar()
                open_orders = int(orders_res) if orders_res else 0
            except Exception:
                pass
                
            wallets.append({
                "account_name": acc_name,
                "exchange": "bybit",
                "account_type": "demo",
                "wallet_balance": wallet_balance,
                "unrealized_pnl": unrealized_pnl,
                "total_realized_pnl": total_realized_pnl,
                "total_strategies": total_strategies,
                "active_positions": active_positions,
                "open_orders": open_orders
            })
            
    return wallets


def get_wallet_detail(account_name: str):
    engine = get_engine()
    
    # Default stats to 0
    stats = {
        "wallet_balance": 0.0,
        "total_unrealized_pnl": 0.0,
        "total_realized_pnl": 0.0,
        "total_equity": 0.0,
        "available_balance": 0.0,
        "margin_balance": 0.0,
        "maintenance_margin": 0.0,
        "initial_margin": 0.0
    }
    history = []
    
    with engine.connect() as conn:
        try:
            stats_res = conn.execute(
                text(f"SELECT * FROM accounts.{account_name}_stats LIMIT 1")
            ).mappings().fetchone()
            
            if stats_res:
                for k, v in stats_res.items():
                    stats[k] = v if v is not None else 0.0
        except Exception:
            pass
            
        try:
            history_res = conn.execute(
                text(f"SELECT order_id, symbol, side, price, qty, fee, exec_time, order_type, is_maker FROM accounts.{account_name}_history ORDER BY exec_time DESC")
            ).mappings().fetchall()
            history = [dict(r) for r in history_res]
        except Exception:
            pass
            
    return {"stats": stats, "history": history}


def update_wallet_keys(account_name: str, api_key: str, api_secret: str):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE accounts.api 
                    SET bybit_api_key = :api_key, bybit_api_secret = :api_secret 
                    WHERE account_name = :account_name
                """),
                {"api_key": api_key, "api_secret": api_secret, "account_name": account_name}
            )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}

def get_unassigned_strategies():
    engine = get_engine()
    strategies = []
    
    with engine.connect() as conn:
        try:
            res = conn.execute(
                text("SELECT strategy_name, config FROM meta_data.strategies WHERE config->>'allow_execution' = 'false' OR config->>'allow_simulation' = 'false'")
            ).mappings().fetchall()
            
            for row in res:
                config = row["config"]
                if isinstance(config, str):
                    config = json.loads(config)
                    
                strategies.append({
                    "strategy_name": row["strategy_name"],
                    "symbol": config.get("symbol", ""),
                    "exchange": config.get("exchange", ""),
                    "timehorizon": config.get("timehorizon", ""),
                    "allow_execution": config.get("allow_execution", False),
                    "allow_simulation": config.get("allow_simulation", False)
                })
        except Exception:
            pass
            
    return strategies

def assign_strategy(strategy_name: str, allow_execution: bool, allow_simulation: bool):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            res = conn.execute(
                text("SELECT config FROM meta_data.strategies WHERE strategy_name = :strategy_name"),
                {"strategy_name": strategy_name}
            ).mappings().fetchone()
            
            if not res:
                return {"success": False, "message": "Strategy not found"}
                
            config = res["config"]
            if isinstance(config, str):
                config = json.loads(config)
                
            config["allow_execution"] = allow_execution
            config["allow_simulation"] = allow_simulation
            
            conn.execute(
                text("UPDATE meta_data.strategies SET config = :config WHERE strategy_name = :strategy_name"),
                {"config": json.dumps(config), "strategy_name": strategy_name}
            )
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}
