from ml.classifiers.base_classifier import BaseClassifier
from xgboost import XGBClassifier

class XGBoostModel(BaseClassifier):
    def __init__(self):
        super().__init__(XGBClassifier())
