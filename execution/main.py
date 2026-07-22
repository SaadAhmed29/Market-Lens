import logging
import os
from execution.execution import execute_strategy
from utils.config import load_strategies_config, load_backtest_config

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
    
    for strategy in strategies:
        strategy_name = strategy['strategy_name']
        strategy_config = strategy['config']
        exchange = strategy_config['exchange']
        symbol = strategy_config['symbol']
        time_horizon = strategy_config['timehorizon']

        try:
            execute_strategy(strategy_name, strategy_config, exchange, symbol, time_horizon, all_bt_configs)
        except Exception as e:
            logger.error(f"Error executing {strategy_name}: {e}")

if __name__ == "__main__":
    run_execution()