from ml.classifiers.base_classifier import BaseClassifier
from sklearn.svm import SVC

class SVMModel(BaseClassifier):
    def __init__(self):
        super().__init__(SVC(probability=True))
