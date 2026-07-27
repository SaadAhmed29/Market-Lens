import uuid
import json
from datetime import datetime
from sqlalchemy import text
from utils.db import get_engine

def init_db():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.backtest_requests (
                request_id UUID PRIMARY KEY,
                request_config JSONB,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                strategy_name TEXT,
                result_summary JSONB
            )
        """))

def get_all_requests():
    init_db()
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT request_id, request_config, status, created_at, completed_at, strategy_name, result_summary 
            FROM public.backtest_requests 
            ORDER BY created_at DESC
        """)).mappings().fetchall()
        
    # Convert UUID and datetime to strings for JSON serialization
    return [{
        **dict(row),
        "request_id": str(row["request_id"]),
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None
    } for row in res]

def get_request_detail(request_id: str):
    init_db()
    engine = get_engine()
    
    with engine.connect() as conn:
        req_res = conn.execute(
            text("SELECT * FROM public.backtest_requests WHERE request_id = :req_id"),
            {"req_id": request_id}
        ).mappings().fetchone()
        
        if not req_res:
            return None
            
        request_data = {
            **dict(req_res),
            "request_id": str(req_res["request_id"]),
            "created_at": req_res["created_at"].isoformat() if req_res["created_at"] else None,
            "completed_at": req_res["completed_at"].isoformat() if req_res["completed_at"] else None
        }
        
        strategy_name = req_res["strategy_name"]
        
        # Read ledger
        try:
            ledger_res = conn.execute(
                text(f"SELECT entry_time, exit_time, direction, entry_price, exit_price, quantity, gross_pnl, commission, slippage, net_pnl, balance_after_trade FROM backtest_ledgers.{strategy_name} ORDER BY exit_time ASC")
            ).mappings().fetchall()
            ledger = [dict(row) for row in ledger_res]
        except Exception:
            ledger = []

    # Compute chart data
    equity_curve = []
    drawdown_curve = []
    monthly_returns = []
    win_loss_pie = []

    if ledger:
        import pandas as pd
        from stats.metrics import calculate_metrics

        df = pd.DataFrame(ledger)
        if 'exit_time' in df.columns and 'balance_after_trade' in df.columns and not df.empty:
            df['exit_time'] = pd.to_datetime(df['exit_time'])
            df = df.sort_values('exit_time').set_index('exit_time')

            # Calculate returns
            # Use fillna(0) to handle the first trade NaN if any
            returns = df['balance_after_trade'].pct_change().fillna(0)
            metrics = calculate_metrics(returns)

            # 1. Equity Curve
            equity_curve = [{"date": str(idx), "value": float(val)} for idx, val in df['balance_after_trade'].items()]

            # 2. Drawdown Curve
            dd_series = metrics.get('to_drawdown_series', {})
            drawdown_curve = [{"date": str(k), "value": float(v) * 100} for k, v in dd_series.items()] if dd_series else []

            # 3. Monthly Returns
            mr_df = metrics.get('monthly_returns', {})
            month_map = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06', 
                         'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}
            
            for col_month, year_dict in mr_df.items():
                if col_month in month_map:
                    for year, val in year_dict.items():
                        if val != 0:
                            monthly_returns.append({
                                "month": f"{year}-{month_map[col_month]}",
                                "return": float(val) * 100
                            })
            monthly_returns.sort(key=lambda x: x['month'])

            # 4. Win/Loss Pie
            win_rate = metrics.get('win_rate', 0)
            if win_rate is None:
                win_rate = 0
            total_trades = len(df)
            win_count = int(total_trades * win_rate)
            loss_count = total_trades - win_count
            win_loss_pie = [
                {"name": "WIN", "value": win_count},
                {"name": "LOSS", "value": loss_count}
            ]

            # 5. Update summary metrics dynamically
            summary = request_data.get("result_summary")
            if isinstance(summary, str):
                summary = json.loads(summary)
            if summary is None:
                summary = {}
                
            summary['sharpe'] = metrics.get('sharpe_ratio')
            summary['max_drawdown'] = metrics.get('max_drawdown', 0) * 100 if metrics.get('max_drawdown') is not None else None
            summary['win_rate'] = win_rate * 100
            
            request_data['result_summary'] = summary
    
    return {
        "request": request_data,
        "equity_curve": equity_curve,
        "drawdown": drawdown_curve,
        "monthly_returns": monthly_returns,
        "win_loss": win_loss_pie,
        "ledger": ledger
    }

