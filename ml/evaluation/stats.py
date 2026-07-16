import pandas as pd
from preprocess_techs.external_backtest import run_backtest_from_predictions
from stats.main import generate_stats
from ml.signals.regression_signals import regression_to_signals
from utils.config import load_config

def calculate_stats(predictions, val_df, model_type):
    if model_type == 'regression':
        predictions = regression_to_signals(predictions)
        
    val_df = val_df.copy()
    val_df['predictions'] = predictions
    
    config = load_config("backtest/config.yaml")

    date_series = val_df['date_time'] if 'date_time' in val_df.columns else val_df.index
    start_date = date_series.min()
    end_date = date_series.max()

    config['start_date'] = start_date
    config['end_date'] = end_date
    
    results = run_backtest_from_predictions(
        config=config,
        predictions_df=val_df,
        technique_name="evaluation",
        model_name=model_type,
        prediction_col="predictions"
    )
    
    stats = generate_stats(results)
    return stats
