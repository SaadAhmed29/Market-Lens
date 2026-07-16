from ml.regressors.base_regressor import BaseRegressor
from sklearn.linear_model import LinearRegression

class LinearRegressionModel(BaseRegressor):
    def __init__(self):
        super().__init__(LinearRegression())
