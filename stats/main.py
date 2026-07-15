import os
import sys
import json
import pandas as pd

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from stats.utils import ledger_to_returns
    from stats.metrics import calculate_metrics
    from stats.plots import generate_plots
except ImportError:
    from .utils import ledger_to_returns
    from .metrics import calculate_metrics
    from .plots import generate_plots

def generate_stats(results, strategy_name='strategy'):
    """
    Accepts the return from BacktestEngine's run() method or a trade ledger DataFrame,
    calculates metrics and plots, and saves them to stats/output/.
    """
    # Accept either the results dict from BacktestEngine or the ledger df directly
    if isinstance(results, dict) and 'trade_ledger' in results:
        ledger_df = results['trade_ledger']
    elif isinstance(results, pd.DataFrame):
        ledger_df = results
    else:
        raise ValueError("Expected results dict from BacktestEngine or trade ledger DataFrame")
        
    if ledger_df is None or ledger_df.empty:
        print("No trades found in ledger. Skipping stats generation.")
        return {}
        
    # Get the directory of this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert ledger to daily returns
    returns = ledger_to_returns(ledger_df)
    
    if returns.empty:
        print("Not enough data to calculate daily returns.")
        return {}
        
    # Calculate Metrics
    metrics = calculate_metrics(returns)
    
    # Save metrics to JSON
    json_path = os.path.join(output_dir, f"{strategy_name}_stats.json")
    with open(json_path, 'w') as f:
        json.dump(metrics, f, indent=4)
        
    # Generate Plots
    generate_plots(returns, output_dir)
    
    return metrics

if __name__ == '__main__':
    from utils.db import run_cli, create_backtest_config_table, load_backtest_config
    try:
        from backtest.backtest import BacktestEngine
    except ImportError:
        import sys
        sys.exit("Could not import BacktestEngine.")
        
    try:
        # Prompt user for backtest configuration
        options = ['strategy', 'exchange', 'symbols', 'start_date', 'end_date']
        cli_config = run_cli(options)
        
        strategy_name = cli_config.get('strategy_name', 'default_strategy')
        
        # Load strategy-specific config
        create_backtest_config_table()
        all_configs = load_backtest_config()
        
        config = all_configs.get(cli_config.get('strategy_id'), {})
        if isinstance(config, str):
            config = json.loads(config)
            
        config.update(cli_config)
        
        sym_val = config.get('symbols')
        if isinstance(sym_val, list) and len(sym_val) > 0:
            config['symbol'] = sym_val[0]
        elif sym_val:
            config['symbol'] = sym_val
            
        print(f"\nRunning backtest for strategy: {strategy_name}...")
        engine = BacktestEngine(config)
        results = engine.run()
        
        print(f"Generating stats...")
        metrics = generate_stats(results, strategy_name)
        
        ledger_df = results.get('trade_ledger', pd.DataFrame())
        
        if metrics:
            print(f"\nStats generated successfully in stats/output/!")
            if 'total_trades' in ledger_df.columns or not ledger_df.empty:
                print(f"Total Trades: {len(ledger_df)}")
                
            win_rate = metrics.get('win_rate')
            if win_rate is not None:
                print(f"Win Rate: {win_rate:.2%}")
                
            sharpe = metrics.get('sharpe_ratio')
            if sharpe is not None:
                print(f"Sharpe Ratio: {sharpe:.2f}")
                
            max_dd = metrics.get('max_drawdown')
            if max_dd is not None:
                print(f"Max Drawdown: {max_dd:.2%}")
                
    except KeyboardInterrupt:
        print("\nCancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
