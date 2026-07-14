"""
Orchestrates: CLI selection → data loading → train/val split →
preprocessing → stationarity analysis → trend preservation →
model training → evaluation → predictions → backtest.
"""

import os
import warnings

import numpy as np
import pandas as pd

from ml.data_formation import build_dataset
from ml.data_utils import load_ml_config
from utils.config import load_config
from preprocess_techs.external_backtest import run_backtest_from_predictions
from preprocess_techs.model_utils import train_and_evaluate, split_train_val
from preprocess_techs.helpers import run_stationarity, run_trend_preservation
from preprocess_techs.data_utils import prompt_user, print_table, apply_preprocessing


# Configs

_PP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
_ML_CONFIG_PATH = "ml/config.yaml"
_BACKTEST_CONFIG_PATH = "backtest/config.yaml"

# Main

def main() -> None:
    warnings.filterwarnings("ignore")

    # Load configs
    pp_cfg = load_config(_PP_CONFIG_PATH)
    ml_cfg = load_ml_config(_ML_CONFIG_PATH)
    model_type = ml_cfg.get("model_type", "regression")
    backtest_cfg = load_config(_BACKTEST_CONFIG_PATH)

    # CLI prompts
    selections = prompt_user(pp_cfg)
    technique = selections["technique"]
    stationarity_methods = selections.get("stationarity_analysis", [])
    trend_methods = selections.get("trend_preservation", [])
    model_name = selections["model"]

    # Date ranges from config
    train_start = pp_cfg["train_start_date"]
    train_end = pp_cfg["train_end_date"]
    val_start = pp_cfg["val_start_date"]
    val_end = pp_cfg["val_end_date"]

    # Build dataset
    print("\n[*] Building dataset …")
    full_df = build_dataset(ml_cfg)
    full_df = full_df.drop(columns=["sen_MARKET"])   # exclude sen_MARKET from features
    print(f"[v] Dataset shape: {full_df.shape}")

    # Train / val split
    train_df, val_df = split_train_val(full_df, train_start, train_end, val_start, val_end)
    print(f"[v] Train: {train_df.shape}  |  Val: {val_df.shape}")

    if train_df.empty or val_df.empty:
        print("[!] Train or validation set is empty after date split. Exiting.")
        return

    # Preprocessing
    print(f"\n[*] Applying preprocessing: {technique}")
    train_df, val_df = apply_preprocessing(technique, train_df, val_df)
    print(f"[v] After preprocessing — Train: {train_df.shape}  |  Val: {val_df.shape}")

    # Save preprocessed dataset (train + val) to CSV
    os.makedirs("preprocessed_datasets", exist_ok=True)
    preprocessed_csv_path = os.path.join("preprocessed_datasets", f"dataset_{technique}.csv")
    pd.concat([train_df, val_df]).to_csv(preprocessed_csv_path)
    print(f"[v] Preprocessed dataset saved to: {preprocessed_csv_path}")

    # Stationarity analysis (on train set)
    if stationarity_methods:
        run_stationarity(train_df, stationarity_methods)

    # Trend preservation (on train set)
    if trend_methods:
        run_trend_preservation(train_df, trend_methods)

    # Model training & evaluation
    print(f"\n[*] Training {model_name} ({model_type}) …")
    _model, predictions_df = train_and_evaluate(model_name, model_type, train_df, val_df)

    # Backtest using the model's predictions as trading signals.
    # target classes are already -1/0/1, so no label_to_signal mapping needed.
    print(f"\n[*] Running backtest for technique='{technique}', model='{model_name}' …")
    backtest_results = run_backtest_from_predictions(
        backtest_cfg,
        predictions_df,
        technique_name=technique,
        model_name=model_name,
    )
    print(f"[v] Backtest complete. Trade ledger saved to: {backtest_results['csv_path']}")
    print(f"    Total trades: {backtest_results['total_trades']}  |  "
          f"Net profit: {backtest_results['total_net_profit']:.2f}  |  "
          f"Final balance: {backtest_results['final_balance']:.2f}")

    # Print predictions
    print(f"\n{'=' * 60}")
    print("  Predictions")
    print(f"{'=' * 60}")
    print(predictions_df.head(10))
    print()


if __name__ == "__main__":
    main()