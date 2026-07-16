import os
import importlib
import inspect
from ml.data_utils import load_ml_config
from ml.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline
from ml.persistence.artifact_manager import save_artifact

def main():
    config_path = "ml/config.yaml"
    config = load_ml_config(config_path)
    config['model_type'] = 'classification'

    train_df, val_df = run_preprocessing_pipeline(config)
    
    scaler_str = "minmax_scaler"
    stationarity_str = "fractional_differencing"
    
    classifier_models = config.get('models', {}).get('classification', [])
    for model_item in classifier_models:
        name = model_item.get('name')
        if not name:
            continue
            
        print(f"--- {name} ---")
        
        module_name = f"ml.classifiers.{name}"
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
        model.save(name)
        
        print("Saving artifact...")
        save_artifact(f"{name}_clf", config, train_df, val_df, model, scaler_str, stationarity_str)

if __name__ == "__main__":
    main()
