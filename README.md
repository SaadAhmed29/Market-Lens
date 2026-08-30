# MarketLens

A full-stack algorithmic trading platform that automates the entire trading lifecycle — from market data collection and signal generation to live execution and performance analysis. Built during a 6-week internship at Neurog (Neuroship Intern Cohort 5).

---

## Overview

MarketLens connects to Binance and Bybit cryptocurrency exchanges and handles everything automatically — downloading OHLCV market data, generating buy and sell signals using technical indicators or machine learning models, backtesting strategies on historical data, simulating trades with paper money, and executing real orders on the exchange via API. A Next.js web dashboard with a cyberpunk dark theme ties everything together in one place.

---

## Supported Symbols

BTC, ETH, SOL, DOGE, ADA, LTC, MINA, SUI

---

## Project Structure

```
MarketLens/
├── data/                        # Data pipeline
│   ├── binance/                 # Binance exchange config and planners
│   ├── bybit/                   # Bybit exchange config and planners
│   └── data_downloader.py       # Incremental OHLCV downloader
├── signals/                     # Signal generation engine
│   ├── config/                  # Strategy YAML configs
│   └── main.py                  # Signal pipeline entry point
├── backtest/                    # Vectorized backtesting engine
│   ├── backtest_engine.py
│   └── main.py
├── ml_module/                   # Machine learning pipeline
│   ├── data_formation.py        # Dataset builder
│   ├── classifiers/             # Classification models
│   ├── regressors/              # Regression models
│   ├── evaluation/              # Metrics and evaluator
│   ├── persistence/             # Artifact manager
│   ├── preprocessing/           # Scaling and stationarity
│   └── utils/                   # ML utilities and logging
├── preprocess_techs/            # Preprocessing techniques runner
├── sentiment_analysis/          # NLP sentiment pipeline
│   ├── data_fetcher.py          # Reddit scraper
│   ├── data_prep.py             # Text cleaning pipeline
│   ├── classifier.py            # FinBERT sentiment classifier
│   └── main.py                  # Sentiment pipeline runner
├── simulator/                   # Paper trading simulator
│   ├── simulator.py
│   └── main.py
├── execution/                   # Live trading execution
│   ├── execution.py             # Bybit API integration
│   ├── account_stats.py         # Account analytics
│   └── main.py
├── stats/                       # Performance analytics
│   ├── metrics.py               # QuantStats metrics
│   ├── plots.py                 # Chart generation
│   └── main.py
├── talib_indicators/            # TA-Lib indicator wrapper
│   └── talib_indicators.py
├── utils/                       # Shared utilities
│   ├── db.py                    # Database helpers and CLI
│   ├── schema.py                # PostgreSQL schema definitions
│   ├── config_loader.py         # Config loading utilities
│   └── ml_utils.py              # ML helper functions
├── backend/                     # FastAPI backend
│   ├── modules/                 # Business logic per module
│   └── routes/                  # API route handlers
└── frontend/marketlens-ui/      # Next.js frontend
    └── src/
        ├── app/                 # App Router pages
        ├── components/          # UI components
        ├── hooks/               # TanStack Query hooks
        ├── lib/                 # Axios and query client
        ├── store/               # Zustand global state
        └── types/               # TypeScript type definitions
```

---

## Modules

### Data Pipeline
Connects to Binance and Bybit APIs using `python-binance` and `pybit`. Downloads historical OHLCV candlestick data for all symbols starting from 2023. Incremental by design — on each run it checks what data already exists in the database and only fetches what is missing. Drops the last incomplete candle on every fetch. Stores data in PostgreSQL under separate schemas (`binance_data`, `bybit_data`) with one table per symbol per timeframe (e.g. `btc_1m`). Runs automatically via Windows Task Scheduler every minute.

### Signal Generation
Rule-based signal engine driven entirely by YAML config files. Each strategy defines long and short conditions using technical indicators and candlestick patterns with operators (`cross_above`, `cross_below`, `<`, `>`) and a `persist_bars` parameter that requires a condition to hold for N consecutive candles before triggering. Conditions are combined using AND/OR rules. Signals output 1 (long), -1 (short), or 0 (no trade).

### Backtesting Engine
Fully vectorized backtesting engine using Pandas and NumPy — no row-by-row iteration. Supports fixed percentage position sizing, percentage-based take profit and stop loss, commission and slippage deduction, long and short trades, and exit on opposite signal. Generates a complete trade ledger and saves it to PostgreSQL. Integrates with the Stats module for full performance reporting.

### Machine Learning Module
End-to-end ML pipeline for training predictive models on market data.

**Classifiers:** Logistic Regression, Decision Tree, Random Forest, Extra Trees, XGBoost, LightGBM, CatBoost, SVM, BiLSTM

**Regressors:** Linear Regression, Ridge, Lasso, Random Forest, Extra Trees, XGBoost, LightGBM, CatBoost, SVR, GRU

**Pipeline:**
- Fetches OHLCV data and resamples from 1m to the configured timeframe
- Computes TA-Lib indicators from a YAML config with aliases
- Maps sentiment labels from the database using nearest timestamp matching
- Generates targets using future direction (3-class: 1/0/-1 with threshold), future return, or next close
- Applies MinMax or MaxAbs scaling and fractional differencing for stationarity
- Trains all configured models, saves artifacts and metrics as JSON
- Evaluates models and ranks by primary metric (accuracy for classifiers, MSE for regressors)

