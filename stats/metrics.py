import quantstats as qs
import pandas as pd
import numpy as np

def calculate_metrics(returns: pd.Series) -> dict:
    """
    Computes all available quantstats metrics excluding monte carlo simulations.
    Returns all results as a flat dictionary.
    """
    if returns is None or returns.empty:
        return {}
        
    metrics = {
        'sharpe_ratio': qs.stats.sharpe(returns),
        'sortino_ratio': qs.stats.sortino(returns),
        'calmar_ratio': qs.stats.calmar(returns),
        'max_drawdown': qs.stats.max_drawdown(returns),
        'cagr': qs.stats.cagr(returns),
        'volatility': qs.stats.volatility(returns),
        'win_rate': qs.stats.win_rate(returns),
        'profit_factor': qs.stats.profit_factor(returns),
        'average_win': qs.stats.avg_win(returns),
        'average_loss': qs.stats.avg_loss(returns),
        'best_day': qs.stats.best(returns),
        'worst_day': qs.stats.worst(returns),
        'var': qs.stats.value_at_risk(returns),
        'cvar': qs.stats.cvar(returns),
        'skewness': qs.stats.skew(returns),
        'kurtosis': qs.stats.kurtosis(returns),
        'recovery_factor': qs.stats.recovery_factor(returns),
        'ulcer_index': qs.stats.ulcer_index(returns),
    }
    
    # Optional: fetch any other basic stats provided by qs
    try:
        metrics['kelly_criterion'] = qs.stats.kelly_criterion(returns)
        metrics['risk_return_ratio'] = qs.stats.risk_return_ratio(returns)
    except Exception:
        pass
        
    # Convert numpy types to python native types for clean JSON serialization
    clean_metrics = {}
    for k, v in metrics.items():
        if pd.isna(v) or v is None or (isinstance(v, float) and np.isinf(v)):
            clean_metrics[k] = None
        elif hasattr(v, 'item'):
            clean_metrics[k] = v.item()
        elif isinstance(v, (pd.Series, pd.DataFrame)):
            clean_metrics[k] = v.to_dict()
        else:
            clean_metrics[k] = v
            
    return clean_metrics
