import logging
import os
from execution.execution import execute_strategy
from utils.db import load_strategies_config, load_backtest_config

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "execution.log")),
            logging.StreamHandler()
        ]
    )

def run_execution():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting live execution runner...")
    
    strategies = load_strategies_config()
    all_bt_configs = load_backtest_config()
    
    from utils.db import get_engine
    from sqlalchemy import text
    engine = get_engine()
    
    bybit_strategies = [s for s in strategies if s['config'].get('exchange') == 'bybit']
    symbols = list(set(s['config'].get('symbol') for s in bybit_strategies if s['config'].get('symbol')))
    
    for symbol in symbols:
        symbol_strategies = [s for s in bybit_strategies if s['config'].get('symbol') == symbol]
        if not symbol_strategies:
            continue
            
        strategy_names = [s['strategy_name'] for s in symbol_strategies]
        placeholders = ", ".join([f":name_{i}" for i in range(len(strategy_names))])
        params = {f"name_{i}": name for i, name in enumerate(strategy_names)}
        
        open_pos = None
        try:
            with engine.connect() as conn:
                query = text(f"SELECT strategy_name FROM execution.positions WHERE status = 'Open' AND strategy_name IN ({placeholders})")
                open_pos = conn.execute(query, params).fetchone()
        except Exception:
            pass
            
        if open_pos:
            # An open position exists for this symbol -- don't skip entirely.
            # We still need to run that strategy so it can monitor/close the
            # position (TP/SL hit, manually closed, etc.) and keep stats
            # up to date. We just don't evaluate new entry signals for a
            # *different* strategy on the same symbol while one is live.
            monitoring_strategy_name = open_pos[0]
            matching = [s for s in symbol_strategies if s['strategy_name'] == monitoring_strategy_name]

            if not matching:
                logger.warning(
                    f"Open position found for {monitoring_strategy_name} but no "
                    f"matching strategy config for {symbol}. Skipping."
                )
                continue

            strategy_config = matching[0]['config']
            exchange = strategy_config['exchange']
            time_horizon = strategy_config['timehorizon']

            logger.info(f"Monitoring open position for {monitoring_strategy_name} on {symbol}")
            try:
                execute_strategy(
                    monitoring_strategy_name, strategy_config, exchange, symbol,
                    time_horizon, all_bt_configs
                )
            except Exception as e:
                logger.error(f"Error monitoring {monitoring_strategy_name}: {e}")
            continue
            
        stats_map = {}
        try:
            with engine.connect() as conn:
                query = text(f"SELECT strategy_name, comp FROM simulation.stats WHERE strategy_name IN ({placeholders})")
                stats_rows = conn.execute(query, params).fetchall()
                stats_map = {row[0]: row[1] for row in stats_rows}
        except Exception:
            pass
            
        def get_comp(strat):
            val = stats_map.get(strat['strategy_name'])
            return float('-inf') if val is None else float(val)
            
        has_stats = len(stats_map) > 0
        if has_stats:
            ranked_strategies = sorted(symbol_strategies, key=get_comp, reverse=True)
        else:
            ranked_strategies = symbol_strategies
            
        selected_strategy = None
        selection_reason = ""
        
        for i, strat in enumerate(ranked_strategies):
            if strat['config'].get('allow_execution', False):
                selected_strategy = strat
                if not has_stats:
                    selection_reason = "default (no stats available)"
                elif i == 0:
                    selection_reason = f"best by stat (comp: {get_comp(strat)})"
                else:
                    selection_reason = f"fallback (comp: {get_comp(strat)})"
                break
                
        if not selected_strategy:
            logger.warning(f"Skipping {symbol} - no strategy with allow_execution=True found")
            continue
            
        strategy_name = selected_strategy['strategy_name']
        strategy_config = selected_strategy['config']
        exchange = strategy_config['exchange']
        time_horizon = strategy_config['timehorizon']
        
        logger.info(f"Selected strategy {strategy_name} for {symbol} - Reason: {selection_reason}")
        
        try:
            execute_strategy(strategy_name, strategy_config, exchange, symbol, time_horizon, all_bt_configs)
        except Exception as e:
            logger.error(f"Error executing {strategy_name}: {e}")

if __name__ == "__main__":
    run_execution()