### TA-Lib Indicators
Full wrapper around the TA-Lib library covering all indicator categories — overlap studies (SMA, EMA, BBANDS, etc.), momentum (RSI, MACD, Stochastic, etc.), volume, cycle, price transform, volatility, statistical functions, math transforms, math operators, and all 61 candlestick pattern recognition functions. Fully config-driven with alias-based column naming.

### Sentiment Analysis
Reddit scraper using PRAW that collects posts and comments for each symbol from dedicated and general crypto subreddits. Text is cleaned (lowercasing, URL removal, HTML stripping, punctuation removal, emoji conversion, language detection) and non-English content is filtered. Posts are classified using FinBERT (`ProsusAI/finbert`) from HuggingFace — a BERT model fine-tuned on financial text — producing positive, negative, or neutral labels with confidence scores.

### Simulation Module
Processes live market data candle by candle to emulate real trading without risking money. Fetches 1-minute candles from the exchange every minute, resamples to the strategy timeframe, and checks for new signals after each completed candle. Uses the backtest engine helpers for entry price, position sizing, TP/SL, PnL, and balance calculation. Saves positions and stats to a shared `simulation` schema in PostgreSQL.

### Execution Module
Live trading on Bybit using their REST API via `pybit`. Places real market orders when signals are generated, sets TP and SL directly on Bybit so the exchange manages exits automatically. Monitors position status every minute via `get_positions`. Uses actual API response values for PnL, fees, and balance instead of calculating them locally. Runs all strategies automatically without CLI input. Selects the best performing strategy per symbol based on Sharpe ratio from simulation stats.

### Stats Module
Calculates over 40 performance metrics using QuantStats including Sharpe, Sortino, Calmar, max drawdown, CAGR, win rate, profit factor, VaR, CVaR, Kelly criterion, and more. Generates equity curve, drawdown, rolling Sharpe, rolling volatility, monthly returns heatmap, yearly returns, and return distribution charts. Saves all metrics as a structured JSON file.

### Strategy Builder
Extends the backtest module with four execution modes — single strategy, single model, strategy combination, and strategy plus model combination. Combination signals are merged using AND (all must agree) or OR (any signal triggers) logic. Models are loaded from saved artifacts and their signals are generated using the same preprocessing pipeline used during training. Composite strategies can be saved to the database with auto-generated names.

---

## Tech Stack

### Backend
- **Language:** Python 3.11
- **API:** FastAPI
- **Database:** PostgreSQL with SQLAlchemy
- **Exchange APIs:** python-binance, pybit
- **ML:** scikit-learn, XGBoost, LightGBM, CatBoost, TensorFlow/Keras, darts
- **Indicators:** TA-Lib
- **NLP:** HuggingFace Transformers (FinBERT), PRAW
- **Analytics:** QuantStats, pandas, numpy
- **Config:** PyYAML, python-dotenv

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui (Nova preset)
- **Data Fetching:** TanStack Query
- **State:** Zustand
- **Charts:** Recharts
- **HTTP:** Axios

### Infrastructure
- **Database:** PostgreSQL (single DB, multiple schemas)
- **Scheduling:** Windows Task Scheduler (data pipeline, 1-minute interval)
- **Environment:** `.env` for all credentials

---

## Database Schemas

| Schema | Purpose |
|---|---|
| `binance_data` | Binance OHLCV tables per symbol/timeframe |
| `bybit_data` | Bybit OHLCV tables per symbol/timeframe |
| `meta_data` | Strategy configs, playbook, data config, sentiment config, backtest config |
| `signal` | Signal history per strategy |
| `simulation` | Live simulation positions and stats |
| `simulation_ledgers` | Paper trading ledgers per strategy |
| `execution` | Live execution positions and stats |
| `execution_ledgers` | Real trading ledgers per strategy |
| `backtest_ledgers` | Backtest results and config |
| `sentiment_data` | Raw and cleaned Reddit posts |
| `accounts` | Bybit API credentials, trade history, account stats |
| `public` | Backtest requests table |

---

## Frontend Pages

| Page | Description |
|---|---|
| Dashboard | Overview widgets and strategy table |
| Strategies | Strategy list and detail with charts |
| Backtests | Request form and results with full ledger |
| Wallets | Account management and trade history |
| Executions | Live execution monitoring and detail |
| ML Models | Trained model list and detail |
| Sentiment | Market sentiment overview and post cards |
| Strategy Builder | Composite strategy creation and backtesting |

---

## Setup

### Prerequisites
- Python 3.11
- Node.js 18+
- PostgreSQL
- TA-Lib (system library)

### Backend
```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

BYBIT_API_KEY=
BYBIT_API_SECRET=

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=

HF_TOKEN=
```

Run the FastAPI backend:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend/marketlens-ui
npm install
npm run dev
```

Create `frontend/marketlens-ui/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Data Pipeline
Run manually or set up Task Scheduler:
```bash
python -m data.binance.main
python -m data.bybit.main
```

---

## Exchanges

| Exchange | Data | Simulation | Execution |
|---|---|---|---|
| Binance | ✅ | ✅ | ❌ |
| Bybit | ✅ | ✅ | ✅ |

---
