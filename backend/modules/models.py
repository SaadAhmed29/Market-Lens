import os
import json
import yaml
from pathlib import Path
import sys

ARTIFACTS_DIR = "ml/artifacts"
METRICS_DIR = "ml/metrics"

# Path setup: allow imports from project root regardless of how this module
# is imported (e.g. when FastAPI is launched from backend/).
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Path to the ML config relative to project root
ML_CONFIG_PATH = ROOT / "ml" / "config.yaml"

def get_all_models():
    models = []
    if not os.path.exists(ARTIFACTS_DIR):
        return models

    for filename in os.listdir(ARTIFACTS_DIR):
        if filename.endswith("_config.json"):
            model_name = filename.replace("_config.json", "")
            config_path = os.path.join(ARTIFACTS_DIR, filename)
            metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
            
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
            except Exception:
                continue
                
            model_info = config.get("model_info", {})
            model_type = model_info.get("model_type", "unknown")
            dataset_info = config.get("dataset", {})
            symbol = dataset_info.get("symbol", "unknown")
            timeframe = dataset_info.get("timeframe", "unknown")
            
            score = None
            primary_metric = "accuracy" if model_type == "classification" else "mse"
            
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, "r") as f:
                        metrics = json.load(f)
                    score = metrics.get(primary_metric)
                except Exception:
                    pass
                    
            models.append({
                "model_name": model_name,
                "model_type": model_type,
                "symbol": symbol,
                "timeframe": timeframe,
                "primary_metric": primary_metric,
                "score": score
            })
            
    return models

def get_model_detail(model_name: str):
    config_path = os.path.join(ARTIFACTS_DIR, f"{model_name}_config.json")
    metrics_path = os.path.join(METRICS_DIR, f"{model_name}_metrics.json")
    
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception:
            pass
            
    metrics = {}
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
        except Exception:
            pass

    try:
        with open(ML_CONFIG_PATH, "r") as f:
            global_config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"ML config not found at expected path: {ML_CONFIG_PATH}")
        return 0
    
    # Dataset Information
    dataset_info = config.get("dataset", {})
    symbol = dataset_info.get("symbol", "")
    exchange = dataset_info.get("exchange", "")
    timeframe = dataset_info.get("timeframe", "")
    dataset_str = f"{symbol} {exchange} {timeframe}".strip()
    
    feature_metadata = config.get("feature_metadata", {})
    features = list(feature_metadata.get("feature_names", {}).keys()) if "feature_names" in feature_metadata else []    

    date_range = f"{dataset_info.get('start_date', '')} to {dataset_info.get('end_date', '')}"
    
    data_split = config.get("data_split", {})
    train_test_split = {
        "train": f"{data_split.get('train_start', '')} to {data_split.get('train_end', '')}",
        "val": f"{data_split.get('val_start', '')} to {data_split.get('val_end', '')}"
    }
    
    # Training Information
    model_info = config.get("model_info", {})
    hyperparameters = model_info.get("hyperparameters", {})
    
    preprocessing = config.get("preprocessing", {})
    scaling = preprocessing.get("scaling_method", "")
    stationarity = preprocessing.get("stationarity_method", "")
    feature_engineering = features
    
    # Evaluation
    model_type = model_info.get("model_type", "unknown")
    target = None
    if model_type == "classification":
        target_con = global_config['target']['classification'][0]
        target = target_con['source'] + '_' + target_con['method']
        ml_metrics = {
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall")
        }
    else:
        target_con = global_config['target']['regression'][0]
        target = target_con['source'] + '_' + target_con['method']
        ml_metrics = {
            "mae": metrics.get("mae"),
            "mse": metrics.get("mse"),
            "rmse": metrics.get("rmse")
        }
        
    backtest_stats = metrics.get("backtest_stats", {})
    backtest_metrics = {
        "sharpe": backtest_stats.get("sharpe_ratio"),
        "max_drawdown": backtest_stats.get("max_drawdown"),
        "win_rate": backtest_stats.get("win_rate")
    }
    
    # Add other backtest fields
    for k, v in backtest_stats.items():
        if k not in ["sharpe_ratio", "max_drawdown", "win_rate"] and not isinstance(v, dict):
            backtest_metrics[k] = v

    return {
        "dataset_information": {
            "dataset": dataset_str,
            "features": features,
            "target": target,
            "date_range": date_range,
            "train_test_split": train_test_split
        },
        "training_information": {
            "model_type": model_type,
            "hyperparameters": hyperparameters,
            "preprocessing": stationarity,
            "feature_engineering": feature_engineering,
            "scaling": scaling,
            "stationarity": stationarity
        },
        "evaluation": {
            "ml_metrics": ml_metrics,
            "backtest_metrics": backtest_metrics
        }
    }
