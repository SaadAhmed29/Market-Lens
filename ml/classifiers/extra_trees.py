from ml.classifiers.base_classifier import BaseClassifier
from sklearn.ensemble import ExtraTreesClassifier

class ExtraTreesModel(BaseClassifier):
    def __init__(self):
        super().__init__(ExtraTreesClassifier())
