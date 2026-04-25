"""
Financial News Dataset Preprocessing Script
Input:  news.csv
Output: news_clean.csv
"""

import pandas as pd
import numpy as np
import re
import os

INPUT_PATH  = "news.csv"
OUTPUT_PATH = "news_clean.csv"

# ── 1. LOAD ───────────────────────────────────────────────────────────────────

def load_data(path):
    ext = os.path.splitext(path)[1].lower()
    sep = "\t" if ext == ".tsv" else ","
    df = pd.read_csv(path, sep=sep, low_memory=False, encoding="utf-8", on_bad_lines="skip")
    print("Loaded {} rows x {} columns".format(len(df), len(df.columns)))
    return df

# ── 2. ENCODING / MOJIBAKE ────────────────────────────────────────────────────

def fix_encoding(text):
    if not isinstance(text, str):
        return text
    try:
        text = text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    text = re.sub(r"[\x80-\x9f]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_text_columns(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(fix_encoding)
    return df

# ── 3. DUPLICATES ─────────────────────────────────────────────────────────────

def remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates()
    if "id" in df.columns:
        df = df.drop_duplicates(subset="id", keep="first")
    subset = [c for c in ["ticker", "headline", "published_date"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="first")
    print("Removed {} duplicate rows -> {} remain".format(before - len(df), len(df)))
    return df

# ── 4. MISSING VALUES ─────────────────────────────────────────────────────────

def handle_missing(df):
    for col in ["description", "content", "full_content_length"]:
        if col not in df.columns:
            continue
        if df[col].dtype == object:
            df[col] = df[col].replace(r"^\s*$", np.nan, regex=True)
            if "headline" in df.columns:
                df[col] = df[col].fillna(df["headline"])
        else:
            df[col] = df[col].fillna(0)

    num_cols = [
        "headline_sentiment_polarity", "headline_sentiment_subjectivity",
        "relevance_score", "financial_kw_count",
        "headline_word_count", "content_word_count",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    bool_cols = [
        "has_numbers", "has_percent", "ticker_in_headline",
        "ticker_in_desc", "ticker_in_content",
        "is_earnings_news", "is_merger_news",
        "is_analyst_news", "is_macro_news",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing):
        print("Missing values after handling:")
        print(missing)
    else:
        print("No missing values remaining.")
    return df

# ── 5. DATA TYPES ─────────────────────────────────────────────────────────────

def cast_types(df):
    for col in ["published_at", "collected_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    if "published_date" in df.columns:
        df["published_date"] = pd.to_datetime(
            df["published_date"], dayfirst=True, errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    int_cols = [
        "published_hour", "api_page",
        "full_content_length", "headline_word_count", "content_word_count",
        "financial_kw_count",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    float_cols = [
        "headline_sentiment_polarity", "headline_sentiment_subjectivity",
        "relevance_score",
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    cat_cols = [
        "ticker", "language", "source_name", "source_id",
        "data_source", "headline_sentiment_label",
    ]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype("category")

    return df

# ── 6. TEXT CLEANING ──────────────────────────────────────────────────────────

def clean_text_field(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r"Most Read from Bloomberg.*", "", text, flags=re.DOTALL)
    text = re.sub(r"\(Bloomberg\)\s*--\s*", "", text)
    text = re.sub(r"Investing\.com\s*--\s*", "", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def clean_text_content(df):
    for col in ["headline", "description", "content"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_text_field)
    return df

# ── 7. FEATURE ENGINEERING ────────────────────────────────────────────────────

def engineer_features(df):
    if "headline_sentiment_polarity" in df.columns:
        df["headline_sentiment_polarity"] = df["headline_sentiment_polarity"].clip(-1, 1)

    if "headline_sentiment_subjectivity" in df.columns:
        df["headline_sentiment_subjectivity"] = df["headline_sentiment_subjectivity"].clip(0, 1)

    if all(c in df.columns for c in ["ticker_in_headline", "ticker_in_desc", "ticker_in_content"]):
        df["is_ticker_focused"] = (
            (df["ticker_in_headline"] + df["ticker_in_desc"] + df["ticker_in_content"]) >= 2
        ).astype(int)

    flag_cols = [c for c in ["is_earnings_news", "is_merger_news", "is_analyst_news", "is_macro_news"]
                 if c in df.columns]
    if flag_cols:
        df["is_special_news"] = (df[flag_cols].sum(axis=1) > 0).astype(int)

    if "full_content_length" in df.columns:
        df["content_length_bucket"] = pd.cut(
            df["full_content_length"],
            bins=[0, 100, 250, 500, np.inf],
            labels=["short", "medium", "long", "very_long"],
        )

    if "published_at" in df.columns:
        df["day_of_week"] = df["published_at"].dt.day_name()

    return df

# ── 8. OUTLIER FLAGGING ───────────────────────────────────────────────────────

def flag_outliers(df):
    if "content_word_count" in df.columns:
        df["is_stub_article"] = (df["content_word_count"] <= 3).astype(int)
        n = df["is_stub_article"].sum()
        if n:
            print("WARNING: {} stub articles flagged as stubs".format(n))
    return df

# ── 9. COLUMN CLEANUP ─────────────────────────────────────────────────────────

# author dropped: all values are 'unknown' across the entire dataset
DROP_COLS = ["api_page", "query_used", "author"]

def drop_low_value_columns(df):
    to_drop = [c for c in DROP_COLS if c in df.columns]
    df = df.drop(columns=to_drop)
    print("Dropped columns: {}".format(to_drop))
    return df

# ── 10. PIPELINE ──────────────────────────────────────────────────────────────

def preprocess(input_path, output_path):
    print("=" * 60)
    print("  FINANCIAL NEWS PREPROCESSING PIPELINE")
    print("  Input  : {}".format(input_path))
    print("  Output : {}".format(output_path))
    print("=" * 60)

    df = load_data(input_path)

    print("\n[1] Fixing encoding / mojibake ...")
    text_cols = ["headline", "description", "content", "headline_sentiment_label"]
    df = clean_text_columns(df, text_cols)

    print("[2] Removing duplicates ...")
    df = remove_duplicates(df)

    print("[3] Handling missing values ...")
    df = handle_missing(df)

    print("[4] Casting data types ...")
    df = cast_types(df)

    print("[5] Cleaning text content ...")
    df = clean_text_content(df)

    print("[6] Engineering features ...")
    df = engineer_features(df)

    print("[7] Flagging outliers ...")
    df = flag_outliers(df)

    print("[8] Dropping low-value columns ...")
    df = drop_low_value_columns(df)

    df.to_csv(output_path, index=False, encoding="utf-8")
    print("\nDone! Clean dataset saved -> {}".format(output_path))
    print("Final shape: {} rows x {} columns".format(df.shape[0], df.shape[1]))
    print("=" * 60)
    return df

# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df_clean = preprocess(INPUT_PATH, OUTPUT_PATH)
    print("\nColumn dtypes:")
    print(df_clean.dtypes.to_string())
    print("\nSample (3 rows, key columns):")
    cols = ["id", "ticker", "headline", "published_date", "headline_sentiment_label"]
    cols = [c for c in cols if c in df_clean.columns]
    print(df_clean[cols].head(3).to_string())