from ml.classifiers.base_classifier import BaseClassifier
from sklearn.ensemble import RandomForestClassifier

class RandomForestModel(BaseClassifier):
    def __init__(self):
        super().__init__(RandomForestClassifier())
