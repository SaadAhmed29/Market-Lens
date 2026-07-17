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
    data_cfg = config.get('data')
    timeframe = data_cfg.get('timeframe')
    train_df, val_df = run_preprocessing_pipeline(config)
    
    models_dir = f'ml/models/'
    if not os.path.exists(models_dir):
        print(f"Directory {models_dir} does not exist.")
        return
        
    for filename in os.listdir(models_dir):
        path = os.path.join(models_dir, filename)
        
        is_dl_model = ('bilstm' in filename or 'gru' in filename) and filename.endswith(f'_{timeframe}.keras')
        is_sklearn_model = filename.endswith(f'_clf_model_{timeframe}.pkl') or filename.endswith(f'_reg_model_{timeframe}.pkl')
        
        if is_dl_model or is_sklearn_model:
            logger.info(f"Model found: {filename}")
            
            if is_dl_model:
                if 'bilstm' in filename:
                    model_name = 'bilstm'
                    model_type = 'classification'
                    from ml.classifiers.bilstm import BiLSTMClassifier
                    base_model = BiLSTMClassifier()
                    base_model.load(model_name, timeframe)
                    full_stem = f"{model_name}_clf_{timeframe}"
                else:
                    model_name = 'gru'
                    model_type = 'regression'
                    from ml.regressors.gru import GRURegressor
                    base_model = GRURegressor()
                    base_model.load(model_name, timeframe)
                    full_stem = f"{model_name}_reg_{timeframe}"
            else:
                if filename.endswith(f'_clf_model_{timeframe}.pkl'):
                    model_name = filename.replace(f'_clf_model_{timeframe}.pkl', '')
                    model_type = 'classification'
                    from ml.classifiers.base_classifier import BaseClassifier
                    base_model = BaseClassifier(None)
                else:
                    model_name = filename.replace(f'_reg_model_{timeframe}.pkl', '')
                    model_type = 'regression'
                    from ml.regressors.base_regressor import BaseRegressor
                    base_model = BaseRegressor(None)
                    
                base_model.load(model_name)
                full_stem = filename.replace('_model', '').replace(f'.pkl', '')

            print(f"Evaluating {model_name}...")
            logger.info(f"Model {model_name} loaded.")
            predictions = base_model.predict(val_df)
            logger.info(f"Predictions generated for {model_name}.")
            
            aligned_val_df = val_df.loc[predictions.index]
            aligned_y_true = aligned_val_df['target']
            
            metrics = {}
            if model_type == 'regression':
                metrics['mae'] = mae(aligned_y_true, predictions)
                metrics['mse'] = mse(aligned_y_true, predictions)
                metrics['rmse'] = rmse(aligned_y_true, predictions)
            else:
                metrics['accuracy'] = accuracy(aligned_y_true, predictions)
                metrics['precision'] = precision(aligned_y_true, predictions)
                metrics['recall'] = recall(aligned_y_true, predictions)
                
            stats = calculate_stats(predictions, aligned_val_df, model_type)
            metrics['backtest_stats'] = stats
            logger.debug(f"Metrics calculated for {model_name}.")
            
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
