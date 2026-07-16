import os
import joblib
import pandas as pd
from typing import Any
from sklearn.preprocessing import LabelEncoder

class BaseClassifier:
    def __init__(self, model: Any):
        self.model = model
        self.le = LabelEncoder()

    def train(self, train_df: pd.DataFrame):
        features = [c for c in train_df.columns if c not in ['target', 'date_time']]
        X_train = train_df[features]
        y_train = self.le.fit_transform(train_df['target'])
        self.model.fit(X_train, y_train)

    def predict(self, df: pd.DataFrame) -> pd.Series:
        features = [c for c in df.columns if c not in ['target', 'date_time']]
        X = df[features]
        preds_encoded = self.model.predict(X)
        
        # Flatten the predictions to a 1D array to avoid sklearn warnings (e.g. CatBoost outputs (N, 1))
        import numpy as np
        preds_encoded = np.ravel(preds_encoded)
        
        preds = self.le.inverse_transform(preds_encoded)
        if 'date_time' in df.columns:
            return pd.Series(preds, index=df['date_time'], name='target')
        else:
            return pd.Series(preds, index=df.index, name='target')

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        features = [c for c in df.columns if c not in ['target', 'date_time']]
        X = df[features]
        probas = self.model.predict_proba(X)
        if 'date_time' in df.columns:
            return pd.DataFrame(probas, index=df['date_time'], columns=self.le.classes_)
        else:
            return pd.DataFrame(probas, index=df.index, columns=self.le.classes_)

    def save(self, model_name: str):
        os.makedirs('ml/models/', exist_ok=True)
        path = f'ml/models/{model_name}_clf_model.pkl'
        joblib.dump({'model': self.model, 'le': self.le}, path)

    def load(self, model_name: str):
        path = f'ml/models/{model_name}_clf_model.pkl'
        data = joblib.load(path)
        if isinstance(data, dict) and 'model' in data:
            self.model = data['model']
            self.le = data['le']
        else:
            # Fallback for older saved models without LE
            self.model = data
            self.le = LabelEncoder()
            self.le.classes_ = self.model.classes_
