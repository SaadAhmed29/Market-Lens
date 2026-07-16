from ml.classifiers.base_classifier import BaseClassifier
from sklearn.linear_model import LogisticRegression

class LogisticRegressionModel(BaseClassifier):
    def __init__(self):
        super().__init__(LogisticRegression())
