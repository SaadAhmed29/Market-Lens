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
        'avg_return': qs.stats.avg_return(returns),
        'common_sense_ratio': qs.stats.common_sense_ratio(returns),
        'comp': qs.stats.comp(returns),
        'compsum': qs.stats.compsum(returns),
        'conditional_value_at_risk': qs.stats.conditional_value_at_risk(returns),
        'consecutive_losses': qs.stats.consecutive_losses(returns),
        'consecutive_wins': qs.stats.consecutive_wins(returns),
        'cpc_index': qs.stats.cpc_index(returns),
        'drawdown_details': qs.stats.drawdown_details(qs.stats.to_drawdown_series(returns)),
        'expected_return': qs.stats.expected_return(returns),
        'expected_shortfall': qs.stats.expected_shortfall(returns),
        'exposure': qs.stats.exposure(returns),
        'gain_to_pain_ratio': qs.stats.gain_to_pain_ratio(returns),
        'geometric_mean': qs.stats.geometric_mean(returns),
        'ghpr': qs.stats.ghpr(returns),
        'monthly_returns': qs.stats.monthly_returns(returns),
        'outlier_loss_ratio': qs.stats.outlier_loss_ratio(returns),
        'outlier_win_ratio': qs.stats.outlier_win_ratio(returns),
        'outliers': qs.stats.outliers(returns),
        'payoff_ratio': qs.stats.payoff_ratio(returns),
        'profit_ratio': qs.stats.profit_ratio(returns),
        'rar': qs.stats.rar(returns),
        'remove_outliers': qs.stats.remove_outliers(returns),
        'risk_of_ruin': qs.stats.risk_of_ruin(returns),
        'ror': qs.stats.ror(returns),
        'tail_ratio': qs.stats.tail_ratio(returns),
        'to_drawdown_series': qs.stats.to_drawdown_series(returns),
        'ulcer_performance_index': qs.stats.ulcer_performance_index(returns),
        'upi': qs.stats.upi(returns),
        'win_loss_ratio': qs.stats.win_loss_ratio(returns),
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
        if isinstance(v, (pd.Series, pd.DataFrame)):
            v = v.copy()
            v.index = v.index.map(str)
            if isinstance(v, pd.DataFrame):
                v.columns = v.columns.map(str)
            clean_metrics[k] = v.to_dict()
        elif v is None:
            clean_metrics[k] = None
        elif hasattr(v, 'item'):
            clean_metrics[k] = None if pd.isna(v) else v.item()
        elif isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            clean_metrics[k] = None
        else:
            clean_metrics[k] = v
            
    return clean_metrics