"""
Preprocessing pipeline runner.

Orchestrates: CLI selection → data loading → train/val split →
preprocessing → stationarity analysis → trend preservation →
model training → evaluation → predictions → backtest.
"""

import os
import warnings

import numpy as np
import pandas as pd
import yaml

from ml.data_formation import build_dataset
from ml.data_utils import load_ml_config
from utils.db import run_cli
from preprocess_techs import helpers
from preprocess_techs.test import run_backtest_from_predictions


# Config

_PP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
_ML_CONFIG_PATH = "ml/config.yaml"
_BACKTEST_CONFIG_PATH = "backtest/config.yaml"


def _load_pp_config() -> dict:
    with open(_PP_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def _load_backtest_config() -> dict:
    with open(_BACKTEST_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


# CLI

def _prompt_user(pp_cfg: dict) -> dict:
    """Run interactive CLI prompts and return selections."""

    technique_names = [t["name"] for t in pp_cfg.get("techniques", [])]
    stationarity_names = [s["name"] for s in pp_cfg.get("stationarity_analysis", [])]
    trend_names = [t["name"] for t in pp_cfg.get("trend_preservation", [])]
    model_task_names = list(pp_cfg.get("models", {}).keys())  # ["classification", "regression"]

    # Single-select items go through the normal options list
    cli_result = run_cli(
        options=[],
        multi_select_options=[
            {
                "key": "stationarity_analysis",
                "prompt": "Select stationarity analyses:",
                "choices": stationarity_names,
            },
            {
                "key": "trend_preservation",
                "prompt": "Select trend preservation checks:",
                "choices": trend_names,
            },
        ],
    )

    # Single-selects handled via questionary directly (not in run_cli)
    import questionary
    from utils.db import _cli_style

    technique = questionary.select(
        "Select preprocessing technique:",
        choices=technique_names,
        style=_cli_style,
    ).ask()
    if technique is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    model_task = questionary.select(
        "Select model task type:",
        choices=model_task_names,
        style=_cli_style,
    ).ask()
    if model_task is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    model_names = [m["name"] for m in pp_cfg.get("models", {}).get(model_task, [])]

    model = questionary.select(
        "Select model:",
        choices=model_names,
        style=_cli_style,
    ).ask()
    if model is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    cli_result["technique"] = technique
    cli_result["model_task"] = model_task
    cli_result["model"] = model
    return cli_result

# Train / Val Split

def _split_train_val(
    df: pd.DataFrame,
    train_start: str,
    train_end: str,
    val_start: str,
    val_end: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split df by date ranges.  Index must be datetime-like."""
    train_df = df.loc[train_start:train_end].copy()
    val_df = df.loc[val_start:val_end].copy()
    return train_df, val_df


# Preprocessing (fit-on-train / apply-on-val)

_EXCLUDE_COLS = {"date_time", "target"}


def _apply_preprocessing(
    technique_name: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the selected preprocessing technique.

    For ``winsorized_robust`` the statistics (percentile bounds, median, IQR)
    are computed on the train set and re-used for the val set.
    All other techniques are applied independently.
    """
    func = getattr(helpers, technique_name)

    if technique_name == "winsorized_robust":
        train_out, val_out = _winsorized_robust_fit_transform(train_df, val_df)
    else:
        train_out = func(train_df)
        val_out = func(val_df)

    return train_out, val_out


def _winsorized_robust_fit_transform(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit winsorized_robust on train, apply the same stats to val."""
    params = helpers._get_technique_params("winsorized_robust")
    lower_pct: float = params.get("lower_percentile", 1.0)
    upper_pct: float = params.get("upper_percentile", 99.0)

    train_out = train_df.copy()
    val_out = val_df.copy()

    feature_cols = helpers._feature_cols(train_df)

    for col in feature_cols:
        # Compute bounds on train
        lower_bound = np.nanpercentile(train_df[col], lower_pct)
        upper_bound = np.nanpercentile(train_df[col], upper_pct)

        # Clip both
        train_clipped = train_out[col].clip(lower=lower_bound, upper=upper_bound)
        val_clipped = val_out[col].clip(lower=lower_bound, upper=upper_bound)

        # Compute median / IQR on train clipped
        median = train_clipped.median()
        q1 = train_clipped.quantile(0.25)
        q3 = train_clipped.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            iqr = 1.0

        train_out[col] = (train_clipped - median) / iqr
        val_out[col] = (val_clipped - median) / iqr

    return train_out, val_out


# Stationarity / Trend Preservation display

def _print_table(title: str, df: pd.DataFrame) -> None:
    """Pretty-print a summary DataFrame as a structured table."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    if df.empty:
        print("  (no results)")
    else:
        print(df.to_string(index=False))
    print()


def _run_stationarity(train_df: pd.DataFrame, methods: list[str]) -> None:
    for method_name in methods:
        func = getattr(helpers, method_name)
        summary = func(train_df)
        _print_table(f"Stationarity — {method_name.upper()}", summary)


def _run_trend_preservation(train_df: pd.DataFrame, methods: list[str]) -> None:
    for method_name in methods:
        func = getattr(helpers, method_name)
        summary = func(train_df)
        # Normalise the result column for display
        if "result" in summary.columns:
            summary["trend_retained"] = summary["result"].apply(
                lambda r: "Yes" if r == "Preserved" else "No"
            )
            display_cols = ["column", "trend_retained"]
            extra = [c for c in summary.columns if c not in ("column", "result", "trend_retained")]
            display_cols = ["column"] + extra + ["trend_retained"]
            summary = summary[display_cols]
        _print_table(f"Trend Preservation — {method_name}", summary)


# Model training & evaluation

def _get_model(model_name: str, model_type: str):
    """Return an untrained sklearn/lightgbm estimator."""

    is_classifier = model_type in ("classification", "timeseries")

    if model_name == "lightgbm":
        from lightgbm import LGBMClassifier, LGBMRegressor
        if is_classifier:
            return LGBMClassifier(verbosity=-1, random_state=42)
        return LGBMRegressor(verbosity=-1, random_state=42)

    if model_name == "svm":
        from sklearn.svm import SVC, SVR
        if is_classifier:
            return SVC(random_state=42)
        return SVR()

    if model_name == "logistic_regression":
        from sklearn.linear_model import LogisticRegression
        return LogisticRegression(max_iter=1000, random_state=42)

    if model_name == "linear_regression":
        from sklearn.linear_model import LinearRegression
        return LinearRegression()

    raise ValueError(f"Unknown model: {model_name}")


def _train_and_evaluate(
    model_name: str,
    model_type: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
) -> tuple[object, pd.DataFrame]:
    """Train model, evaluate, return (fitted model, predictions_df)."""

    feature_cols = helpers._feature_cols(train_df)

    X_train = train_df[feature_cols]
    y_train = train_df["target"]
    X_val = val_df[feature_cols]
    y_val = val_df["target"]

    model = _get_model(model_name, model_type)
    model.fit(X_train, y_train)

    preds = model.predict(X_val)

    # Metrics
    is_classifier = model_type in ("classification", "timeseries")

    print(f"\n{'=' * 60}")
    print(f"  Model: {model_name}  |  Type: {model_type}")
    print(f"{'=' * 60}")

    if is_classifier:
        from sklearn.metrics import accuracy_score, precision_score
        acc = accuracy_score(y_val, preds)
        # Use weighted average for multi-class safety
        prec = precision_score(y_val, preds, average="weighted", zero_division=0)
        print(f"  Accuracy  : {acc:.4f}")
        print(f"  Precision : {prec:.4f}")
    else:
        from sklearn.metrics import mean_absolute_error, root_mean_squared_error
        mae = mean_absolute_error(y_val, preds)
        rmse = root_mean_squared_error(y_val, preds)
        print(f"  MAE  : {mae:.4f}")
        print(f"  RMSE : {rmse:.4f}")
    print()

    # Build predictions df
    predictions_df = pd.DataFrame(
        {"predictions": preds},
        index=val_df.index,
    )
    predictions_df.index.name = "date_time"

    return model, predictions_df


# Main

def main() -> None:
    warnings.filterwarnings("ignore")

    # 1. Load configs
    pp_cfg = _load_pp_config()
    ml_cfg = load_ml_config(_ML_CONFIG_PATH)
    model_type = ml_cfg.get("model_type", "regression")
    backtest_cfg = _load_backtest_config()

    # 2. CLI prompts
    selections = _prompt_user(pp_cfg)
    technique = selections["technique"]
    stationarity_methods = selections.get("stationarity_analysis", [])
    trend_methods = selections.get("trend_preservation", [])
    model_name = selections["model"]

    # 3. Date ranges from config
    train_start = pp_cfg["train_start_date"]
    train_end = pp_cfg["train_end_date"]
    val_start = pp_cfg["val_start_date"]
    val_end = pp_cfg["val_end_date"]

    # 4. Build dataset
    print("\n[*] Building dataset …")
    full_df = build_dataset(ml_cfg)
    print(f"[v] Dataset shape: {full_df.shape}")

    # 5. Train / val split
    train_df, val_df = _split_train_val(full_df, train_start, train_end, val_start, val_end)
    print(f"[v] Train: {train_df.shape}  |  Val: {val_df.shape}")

    if train_df.empty or val_df.empty:
        print("[!] Train or validation set is empty after date split. Exiting.")
        return

    # 6. Preprocessing
    print(f"\n[*] Applying preprocessing: {technique}")
    train_df, val_df = _apply_preprocessing(technique, train_df, val_df)
    print(f"[v] After preprocessing — Train: {train_df.shape}  |  Val: {val_df.shape}")

    # 7. Stationarity analysis (on train set)
    if stationarity_methods:
        _run_stationarity(train_df, stationarity_methods)

    # 8. Trend preservation (on train set)
    if trend_methods:
        _run_trend_preservation(train_df, trend_methods)

    # 9. Model training & evaluation
    print(f"\n[*] Training {model_name} ({model_type}) …")
    _model, predictions_df = _train_and_evaluate(model_name, model_type, train_df, val_df)

    # 9b. Backtest using the model's predictions as trading signals.
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

    # 10. Print predictions
    print(f"\n{'=' * 60}")
    print("  Predictions")
    print(f"{'=' * 60}")
    print(predictions_df.head(10))
    print()


if __name__ == "__main__":
    main()