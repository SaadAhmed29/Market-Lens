from ml.regressors.base_regressor import BaseRegressor
from sklearn.linear_model import Lasso

class LassoModel(BaseRegressor):
    def __init__(self):
        super().__init__(Lasso())
