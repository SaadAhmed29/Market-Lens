from sklearn.metrics import accuracy_score, precision_score, recall_score

def accuracy(y_true, y_pred) -> float:
    return float(accuracy_score(y_true, y_pred))

def precision(y_true, y_pred) -> float:
    return float(precision_score(y_true, y_pred, average='weighted', zero_division=0))

def recall(y_true, y_pred) -> float:
    return float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
