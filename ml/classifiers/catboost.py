from ml.classifiers.base_classifier import BaseClassifier
from catboost import CatBoostClassifier

class CatBoostModel(BaseClassifier):
    def __init__(self):
        super().__init__(CatBoostClassifier(verbose=0, allow_writing_files=False))
