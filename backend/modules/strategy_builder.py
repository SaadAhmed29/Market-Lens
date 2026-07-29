"""
Strategy Builder Module
Extends the backtest module with multi-mode signal generation
(strategy, model, combinations) and strategy saving.
"""

import uuid
import os
import json
import glob
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from utils.db import get_engine
import math


# Database initialisation

def init_db():
    """Create backtest_requests table (with source column) and
    meta_data.playbook table; populate playbook from meta_data.strategies
    if empty."""
    engine = get_engine()
    with engine.begin() as conn:
        # Ensure backtest_requests table exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS public.backtest_requests (
                request_id UUID PRIMARY KEY,
                request_config JSONB,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                strategy_name TEXT,
                result_summary JSONB
            )
        """))

        # Add source column if not present
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'backtest_requests'
                      AND column_name = 'source'
                ) THEN
                    ALTER TABLE public.backtest_requests
                        ADD COLUMN source TEXT DEFAULT 'backtest';
                END IF;
            END $$;
        """))

        # Create meta_data.playbook table
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS meta_data"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta_data.playbook (
                id            SERIAL PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                config        JSONB NOT NULL
            )
        """))

        # Populate playbook from meta_data.strategies if empty
        count = conn.execute(
            text("SELECT COUNT(*) FROM meta_data.playbook")
        ).scalar()

        if count == 0:
            _populate_playbook(conn)


def sanitize_json_value(value):
    """Recursively replace non-JSON-compliant float values (inf, -inf, nan) with None."""
    if isinstance(value, float):
        if math.isinf(value) or math.isnan(value):
            return None
        return value
    if isinstance(value, dict):
        return {k: sanitize_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_json_value(v) for v in value]
    return value


def _strip_config_for_playbook(config: dict) -> dict:
    """Keep only the signal-relevant fields from a strategy config."""
    stripped = {}
    for key in ("exchange", "symbol", "timehorizon"):
        if key in config:
            stripped[key] = config[key]

    for side in ("long", "short"):
        if side in config:
            side_cfg = config[side]
            stripped[side] = {
                "rule": side_cfg.get("rule"),
                "conditions": side_cfg.get("conditions", []),
            }
            # persist_bars lives on each condition, not at side level,
            # so it's already included inside conditions.
    return stripped


def _populate_playbook(conn):
    """Read meta_data.strategies and insert stripped configs into playbook."""
    try:
        rows = conn.execute(
            text("SELECT strategy_name, config FROM meta_data.strategies")
        ).mappings().fetchall()
    except Exception:
        return

    for row in rows:
        config = row.get("config") or {}
        if isinstance(config, str):
            config = json.loads(config)
        stripped = _strip_config_for_playbook(config)
        conn.execute(
            text("""
                INSERT INTO meta_data.playbook (strategy_name, config)
                VALUES (:name, :config)
            """),
            {"name": row["strategy_name"], "config": json.dumps(stripped)},
        )


# Options: strategies + ML models

def get_strategy_options() -> dict:
    """Return available strategies (from playbook) and saved ML models."""
    init_db()
    engine = get_engine()
    strategies = []
    models = []

    # --- Strategies from playbook ---
    with engine.connect() as conn:
        try:
            res = conn.execute(
                text("SELECT strategy_name, config FROM meta_data.playbook")
            ).mappings().fetchall()
            for row in res:
                config = row.get("config") or {}
                if isinstance(config, str):
                    config = json.loads(config)
                strategies.append({
                    "strategy_name": row["strategy_name"],
                    "symbol": config.get("symbol"),
                    "exchange": config.get("exchange"),
                    "timehorizon": config.get("timehorizon"),
                })
        except Exception:
            pass

    # --- ML models from filesystem ---
    model_dir = "ml/models"
    artifact_dir = "ml/artifacts"

    if os.path.isdir(model_dir):
        for model_file in os.listdir(model_dir):
            if model_file.startswith("__"):
                continue

            model_path = os.path.join(model_dir, model_file)
            if not os.path.isfile(model_path):
                continue

            base_name = model_file  # e.g. "lightgbm_clf_model_15m.pkl"

            # Derive artifact config name by scanning artifacts for a match
            artifact_config = _find_artifact_config(base_name, artifact_dir)
            if artifact_config is None:
                continue

            model_info = artifact_config.get("model_info", {})
            dataset_info = artifact_config.get("dataset", {})
            preprocessing = artifact_config.get("preprocessing", {})

            # Scaler filename
            scaling_method = preprocessing.get("scaling_method", "")
            scaler_filename = None
            if scaling_method:
                candidate = os.path.join(artifact_dir, f"{scaling_method}.pkl")
                if os.path.isfile(candidate):
                    scaler_filename = f"{scaling_method}.pkl"

            # Label encoder — only BiLSTM uses one
            le_filename = None
            if "bilstm" in base_name.lower():
                timeframe = dataset_info.get("timeframe", "")
                le_candidate = os.path.join(artifact_dir, f"bilstm_{timeframe}_le.pkl")
                if os.path.isfile(le_candidate):
                    le_filename = f"bilstm_{timeframe}_le.pkl"

            models.append({
                "model_file": model_file,
                "model_name": _derive_model_display_name(base_name),
                "model_type": model_info.get("model_type", ""),
                "symbol": dataset_info.get("symbol", ""),
                "timeframe": dataset_info.get("timeframe", ""),
                "hyperparameters": model_info.get("hyperparameters", {}),
                "scaler_filename": scaler_filename,
                "label_encoder_filename": le_filename,
            })

    return sanitize_json_value({"strategies": strategies, "models": models})


def _derive_model_display_name(filename: str) -> str:
    """Turn a model filename into a human-readable display name.
    e.g. 'lightgbm_clf_model_15m.pkl' -> 'lightgbm_clf_15m'
         'bilstm_15m.keras' -> 'bilstm_15m'
    """
    name = filename.rsplit(".", 1)[0]          # strip extension
    name = name.replace("_model", "")          # remove '_model' suffix
    return name


def _find_artifact_config(model_filename: str, artifact_dir: str) -> dict | None:
    """Find and load the artifact config JSON for a given model file.
    Naming patterns:
        model file:    lightgbm_clf_model_15m.pkl   -> artifact: lightgbm_clf_15m_config.json
        model file:    bilstm_15m.keras             -> artifact: bilstm_clf_15m_config.json
        model file:    gru_15m.keras                -> artifact: gru_reg_15m_config.json
    """
    base = model_filename.rsplit(".", 1)[0]    # strip extension
    base = base.replace("_model", "")          # e.g. lightgbm_clf_15m

    # Try direct match first
    candidate = os.path.join(artifact_dir, f"{base}_config.json")
    if os.path.isfile(candidate):
        return _load_json(candidate)

    # For keras models without _clf/_reg suffix, try both
    for suffix in ("_clf", "_reg"):
        # e.g. bilstm_15m -> bilstm_clf_15m_config.json
        parts = base.rsplit("_", 1)
        if len(parts) == 2:
            candidate = os.path.join(artifact_dir, f"{parts[0]}{suffix}_{parts[1]}_config.json")
            if os.path.isfile(candidate):
                return _load_json(candidate)

    return None


def _load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


# Signal generation helpers

def _generate_strategy_signals(strategy_name: str, config: dict) -> pd.DataFrame:
    """Generate signals for a single strategy using get_signal_df
    (same path as BacktestEngine.load_signals).
    Returns a DataFrame with a 'signal' column, indexed by datetime."""
    from signals.main import get_signal_df, _extract_indicators_for_strategy
    from utils.config import load_config

    engine = get_engine()

    # Fetch the full strategy config from meta_data.strategies
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT config FROM meta_data.strategies WHERE strategy_name = :name LIMIT 1"),
            {"name": strategy_name},
        ).mappings().fetchone()

    if not row:
        # Fallback: try playbook
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT config FROM meta_data.playbook WHERE strategy_name = :name LIMIT 1"),
                {"name": strategy_name},
            ).mappings().fetchone()

    if not row:
        raise ValueError(f"Strategy '{strategy_name}' not found")

    strat_config = row["config"]
    if isinstance(strat_config, str):
        strat_config = json.loads(strat_config)

    # Merge timehorizon from config (user's chosen timeframe overrides)
    strat_config["timehorizon"] = config.get("timehorizon", strat_config.get("timehorizon", "5m"))

    indicator_config = load_config("indicators/config.yaml")
    selected_indicators = _extract_indicators_for_strategy(strat_config, indicator_config)

    signal_df = get_signal_df(
        save_csv=False,
        exchange=config.get("exchange", "binance"),
        symbol=config.get("symbol", "BTC"),
        start=config.get("start_date"),
        end=config.get("end_date"),
        strategy_name=strategy_name,
        selected_indicators=selected_indicators,
        strategy_config=strat_config,
    )

    if signal_df is None or signal_df.empty:
        return pd.DataFrame(columns=["signal"])

    # Ensure we have a clean signal column
    if "signal" in signal_df.columns:
        return signal_df[["signal"]]
    return signal_df[[signal_df.columns[0]]].rename(columns={signal_df.columns[0]: "signal"})


def _generate_model_signals(model_info: dict, config: dict) -> pd.DataFrame:
    """Load a saved ML model and generate prediction-based signals.
    Uses the user's start_date/end_date for data range, not the model's
    training dates.  Returns a DataFrame with a 'signal' column."""
    import joblib
    from ml.data_formation import build_dataset
    from ml.data_utils import load_ml_config
    from preprocess_techs.external_backtest import _predictions_to_signal_df

    model_file = model_info["model_file"]
    model_path = os.path.join("ml/models", model_file)
    artifact_dir = "ml/artifacts"

    # Load artifact config for feature/preprocessing info
    artifact_config = _find_artifact_config(model_file, artifact_dir)
    if artifact_config is None:
        raise ValueError(f"No artifact config found for model '{model_file}'")

    model_type = artifact_config.get("model_info", {}).get("model_type", "classification")
    dataset_cfg = artifact_config.get("dataset", {})
    preprocessing_cfg = artifact_config.get("preprocessing", {})
    feature_metadata = artifact_config.get("feature_metadata", {})
    feature_order = feature_metadata.get("feature_order", [])

    # Build the ML config for dataset construction, using the USER's date range
    ml_cfg = load_ml_config("ml/config.yaml")
    ml_cfg["data"] = {
        "enabled": True,
        "symbol": config.get("symbol", dataset_cfg.get("symbol", "BTC")),
        "exchange": config.get("exchange", dataset_cfg.get("exchange", "binance")),
        "timeframe": dataset_cfg.get("timeframe", "15m"),
        "start_date": config.get("start_date", dataset_cfg.get("start_date")),
        "end_date": config.get("end_date", dataset_cfg.get("end_date")),
    }
    ml_cfg["model_type"] = model_type

    # Build dataset (OHLCV + indicators + target)
    full_df = build_dataset(ml_cfg)
    if full_df.empty:
        return pd.DataFrame(columns=["signal"])

    # Drop sentiment column if present
    if "sen_MARKET" in full_df.columns:
        full_df = full_df.drop(columns=["sen_MARKET"])

    feat_cols = [c for c in full_df.columns if c not in ("target", "date_time")]
    # Only scale columns that the scaler was fitted on
    cols_to_scale = [c for c in feat_cols if c in feature_order]

    # Apply preprocessing/scaling
    scaling_method = preprocessing_cfg.get("scaling_method", "")
    if scaling_method:
        print(scaling_method)
        scaler_path = os.path.join(artifact_dir, f"{scaling_method}.pkl")
        if os.path.isfile(scaler_path):
            scaler = joblib.load(scaler_path)
            if cols_to_scale:
                full_df[cols_to_scale] = scaler.transform(full_df[cols_to_scale])

    # Prepare features in the correct order
    available_features = [c for c in feature_order if c in full_df.columns]
    if not available_features:
        available_features = [c for c in full_df.columns if c not in ("target", "date_time")]

    # Apply stationarity method (e.g., fractional differencing)
    stationarity_method = preprocessing_cfg.get("stationarity_method", "")
    if stationarity_method == "fractional_differencing":
        from ml.preprocessing.stationarity import fractional_differencing
        if cols_to_scale:
            full_df[cols_to_scale] = fractional_differencing(full_df[cols_to_scale])

    print(available_features)
    full_df = full_df.dropna(axis=0, how='any')

    is_keras = model_file.endswith(".keras")
    is_bilstm = "bilstm" in model_file.lower()
    is_gru = "gru" in model_file.lower()

    if is_keras:
        if is_bilstm:
            from ml.classifiers.bilstm import BiLSTMClassifier
            model_obj = BiLSTMClassifier()
            # Derive timeframe from filename
            timeframe = dataset_cfg.get("timeframe", "15m")
            model_obj.model = __import__("tensorflow").keras.models.load_model(model_path)
            # Load label encoder
            le_path = os.path.join(artifact_dir, f"bilstm_{timeframe}_le.pkl")
            if os.path.isfile(le_path):
                model_obj.le = joblib.load(le_path)

            preds_series = model_obj.predict(full_df[available_features + (["target"] if "target" in full_df.columns else [])])
            predictions_df = pd.DataFrame({"predictions": preds_series.values}, index=preds_series.index)
            predictions_df.index.name = "date_time"

        elif is_gru:
            from ml.regressors.gru import GRURegressor
            model_obj = GRURegressor()
            model_obj.model = __import__("tensorflow").keras.models.load_model(model_path)

            preds_series = model_obj.predict(full_df[available_features + (["target"] if "target" in full_df.columns else [])])
            predictions_df = pd.DataFrame({"predictions": preds_series.values}, index=preds_series.index)
            predictions_df.index.name = "date_time"

            # Convert regression output to signals
            threshold = 0.25
            predictions_df["predictions"] = np.where(
                predictions_df["predictions"] > threshold, 1,
                np.where(predictions_df["predictions"] < -threshold, -1, 0)
            )
    else:
        # Standard sklearn/lightgbm/xgboost .pkl model
        loaded_data = joblib.load(model_path)

        # BaseClassifier saves as {'model': ..., 'le': ...}
        # BaseRegressor saves just the model object
        if isinstance(loaded_data, dict) and "model" in loaded_data:
            model_obj = loaded_data["model"]
            label_encoder = loaded_data.get("le")
        else:
            model_obj = loaded_data
            label_encoder = None

        X = full_df[available_features]
        preds = model_obj.predict(X)
        preds = np.ravel(preds)

        # Inverse-transform label-encoded predictions for classifiers
        if label_encoder is not None:
            preds = label_encoder.inverse_transform(preds)

        # Convert regression output to -1/0/1 signals
        is_classifier = model_type in ("classification", "timeseries")
        if not is_classifier:
            threshold = 0.25
            preds = np.where(
                preds > threshold, 1,
                np.where(preds < -threshold, -1, 0)
            )

        predictions_df = pd.DataFrame(
            {"predictions": preds},
            index=full_df.index,
        )
        predictions_df.index.name = "date_time"

    # Convert predictions to signal_df format
    signal_df = _predictions_to_signal_df(predictions_df)
    print('Number of signals:', signal_df['signal'].value_counts())
    return signal_df


def _combine_signals(signal_dfs: list[pd.DataFrame], combination_rule: str) -> pd.DataFrame:
    """Combine multiple signal DataFrames using AND/OR logic.

    AND: signal = 1 only if ALL signal 1, -1 only if ALL signal -1, else 0
    OR:  signal = 1 if ANY signal 1, -1 if ANY signal -1, long priority on conflict, else 0
    """
    if not signal_dfs:
        return pd.DataFrame(columns=["signal"])

    if len(signal_dfs) == 1:
        return signal_dfs[0]

    # Align all signal DataFrames on their index (intersection)
    combined = pd.DataFrame(index=signal_dfs[0].index)
    for i, sdf in enumerate(signal_dfs):
        col = f"sig_{i}"
        s = sdf["signal"] if "signal" in sdf.columns else sdf.iloc[:, 0]
        combined[col] = s
    combined = combined.dropna()

    sig_cols = [c for c in combined.columns if c.startswith("sig_")]

    if combination_rule.upper() == "AND":
        # 1 only if ALL are 1
        all_long = (combined[sig_cols] == 1).all(axis=1)
        # -1 only if ALL are -1
        all_short = (combined[sig_cols] == -1).all(axis=1)

        result = pd.Series(0, index=combined.index, name="signal")
        result[all_long] = 1
        result[all_short] = -1
    else:  # OR
        any_long = (combined[sig_cols] == 1).any(axis=1)
        any_short = (combined[sig_cols] == -1).any(axis=1)

        result = pd.Series(0, index=combined.index, name="signal")
        # Short first, then long overrides (long takes priority on conflict)
        result[any_short] = -1
        result[any_long] = 1

    return pd.DataFrame({"signal": result})


# Backtest execution

def run_backtest_task(req_id: str, config: dict, strategy_name: str):
    """Background task: generate signals based on mode, run backtest, save results."""
    engine = get_engine()

    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE public.backtest_requests SET status = 'Running' WHERE request_id = :req_id"),
                {"req_id": req_id},
            )

        mode = config.get("mode", "strategy")
        selected_strategies = config.get("selected_strategies", [])
        selected_models = config.get("selected_models", [])
        combination_rule = config.get("combination_rule", "AND")

        # ----- Signal generation by mode -----
        signal_df = None

        if mode == "strategy":
            strat_name = selected_strategies[0] if selected_strategies else config.get("strategy_name")
            signal_df = _generate_strategy_signals(strat_name, config)

        elif mode == "model":
            model_info = selected_models[0] if selected_models else {}
            signal_df = _generate_model_signals(model_info, config)

        elif mode == "strategy_combination":
            sig_list = []
            for sname in selected_strategies:
                sdf = _generate_strategy_signals(sname, config)
                if sdf is not None and not sdf.empty:
                    sig_list.append(sdf)
            signal_df = _combine_signals(sig_list, combination_rule)

        elif mode == "strategy_model_combination":
            sig_list = []
            for sname in selected_strategies:
                sdf = _generate_strategy_signals(sname, config)
                if sdf is not None and not sdf.empty:
                    sig_list.append(sdf)
            for minfo in selected_models:
                mdf = _generate_model_signals(minfo, config)
                if mdf is not None and not mdf.empty:
                    sig_list.append(mdf)
            signal_df = _combine_signals(sig_list, combination_rule)

        # ----- Run backtest engine with the generated signals -----
        from backtest.backtest import BacktestEngine
        from preprocess_techs.external_backtest import _predictions_to_signal_df
        from utils.db import save_ledger

        backtest_engine = BacktestEngine(config)
        backtest_engine.load_data()

        # Inject the signal_df instead of engine.load_signals()
        if signal_df is not None and not signal_df.empty:
            # Ensure column is named 'signal'
            if "signal" not in signal_df.columns and len(signal_df.columns) > 0:
                signal_df = signal_df.rename(columns={signal_df.columns[0]: "signal"})
            backtest_engine.signal_df = signal_df

        # Map signals and build trades
        if backtest_engine.signal_df is not None and not backtest_engine.signal_df.empty:
            backtest_engine._map_signals_to_1m()
            if backtest_engine.mapped_signals is not None and not backtest_engine.mapped_signals.empty:
                backtest_engine._build_trades()

        # Execute
        results = backtest_engine.execute()

        if backtest_engine.trade_ledger is not None and not backtest_engine.trade_ledger.empty:
            backtest_engine.trade_ledger = backtest_engine.trade_ledger.sort_values("entry_time").reset_index(drop=True)
            results["trade_ledger"] = backtest_engine.trade_ledger
            save_ledger(backtest_engine.trade_ledger, strategy_name, schema="backtest_ledgers", table_suffix="")

        # Compute result summary
        result_summary = {
            "total_trades": results.get("total_trades", 0),
            "final_balance": results.get("final_balance", 0),
        }

        try:
            with engine.connect() as conn:
                ledger_res = conn.execute(
                    text(f"SELECT net_pnl, balance_after_trade, exit_time FROM backtest_ledgers.{strategy_name} ORDER BY exit_time ASC")
                ).mappings().fetchall()
                ledger = [dict(row) for row in ledger_res]

            if ledger:
                from stats.metrics import calculate_metrics

                df = pd.DataFrame(ledger)
                df["exit_time"] = pd.to_datetime(df["exit_time"])
                df = df.sort_values("exit_time").set_index("exit_time")
                returns = df["balance_after_trade"].pct_change().fillna(0)

                if not returns.empty and returns.std() != 0:
                    metrics = calculate_metrics(returns)
                else:
                    metrics = {}

                win_rate = metrics.get("win_rate", 0) or 0
                result_summary["sharpe"] = metrics.get("sharpe_ratio")
                result_summary["max_drawdown"] = (metrics.get("max_drawdown", 0) or 0) * 100
                result_summary["win_rate"] = win_rate * 100
                result_summary["final_balance"] = float(df["balance_after_trade"].iloc[-1])

        except Exception as metrics_err:
            print(f"Strategy builder metrics computation failed: {metrics_err}")

        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE public.backtest_requests
                    SET status = 'Completed',
                        completed_at = CURRENT_TIMESTAMP,
                        result_summary = :result_summary
                    WHERE request_id = :req_id
                """),
                {
                    "result_summary": json.dumps(result_summary),
                    "req_id": req_id,
                },
            )

    except Exception as e:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE public.backtest_requests
                    SET status = 'Failed',
                        completed_at = CURRENT_TIMESTAMP,
                        result_summary = :error_summary
                    WHERE request_id = :req_id
                """),
                {
                    "error_summary": json.dumps({"error": str(e)}),
                    "req_id": req_id,
                },
            )


def submit_backtest(config: dict, background_tasks):
    """Insert a new backtest request with source='strategy_builder' and
    launch the backtest task in the background."""
    init_db()
    req_id = str(uuid.uuid4())
    mode = config.get("mode", "strategy")
    exchange = config.get("exchange", "UNKNOWN")
    symbol = config.get("symbol", "UNKNOWN")
    timehorizon = config.get("timehorizon", "UNKNOWN")

    if mode == "strategy":
        base_name = config.get("selected_strategies", [""])[0]
    elif mode == "model":
        models = config.get("selected_models", [])
        base_name = models[0].get("model_name", "model") if models else "model"
    else:
        base_name = config.get("strategy_name", "combo")
        
    strategy_name = f"{base_name}_{exchange}_{symbol}_{timehorizon}"

    engine = get_engine()

    # For single-strategy mode, fetch strategy_config from DB and attach
    if mode == "strategy":
        selected = config.get("selected_strategies", [])
        sname = selected[0] if selected else config.get("strategy_name")
        if sname:
            with engine.connect() as conn:
                try:
                    res = conn.execute(
                        text("SELECT config FROM meta_data.strategies WHERE strategy_name = :name LIMIT 1"),
                        {"name": sname},
                    ).mappings().fetchone()
                    if res and res.get("config"):
                        strat_config = res["config"]
                        if isinstance(strat_config, str):
                            strat_config = json.loads(strat_config)
                        config["strategy_config"] = strat_config
                except Exception:
                    pass

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.backtest_requests
                    (request_id, request_config, status, strategy_name, source)
                VALUES (:req_id, :config, 'Pending', :strategy_name, 'strategy_builder')
            """),
            {
                "req_id": req_id,
                "config": json.dumps(config),
                "strategy_name": strategy_name,
            },
        )
    background_tasks.add_task(run_backtest_task, req_id, config, strategy_name)
    return req_id


