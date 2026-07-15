import os
import quantstats as qs
import matplotlib.pyplot as plt
import pandas as pd

def generate_plots(returns: pd.Series, output_dir: str):
    """
    Generates and saves quantstats plots (excluding monte carlo) to the output directory.
    Saves each plot as a PNG file named after the plot type.
    """
    if returns is None or returns.empty:
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Use Agg backend to prevent plots from trying to open interactively
    plt.switch_backend('Agg')
    
    try:
        qs.plots.returns(returns, savefig=os.path.join(output_dir, 'returns.png'), show=False)
        qs.plots.log_returns(returns, savefig=os.path.join(output_dir, 'log_returns.png'), show=False)
        qs.plots.drawdown(returns, savefig=os.path.join(output_dir, 'drawdown.png'), show=False)
        qs.plots.monthly_heatmap(returns, savefig=os.path.join(output_dir, 'monthly_returns_heatmap.png'), show=False)
        qs.plots.yearly_returns(returns, savefig=os.path.join(output_dir, 'yearly_returns.png'), show=False)
    except Exception as e:
        print(f"Warning: Failed to generate some plots: {e}")
    finally:
        plt.close('all')