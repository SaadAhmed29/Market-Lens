import numpy as np
import pandas as pd

def directional_accuracy(y_true, y_pred):
    """
    Computes the percentage of times the predicted direction (up/down) 
    matches the actual direction relative to the previous value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    if len(y_true) < 2:
        return 0.0
        
    actual_diff = np.diff(y_true)
    pred_diff = np.diff(y_pred)
    
    # Match if both go up, both go down, or both stay same
    matches = (np.sign(actual_diff) == np.sign(pred_diff))
    
    return float(np.mean(matches)) * 100.0

def trend_accuracy(y_true, y_pred, window=5):
    """
    Computes the percentage of times the predicted rolling trend (using a rolling mean 
    of given window) matches the actual rolling trend direction.
    """
    y_true_s = pd.Series(y_true)
    y_pred_s = pd.Series(y_pred)
    
    if len(y_true_s) < window + 1:
        return 0.0
        
    actual_trend = y_true_s.rolling(window=window).mean()
    pred_trend = y_pred_s.rolling(window=window).mean()
    
    actual_diff = actual_trend.diff()
    pred_diff = pred_trend.diff()
    
    # Drop NaNs that occur due to rolling and diff
    valid_idx = ~(actual_diff.isna() | pred_diff.isna())
    
    if not valid_idx.any():
        return 0.0
        
    matches = (np.sign(actual_diff[valid_idx]) == np.sign(pred_diff[valid_idx]))
    
    return float(np.mean(matches)) * 100.0
