"""
StockSense AI — Stock Price Collector v2
CS4063 NLP Project | Mohammad Haider 23i-2558
153 tickers across 17 sectors — US Market Focus
"""

import sqlite3
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "stocksense.db"

# ── 153 Tickers ─────────────────────────────────────────────────────────────────
TARGET_TICKS = [
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

# ── Database setup ──────────────────────────────────────────────────────────────
def init_stock_table(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id                  TEXT PRIMARY KEY,
            ticker              TEXT NOT NULL,
            date                TEXT NOT NULL,
            collected_at        TEXT,
            open                REAL,
            high                REAL,
            low                 REAL,
            close               REAL,
            adj_close           REAL,
            volume              INTEGER,
            daily_return_pct    REAL,
            log_return          REAL,
            price_change        REAL,
            intraday_range      REAL,
            intraday_range_pct  REAL,
            sma_5               REAL,
            sma_10              REAL,
            sma_20              REAL,
            sma_50              REAL,
            ema_12              REAL,
            ema_26              REAL,
            volatility_5d       REAL,
            volatility_20d      REAL,
            atr_14              REAL,
            rsi_14              REAL,
            macd                REAL,
            macd_signal         REAL,
            macd_histogram      REAL,
            volume_sma_10       INTEGER,
            volume_ratio        REAL,
            on_balance_volume   REAL,
            bb_upper            REAL,
            bb_middle           REAL,
            bb_lower            REAL,
            bb_width            REAL,
            bb_pct              REAL,
            above_sma_20        INTEGER,
            above_sma_50        INTEGER,
            golden_cross        INTEGER,
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
            is_market_day       INTEGER DEFAULT 1,
            day_of_week         INTEGER,
            week_of_year        INTEGER,
            month               INTEGER,
            quarter             INTEGER,
            is_earnings_week    INTEGER DEFAULT 0
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

def compute_atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def compute_obv(close, volume):
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


# ── Feature builder ──────────────────────────────────────────────────────────────
def build_feature_df(ticker: str, period: str = "5y") -> Optional[pd.DataFrame]:
    logger.info("Fetching %s ...", ticker)
    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period=period, auto_adjust=False)
        if hist.empty:
            logger.warning("No data for %s", ticker)
            return None
    except Exception as e:
        logger.error("yfinance error for %s: %s", ticker, e)
        return None

    df = hist[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "adj_close", "volume"]
    df.index   = pd.to_datetime(df.index).tz_localize(None)

    # Returns
    df["daily_return_pct"]   = df["close"].pct_change() * 100
    df["log_return"]         = np.log(df["close"] / df["close"].shift(1))
    df["price_change"]       = df["close"].diff()
    df["intraday_range"]     = df["high"] - df["low"]
    df["intraday_range_pct"] = (df["high"] - df["low"]) / df["open"] * 100

    # Moving averages
    for w in [5, 10, 20, 50]:
        df[f"sma_{w}"] = df["close"].rolling(w).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

    # Volatility
    df["volatility_5d"]  = df["daily_return_pct"].rolling(5).std()
    df["volatility_20d"] = df["daily_return_pct"].rolling(20).std()
    df["atr_14"]         = compute_atr(df["high"], df["low"], df["close"])

    # RSI & MACD
    df["rsi_14"]         = compute_rsi(df["close"])
    df["macd"]           = df["ema_12"] - df["ema_26"]
    df["macd_signal"]    = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]

    # Volume
    df["volume_sma_10"]     = df["volume"].rolling(10).mean().round(0).astype("float64")
    df["volume_ratio"]      = df["volume"] / df["volume_sma_10"].replace(0, np.nan)
    df["on_balance_volume"] = compute_obv(df["close"], df["volume"])

    # Bollinger Bands
    df["bb_middle"] = df["close"].rolling(20).mean()
    bb_std          = df["close"].rolling(20).std()
    df["bb_upper"]  = df["bb_middle"] + 2 * bb_std
    df["bb_lower"]  = df["bb_middle"] - 2 * bb_std
    df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["bb_pct"]    = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # Signal flags
    df["above_sma_20"] = (df["close"] > df["sma_20"]).astype(int)
    df["above_sma_50"] = (df["close"] > df["sma_50"]).astype(int)
    df["golden_cross"] = (df["sma_5"]  > df["sma_20"]).astype(int)

    # Calendar
    df["day_of_week"]  = df.index.dayofweek
    df["week_of_year"] = df.index.isocalendar().week.astype(int)
    df["month"]        = df.index.month
    df["quarter"]      = df.index.quarter

    # Company info
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

    # Identifiers
    df["ticker"]           = ticker
    df["date"]             = df.index.strftime("%Y-%m-%d")
    df["id"]               = ticker + "_" + df["date"]
    df["collected_at"]     = datetime.now(timezone.utc).isoformat()
    df["is_market_day"]    = 1
    df["is_earnings_week"] = 0

    return df.reset_index(drop=True).round(4)


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
def collect_all_stocks(period: str = "5y"):
    init_stock_table()
    total = 0
    logger.info("Collecting stock data for %d tickers...", len(TARGET_TICKS))
    for i, ticker in enumerate(TARGET_TICKS, 1):
        logger.info("[%d/%d] Fetching %s ...", i, len(TARGET_TICKS), ticker)
        df     = build_feature_df(ticker, period=period)
        total += save_stock_data(df)
    logger.info("Stock collection done. Total new rows: %d", total)
    return export_stock_csv()


if __name__ == "__main__":
    df = collect_all_stocks(period="5y")
    print("\n── Summary ──")
    print(f"Total rows    : {len(df)}")
    print(f"Total tickers : {df['ticker'].nunique()}")
    print(f"Date range    : {df['date'].min()} → {df['date'].max()}")
    print("\n── Rows per ticker ──")
    print(df["ticker"].value_counts().to_string())