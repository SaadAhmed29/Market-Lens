from ml.regressors.base_regressor import BaseRegressor
from sklearn.linear_model import Ridge

class RidgeModel(BaseRegressor):
    def __init__(self):
        super().__init__(Ridge())