# Save strategy

def save_strategy(config: dict) -> dict:
    """Save a new strategy to meta_data.strategies.

    Single strategy (not a combination): name is auto-generated as
    {exchange}_{symbol}_{timehorizon}_{strategy_name}; long/short conditions
    are pulled from the source strategy's real config.

    Combination (strategy_combination / strategy_model_combination): user
    provides a name; config is saved as:
        {
            "<strategy_name_1>": {"long": {...}, "short": {...}},
            "<strategy_name_2>": {"long": {...}, "short": {...}},
            "model": "<model_name>" | ["<model_name>", ...],   # only if models selected
            "symbol": ..., "exchange": ..., "timehorizon": ...,
            "allow_simulation": ..., "allow_execution": ...,
            "allow_combination": True,
            "combination_rule": "AND" | "OR"
        }
    """
    engine = get_engine()

    strategy_name = config.get("strategy_name", "")
    exchange = config.get("exchange", "")
    symbol = config.get("symbol", "")
    timehorizon = config.get("timehorizon", "")
    allow_execution = False
    allow_simulation = False
    is_combination = config.get("is_combination", False)
    selected_strategies = config.get("selected_strategies", [])
    selected_models = config.get("selected_models", [])
    combination_rule = config.get("combination_rule", "AND")

    def _fetch_long_short(name: str) -> dict:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT config FROM meta_data.strategies WHERE strategy_name = :name LIMIT 1"),
                {"name": name},
            ).mappings().fetchone()
        if not row:
            return {"long": {}, "short": {}}
        cfg = row["config"]
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        return {"long": cfg.get("long", {}), "short": cfg.get("short", {})}

    if is_combination:
        # User-provided name — check uniqueness
        final_name = strategy_name
        with engine.connect() as conn:
            existing = conn.execute(
                text("SELECT 1 FROM meta_data.strategies WHERE strategy_name = :name LIMIT 1"),
                {"name": final_name},
            ).fetchone()
        if existing:
            return {"error": "Strategy name already exists, please choose a different name"}

        full_config: dict = {}
        for sname in selected_strategies:
            full_config[sname] = _fetch_long_short(sname)

        if selected_models:
            model_names = [m.get("model_name") or m.get("model_file") for m in selected_models]
            full_config["model"] = model_names[0] if len(model_names) == 1 else model_names

        full_config["symbol"] = symbol
        full_config["exchange"] = exchange
        full_config["timehorizon"] = timehorizon
        full_config["allow_simulation"] = allow_simulation
        full_config["allow_execution"] = allow_execution
        full_config["allow_combination"] = True
        full_config["combination_rule"] = combination_rule

    else:
        # Single strategy — auto-generate name, pull real long/short from source
        final_name = f"{exchange}_{symbol}_{timehorizon}_{strategy_name}"
        source = _fetch_long_short(strategy_name) if strategy_name else {"long": {}, "short": {}}
        full_config = {
            "exchange": exchange,
            "symbol": symbol,
            "timehorizon": timehorizon,
            "allow_execution": allow_execution,
            "allow_simulation": allow_simulation,
            "long": source["long"],
            "short": source["short"],
        }

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO meta_data.strategies (strategy_name, config)
                VALUES (:name, :config)
            """),
            {"name": final_name, "config": json.dumps(full_config)},
        )

    return {"success": True, "strategy_name": final_name}


# Request listing / detail  (filtered by source = 'strategy_builder')

def get_all_requests():
    init_db()
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT request_id, request_config, status, created_at,
                   completed_at, strategy_name, result_summary
            FROM public.backtest_requests
            WHERE source = 'strategy_builder'
            ORDER BY created_at DESC
        """)).mappings().fetchall()

    return [{
        **dict(row),
        "request_id": str(row["request_id"]),
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
    } for row in res]


