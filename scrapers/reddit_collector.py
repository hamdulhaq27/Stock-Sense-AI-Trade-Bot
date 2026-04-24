import requests
import time
import csv
import re
import html
from datetime import datetime

########
# CONFIG
########

HEADERS = {
    "User-Agent": "Mozilla/5.0 (StockSentimentBot/1.0)"
}

BASE_URL = "https://www.reddit.com"

TARGET_STOCKS = {
    "AAPL":  ["Apple", "AAPL", "iPhone", "Tim Cook"],
    "TSLA":  ["Tesla", "TSLA", "Elon Musk", "electric vehicle"],
    "AMZN":  ["Amazon", "AMZN", "AWS", "Andy Jassy"],
    "MSFT":  ["Microsoft", "MSFT", "Azure", "Satya Nadella"],
    "NVDA":  ["Nvidia", "NVDA", "GPU", "Jensen Huang"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "Sundar Pichai"],
    "META":  ["Meta", "Facebook", "META", "Zuckerberg"],
    "JPM":   ["JPMorgan", "JPM", "Jamie Dimon"],
    "GS":    ["Goldman Sachs", "GS", "Goldman"],
    "BAC":   ["Bank of America", "BAC"],
    "NFLX":  ["Netflix", "NFLX", "streaming"],
    "DIS":   ["Disney", "DIS", "Walt Disney"],
    "UBER":  ["Uber", "UBER", "rideshare"],
    "SPOT":  ["Spotify", "SPOT", "podcast"],
    "AMD":   ["AMD", "Advanced Micro Devices", "Lisa Su"],
    "INTC":  ["Intel", "INTC", "Pat Gelsinger"],
    "QCOM":  ["Qualcomm", "QCOM", "snapdragon"],
    "PYPL":  ["PayPal", "PYPL"],
    "SQ":    ["Block", "Square", "SQ", "Jack Dorsey"],
    "SHOP":  ["Shopify", "SHOP"],
    "JNJ":   ["Johnson Johnson", "JNJ"],
    "PFE":   ["Pfizer", "PFE"],
    "XOM":   ["ExxonMobil", "Exxon", "XOM"],
    "CVX":   ["Chevron", "CVX"],
    "RIVN":  ["Rivian", "RIVN"],
    "PLTR":  ["Palantir", "PLTR", "Alex Karp"],
    "WMT":   ["Walmart", "WMT"],
}

SUBREDDITS = [
    "stocks",
    "wallstreetbets",
    "investing",
    "StockMarket",
    "Daytrading",
    "ValueInvesting",
    "pennystocks"
]
OUTPUT_FILE = "reddit_stock_data.csv"

###############
# TEXT CLEANING
###############

def safe_text(text):
    """
    Clean text:
    - Decode HTML entities
    - Ensure UTF-8 safe
    """
    if text is None:
        return ""

    text = str(text)

    # Decode ALL HTML entities
    text = html.unescape(text)

    # UTF-8 safety
    return text.encode("utf-8", "ignore").decode("utf-8")

#####################
# FEATURE ENGINEERING
#####################

def extract_features(text):
    words = text.split()
    cashtags = re.findall(r"\$[A-Z]+", text)

    return {
        "text_length": len(text),
        "word_count": len(words),
        "has_cashtag": int(len(cashtags) > 0),
        "cashtag_count": len(cashtags),
        "has_url": int("http" in text),
        "is_noise": int(len(words) < 5)
    }

def convert_time(utc):
    dt = datetime.utcfromtimestamp(utc)
    return dt, dt.date(), dt.hour

#########
# SCRAPER
#########

def fetch_posts(subreddit, query, limit=25):
    url = f"{BASE_URL}/r/{subreddit}/search.json"

    params = {
        "q": query,
        "restrict_sr": 1,
        "sort": "new",
        "limit": limit
    }

    try:
        res = requests.get(url, headers=HEADERS, params=params)

        if res.status_code != 200:
            print(f"❌ Error {res.status_code} for {query} in r/{subreddit}")
            return []

        data = res.json()
        return data["data"]["children"]

    except Exception as e:
        print("Error:", e)
        return []

#############
# SAVE TO CSV
#############

def save_csv(data):
    if not data:
        print("⚠ No data to save")
        return

    keys = data[0].keys()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()

        for row in data:
            clean_row = {k: safe_text(v) for k, v in row.items()}
            writer.writerow(clean_row)

    print(f"\n💾 Saved → {OUTPUT_FILE}")

###############
# MAIN FUNCTION
###############

def main():
    all_rows = []

    for symbol, keywords in TARGET_STOCKS.items():
        print(f"\n🔍 Scraping {symbol}...")

        for keyword in keywords:
            for subreddit in SUBREDDITS:

                posts = fetch_posts(subreddit, keyword)

                for post in posts:
                    data = post["data"]

                    raw_text = data.get("title", "") + " " + data.get("selftext", "")
                    text = safe_text(raw_text).replace("\n", " ").replace("\r", " ").strip()

                    if not text:
                        continue

                    dt, post_date, post_hour = convert_time(data["created_utc"])

                    features = extract_features(text)

                    row = {
                        "symbol": symbol,
                        "text": safe_text(text),   # IMPORTANT FIX
                        "created_at": dt,
                        "post_date": post_date,
                        "post_hour": post_hour,
                        "username": safe_text(data.get("author", "")),
                        "score": data.get("score", 0),
                        "num_comments": data.get("num_comments", 0),
                        **features,
                        "finbert_sentiment": "",
                        "finbert_score": ""
                    }

                    all_rows.append(row)

                time.sleep(5)

    # Save data
    save_csv(all_rows)


if __name__ == "__main__":
    main()