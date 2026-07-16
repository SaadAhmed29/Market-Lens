from ml.classifiers.base_classifier import BaseClassifier
from sklearn.tree import DecisionTreeClassifier

class DecisionTreeModel(BaseClassifier):
    def __init__(self):
        super().__init__(DecisionTreeClassifier())
