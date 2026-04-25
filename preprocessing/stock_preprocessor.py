"""
StockSense AI — Stock Data Preprocessing
CS4063 NLP Project | Mohammad Haider 23i-2558
Cleans, validates, and preprocesses stock_data.csv for NLP + ML pipeline.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE  = "stock_data.csv"
OUTPUT_FILE = "stock_data_clean.csv"

# ── Step 1: Load Data ───────────────────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    logger.info("Loaded %d rows, %d columns from %s", len(df), len(df.columns), path)
    return df


# ── Step 2: Basic Info & Audit ──────────────────────────────────────────────────
def audit_data(df: pd.DataFrame):
    print("\n" + "="*60)
    print("STEP 2 — DATA AUDIT")
    print("="*60)

    print(f"\nShape          : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"Tickers        : {sorted(df['ticker'].unique().tolist())}")
    print(f"Tickers count  : {df['ticker'].nunique()}")
    print(f"Date range     : {df['date'].min()} → {df['date'].max()}")

    print("\n── Missing Values ──")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("  No missing values found ✓")
    else:
        print(missing.to_string())

    print("\n── Duplicate Rows ──")
    dups = df.duplicated().sum()
    print(f"  {dups} duplicate rows found")

    print("\n── Duplicate IDs ──")
    dup_ids = df.duplicated(subset=["id"]).sum()
    print(f"  {dup_ids} duplicate IDs found")

    print("\n── Data Types ──")
    print(df.dtypes.to_string())

    print("\n── Numeric Summary ──")
    print(df[["open","high","low","close","volume","daily_return_pct",
              "rsi_14","macd","volatility_5d"]].describe().round(4).to_string())


# ── Step 3: Fix Date Column ─────────────────────────────────────────────────────
def fix_dates(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 3 — FIX DATES")
    print("="*60)

    # date column has mixed formats: DD/MM/YYYY and YYYY-MM-DD
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    failed = df["date"].isnull().sum()
    print(f"  Date parse failures : {failed}")

    # Drop rows where date couldn't be parsed
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Also parse collected_at
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")

    print(f"  Date range after fix: {df['date'].min()} → {df['date'].max()}")
    print(f"  Rows after date fix : {len(df)}")
    return df


# ── Step 4: Remove Duplicates ───────────────────────────────────────────────────
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 4 — REMOVE DUPLICATES")
    print("="*60)

    before = len(df)
    df = df.drop_duplicates(subset=["id"])
    df = df.drop_duplicates(subset=["ticker", "date"])
    after = len(df)
    print(f"  Removed {before - after} duplicate rows")
    print(f"  Rows remaining: {after}")
    return df


# ── Step 5: Fix Data Types ──────────────────────────────────────────────────────
def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 5 — FIX DATA TYPES")
    print("="*60)

    # Float columns
    float_cols = [
        "open", "high", "low", "close", "adj_close",
        "daily_return_pct", "log_return", "price_change",
        "intraday_range", "intraday_range_pct",
        "sma_5", "sma_10", "sma_20", "sma_50", "ema_12", "ema_26",
        "volatility_5d", "volatility_20d", "atr_14",
        "rsi_14", "macd", "macd_signal", "macd_histogram",
        "volume_ratio", "on_balance_volume",
        "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_pct",
        "market_cap", "pe_ratio", "forward_pe", "price_to_book",
        "dividend_yield", "beta", "shares_outstanding", "float_shares",
        "week_high_52", "week_low_52", "distance_from_52h",
    ]

    # Integer columns
    int_cols = [
        "volume", "volume_sma_10", "avg_volume_10d",
        "above_sma_20", "above_sma_50", "golden_cross",
        "is_market_day", "day_of_week", "week_of_year",
        "month", "quarter", "is_earnings_week",
    ]

    # String columns
    str_cols = ["id", "ticker", "date", "company_name", "sector", "industry"]

    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    print("  Data types fixed ✓")
    return df


# ── Step 6: Validate OHLCV Logic ────────────────────────────────────────────────
def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 6 — VALIDATE OHLCV LOGIC")
    print("="*60)

    before = len(df)

    # High must be >= Low
    invalid_hl = df["high"] < df["low"]
    print(f"  Rows where high < low      : {invalid_hl.sum()}")
    df = df[~invalid_hl]

    # Close must be between Low and High
    invalid_close = (df["close"] < df["low"]) | (df["close"] > df["high"])
    print(f"  Rows where close out of range: {invalid_close.sum()}")
    df = df[~invalid_close]

    # Volume must be positive
    invalid_vol = df["volume"] <= 0
    print(f"  Rows where volume <= 0     : {invalid_vol.sum()}")
    df = df[~invalid_vol]

    # Prices must be positive
    invalid_price = (df["close"] <= 0) | (df["open"] <= 0)
    print(f"  Rows where price <= 0      : {invalid_price.sum()}")
    df = df[~invalid_price]

    after = len(df)
    print(f"  Rows removed: {before - after}")
    print(f"  Rows remaining: {after}")
    return df


# ── Step 7: Handle Missing Values ───────────────────────────────────────────────
def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 7 — HANDLE MISSING VALUES")
    print("="*60)

    # Sort for proper forward fill
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Columns that can be forward-filled within each ticker group
    # (technical indicators from rolling windows will be NaN for early rows)
    ffill_cols = [
        "sma_5", "sma_10", "sma_20", "sma_50",
        "ema_12", "ema_26",
        "volatility_5d", "volatility_20d", "atr_14",
        "rsi_14", "macd", "macd_signal", "macd_histogram",
        "volume_sma_10", "volume_ratio", "on_balance_volume",
        "bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_pct",
    ]

    for col in ffill_cols:
     if col in df.columns:
        df[col] = df.groupby("ticker")[col].transform(
            lambda x: x.ffill().bfill()
        )

    # Fundamental columns — fill with ticker-level median
    fundamental_cols = [
        "pe_ratio", "forward_pe", "price_to_book",
        "dividend_yield", "beta", "market_cap",
        "shares_outstanding", "float_shares", "avg_volume_10d",
        "week_high_52", "week_low_52",
    ]

    for col in fundamental_cols:
     if col in df.columns:
        df[col] = df.groupby("ticker")[col].transform(
            lambda x: x.fillna(x.median())
        )
    # Fill remaining binary flags with 0
    flag_cols = [
        "above_sma_20", "above_sma_50", "golden_cross",
        "is_earnings_week", "is_market_day",
    ]
    for col in flag_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # Fill distance_from_52h
    if "distance_from_52h" in df.columns:
        df["distance_from_52h"] = df.groupby("ticker")["distance_from_52h"].transform(
            lambda x: x.fillna(x.median())
        )

    # Report remaining missing
    remaining = df.isnull().sum()
    remaining = remaining[remaining > 0]
    if remaining.empty:
        print("  All missing values handled ✓")
    else:
        print("  Remaining missing values:")
        print(remaining.to_string())

    return df


# ── Step 8: Handle Outliers ─────────────────────────────────────────────────────
def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 8 — HANDLE OUTLIERS")
    print("="*60)

    # For daily_return_pct — clip extreme values (beyond ±50% in a day is likely bad data)
    if "daily_return_pct" in df.columns:
        before = (df["daily_return_pct"].abs() > 50).sum()
        df["daily_return_pct"] = df["daily_return_pct"].clip(-50, 50)
        print(f"  Clipped {before} extreme daily_return_pct values (>±50%)")

    # For RSI — must be 0-100
    if "rsi_14" in df.columns:
        invalid_rsi = ((df["rsi_14"] < 0) | (df["rsi_14"] > 100)).sum()
        df["rsi_14"] = df["rsi_14"].clip(0, 100)
        print(f"  Clipped {invalid_rsi} invalid RSI values (outside 0-100)")

    # For volume_ratio — clip extreme spikes (>20x average is likely bad data)
    if "volume_ratio" in df.columns:
        before = (df["volume_ratio"] > 20).sum()
        df["volume_ratio"] = df["volume_ratio"].clip(0, 20)
        print(f"  Clipped {before} extreme volume_ratio values (>20x)")

    print("  Outlier handling complete ✓")
    return df


# ── Step 9: Add Label Column (Target Variable) ──────────────────────────────────
def add_target_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add the target variable for ML prediction:
    - next_day_return: what the stock did the NEXT trading day
    - price_direction: 1 = went up, 0 = went down or flat (for classification)
    This is what your LSTM will try to predict.
    """
    print("\n" + "="*60)
    print("STEP 9 — ADD TARGET LABELS")
    print("="*60)

    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Next day's closing return (what we want to predict)
    df["next_day_return"] = df.groupby("ticker")["daily_return_pct"].shift(-1)

    # Binary classification label: 1 = price went up next day, 0 = went down
    df["price_direction"] = (df["next_day_return"] > 0).astype(int)

    # 3-class label: 2=bullish(>1%), 1=neutral(-1% to 1%), 0=bearish(<-1%)
    df["price_direction_3class"] = pd.cut(
        df["next_day_return"],
        bins=[-np.inf, -1.0, 1.0, np.inf],
        labels=[0, 1, 2]   # 0=bearish, 1=neutral, 2=bullish
    ).astype("Int64")

    # Drop last row per ticker (no next day available)
    before = len(df)
    df = df.dropna(subset=["next_day_return"])
    after = len(df)
    print(f"  Dropped {before - after} rows (last day per ticker — no next day available)")

    print(f"\n  Label distribution (price_direction):")
    print(f"  Up   (1): {(df['price_direction'] == 1).sum()} rows ({(df['price_direction'] == 1).mean()*100:.1f}%)")
    print(f"  Down (0): {(df['price_direction'] == 0).sum()} rows ({(df['price_direction'] == 0).mean()*100:.1f}%)")

    print(f"\n  Label distribution (price_direction_3class):")
    print(f"  Bullish (2): {(df['price_direction_3class'] == 2).sum()} rows")
    print(f"  Neutral (1): {(df['price_direction_3class'] == 1).sum()} rows")
    print(f"  Bearish (0): {(df['price_direction_3class'] == 0).sum()} rows")

    return df


