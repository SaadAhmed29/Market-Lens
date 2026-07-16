import os
from ml.data_utils import load_ml_config
from ml.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline

from ml.classifiers.logistic_regression import LogisticRegressionModel
from ml.classifiers.decision_tree import DecisionTreeModel
from ml.classifiers.random_forest import RandomForestModel
from ml.classifiers.extra_trees import ExtraTreesModel
from ml.classifiers.xgboost import XGBoostModel
from ml.classifiers.lightgbm import LightGBMModel
from ml.classifiers.catboost import CatBoostModel
from ml.classifiers.svm import SVMModel

def main():
    config_path = "ml/config.yaml"
    config = load_ml_config(config_path)
    config['model_type'] = 'classification'

    train_df, val_df = run_preprocessing_pipeline(config)
    
    models = {
        'logistic_regression': LogisticRegressionModel(),
        'decision_tree': DecisionTreeModel(),
        'random_forest': RandomForestModel(),
        'extra_trees': ExtraTreesModel(),
        'xgboost': XGBoostModel(),
        'lightgbm': LightGBMModel(),
        'catboost': CatBoostModel(),
        'svm': SVMModel()
    }
    
    for name, model in models.items():
        print(f"--- {name} ---")
        print("Training...")
        model.train(train_df)
        
        print("Saving...")
        model.save(name)


if __name__ == "__main__":
    main()
