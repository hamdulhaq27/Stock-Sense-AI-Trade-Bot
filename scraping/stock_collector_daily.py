"""
Incremental Stock Data Scraper v2
==================================
Fetches ONLY TODAY'S stock data from yfinance and appends to existing CSV.
This is the daily version of stock_collector.py - only collects new data.
"""

import sqlite3
import logging
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TARGET_TICKERS, DATA_DIR
from logging_config import get_logger

logger = get_logger("scraper")

DB_PATH = DATA_DIR / "stocksense.db"
CSV_PATH = DATA_DIR / "stock_data_clean.csv"


# ── Technical indicator helpers (from original) ──────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_atr(high, low, close, period=14):
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_obv(close, volume):
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


# ── Feature builder ────────────────────────────────────────────────────────
def build_feature_df(ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """Build feature dataframe for a specific date range."""
    logger.debug("Fetching %s from %s to %s", ticker, start_date, end_date)
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(start=start_date, end=end_date, auto_adjust=False)

        if hist.empty:
            logger.warning("No data for %s in range %s to %s", ticker, start_date, end_date)
            return None
    except Exception as e:
        logger.error("yfinance error for %s: %s", ticker, e)
        return None

    df = hist[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "adj_close", "volume"]
    df.index = pd.to_datetime(df.index).tz_localize(None)

    # Returns
    df["daily_return_pct"] = df["close"].pct_change() * 100
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))
    df["price_change"] = df["close"].diff()
    df["intraday_range"] = df["high"] - df["low"]
    df["intraday_range_pct"] = (df["high"] - df["low"]) / df["open"] * 100

    # Moving averages
    for w in [5, 10, 20, 50]:
        df[f"sma_{w}"] = df["close"].rolling(w).mean()
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

    # Volatility
    df["volatility_5d"] = df["daily_return_pct"].rolling(5).std()
    df["volatility_20d"] = df["daily_return_pct"].rolling(20).std()
    df["atr_14"] = compute_atr(df["high"], df["low"], df["close"])

    # RSI & MACD
    df["rsi_14"] = compute_rsi(df["close"])
    df["macd"] = df["ema_12"] - df["ema_26"]
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]

    # Volume
    df["volume_sma_10"] = df["volume"].rolling(10).mean().round(0).astype("float64")
    df["volume_ratio"] = df["volume"] / df["volume_sma_10"].replace(0, np.nan)
    df["on_balance_volume"] = compute_obv(df["close"], df["volume"])

    # Bollinger Bands
    df["bb_middle"] = df["close"].rolling(20).mean()
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_middle"] + 2 * bb_std
    df["bb_lower"] = df["bb_middle"] - 2 * bb_std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
    df["bb_pct"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    # Signal flags
    df["above_sma_20"] = (df["close"] > df["sma_20"]).astype(int)
    df["above_sma_50"] = (df["close"] > df["sma_50"]).astype(int)
    df["golden_cross"] = (df["sma_5"] > df["sma_20"]).astype(int)

    # Calendar
    df["day_of_week"] = df.index.dayofweek
    df["week_of_year"] = df.index.isocalendar().week.astype(int)
    df["month"] = df.index.month
    df["quarter"] = df.index.quarter

    # Company info (static per ticker)
    try:
        info = tk.info
    except Exception:
        info = {}

    week52_high = info.get("fiftyTwoWeekHigh", np.nan)
    df["company_name"] = info.get("longName", ticker)
    df["sector"] = info.get("sector", None)
    df["industry"] = info.get("industry", None)
    df["market_cap"] = info.get("marketCap", np.nan)
    df["pe_ratio"] = info.get("trailingPE", np.nan)
    df["forward_pe"] = info.get("forwardPE", np.nan)
    df["price_to_book"] = info.get("priceToBook", np.nan)
    df["dividend_yield"] = info.get("dividendYield", np.nan)
    df["beta"] = info.get("beta", np.nan)
    df["shares_outstanding"] = info.get("sharesOutstanding", np.nan)
    df["float_shares"] = info.get("floatShares", np.nan)
    df["avg_volume_10d"] = info.get("averageVolume10days", np.nan)
    df["week_high_52"] = week52_high
    df["week_low_52"] = info.get("fiftyTwoWeekLow", np.nan)
    df["distance_from_52h"] = (df["close"] - week52_high) / (week52_high or np.nan) * 100

    # Identifiers
    df["ticker"] = ticker
    df["date"] = df.index.strftime("%Y-%m-%d")
    df["id"] = ticker + "_" + df["date"]
    df["collected_at"] = datetime.now(timezone.utc).isoformat()
    df["is_market_day"] = 1
    df["is_earnings_week"] = 0

    return df.reset_index(drop=True).round(4)


# ── Get latest date in CSV ─────────────────────────────────────────────────
def get_latest_csv_date(csv_path: Path = CSV_PATH) -> Optional[str]:
    """Get the latest date from the existing CSV."""
    if not csv_path.exists():
        return None
    try:
        df = pd.read_csv(csv_path, usecols=["date"], nrows=1)
        if not df.empty:
            return str(df["date"].iloc[0])
    except Exception as e:
        logger.warning("Failed to read latest date from CSV: %s", e)
    return None


# ── DB writer ──────────────────────────────────────────────────────────────
def save_stock_data(df: pd.DataFrame, csv_path: Path = CSV_PATH) -> int:
    """Append new stock data to CSV (no duplicates)."""
    if df is None or df.empty:
        return 0

    try:
        if csv_path.exists():
            existing = pd.read_csv(csv_path, usecols=["id"])
            existing_ids = set(existing["id"].tolist())
            new_rows = df[~df["id"].isin(existing_ids)]
        else:
            new_rows = df

        if not new_rows.empty:
            # Append to CSV
            if csv_path.exists():
                new_rows.to_csv(csv_path, mode="a", header=False, index=False)
            else:
                new_rows.to_csv(csv_path, index=False)
            logger.info("Saved %d new rows to %s", len(new_rows), csv_path.name)
            return len(new_rows)
    except Exception as e:
        logger.error("Error saving stock data: %s", e)
    return 0


# ── Main incremental collector ─────────────────────────────────────────────
def collect_stocks_incremental(target_date: Optional[str] = None) -> Tuple[int, list]:
    """
    Collect stock data for a specific date (default: yesterday, since market closes 4 PM).

    Returns:
        Tuple of (total_new_rows, error_tickers)
    """
    if target_date is None:
        # Fetch yesterday's data (since market closes 4 PM)
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info("=" * 70)
    logger.info("Starting incremental stock collection for %s", target_date)
    logger.info("=" * 70)

    # Ensure we fetch at least 5 days of data to compute indicators properly
    start_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

    total_new_rows = 0
    error_tickers = []

    for i, ticker in enumerate(TARGET_TICKERS, 1):
        try:
            logger.info("[%d/%d] Fetching %s ...", i, len(TARGET_TICKERS), ticker)
            df = build_feature_df(ticker, start_date, end_date)

            if df is None:
                logger.warning("  → No data for %s", ticker)
                continue

            # Filter to only today's data (but compute indicators on 5 days)
            today_df = df[df["date"] == target_date].copy()

            if today_df.empty:
                logger.warning("  → No data for %s on %s (market holiday?)", ticker, target_date)
                continue

            new_rows = save_stock_data(today_df)
            total_new_rows += new_rows

            if new_rows > 0:
                logger.info("  → %d new rows saved", new_rows)
            else:
                logger.debug("  → Already exists, skipped", )

        except Exception as e:
            logger.error("Error processing %s: %s", ticker, e)
            error_tickers.append(ticker)

    logger.info("=" * 70)
    logger.info("Stock collection complete. Total new rows: %d", total_new_rows)
    if error_tickers:
        logger.warning("Failed tickers (%d): %s", len(error_tickers), ", ".join(error_tickers))
    logger.info("=" * 70)

    return total_new_rows, error_tickers


if __name__ == "__main__":
    total, errors = collect_stocks_incremental()
    print(f"\n✅ Added {total} new stock records")
    if errors:
        print(f"⚠️  Errors for: {', '.join(errors)}")
