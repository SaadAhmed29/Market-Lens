from ml.regressors.base_regressor import BaseRegressor
from sklearn.ensemble import RandomForestRegressor

class RandomForestModel(BaseRegressor):
    def __init__(self):
        super().__init__(RandomForestRegressor())
