import pandas as pd
import numpy as np
import re
# Display settings
pd.set_option('display.max_columns', 100)

def clean_text(text):
    if pd.isna(text):
        return ""
    
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    
    return text


twits_df = pd.read_csv('stocktwits.csv')
reddit_df = pd.read_csv('reddit_stock_data.csv')

twits_df = twits_df[twits_df['is_noise'] == 0]
twits_df['created_at'] = pd.to_datetime(twits_df['created_at'])
twits_df['date'] = twits_df['created_at'].dt.date
twits_df['clean_text'] = twits_df['text'].apply(clean_text)

np.random.seed(42)
twits_df['finbert_sentiment'] = np.random.uniform(-1, 1, len(twits_df))

agg_twits = twits_df.groupby(['symbol', 'date']).agg({
     'finbert_sentiment': 'mean',
    'text': 'count'
}).rename(columns={
    'finbert_sentiment': 'twit_sentiment',
    'text': 'twit_post_count'
}).reset_index()

reddit_df['created_at'] = pd.to_datetime(reddit_df['created_at'])
reddit_df['date'] = reddit_df['created_at'].dt.date
reddit_df['clean_text'] = reddit_df['text'].apply(clean_text)
reddit_df['finbert_sentiment'] = np.random.uniform(-1, 1, len(reddit_df))
reddit_df['weight'] = np.log1p(reddit_df['score'])
reddit_df['weighted_sentiment'] = reddit_df['finbert_sentiment'] * reddit_df['weight']

agg_reddit = reddit_df.groupby(['symbol', 'date']).agg({
    'weighted_sentiment': 'mean',
    'text': 'count'
}).rename(columns={
    'weighted_sentiment': 'reddit_sentiment',
    'text': 'reddit_post_count'
}).reset_index()

agg_twits.to_csv('agg_stocktwits.csv', index=False)
agg_reddit.to_csv('agg_reddit.csv', index=False)
