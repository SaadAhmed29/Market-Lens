import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import GRU, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping
from utils.config import load_config
from ml.utils.logging import get_logger

logger = get_logger(__name__)

class GRURegressor:
    def __init__(self):
        self.config = load_config('ml/config.yaml')
        models_cfg = self.config.get('models', {}).get('regression', [])
        self.params = {}
        for m in models_cfg:
            if m.get('name') == 'gru':
                self.params = m.get('params', {})
                break
        
        self.sequence_length = self.params.get('sequence_length', 60)
        self.batch_size = self.params.get('batch_size', 32)
        self.epochs = self.params.get('epochs', 10)
        self.early_stopping_patience = self.params.get('early_stopping_patience', 5)
        
        self.model = None

    def get_model(self, input_shape):
        model = Sequential()
        model.add(Input(shape=input_shape))
        
        hidden_units = self.params.get('hidden_units', [64, 32])
        dropout = self.params.get('dropout', 0.2)
        recurrent_dropout = self.params.get('recurrent_dropout', 0.2)
        dense_units = self.params.get('dense_units', 16)
        activation = self.params.get('activation', 'relu')
        output_activation = self.params.get('output_activation', 'linear')
        
        for i, units in enumerate(hidden_units):
            return_sequences = i < len(hidden_units) - 1
            model.add(GRU(
                units, 
                return_sequences=return_sequences,
                dropout=dropout, 
                recurrent_dropout=recurrent_dropout
            ))
            
        model.add(Dense(dense_units, activation=activation))
        model.add(Dense(1, activation=output_activation))
        
        optimizer_name = self.params.get('optimizer', 'adam')
        learning_rate = self.params.get('learning_rate', 0.001)
        optimizer_class = getattr(tf.keras.optimizers, optimizer_name.capitalize(), tf.keras.optimizers.Adam)
        optimizer = optimizer_class(learning_rate=learning_rate)
        
        loss = self.params.get('loss', 'mse')
        metrics = self.params.get('metrics', ['mae', 'rmse'])
        
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        return model

    def _create_sequences(self, X, y=None):
        Xs = []
        ys = []
        for i in range(self.sequence_length - 1, len(X)):
            Xs.append(X[i - self.sequence_length + 1 : i + 1])
            if y is not None:
                ys.append(y[i])
                
        if y is not None:
            return np.array(Xs), np.array(ys)
        return np.array(Xs)

    def train(self, train_df: pd.DataFrame):
        features = [c for c in train_df.columns if c not in ['target', 'date_time']]
        X_train = train_df[features].values
        y_train = train_df['target'].values
        
        X_seq, y_seq = self._create_sequences(X_train, y_train)
        
        input_shape = (X_seq.shape[1], X_seq.shape[2])
        
        self.model = self.get_model(input_shape)
        
        early_stopping = EarlyStopping(
            monitor='loss', 
            patience=self.early_stopping_patience, 
            restore_best_weights=True
        )
        
        self.model.fit(
            X_seq, y_seq,
            batch_size=self.batch_size,
            epochs=self.epochs,
            callbacks=[early_stopping],
            verbose=1
        )

    def save(self, model_name: str, timeframe: str):
        os.makedirs('ml/models/', exist_ok=True)
        path = f'ml/models/{model_name}_{timeframe}.keras'
        self.model.save(path)
        logger.info(f"Model saved to {path}")

    def load(self, model_name: str, timeframe: str):
        path = f'ml/models/{model_name}_{timeframe}.keras'
        self.model = load_model(path)
        logger.info(f"Model loaded from {path}")

    def predict(self, val_df: pd.DataFrame) -> pd.Series:
        features = [c for c in val_df.columns if c not in ['target', 'date_time']]
        X_val = val_df[features].values
        X_seq = self._create_sequences(X_val)
        
        preds = self.model.predict(X_seq)
        preds = preds.flatten()
        
        if 'date_time' in val_df.columns:
            idx = val_df['date_time'].iloc[self.sequence_length - 1 :]
        else:
            idx = val_df.index[self.sequence_length - 1 :]
            
        return pd.Series(preds, index=idx, name='target')
