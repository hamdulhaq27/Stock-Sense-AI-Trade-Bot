"""
StockSense AI — Stock Data Preprocessing v2
CS4063 NLP Project | Mohammad Haider 23i-2558
Handles 176,170 rows × 141 tickers × 5 years
Fixes: fillna method, volume_sma_10 cast, unreliable columns
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE  = "stock_data.csv"
OUTPUT_FILE = "stock_data_clean.csv"


# ── Step 1: Load ────────────────────────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    logger.info("Loaded %d rows, %d columns from %s", len(df), len(df.columns), path)
    return df


# ── Step 2: Audit ───────────────────────────────────────────────────────────────
def audit_data(df: pd.DataFrame):
    print("\n" + "="*60)
    print("STEP 2 — DATA AUDIT")
    print("="*60)
    print(f"\n  Shape         : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Tickers       : {df['ticker'].nunique()} unique")
    print(f"  Date range    : {df['date'].min()} → {df['date'].max()}")

    print("\n── Missing Values (columns with nulls) ──")
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("  None ✓")
    else:
        for col, cnt in missing.items():
            print(f"  {col:<30} {cnt:>8,} ({cnt/len(df)*100:.1f}%)")

    print(f"\n── Duplicates ──")
    print(f"  Duplicate rows      : {df.duplicated().sum():,}")
    print(f"  Duplicate IDs       : {df.duplicated(subset=['id']).sum():,}")
    print(f"  Duplicate tick+date : {df.duplicated(subset=['ticker','date']).sum():,}")

    print("\n── Numeric Summary (key columns) ──")
    cols = ["open","high","low","close","volume","daily_return_pct","rsi_14","volatility_5d"]
    print(df[cols].describe().round(3).to_string())


# ── Step 3: Fix Dates ───────────────────────────────────────────────────────────
def fix_dates(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 3 — FIX DATES")
    print("="*60)

    # Handle mixed formats: DD/MM/YYYY and YYYY-MM-DD
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    failed = df["date"].isnull().sum()
    print(f"  Parse failures : {failed}")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Fix collected_at — drop timezone suffix safely
    df["collected_at"] = df["collected_at"].astype(str).str[:19]
    df["collected_at"] = pd.to_datetime(df["collected_at"], errors="coerce")

    print(f"  Date range     : {df['date'].min()} → {df['date'].max()}")
    print(f"  Rows remaining : {len(df):,}")
    return df


# ── Step 4: Remove Duplicates ───────────────────────────────────────────────────
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 4 — REMOVE DUPLICATES")
    print("="*60)
    before = len(df)
    df = df.drop_duplicates(subset=["id"])
    df = df.drop_duplicates(subset=["ticker", "date"])
    print(f"  Removed {before - len(df):,} duplicates")
    print(f"  Rows remaining : {len(df):,}")
    return df


# ── Step 5: Fix Data Types ──────────────────────────────────────────────────────
def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 5 — FIX DATA TYPES")
    print("="*60)

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
        "volume_sma_10",   # keep as float to avoid NaN cast issues
    ]

    int_cols = [
        "volume", "avg_volume_10d",
        "above_sma_20", "above_sma_50", "golden_cross",
        "is_market_day", "day_of_week", "week_of_year",
        "month", "quarter", "is_earnings_week",
    ]

    str_cols = ["id", "ticker", "date", "company_name", "sector", "industry"]

    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    print("  Data types fixed ✓")
    return df


# ── Step 6: Validate OHLCV ──────────────────────────────────────────────────────
def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 6 — VALIDATE OHLCV")
    print("="*60)
    before = len(df)

    bad_hl    = df["high"] < df["low"]
    bad_close = (df["close"] < df["low"]) | (df["close"] > df["high"])
    bad_vol   = df["volume"] <= 0
    bad_price = (df["close"] <= 0) | (df["open"] <= 0)

    print(f"  high < low          : {bad_hl.sum():,}")
    print(f"  close out of range  : {bad_close.sum():,}")
    print(f"  volume <= 0         : {bad_vol.sum():,}")
    print(f"  price <= 0          : {bad_price.sum():,}")

    df = df[~(bad_hl | bad_close | bad_vol | bad_price)]
    print(f"  Removed {before - len(df):,} invalid rows")
    print(f"  Rows remaining : {len(df):,}")
    return df


# ── Step 7: Handle Missing Values ───────────────────────────────────────────────
def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 7 — HANDLE MISSING VALUES")
    print("="*60)

    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Forward fill technical indicators within each ticker
    ffill_cols = [
        "sma_5", "sma_10", "sma_20", "sma_50", "ema_12", "ema_26",
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

    # Fill fundamentals with ticker-level median
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

    # Binary flags → fill with 0
    for col in ["above_sma_20", "above_sma_50", "golden_cross",
                "is_earnings_week", "is_market_day"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # distance_from_52h
    if "distance_from_52h" in df.columns:
        df["distance_from_52h"] = df.groupby("ticker")["distance_from_52h"].transform(
            lambda x: x.fillna(x.median())
        )

    # daily_return_pct / log_return / price_change — fill first row per ticker with 0
    for col in ["daily_return_pct", "log_return", "price_change"]:
        if col in df.columns:
            df[col] = df.groupby("ticker")[col].transform(lambda x: x.fillna(0))

    remaining = df.isnull().sum()
    remaining = remaining[remaining > 0]
    if remaining.empty:
        print("  All missing values handled ✓")
    else:
        print("  Remaining nulls:")
        for col, cnt in remaining.items():
            print(f"    {col:<30} {cnt:>8,}")
    return df


# ── Step 8: Handle Outliers ─────────────────────────────────────────────────────
def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 8 — HANDLE OUTLIERS")
    print("="*60)

    if "daily_return_pct" in df.columns:
        n = (df["daily_return_pct"].abs() > 50).sum()
        df["daily_return_pct"] = df["daily_return_pct"].clip(-50, 50)
        print(f"  Clipped {n:,} daily_return_pct values (>±50%)")

    if "rsi_14" in df.columns:
        n = ((df["rsi_14"] < 0) | (df["rsi_14"] > 100)).sum()
        df["rsi_14"] = df["rsi_14"].clip(0, 100)
        print(f"  Clipped {n:,} RSI values (outside 0-100)")

    if "volume_ratio" in df.columns:
        n = (df["volume_ratio"] > 20).sum()
        df["volume_ratio"] = df["volume_ratio"].clip(0, 20)
        print(f"  Clipped {n:,} volume_ratio values (>20x)")

    if "bb_pct" in df.columns:
        n = ((df["bb_pct"] < -1) | (df["bb_pct"] > 2)).sum()
        df["bb_pct"] = df["bb_pct"].clip(-1, 2)
        print(f"  Clipped {n:,} bb_pct extreme values")

    print("  Outlier handling complete ✓")
    return df


# ── Step 9: Add Target Labels ───────────────────────────────────────────────────
def add_target_label(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 9 — ADD TARGET LABELS")
    print("="*60)

    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    # Next day's return — what the model predicts
    df["next_day_return"] = df.groupby("ticker")["daily_return_pct"].shift(-1)

    # Binary: 1 = went up, 0 = went down or flat
    df["price_direction"] = (df["next_day_return"] > 0).astype(int)

    # 3-class: 0=bearish(<-1%), 1=neutral(-1% to 1%), 2=bullish(>1%)
    df["price_direction_3class"] = pd.cut(
        df["next_day_return"],
        bins=[-np.inf, -1.0, 1.0, np.inf],
        labels=[0, 1, 2]
    ).astype("Int64")

    before = len(df)
    df = df.dropna(subset=["next_day_return"])
    print(f"  Dropped {before - len(df):,} rows (last day per ticker)")

    up   = (df["price_direction"] == 1).sum()
    down = (df["price_direction"] == 0).sum()
    total = len(df)
    print(f"\n  price_direction:")
    print(f"    Up   (1) : {up:>8,}  ({up/total*100:.1f}%)")
    print(f"    Down (0) : {down:>8,}  ({down/total*100:.1f}%)")

    bull = (df["price_direction_3class"] == 2).sum()
    neut = (df["price_direction_3class"] == 1).sum()
    bear = (df["price_direction_3class"] == 0).sum()
    print(f"\n  price_direction_3class:")
    print(f"    Bullish (2) : {bull:>8,}  ({bull/total*100:.1f}%)")
    print(f"    Neutral (1) : {neut:>8,}  ({neut/total*100:.1f}%)")
    print(f"    Bearish (0) : {bear:>8,}  ({bear/total*100:.1f}%)")

    return df


# ── Step 10: Drop Unreliable Columns ────────────────────────────────────────────
def drop_unreliable_cols(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "="*60)
    print("STEP 10 — DROP UNRELIABLE COLUMNS")
    print("="*60)

    to_drop = [
        "collected_at",      # broken / not useful for ML
        "distance_from_52h", # uses today's 52wk high — wrong for historical rows
        "week_high_52",      # static snapshot — not historical
        "week_low_52",       # static snapshot — not historical
        "id",                # not a feature
    ]

    dropped = [c for c in to_drop if c in df.columns]
    df = df.drop(columns=dropped)
    print(f"  Dropped: {dropped}")
    print(f"  Remaining columns: {df.shape[1]}")
    return df


# ── Step 11: Sort & Reset ───────────────────────────────────────────────────────
def sort_and_reset(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


# ── Final Report ────────────────────────────────────────────────────────────────
def final_report(df: pd.DataFrame):
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(f"  Final shape    : {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Tickers        : {df['ticker'].nunique()}")
    print(f"  Date range     : {df['date'].min()} → {df['date'].max()}")
    print(f"  Missing values : {df.isnull().sum().sum():,}")
    print(f"\n  Columns ({df.shape[1]}):")
    for i, col in enumerate(df.columns, 1):
        print(f"    {i:>3}. {col}")
    print(f"\n  Rows per ticker (sample):")
    print(df["ticker"].value_counts().head(10).to_string())


# ── Main Pipeline ────────────────────────────────────────────────────────────────
def preprocess_stock_data():
    print("\n" + "="*60)
    print("StockSense AI — Stock Preprocessing Pipeline v2")
    print("="*60)

    df = load_data(INPUT_FILE)
    audit_data(df)
    df = fix_dates(df)
    df = remove_duplicates(df)
    df = fix_dtypes(df)
    df = validate_ohlcv(df)
    df = handle_missing(df)
    df = handle_outliers(df)
    df = add_target_label(df)
    df = drop_unreliable_cols(df)
    df = sort_and_reset(df)
    final_report(df)

    df.to_csv(OUTPUT_FILE, index=False)
    logger.info("Saved → %s  (%d rows)", OUTPUT_FILE, len(df))
    return df


if __name__ == "__main__":
    df = preprocess_stock_data()
    print("\n── Sample output ──")
    print(df[[
        "ticker", "date", "close", "daily_return_pct",
        "rsi_14", "above_sma_20", "next_day_return", "price_direction"
    ]].head(20).to_string(index=False))