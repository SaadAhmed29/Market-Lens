import logging
import os
from simulator.simulator import simulate_strategy
from utils.config import load_config
from utils.db import load_backtest_config, load_strategies_config

def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "simulation.log")),
            logging.StreamHandler()
        ]
    )

def run_simulator():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    sim_config = load_config("simulator/config.yaml")
    strategies = load_strategies_config()
    all_bt_configs = load_backtest_config()
    
    for strategy in strategies:
        strategy_name = strategy['strategy_name']
        strategy_config = strategy['config']
        exchange = strategy_config['exchange']
        symbol = strategy_config['symbol']
        time_horizon = strategy_config['timehorizon']

        sim_permission = strategy_config['allow_simulation']
        if not sim_permission:
            logger.info(f"Skipping {strategy_name} - not allowed for simulation")
            continue

        try:
            simulate_strategy(strategy_name, strategy_config, exchange, symbol, time_horizon, sim_config, all_bt_configs)
        except Exception as e:
            logger.error(f"Error simulating {strategy_name}: {e}")

if __name__ == "__main__":
    run_simulator()