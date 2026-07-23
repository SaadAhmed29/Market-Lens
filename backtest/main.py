import argparse
import sys
import json
from pathlib import Path

def _ensure_import_path():
    # Ensure project root is on sys.path when running the script directly
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

def main():
    _ensure_import_path()
    try:
        from backtest.backtest import BacktestEngine
    except Exception:
        # As a fallback, try importing using relative path
        from backtest.backtest import BacktestEngine

    from utils.db import run_cli, create_backtest_config_table, load_backtest_config, get_engine
    from sqlalchemy import text

    parser = argparse.ArgumentParser(description="Run backtest pipeline")
    args = parser.parse_args()

    # Prompt user for CLI inputs first, since we now need the strategy name
    # to look up which backtest_config row to use
    options = ['strategy', 'exchange', 'symbols', 'start_date', 'end_date', 'timehorizon']
    cli_config = run_cli(options)

    # Load backtest config from DB for parameters like initial_balance, position_size, take_profit, stop_loss
    create_backtest_config_table()
    all_configs = load_backtest_config()

    # Resolve the strategy_id matching the given strategy name, then pick that row's config
    config = all_configs.get(cli_config.get('strategy_id'), {})
    if isinstance(config, str):
        config = json.loads(config)

    # Merge CLI config into the main config
    config.update(cli_config)
    
    # 'symbols' returns a list when using run_cli (or single string from our previous change). 
    # Let's ensure it's mapped to 'symbol' as the engine expects.
    sym_val = config.get('symbols')
    if isinstance(sym_val, list) and len(sym_val) > 0:
        config['symbol'] = sym_val[0]
    elif sym_val:
        config['symbol'] = sym_val

    engine = BacktestEngine(config)
    results = engine.run()
    print(results.get('trade_ledger'))
    print("Final balance:", results.get('final_balance'))
    print("Total net profit:", results.get('total_net_profit'))
    print(f"Trades: {results.get('total_trades')} | Wins: {results.get('win_count')} | Losses: {results.get('loss_count')}")

if __name__ == "__main__":
    main()