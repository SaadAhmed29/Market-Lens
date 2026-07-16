from ml.regressors.base_regressor import BaseRegressor
from xgboost import XGBRegressor

class XGBoostModel(BaseRegressor):
    def __init__(self):
        super().__init__(XGBRegressor())
