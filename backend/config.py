"""
Configuration for the daily automated prediction pipeline.
Adjust these values to control pipeline behavior.
"""

from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR.parent / "models"
LOGS_DIR = BASE_DIR / "logs"

# Database
PREDICTIONS_DB = DATA_DIR / "predictions.db"
STOCK_DB = DATA_DIR / "stocksense.db"

# CSV Files (for backup exports)
PREDICTIONS_CSV_BACKUP = DATA_DIR / "predictions_backup.csv"

# Scheduler
SCHEDULER_TIME = "16:00"  # 4:00 PM (after market close)
TIMEZONE = "US/Eastern"

# Scraping
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 300  # 5 minutes

# Processing
BATCH_SIZE_FINBERT = 32  # FinBERT batch size (adjust for GPU memory)
USE_TRANSFORMER_GPU = True  # Use GPU for transformer if available

# Prediction
USE_ML_MODELS = True
BACKUP_TO_RULE_BASED = True  # Use rule-based if ML fails

# Model versions
MODEL_CATBOOST_PATH = MODELS_DIR / "catboost.pkl"
MODEL_LGB_PATH = MODELS_DIR / "lgb.pkl"
MODEL_XGB_PATH = MODELS_DIR / "xgboost.pkl"
MODEL_TRANSFORMER_PATH = MODELS_DIR / "transformer.pt"
MODEL_CONFIG_PATH = MODELS_DIR / "config.pkl"
MODEL_NORM_STATS_PATH = MODELS_DIR / "norm_stats.pkl"
MODEL_SECTOR_ENCODER_PATH = MODELS_DIR / "sector_encoder.pkl"
MODEL_TICKER_TO_ID_PATH = MODELS_DIR / "ticker_to_id.pkl"

# Logging
LOG_DIR = LOGS_DIR
LOG_LEVEL = "INFO"

# API
API_HOST = "127.0.0.1"
API_PORT = 8000
API_WORKERS = 1

# Feature names (must match trained model)
FEATURE_COLUMNS = [
    "open", "high", "low", "close", "adj_close", "volume",
    "daily_return_pct", "log_return", "price_change",
    "intraday_range", "intraday_range_pct",
    "sma_5", "sma_10", "sma_20", "sma_50",
    "ema_12", "ema_26",
    "volatility_5d", "volatility_20d", "atr_14",
    "rsi_14", "macd", "macd_signal", "macd_histogram",
    "volume_sma_10", "volume_ratio", "on_balance_volume",
    "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_pct",
    "above_sma_20", "above_sma_50", "golden_cross",
    "market_cap", "pe_ratio", "forward_pe", "price_to_book",
    "dividend_yield", "beta", "shares_outstanding", "float_shares",
    "avg_volume_10d",
    "day_of_week", "week_of_year", "month", "quarter",
    "is_market_day", "is_earnings_week",
]

# Target stocks (153 tickers across 17 sectors)
TARGET_TICKERS = [
    # Big Tech
    "AAPL", "TSLA", "AMZN", "MSFT", "NVDA", "GOOGL", "META", "AMD", "INTC",
    # Semiconductors & Hardware
    "QCOM", "AVGO", "TSM", "ASML", "MU", "AMAT", "KLAC", "LRCX", "ARM",
    # Software & SaaS
    "CRM", "NOW", "WDAY", "SNOW", "PLTR", "ADBE", "ORCL", "INTU", "DDOG",
    # E-Commerce & Consumer Internet
    "SHOP", "PYPL", "NFLX", "SPOT", "UBER", "ABNB", "BKNG", "DASH",
    # Finance & Banking
    "JPM", "GS", "BAC", "MS", "C", "WFC", "BLK", "AXP", "SCHW",
    # Insurance & Asset Management
    "BRK-B", "CB", "MET", "PRU", "ALL", "PGR", "AFL", "AIG", "TRV",
    # Oil & Gas / Energy
    "XOM", "CVX", "COP", "BP", "SHEL", "SLB", "OXY", "PSX", "HAL",
    # Renewable Energy & Utilities
    "NEE", "ENPH", "SEDG", "FSLR", "RUN", "BE", "CEG", "VST", "AEP",
    # Healthcare & Pharma
    "JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "CVS", "BMY", "AMGN",
    # Biotech & Medical Devices
    "GILD", "REGN", "VRTX", "MRNA", "ISRG", "BSX", "MDT", "SYK", "EW",
    # Consumer Staples
    "KO", "PEP", "PG", "COST", "WMT", "MCD", "MDLZ", "CL", "GIS",
    # Consumer Discretionary & Retail
    "NKE", "SBUX", "TGT", "HD", "DIS", "RIVN", "GM", "F", "LOW",
    # Industrials & Aerospace
    "BA", "CAT", "GE", "RTX", "LMT", "HON", "UPS", "FDX", "DE",
    # Materials & Mining
    "NEM", "FCX", "BHP", "RIO", "AA", "NUE", "X", "LIN", "APD",
    # Real Estate REITs
    "PLD", "AMT", "EQIX", "CCI", "SPG", "WELL", "AVB", "EQR", "DLR",
    # Telecommunications
    "T", "VZ", "TMUS", "LUMN", "DISH", "CHTR", "CMCSA", "VOD", "SATS",
]

assert len(TARGET_TICKERS) == 143, f"Expected 143 tickers, got {len(TARGET_TICKERS)}"
