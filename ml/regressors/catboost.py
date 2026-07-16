from ml.regressors.base_regressor import BaseRegressor
from catboost import CatBoostRegressor

class CatBoostModel(BaseRegressor):
    def __init__(self):
        super().__init__(CatBoostRegressor(verbose=0, allow_writing_files=False))
