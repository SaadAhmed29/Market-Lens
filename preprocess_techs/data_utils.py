"""
Utils for data interactions in preprocess_techs.
"""

import pandas as pd
from utils.db import run_cli
from preprocess_techs import helpers


FIT_TRANSFORM_TECHNIQUES = {
    "winsorized_robust", "standard_scaler", "minmax_scaler",
    "robust_scaler", "maxabs_scaler", "quantile_transformer",
}

# CLI

def prompt_user(pp_cfg: dict) -> dict:
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


# Stationarity / Trend Preservation display

def print_table(title: str, df: pd.DataFrame) -> None:
    """Pretty-print a summary DataFrame as a structured table."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    if df.empty:
        print("  (no results)")
    else:
        print(df.to_string(index=False))
    print()


# Preprocessing (fit-on-train / apply-on-val)

def apply_preprocessing(technique_name: str, train_df: pd.DataFrame, val_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the selected preprocessing technique.

    For ``winsorized_robust`` the statistics (percentile bounds, median, IQR)
    are computed on the train set and re-used for the val set.
    All other techniques are applied independently.
    """
    func = getattr(helpers, technique_name)

    if technique_name in FIT_TRANSFORM_TECHNIQUES:
        train_out, val_out = func(train_df, val_df)
    else:
        train_out = func(train_df)
        val_out = func(val_df)

    return train_out, val_out