# ── Step 10: Sort & Reset Index ─────────────────────────────────────────────────
def sort_and_reset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return df


# ── Step 11: Final Report ───────────────────────────────────────────────────────
def final_report(df: pd.DataFrame):
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(f"  Final shape    : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Tickers        : {df['ticker'].nunique()}")
    print(f"  Date range     : {df['date'].min()} → {df['date'].max()}")
    print(f"  Missing values : {df.isnull().sum().sum()}")
    print(f"  Columns        : {list(df.columns)}")
    print(f"\n  Rows per ticker:")
    print(df["ticker"].value_counts().to_string())


# ── Main Pipeline ────────────────────────────────────────────────────────────────
def preprocess_stock_data():
    print("\n" + "="*60)
    print("StockSense AI — Stock Data Preprocessing Pipeline")
    print("="*60)

    # Load
    df = load_data(INPUT_FILE)

    # Audit original data
    audit_data(df)

    # Clean pipeline
    df = fix_dates(df)
    df = remove_duplicates(df)
    df = fix_dtypes(df)
    df = validate_ohlcv(df)
    df = handle_missing(df)
    df = handle_outliers(df)
    df = add_target_label(df)
    df = sort_and_reset(df)

    # Final report
    final_report(df)

    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info("\nSaved clean data → %s", OUTPUT_FILE)

    return df


if __name__ == "__main__":
    df = preprocess_stock_data()

    print("\n── Sample clean output ──")
    print(df[[
        "ticker", "date", "close", "daily_return_pct",
        "rsi_14", "macd", "above_sma_20",
        "next_day_return", "price_direction"
    ]].head(20).to_string(index=False))
