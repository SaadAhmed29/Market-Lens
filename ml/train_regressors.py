import os
from ml.data_utils import load_ml_config
from ml.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline

from ml.regressors.linear_regression import LinearRegressionModel
from ml.regressors.ridge import RidgeModel
from ml.regressors.lasso import LassoModel
from ml.regressors.random_forest import RandomForestModel
from ml.regressors.extra_trees import ExtraTreesModel
from ml.regressors.xgboost import XGBoostModel
from ml.regressors.lightgbm import LightGBMModel
from ml.regressors.catboost import CatBoostModel
from ml.regressors.svr import SVRModel

def main():
    config_path = "ml/config.yaml"
    config = load_ml_config(config_path)
    config['model_type'] = 'regression'

    train_df, val_df = run_preprocessing_pipeline(config)
    
    models = {
        'linear_regression': LinearRegressionModel(),
        'ridge': RidgeModel(),
        'lasso': LassoModel(),
        'random_forest': RandomForestModel(),
        'extra_trees': ExtraTreesModel(),
        'xgboost': XGBoostModel(),
        'lightgbm': LightGBMModel(),
        'catboost': CatBoostModel(),
        'svr': SVRModel()
    }
    
    for name, model in models.items():
        print(f"--- {name} ---")
        print("Training...")
        model.train(train_df)
        
        print("Saving...")
        model.save(name)

if __name__ == "__main__":
    main()
