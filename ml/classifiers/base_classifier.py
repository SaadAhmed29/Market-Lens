import os
import joblib
import pandas as pd
from typing import Any

class BaseClassifier:
    def __init__(self, model: Any):
        self.model = model

    def train(self, train_df: pd.DataFrame):
        features = [c for c in train_df.columns if c not in ['target', 'date_time']]
        X_train = train_df[features]
        y_train = train_df['target']
        self.model.fit(X_train, y_train)

    def predict(self, df: pd.DataFrame) -> pd.Series:
        features = [c for c in df.columns if c not in ['target', 'date_time']]
        X = df[features]
        preds = self.model.predict(X)
        if 'date_time' in df.columns:
            return pd.Series(preds, index=df['date_time'], name='target')
        else:
            return pd.Series(preds, index=df.index, name='target')

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        features = [c for c in df.columns if c not in ['target', 'date_time']]
        X = df[features]
        probas = self.model.predict_proba(X)
        if 'date_time' in df.columns:
            return pd.DataFrame(probas, index=df['date_time'], columns=self.model.classes_)
        else:
            return pd.DataFrame(probas, index=df.index, columns=self.model.classes_)

    def save(self, model_name: str):
        os.makedirs('ml/models/', exist_ok=True)
        path = f'ml/models/{model_name}_model.pkl'
        joblib.dump(self.model, path)

    def load(self, model_name: str):
        path = f'ml/models/{model_name}_model.pkl'
        self.model = joblib.load(path)