def get_strategy_options():
    engine = get_engine()
    options = []
    
    with engine.connect() as conn:
        try:
            res = conn.execute(text("SELECT strategy_name, config FROM meta_data.strategies")).mappings().fetchall()
            for row in res:
                config = row.get("config") or {}
                if isinstance(config, str):
                    config = json.loads(config)
                options.append({
                    "strategy_name": row["strategy_name"],
                    "symbol": config.get("symbol", config.get("symbols")),
                    "exchange": config.get("exchange"),
                    "timehorizon": config.get("timehorizon")
                })
        except Exception:
            pass
    return options

def run_backtest_task(req_id: str, config: dict, strategy_name: str):
    engine = get_engine()
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE public.backtest_requests SET status = 'Running' WHERE request_id = :req_id"),
                {"req_id": req_id}
            )

        from backtest.backtest import BacktestEngine

        backtest_engine = BacktestEngine(config)
        results = backtest_engine.run()

        # Re-read ledger and compute metrics the same way as get_request_detail
        result_summary = {
            "total_trades": results.get("total_trades", 0),
            "final_balance": results.get("final_balance", 0)
        }

        try:
            import pandas as pd
            from stats.metrics import calculate_metrics

            with engine.connect() as conn:
                ledger_res = conn.execute(
                    text(f"SELECT net_pnl, balance_after_trade, exit_time FROM backtest_ledgers.{strategy_name} ORDER BY exit_time ASC")
                ).mappings().fetchall()
                ledger = [dict(row) for row in ledger_res]

            if ledger:
                df = pd.DataFrame(ledger)
                df['exit_time'] = pd.to_datetime(df['exit_time'])
                df = df.sort_values('exit_time').set_index('exit_time')

                returns = df['balance_after_trade'].pct_change().fillna(0)

                if not returns.empty and returns.std() != 0:
                    metrics = calculate_metrics(returns)
                else:
                    metrics = {}

                win_rate = metrics.get('win_rate', 0) or 0
                result_summary['sharpe']       = metrics.get('sharpe_ratio')
                result_summary['max_drawdown'] = (metrics.get('max_drawdown', 0) or 0) * 100
                result_summary['win_rate']     = win_rate * 100
                result_summary['final_balance'] = float(df['balance_after_trade'].iloc[-1])

        except Exception as metrics_err:
            print(f"Metrics computation failed: {metrics_err}")

        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE public.backtest_requests 
                    SET status = 'Completed', 
                        completed_at = CURRENT_TIMESTAMP, 
                        result_summary = :result_summary 
                    WHERE request_id = :req_id
                """),
                {
                    "result_summary": json.dumps(result_summary),
                    "req_id": req_id
                }
            )

    except Exception as e:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE public.backtest_requests 
                    SET status = 'Failed', 
                        completed_at = CURRENT_TIMESTAMP, 
                        result_summary = :error_summary 
                    WHERE request_id = :req_id
                """),
                {
                    "error_summary": json.dumps({"error": str(e)}),
                    "req_id": req_id
                }
            )

def submit_backtest(config: dict, background_tasks):
    init_db()
    req_id = str(uuid.uuid4())
    strategy_name = config.get("strategy_name")
    
    engine = get_engine()
    
    # Fetch strategy_config from meta_data.strategies
    with engine.connect() as conn:
        try:
            res = conn.execute(
                text("SELECT config FROM meta_data.strategies WHERE strategy_name = :strategy_name LIMIT 1"),
                {"strategy_name": strategy_name}
            ).mappings().fetchone()
            
            if res and res.get("config"):
                strat_config = res["config"]
                if isinstance(strat_config, str):
                    strat_config = json.loads(strat_config)
                config["strategy_config"] = strat_config
        except Exception as e:
            pass
            
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.backtest_requests (request_id, request_config, status, strategy_name)
                VALUES (:req_id, :config, 'Pending', :strategy_name)
            """),
            {
                "req_id": req_id,
                "config": json.dumps(config),
                "strategy_name": strategy_name
            }
        )
    background_tasks.add_task(run_backtest_task, req_id, config, strategy_name)
    return req_id
