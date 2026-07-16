from ml.regressors.base_regressor import BaseRegressor
from sklearn.ensemble import ExtraTreesRegressor

class ExtraTreesModel(BaseRegressor):
    def __init__(self):
        super().__init__(ExtraTreesRegressor())
