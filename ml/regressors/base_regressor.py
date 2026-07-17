import os
import joblib
import pandas as pd
from typing import Any
from ml.utils.logging import get_logger
from utils.config import load_config

logger = get_logger(__name__)

class BaseRegressor:
    def __init__(self, model: Any):
        self.model = model
        self.config = load_config('ml/config.yaml')
        self.data_cfg = self.config.get('data')
        self.timeframe = self.data_cfg.get('timeframe')

    def train(self, train_df: pd.DataFrame):
        logger.info("Training started...")
        features = [c for c in train_df.columns if c not in ['target', 'date_time']]
        X_train = train_df[features]
        y_train = train_df['target']
        try:
            self.model.fit(X_train, y_train)
            logger.info("Training completed.")
        except Exception as e:
            logger.error(f"Error during training: {e}")
            raise

    def predict(self, df: pd.DataFrame) -> pd.Series:
        features = [c for c in df.columns if c not in ['target', 'date_time']]
        X = df[features]
        try:
            preds = self.model.predict(X)
            logger.debug("Prediction generated.")
            if 'date_time' in df.columns:
                return pd.Series(preds, index=df['date_time'], name='target')
            else:
                return pd.Series(preds, index=df.index, name='target')
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            raise

    def save(self, model_name: str):
        os.makedirs('ml/models/', exist_ok=True)
        path = f'ml/models/{model_name}_reg_model_{self.timeframe}.pkl'
        try:
            joblib.dump(self.model, path)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise

    def load(self, model_name: str):
        path = f'ml/models/{model_name}_reg_model_{self.timeframe}.pkl'
        try:
            self.model = joblib.load(path)
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
