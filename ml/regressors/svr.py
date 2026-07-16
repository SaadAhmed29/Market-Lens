from ml.regressors.base_regressor import BaseRegressor
from sklearn.svm import SVR

class SVRModel(BaseRegressor):
    def __init__(self):
        super().__init__(SVR())
