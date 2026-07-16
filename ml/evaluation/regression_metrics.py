from sklearn.metrics import mean_absolute_error, mean_squared_error, root_mean_squared_error

def mae(y_true, y_pred) -> float:
    return float(mean_absolute_error(y_true, y_pred))

def mse(y_true, y_pred) -> float:
    return float(mean_squared_error(y_true, y_pred))

def rmse(y_true, y_pred) -> float:
    return float(root_mean_squared_error(y_true, y_pred))
