from ml.regressors.base_regressor import BaseRegressor
from lightgbm import LGBMRegressor

class LightGBMModel(BaseRegressor):
    def __init__(self):
        super().__init__(LGBMRegressor())
