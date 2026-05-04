import pandas as pd
import html
import re
from transformers import pipeline
from tqdm import tqdm

# ─────────────────────────────────────────────
# LOAD FINBERT
# ─────────────────────────────────────────────
finbert = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    truncation=True,        # Fix 1: let the tokenizer handle truncation properly
    max_length=512          # Fix 1: token-based limit, not character-based
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
INPUT_FILE  = "news_final.csv"
OUTPUT_FILE = "cleaned_news.csv"
AGG_FILE    = "agg_news.csv"          # Fix 2: we now actually save this

DELETE_ROWS = [39, 40]                # 1-based row numbers in the ORIGINAL file

# ─────────────────────────────────────────────
# TEXT CLEANING FUNCTION
# ─────────────────────────────────────────────
def clean_text(text):
    if pd.isna(text):
        return ""

    text = str(text)
    text = html.unescape(text)

    replacements = { "â€™": "'", "â€˜": "'", "â€œ": '"', "â€": '"', "â€“": "-", "â€”": "-", "â€¦": "...", }
    
    for bad, good in replacements.items():
        text = text.replace(bad, good)

    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df = pd.read_csv(INPUT_FILE, on_bad_lines="skip", low_memory=False)

# Drop hundreds of empty Unnamed columns produced by trailing commas
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

print(f"Original rows: {len(df)}")

# ─────────────────────────────────────────────
# FIX 3: DELETE SPECIFIC ROWS *BEFORE* ANY FILTERING
# so row numbers match the original file
# ─────────────────────────────────────────────
# DELETE_ROWS are 1-based; iloc positions are 0-based
delete_positions = [r - 1 for r in DELETE_ROWS if 1 <= r <= len(df)]
df = df.drop(df.index[delete_positions]).reset_index(drop=True)

# ─────────────────────────────────────────────
# DROP EMPTY SUMMARY ROWS
# ─────────────────────────────────────────────
df["summary"] = df["summary"].fillna("").astype(str)
df = df[df["summary"].str.strip() != ""].reset_index(drop=True)

# ─────────────────────────────────────────────
# FILL FULL TEXT IF EMPTY (fall back to summary)
# ─────────────────────────────────────────────
df["full_text"] = df["full_text"].fillna("").astype(str)
df["full_text"] = df.apply(
    lambda row: row["summary"] if row["full_text"].strip() == "" else row["full_text"],
    axis=1
)

# ─────────────────────────────────────────────
# CLEAN TEXT COLUMNS
# ─────────────────────────────────────────────
for col in ["headline", "summary", "full_text"]:
    if col in df.columns:
        df[col] = df[col].apply(clean_text)

# ─────────────────────────────────────────────
# STANDARDIZE SOURCE
# ─────────────────────────────────────────────
if "text_source" in df.columns:
    df["text_source"] = "finnhub"

# ─────────────────────────────────────────────
# COMBINE TEXT FOR FINBERT
# Fix 4: use only headline + summary to avoid double-counting
# (full_text already falls back to summary when empty)
# ─────────────────────────────────────────────
df["text"] = (
    df["headline"].fillna("") + ". " +
    df["summary"].fillna("")
).str.strip()

# ─────────────────────────────────────────────
# FINBERT — BATCHED WITH PROGRESS BAR
# Fix 1: truncation is now handled by the pipeline (token-aware),
#        so we removed the incorrect character-slice loop
# ─────────────────────────────────────────────
texts      = df["text"].fillna("").astype(str).tolist()
batch_size = 16
all_results = []

print("Running FinBERT sentiment analysis...")

for i in tqdm(range(0, len(texts), batch_size)):
    batch   = texts[i : i + batch_size]
    results = finbert(batch)
    all_results.extend(results)

# Map labels to numeric scores
sentiment_map = {
    "positive":  1,
    "neutral":   0,
    "negative": -1
}

df["finbert_sentiment"] = [sentiment_map[r["label"]] for r in all_results]
df["finbert_score"]     = [round(r["score"], 4)       for r in all_results]

# ─────────────────────────────────────────────
# DATE PARSING
# ─────────────────────────────────────────────
df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
df["date"]           = df["published_date"].dt.date

# ─────────────────────────────────────────────
# AGGREGATION BY TICKER + DATE
# ─────────────────────────────────────────────
agg_news = df.groupby(["ticker", "date"], as_index=False).agg(
    avg_sentiment=("finbert_sentiment", "mean"),
    news_count   =("headline", "count")
)

# Round for readability
agg_news["avg_sentiment"] = agg_news["avg_sentiment"].round(4)

# ─────────────────────────────────────────────
# SAVE OUTPUTS
# Fix 2: both row-level and aggregated files are now saved
# ─────────────────────────────────────────────
df.reset_index(drop=True, inplace=True)
df.to_csv(OUTPUT_FILE, index=False)
agg_news.to_csv(AGG_FILE, index=False)

print(f"Cleaned rows : {len(df)}")
print(f"Agg rows     : {len(agg_news)}")
print(f"✅ Row-level  saved → {OUTPUT_FILE}")
print(f"✅ Aggregated saved → {AGG_FILE}")