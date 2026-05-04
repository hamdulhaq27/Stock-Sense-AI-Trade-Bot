import pandas as pd
import numpy as np
import re
import torch
from transformers import pipeline
from tqdm import tqdm
from google.colab import drive
drive.mount('/content/drive')

# -----------------------------
# CHECK GPU
# -----------------------------
device = 0 if torch.cuda.is_available() else -1
print("Using device:", "GPU (T4)" if device == 0 else "CPU")

# -----------------------------
# CONFIG (CHANGE PATHS IF NEEDED)
# -----------------------------
BASE_PATH = "/content/drive/MyDrive/stock_project/"

TWITS_PATH = BASE_PATH + "stocktwits.csv"
REDDIT_PATH = BASE_PATH + "reddit_stock_data.csv"

OUT_TWITS = BASE_PATH + "agg_stocktwits_2.csv"
OUT_REDDIT = BASE_PATH + "agg_reddit_2.csv"

# -----------------------------
# TEXT CLEANING
# -----------------------------
def clean_text(text):
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    
    return text


# -----------------------------
# LOAD DATA
# -----------------------------
print("Loading datasets...")

twits_df = pd.read_csv(TWITS_PATH)
reddit_df = pd.read_csv(REDDIT_PATH)

twits_df = twits_df[twits_df['is_noise'] == 0]

# datetime
twits_df['created_at'] = pd.to_datetime(twits_df['created_at'])
twits_df['date'] = twits_df['created_at'].dt.date

reddit_df['created_at'] = pd.to_datetime(reddit_df['created_at'])
reddit_df['date'] = reddit_df['created_at'].dt.date

# clean text
print("Cleaning text...")
twits_df['clean_text'] = twits_df['text'].apply(clean_text)
reddit_df['clean_text'] = reddit_df['text'].apply(clean_text)


# -----------------------------
# LOAD FINBERT (GPU)
# -----------------------------
print("Loading FinBERT...")

finbert = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert",
    device=device,   # 🔥 GPU ENABLED
    truncation=True
)


# -----------------------------
# BATCH FINBERT FUNCTION
# -----------------------------
def finbert_score(texts):
    texts = [t[:512] for t in texts]

    batch_size = 32 if device == 0 else 16  # larger batch for GPU
    all_results = []

    for i in tqdm(range(0, len(texts), batch_size), desc="FinBERT inference"):
        batch = texts[i:i+batch_size]
        results = finbert(batch)
        all_results.extend(results)

    scores = []
    for r in all_results:
        label = r['label'].lower()
        score = r['score']

        if label == "positive":
            scores.append(score)
        elif label == "negative":
            scores.append(-score)
        else:
            scores.append(0)

    return np.array(scores)


# -----------------------------
# APPLY FINBERT
# -----------------------------
print("Running FinBERT on StockTwits...")
twits_df['finbert_sentiment'] = finbert_score(
    twits_df['clean_text'].tolist()
)

print("Running FinBERT on Reddit...")
reddit_df['finbert_sentiment'] = finbert_score(
    reddit_df['clean_text'].tolist()
)


# -----------------------------
# STOCKTWITS AGGREGATION
# -----------------------------
print("Aggregating StockTwits...")

agg_twits = twits_df.groupby(['symbol', 'date']).agg({
    'finbert_sentiment': 'mean',
    'text': 'count'
}).rename(columns={
    'finbert_sentiment': 'twit_sentiment',
    'text': 'twit_post_count'
}).reset_index()


# -----------------------------
# REDDIT WEIGHTING
# -----------------------------
print("Aggregating Reddit...")

reddit_df['weight'] = np.log1p(reddit_df['score'])
reddit_df['weighted_sentiment'] = reddit_df['finbert_sentiment'] * reddit_df['weight']

agg_reddit = reddit_df.groupby(['symbol', 'date']).agg({
    'weighted_sentiment': 'mean',
    'text': 'count'
}).rename(columns={
    'weighted_sentiment': 'reddit_sentiment',
    'text': 'reddit_post_count'
}).reset_index()


# -----------------------------
# SAVE OUTPUTS TO DRIVE
# -----------------------------
print("Saving outputs...")

agg_twits.to_csv(OUT_TWITS, index=False)
agg_reddit.to_csv(OUT_REDDIT, index=False)

print("✅ Done! Files saved to Google Drive")