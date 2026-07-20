from simulator.simulator import simulate_strategy
from utils.config import load_config
from utils.db import load_backtest_config


def run_simulator():
    sim_config = load_config("simulator/config.yaml")
    strategies = load_config("signals/config.yaml")
    
    exchange = sim_config.get('exchange', 'binance')
    symbol = sim_config.get('symbol', 'BTC')
    
    all_bt_configs = load_backtest_config()
    
    for strategy_name, strategy_config in strategies.items():
        time_horizon = strategy_config.get('timehorizon', '1m')
        try:
            simulate_strategy(strategy_name, strategy_config, exchange, symbol, time_horizon, sim_config, all_bt_configs)
        except Exception as e:
            print(f"Error simulating {strategy_name}: {e}")

if __name__ == "__main__":
    run_simulator()