def get_request_detail(request_id: str):
    """Identical to backtest.get_request_detail — reused here to keep
    the strategy builder self-contained."""
    init_db()
    engine = get_engine()

    with engine.connect() as conn:
        req_res = conn.execute(
            text("SELECT * FROM public.backtest_requests WHERE request_id = :req_id"),
            {"req_id": request_id},
        ).mappings().fetchone()

        if not req_res:
            return None

        request_data = {
            **dict(req_res),
            "request_id": str(req_res["request_id"]),
            "created_at": req_res["created_at"].isoformat() if req_res["created_at"] else None,
            "completed_at": req_res["completed_at"].isoformat() if req_res["completed_at"] else None,
        }

        strategy_name = req_res["strategy_name"]

        # Read ledger
        try:
            ledger_res = conn.execute(
                text(f"SELECT entry_time, exit_time, direction, entry_price, exit_price, quantity, gross_pnl, commission, slippage, net_pnl, balance_after_trade FROM backtest_ledgers.{strategy_name} ORDER BY exit_time ASC")
            ).mappings().fetchall()
            ledger = [dict(row) for row in ledger_res]
        except Exception:
            ledger = []

    # Compute chart data
    equity_curve = []
    drawdown_curve = []
    monthly_returns = []
    win_loss_pie = []

    if ledger:
        from stats.metrics import calculate_metrics

        df = pd.DataFrame(ledger)
        if "exit_time" in df.columns and "balance_after_trade" in df.columns and not df.empty:
            df["exit_time"] = pd.to_datetime(df["exit_time"])
            df = df.sort_values("exit_time").set_index("exit_time")

            returns = df["balance_after_trade"].pct_change().fillna(0)
            metrics = calculate_metrics(returns)

            # 1. Equity Curve
            equity_curve = [{"date": str(idx), "value": float(val)} for idx, val in df["balance_after_trade"].items()]

            # 2. Drawdown Curve
            dd_series = metrics.get("to_drawdown_series", {})
            drawdown_curve = [{"date": str(k), "value": float(v) * 100} for k, v in dd_series.items()] if dd_series else []

            # 3. Monthly Returns
            mr_df = metrics.get("monthly_returns", {})
            month_map = {
                "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
                "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
                "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
            }
            for col_month, year_dict in mr_df.items():
                if col_month in month_map:
                    for year, val in year_dict.items():
                        if val != 0:
                            monthly_returns.append({
                                "month": f"{year}-{month_map[col_month]}",
                                "return": float(val) * 100,
                            })
            monthly_returns.sort(key=lambda x: x["month"])

            # 4. Win/Loss Pie
            win_rate = metrics.get("win_rate", 0)
            if win_rate is None:
                win_rate = 0
            total_trades = len(df)
            win_count = int(total_trades * win_rate)
            loss_count = total_trades - win_count
            win_loss_pie = [
                {"name": "WIN", "value": win_count},
                {"name": "LOSS", "value": loss_count},
            ]

            # 5. Update summary metrics
            summary = request_data.get("result_summary")
            if isinstance(summary, str):
                summary = json.loads(summary)
            if summary is None:
                summary = {}

            summary["sharpe"] = metrics.get("sharpe_ratio")
            summary["max_drawdown"] = metrics.get("max_drawdown", 0) * 100 if metrics.get("max_drawdown") is not None else None
            summary["win_rate"] = win_rate * 100

            request_data["result_summary"] = summary

    return {
        "request": request_data,
        "equity_curve": equity_curve,
        "drawdown": drawdown_curve,
        "monthly_returns": monthly_returns,
        "win_loss": win_loss_pie,
        "ledger": ledger,
    }
