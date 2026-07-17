import os
import importlib
import inspect
from ml.data_utils import load_ml_config
from ml.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline
from ml.persistence.artifact_manager import save_artifact

def main():
    config_path = "ml/config.yaml"
    config = load_ml_config(config_path)
    config['model_type'] = 'regression'

    train_df, val_df = run_preprocessing_pipeline(config)
    
    scaler_str = "maxabs_scaler"
    stationarity_str = "fractional_differencing"
    
    regression_models = config.get('models', {}).get('regression', [])
    for model_item in regression_models:
        name = model_item.get('name')
        if not name:
            continue
            
        print(f"--- {name} ---")
        
        if name == 'gru':
            from ml.regressors.gru import GRURegressor
            model = GRURegressor()
        else:
            module_name = f"ml.regressors.{name}"
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                print(f"Module {module_name} not found. Skipping.")
                continue
                
            model_class = None
            for obj_name, obj in inspect.getmembers(module, inspect.isclass):
                if obj_name.endswith('Model') and obj.__module__ == module_name:
                    model_class = obj
                    break
                    
            if not model_class:
                print(f"No class ending with 'Model' found in {module_name}. Skipping.")
                continue
                
            model = model_class()
        
        print("Training...")
        model.train(train_df)
        
        print("Saving...")
        if name == 'gru':
            timeframe = config.get('data', {}).get('timeframe')
            model.save(name, timeframe)
        else:
            model.save(name)
        
        print("Saving artifact...")
        save_artifact(f"{name}_reg", config, train_df, val_df, model, scaler_str, stationarity_str)

if __name__ == "__main__":
    main()
