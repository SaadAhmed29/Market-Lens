import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Bidirectional, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
import joblib
from utils.config import load_config
from ml.utils.logging import get_logger

logger = get_logger(__name__)

class BiLSTMClassifier:
    def __init__(self):
        self.config = load_config('ml/config.yaml')
        models_cfg = self.config.get('models', {}).get('classification', [])
        self.params = {}
        for m in models_cfg:
            if m.get('name') == 'bilstm':
                self.params = m.get('params', {})
                break
        
        self.sequence_length = self.params.get('sequence_length', 60)
        self.batch_size = self.params.get('batch_size', 32)
        self.epochs = self.params.get('epochs', 10)
        self.early_stopping_patience = self.params.get('early_stopping_patience', 5)
        
        self.model = None
        self.le = LabelEncoder()

    def get_model(self, input_shape, num_classes):
        model = Sequential()
        model.add(Input(shape=input_shape))
        
        hidden_units = self.params.get('hidden_units', [64, 32])
        dropout = self.params.get('dropout', 0.2)
        recurrent_dropout = self.params.get('recurrent_dropout', 0.2)
        dense_units = self.params.get('dense_units', 16)
        activation = self.params.get('activation', 'relu')
        output_activation = self.params.get('output_activation', 'softmax')
        
        for i, units in enumerate(hidden_units):
            return_sequences = i < len(hidden_units) - 1
            model.add(Bidirectional(LSTM(
                units, 
                return_sequences=return_sequences,
                dropout=dropout, 
                recurrent_dropout=recurrent_dropout
            )))
            
        model.add(Dense(dense_units, activation=activation))
        model.add(Dense(num_classes, activation=output_activation))
        
        optimizer_name = self.params.get('optimizer', 'adam')
        learning_rate = self.params.get('learning_rate', 0.001)
        optimizer_class = getattr(tf.keras.optimizers, optimizer_name.capitalize(), tf.keras.optimizers.Adam)
        optimizer = optimizer_class(learning_rate=learning_rate)
        
        loss = self.params.get('loss', 'categorical_crossentropy')
        metrics = self.params.get('metrics', ['accuracy'])
        
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
        
        y_train_encoded = self.le.fit_transform(train_df['target'])
        y_train_categorical = to_categorical(y_train_encoded)
        
        X_seq, y_seq = self._create_sequences(X_train, y_train_categorical)
        
        input_shape = (X_seq.shape[1], X_seq.shape[2])
        num_classes = y_seq.shape[1]
        
        self.model = self.get_model(input_shape, num_classes)
        
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
        model_path = f'ml/models/{model_name}_{timeframe}.keras'
        self.model.save(model_path)
        
        le_path = f'ml/artifacts/{model_name}_{timeframe}_le.pkl'
        joblib.dump(self.le, le_path)
        logger.info(f"Model saved to {model_path} and LE to {le_path}")

    def load(self, model_name: str, timeframe: str):
        model_path = f'ml/models/{model_name}_{timeframe}.keras'
        self.model = load_model(model_path)
        
        le_path = f'ml/artifacts/{model_name}_{timeframe}_le.pkl'
        self.le = joblib.load(le_path)
        logger.info(f"Model loaded from {model_path}")

    def predict(self, val_df: pd.DataFrame) -> pd.Series:
        features = [c for c in val_df.columns if c not in ['target', 'date_time']]
        X_val = val_df[features].values
        X_seq = self._create_sequences(X_val)
        
        preds_proba = self.model.predict(X_seq)
        preds_classes = np.argmax(preds_proba, axis=1)
        preds = self.le.inverse_transform(preds_classes)
        
        if 'date_time' in val_df.columns:
            idx = val_df['date_time'].iloc[self.sequence_length - 1 :]
        else:
            idx = val_df.index[self.sequence_length - 1 :]
            
        return pd.Series(preds, index=idx, name='target')
