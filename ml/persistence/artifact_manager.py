import os
import json
import pandas as pd
from typing import Any
from ml.utils.logging import get_logger

logger = get_logger(__name__)

def save_artifact(model_name: str, config: dict, train_df: pd.DataFrame, val_df: pd.DataFrame, model: Any, scaler: str, stationarity: str):
    logger.info("Artifact saving started.")
    artifacts_dir = 'ml/artifacts/'
    os.makedirs(artifacts_dir, exist_ok=True)
    
    features_list = [c for c in train_df.columns if c not in ['target', 'date_time']]
    
    # Extract underlying model for hyperparameters
    actual_model = getattr(model, 'model', model)
    try:
        hyperparams = actual_model.get_params()
    except Exception:
        hyperparams = {}

    def safe_serialize(obj):
        try:
            json.dumps(obj)
            return obj
        except Exception:
            return str(obj)

    safe_hyperparams = {k: safe_serialize(v) for k, v in hyperparams.items()}

    artifact = {
        "dataset": {
            "symbol": config.get('data', {}).get('symbol', ''),
            "exchange": config.get('data', {}).get('exchange', ''),
            "timeframe": config.get('data', {}).get('timeframe', ''),
            "start_date": config.get('data', {}).get('start_date', ''),
            "end_date": config.get('data', {}).get('end_date', '')
        },
        "features": {
            "feature_list": features_list,
            "target_column": "target",
            "timestamp_column": "date_time"
        },
        "data_split": {
            "train_start": config.get('train_start_date', ''),
            "train_end": config.get('train_end_date', ''),
            "val_start": config.get('val_start_date', ''),
            "val_end": config.get('val_end_date', '')
        },
        "preprocessing": {
            "scaling_method": scaler,
            "stationarity_method": stationarity
        },
        "model_info": {
            "model_type": config.get('model_type', ''),
            "hyperparameters": safe_hyperparams
        },
        "feature_metadata": {
            "feature_order": features_list,
            "feature_names": features_list,
            "target_column": "target",
            "timestamp_column": "date_time"
        }
    }
    
    file_path = os.path.join(artifacts_dir, f"{model_name}_config.json")
    try:
        with open(file_path, 'w') as f:
            json.dump(artifact, f, indent=4)
        logger.info(f"Artifact saved successfully to {file_path}")
    except Exception as e:
        logger.error(f"Error saving artifact: {e}")
        raise
