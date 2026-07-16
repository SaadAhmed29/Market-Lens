from ml.classifiers.base_classifier import BaseClassifier
from lightgbm import LGBMClassifier

class LightGBMModel(BaseClassifier):
    def __init__(self):
        super().__init__(LGBMClassifier())
