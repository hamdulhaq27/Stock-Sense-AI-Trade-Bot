"""
StockSense AI — Stock Price Data Collector
CS4063 NLP Project | Mohammad Haider 23i-2558
Fetches OHLCV + derived technical features via yfinance with maximum columns.
"""

import sqlite3
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta, timezone
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH      = "stocksense.db"
TARGET_TICKS = [
    "AAPL", "TSLA", "AMZN", "MSFT", "NVDA", "GOOGL", "META",
    "JPM", "GS", "BAC",
    "NFLX", "DIS", "UBER", "SPOT",
    "AMD", "INTC", "QCOM",
    "PYPL", "SQ", "SHOP",
    "JNJ", "PFE",
    "XOM", "CVX",
    "RIVN", "PLTR", "WMT"
]

# ── Database setup ──────────────────────────────────────────────────────────────
def init_stock_table(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            -- Identity
            id              TEXT PRIMARY KEY,   -- ticker_YYYY-MM-DD
            ticker          TEXT NOT NULL,
            date            TEXT NOT NULL,      -- YYYY-MM-DD
            collected_at    TEXT,

            -- OHLCV (raw from yfinance)
            open            REAL,
            high            REAL,
            low             REAL,
            close           REAL,
            adj_close       REAL,
            volume          INTEGER,

            -- Returns & changes
            daily_return_pct    REAL,   -- (close - prev_close) / prev_close * 100
            log_return          REAL,   -- log(close / prev_close)
            price_change        REAL,   -- close - prev_close
            intraday_range      REAL,   -- high - low
            intraday_range_pct  REAL,   -- (high - low) / open * 100

            -- Moving averages
            sma_5           REAL,
            sma_10          REAL,
            sma_20          REAL,
            sma_50          REAL,
            ema_12          REAL,
            ema_26          REAL,

            -- Volatility
            volatility_5d   REAL,   -- rolling 5-day std of daily returns
            volatility_20d  REAL,   -- rolling 20-day std
            atr_14          REAL,   -- average true range (14 days)

            -- Momentum indicators
            rsi_14          REAL,   -- Relative Strength Index
            macd            REAL,   -- EMA12 - EMA26
            macd_signal     REAL,   -- 9-day EMA of MACD
            macd_histogram  REAL,

            -- Volume indicators
            volume_sma_10       INTEGER,
            volume_ratio        REAL,   -- volume / volume_sma_10
            on_balance_volume   REAL,   -- OBV

            -- Bollinger Bands (20-day, 2 std)
            bb_upper        REAL,
            bb_middle       REAL,
            bb_lower        REAL,
            bb_width        REAL,   -- (upper - lower) / middle
            bb_pct          REAL,   -- (close - lower) / (upper - lower)

            -- Price vs MA signals
            above_sma_20        INTEGER,    -- 1 / 0
            above_sma_50        INTEGER,
            golden_cross        INTEGER,    -- sma_5 > sma_20 => 1

            -- Company-level static info (fetched once)
            company_name        TEXT,
            sector              TEXT,
            industry            TEXT,
            market_cap          REAL,
            pe_ratio            REAL,
            forward_pe          REAL,
            price_to_book       REAL,
            dividend_yield      REAL,
            beta                REAL,
            shares_outstanding  REAL,
            float_shares        REAL,
            avg_volume_10d      INTEGER,
            week_high_52        REAL,
            week_low_52         REAL,
            distance_from_52h   REAL,

            -- Market context
            is_market_day       INTEGER DEFAULT 1,
            day_of_week         INTEGER,    -- 0=Mon, 4=Fri
            week_of_year        INTEGER,
            month               INTEGER,
            quarter             INTEGER,
            is_earnings_week    INTEGER DEFAULT 0  -- set externally by pipeline
        )
    """)
    conn.commit()
    conn.close()
    logger.info("stock_prices table ready in %s", db_path)


# ── Technical indicator helpers ──────────────────────────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def build_feature_df(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """Download OHLCV and compute all derived columns for a ticker."""
    logger.info("Fetching %s ...", ticker)
    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period=period, auto_adjust=False)
        if hist.empty:
            logger.warning("No data returned for %s", ticker)
            return None
    except Exception as e:
        logger.error("yfinance error for %s: %s", ticker, e)
        return None

    df = hist[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "adj_close", "volume"]
    df.index   = pd.to_datetime(df.index).tz_localize(None)   # strip tz for SQLite

    # ── Returns ──────────────────────────────────────────────────────────────
    df["daily_return_pct"]   = df["close"].pct_change() * 100
    df["log_return"]         = np.log(df["close"] / df["close"].shift(1))
    df["price_change"]       = df["close"].diff()
    df["intraday_range"]     = df["high"] - df["low"]
    df["intraday_range_pct"] = (df["high"] - df["low"]) / df["open"] * 100

    # ── Moving averages ───────────────────────────────────────────────────────
    for w in [5, 10, 20, 50]:
        df[f"sma_{w}"] = df["close"].rolling(w).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

    # ── Volatility ────────────────────────────────────────────────────────────
    df["volatility_5d"]  = df["daily_return_pct"].rolling(5).std()
    df["volatility_20d"] = df["daily_return_pct"].rolling(20).std()
    df["atr_14"]         = compute_atr(df["high"], df["low"], df["close"])

    # ── RSI & MACD ────────────────────────────────────────────────────────────
    df["rsi_14"]        = compute_rsi(df["close"])
    df["macd"]          = df["ema_12"] - df["ema_26"]
    df["macd_signal"]   = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"]= df["macd"] - df["macd_signal"]

    # ── Volume ────────────────────────────────────────────────────────────────
    df["volume_sma_10"]     = df["volume"].rolling(10).mean().astype("Int64")
    df["volume_ratio"]      = df["volume"] / df["volume_sma_10"].replace(0, np.nan)
    df["on_balance_volume"] = compute_obv(df["close"], df["volume"])

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    df["bb_middle"] = df["close"].rolling(20).mean()
    bb_std          = df["close"].rolling(20).std()
    df["bb_upper"]  = df["bb_middle"] + 2 * bb_std
    df["bb_lower"]  = df["bb_middle"] - 2 * bb_std
    df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["bb_pct"]    = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # ── Signal flags ──────────────────────────────────────────────────────────
    df["above_sma_20"]  = (df["close"] > df["sma_20"]).astype(int)
    df["above_sma_50"]  = (df["close"] > df["sma_50"]).astype(int)
    df["golden_cross"]  = (df["sma_5"]  > df["sma_20"]).astype(int)

    # ── Calendar features ─────────────────────────────────────────────────────
    df["day_of_week"]   = df.index.dayofweek
    df["week_of_year"]  = df.index.isocalendar().week.astype(int)
    df["month"]         = df.index.month
    df["quarter"]       = df.index.quarter

    # ── Static company info ───────────────────────────────────────────────────
    try:
        info = tk.info
    except Exception:
        info = {}

    week52_high = info.get("fiftyTwoWeekHigh", np.nan)
    df["company_name"]       = info.get("longName", ticker)
    df["sector"]             = info.get("sector", None)
    df["industry"]           = info.get("industry", None)
    df["market_cap"]         = info.get("marketCap", np.nan)
    df["pe_ratio"]           = info.get("trailingPE", np.nan)
    df["forward_pe"]         = info.get("forwardPE", np.nan)
    df["price_to_book"]      = info.get("priceToBook", np.nan)
    df["dividend_yield"]     = info.get("dividendYield", np.nan)
    df["beta"]               = info.get("beta", np.nan)
    df["shares_outstanding"] = info.get("sharesOutstanding", np.nan)
    df["float_shares"]       = info.get("floatShares", np.nan)
    df["avg_volume_10d"]     = info.get("averageVolume10days", np.nan)
   
    df["week_high_52"]       = week52_high
    df["week_low_52"]        = info.get("fiftyTwoWeekLow", np.nan)
    df["distance_from_52h"]  = (df["close"] - week52_high) / (week52_high or np.nan) * 100
        

    # ── Identifiers ───────────────────────────────────────────────────────────
    df["ticker"]         = ticker
    df["date"]           = df.index.strftime("%Y-%m-%d")
    df["id"]             = ticker + "_" + df["date"]
    df["collected_at"]   = datetime.utcnow().isoformat()
    df["is_market_day"]  = 1
    df["is_earnings_week"] = 0   # updated externally

    df = df.reset_index(drop=True)
    df = df.round(4)
    return df


# ── DB writer ───────────────────────────────────────────────────────────────────
def save_stock_data(df: pd.DataFrame, db_path: str = DB_PATH) -> int:
    if df is None or df.empty:
        return 0
    conn     = sqlite3.connect(db_path)
    existing = pd.read_sql(
        f"SELECT id FROM stock_prices WHERE ticker = '{df['ticker'].iloc[0]}'", conn
    )["id"].tolist()
    new_rows = df[~df["id"].isin(existing)]
    if not new_rows.empty:
        new_rows.to_sql("stock_prices", conn, if_exists="append", index=False)
    conn.close()
    logger.info("  → %d new rows saved", len(new_rows))
    return len(new_rows)


# ── Export ───────────────────────────────────────────────────────────────────────
def export_stock_csv(db_path: str = DB_PATH, output: str = "stock_data.csv"):
    conn = sqlite3.connect(db_path)
    df   = pd.read_sql("SELECT * FROM stock_prices ORDER BY ticker, date DESC", conn)
    conn.close()
    df.to_csv(output, index=False)
    logger.info("Exported %d rows → %s", len(df), output)
    return df


# ── Main runner ─────────────────────────────────────────────────────────────────
def collect_all_stocks(period: str = "6mo"):
    init_stock_table()
    total = 0
    for ticker in TARGET_TICKS:
        df = build_feature_df(ticker, period=period)
        total += save_stock_data(df)
    logger.info("Stock collection done. Total new rows: %d", total)
    return export_stock_csv()


if __name__ == "__main__":
    df = collect_all_stocks(period="1y")
    preview_cols = [
        "ticker", "date", "close", "daily_return_pct", "rsi_14",
        "macd", "volatility_5d", "above_sma_20", "bb_pct", "volume_ratio"
    ]
    print(df[preview_cols].head(20).to_string(index=False))
