import os
import json
from utils.config import load_config
from ml.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline
from ml.evaluation.regression_metrics import mae, mse, rmse
from ml.evaluation.classification_metrics import accuracy, precision, recall
from ml.evaluation.stats import calculate_stats
from ml.utils.logging import get_logger

logger = get_logger(__name__)

def run_evaluation(config_path):
    config = load_config(config_path)
    train_df, val_df = run_preprocessing_pipeline(config)
    
    models_dir = 'ml/models/'
    if not os.path.exists(models_dir):
        print(f"Directory {models_dir} does not exist.")
        return
        
    for filename in os.listdir(models_dir):
        if filename.endswith('_clf_model.pkl') or filename.endswith('_reg_model.pkl'):
            logger.info(f"Model found: {filename}")
            if filename.endswith('_clf_model.pkl'):
                model_name = filename.replace('_clf_model.pkl', '')
                model_type = 'classification'
            else:
                model_name = filename.replace('_reg_model.pkl', '')
                model_type = 'regression'
            print(f"Evaluating {model_name}...")
            
            if 'reg_model' in filename:
                from ml.regressors.base_regressor import BaseRegressor
                base_model = BaseRegressor(None)
            elif 'clf_model' in filename:
                from ml.classifiers.base_classifier import BaseClassifier
                base_model = BaseClassifier(None)
                
            base_model.load(model_name)
            logger.info(f"Model {model_name} loaded.")
            predictions = base_model.predict(val_df)
            logger.info(f"Predictions generated for {model_name}.")
            
            metrics = {}
            if model_type == 'regression':
                metrics['mae'] = mae(val_df['target'], predictions)
                metrics['mse'] = mse(val_df['target'], predictions)
                metrics['rmse'] = rmse(val_df['target'], predictions)
            else:
                metrics['accuracy'] = accuracy(val_df['target'], predictions)
                metrics['precision'] = precision(val_df['target'], predictions)
                metrics['recall'] = recall(val_df['target'], predictions)
                
            stats = calculate_stats(predictions, val_df, model_type)
            metrics['backtest_stats'] = stats
            logger.debug(f"Metrics calculated for {model_name}.")
            
            # Use full stem (e.g. xgboost_clf or xgboost_reg) so clf/reg don't overwrite each other
            full_stem = filename.replace('_model.pkl', '')
            metrics_dir = 'ml/metrics/'
            os.makedirs(metrics_dir, exist_ok=True)
            metrics_path = os.path.join(metrics_dir, f"{full_stem}_metrics.json")
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=4)
            logger.info(f"Saved metrics to {metrics_path}")

    # Read primary metric and rank models
    primary_metric = config.get('primary_metric')
    if not primary_metric:
        print("No primary_metric found in config. Skipping ranking.")
        return
        
    metrics_dir = 'ml/metrics/'
    if not os.path.exists(metrics_dir):
        return
        
    results = []
    for filename in os.listdir(metrics_dir):
        if not filename.endswith('_metrics.json'):
            continue
            
        filepath = os.path.join(metrics_dir, filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        val = None
        if primary_metric in data:
            val = data[primary_metric]
        elif 'backtest_stats' in data and primary_metric in data['backtest_stats']:
            val = data['backtest_stats'][primary_metric]
            
        if val is not None:
            model_name_display = filename.replace('_metrics.json', '')
            results.append((model_name_display, val))
            
    results.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nModel Ranking by {primary_metric} (Descending):")
    logger.info(f"Printing model ranking by {primary_metric}")
    print("-" * 50)
    for idx, (name, val) in enumerate(results, 1):
        print(f"{idx}. {name:<30} | {val:.4f}")

if __name__ == "__main__":
    run_evaluation("ml/config.yaml")
