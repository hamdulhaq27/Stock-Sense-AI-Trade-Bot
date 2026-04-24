"""
StockSense AI — Finnhub News Collector
CS4063 NLP Project | Mohammad Haider 23i-2558
Fetches US stock news from Finnhub API — goes back 1+ year, free tier.
Saves into the same stocksense.db as news_collector.py (NewsAPI).
"""

import sqlite3
import hashlib
import logging
import requests
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from textblob import TextBlob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
FINNHUB_API_KEY = "d7luthpr01qk7lvugjp0d7luthpr01qk7lvugjpg"
FINNHUB_URL     = "https://finnhub.io/api/v1/company-news"
DB_PATH         = "stocksense.db"

# ── Same TARGET_STOCKS dictionary — unchanged ───────────────────────────────────
TARGET_STOCKS = {
    # Big Tech
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

FINANCIAL_KEYWORDS = [
    "earnings", "revenue", "profit", "loss", "guidance", "forecast",
    "acquisition", "merger", "IPO", "dividend", "buyback", "stock split",
    "SEC", "analyst", "upgrade", "downgrade", "price target",
    "bull", "bear", "rally", "selloff", "volatility"
]

# ── Database setup ──────────────────────────────────────────────────────────────
def init_db(db_path: str = DB_PATH):
    """
    Creates the same news_articles table as news_collector.py.
    If it already exists (from NewsAPI run), it just skips — no data lost.
    Extra column 'data_source' tells us if article came from NewsAPI or Finnhub.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id                              TEXT PRIMARY KEY,
            url                             TEXT UNIQUE NOT NULL,
            ticker                          TEXT,
            headline                        TEXT,
            description                     TEXT,
            content                         TEXT,
            full_content_length             INTEGER,
            source_name                     TEXT,
            source_id                       TEXT,
            author                          TEXT,
            language                        TEXT,
            published_at                    TEXT,
            published_date                  TEXT,
            published_hour                  INTEGER,
            collected_at                    TEXT,
            headline_word_count             INTEGER,
            content_word_count              INTEGER,
            has_numbers                     INTEGER,
            has_percent                     INTEGER,
            financial_kw_count              INTEGER,
            headline_sentiment_polarity     REAL,
            headline_sentiment_subjectivity REAL,
            headline_sentiment_label        TEXT,
            ticker_in_headline              INTEGER,
            ticker_in_desc                  INTEGER,
            ticker_in_content               INTEGER,
            relevance_score                 REAL,
            is_earnings_news                INTEGER DEFAULT 0,
            is_merger_news                  INTEGER DEFAULT 0,
            is_analyst_news                 INTEGER DEFAULT 0,
            is_macro_news                   INTEGER DEFAULT 0,
            query_used                      TEXT,
            api_page                        INTEGER,
            data_source                     TEXT DEFAULT 'newsapi'
        )
    """)

    # Add data_source column if table already exists from NewsAPI run
    try:
        conn.execute("ALTER TABLE news_articles ADD COLUMN data_source TEXT DEFAULT 'newsapi'")
        logger.info("Added data_source column to existing table")
    except sqlite3.OperationalError:
        pass  # Column already exists, that's fine

    conn.commit()
    conn.close()
    logger.info("Database ready at %s", db_path)


# ── Helpers (same as news_collector.py) ────────────────────────────────────────
def make_article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def compute_sentiment(text: str) -> dict:
    if not text:
        return {"polarity": None, "subjectivity": None, "label": "neutral"}
    blob  = TextBlob(text)
    pol   = round(blob.sentiment.polarity, 4)
    sub   = round(blob.sentiment.subjectivity, 4)
    label = "positive" if pol > 0.05 else ("negative" if pol < -0.05 else "neutral")
    return {"polarity": pol, "subjectivity": sub, "label": label}


def count_financial_keywords(text: str) -> int:
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in FINANCIAL_KEYWORDS if kw in text_lower)


def compute_relevance(ticker: str, headline: str, desc: str, content: str) -> float:
    keywords = TARGET_STOCKS.get(ticker, [ticker])
    combined = f"{headline} {desc} {content}".lower()
    hits     = sum(1 for kw in keywords if kw.lower() in combined)
    score    = min(hits / max(len(keywords), 1), 1.0)
    return round(score, 3)


def classify_news_type(headline: str, desc: str) -> dict:
    combined = f"{headline} {desc}".lower()
    return {
        "is_earnings": int(any(w in combined for w in ["earnings", "eps", "revenue beat", "guidance"])),
        "is_merger":   int(any(w in combined for w in ["merger", "acquisition", "deal", "buyout"])),
        "is_analyst":  int(any(w in combined for w in ["analyst", "upgrade", "downgrade", "price target", "rating"])),
        "is_macro":    int(any(w in combined for w in ["fed", "inflation", "interest rate", "gdp", "recession"])),
    }


# ── Finnhub fetcher ─────────────────────────────────────────────────────────────
def fetch_finnhub_news(ticker: str, days_back: int = 365) -> list[dict]:
    """
    Fetch news from Finnhub for a single ticker.
    Finnhub free tier: query by symbol directly, no keyword guessing needed.
    Goes back up to 1 year on free tier.
    """
    end_dt   = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days_back)

    from_str = start_dt.strftime("%Y-%m-%d")
    to_str   = end_dt.strftime("%Y-%m-%d")

    params = {
        "symbol": ticker,
        "from":   from_str,
        "to":     to_str,
        "token":  FINNHUB_API_KEY,
    }

    try:
        resp = requests.get(FINNHUB_URL, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json()

        if not isinstance(articles, list):
            logger.warning("Unexpected response for %s: %s", ticker, articles)
            return []

        # Tag each article with ticker info
        for art in articles:
            art["_ticker"] = ticker

        logger.info("  [%s] → %d articles from Finnhub", ticker, len(articles))
        return articles

    except requests.RequestException as e:
        logger.error("Finnhub error for %s: %s", ticker, e)
        return []


# ── Parser — converts Finnhub format to our standard DB format ──────────────────
def parse_finnhub_article(raw: dict) -> Optional[dict]:
    """
    Finnhub article fields:
      - headline, summary, url, source, datetime (unix timestamp), image, id, category
    We map these to the same columns as our NewsAPI collector.
    """
    url = raw.get("url", "")
    if not url:
        return None

    headline = raw.get("headline", "") or ""
    desc     = raw.get("summary", "") or ""   # Finnhub calls it 'summary'
    content  = desc                            # Finnhub doesn't give full content, use summary
    ticker   = raw.get("_ticker", "")

    # Finnhub gives datetime as Unix timestamp
    unix_ts  = raw.get("datetime", 0)
    try:
        pub_dt   = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        pub_raw  = pub_dt.isoformat()
        pub_date = pub_dt.strftime("%Y-%m-%d")
        pub_hour = pub_dt.hour
    except Exception:
        pub_raw  = None
        pub_date = None
        pub_hour = None

    sentiment  = compute_sentiment(headline)
    news_type  = classify_news_type(headline, desc)

    return {
        "id":                   make_article_id(url),
        "url":                  url,
        "ticker":               ticker,
        "headline":             headline,
        "description":          desc,
        "content":              content,
        "full_content_length":  len(content),

        "source_name":          raw.get("source"),
        "source_id":            raw.get("source", "").lower().replace(" ", "-"),
        "author":               None,           # Finnhub doesn't provide author
        "language":             "en",

        "published_at":         pub_raw,
        "published_date":       pub_date,
        "published_hour":       pub_hour,
        "collected_at":         datetime.now(timezone.utc).isoformat(),

        "headline_word_count":  len(headline.split()),
        "content_word_count":   len(content.split()),
        "has_numbers":          int(bool(re.search(r"\d", headline))),
        "has_percent":          int("%" in headline),
        "financial_kw_count":   count_financial_keywords(headline + " " + desc),

        "headline_sentiment_polarity":     sentiment["polarity"],
        "headline_sentiment_subjectivity": sentiment["subjectivity"],
        "headline_sentiment_label":        sentiment["label"],

        "ticker_in_headline":   int(ticker.upper() in headline.upper()),
        "ticker_in_desc":       int(ticker.upper() in desc.upper()),
        "ticker_in_content":    int(ticker.upper() in content.upper()),
        "relevance_score":      compute_relevance(ticker, headline, desc, content),

        "is_earnings_news":     news_type["is_earnings"],
        "is_merger_news":       news_type["is_merger"],
        "is_analyst_news":      news_type["is_analyst"],
        "is_macro_news":        news_type["is_macro"],

        "query_used":           f"finnhub:symbol={ticker}",
        "api_page":             1,
        "data_source":          "finnhub",
    }


# ── DB writer ───────────────────────────────────────────────────────────────────
def save_articles(articles: list[dict], db_path: str = DB_PATH) -> int:
    if not articles:
        return 0
    conn     = sqlite3.connect(db_path)
    cursor   = conn.cursor()
    inserted = 0
    for row in articles:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO news_articles VALUES (
                    :id, :url, :ticker, :headline, :description, :content,
                    :full_content_length, :source_name, :source_id, :author, :language,
                    :published_at, :published_date, :published_hour, :collected_at,
                    :headline_word_count, :content_word_count, :has_numbers, :has_percent,
                    :financial_kw_count,
                    :headline_sentiment_polarity, :headline_sentiment_subjectivity,
                    :headline_sentiment_label,
                    :ticker_in_headline, :ticker_in_desc, :ticker_in_content,
                    :relevance_score,
                    :is_earnings_news, :is_merger_news, :is_analyst_news, :is_macro_news,
                    :query_used, :api_page, :data_source
                )
            """, row)
            inserted += cursor.rowcount
        except sqlite3.Error as e:
            logger.warning("DB insert error: %s", e)
    conn.commit()
    conn.close()
    return inserted


# ── Export ───────────────────────────────────────────────────────────────────────
def export_to_csv(db_path: str = DB_PATH, output: str = "news_data.csv"):
    conn = sqlite3.connect(db_path)
    df   = pd.read_sql("SELECT * FROM news_articles ORDER BY published_at DESC", conn)
    conn.close()
    df.to_csv(output, index=False)
    logger.info("Exported %d total rows to %s", len(df), output)
    return df


# ── Main runner ─────────────────────────────────────────────────────────────────
def collect_all_finnhub_news(days_back: int = 365):
    """
    Collect news from Finnhub for all tickers.
    days_back=365 gives you 1 full year — way more than NewsAPI's 30 days.
    Saves into the same stocksense.db so all news is in one place.
    """
    init_db()
    total = 0
    for ticker in TARGET_STOCKS:
        logger.info("Collecting Finnhub news for %s ...", ticker)
        raw_articles = fetch_finnhub_news(ticker, days_back=days_back)
        parsed       = [parse_finnhub_article(a) for a in raw_articles]
        parsed       = [p for p in parsed if p is not None]
        inserted     = save_articles(parsed)
        total       += inserted
        logger.info("  → %d new articles saved for %s", inserted, ticker)

    logger.info("Done. Total new Finnhub articles: %d", total)
    return export_to_csv()


if __name__ == "__main__":
    df = collect_all_finnhub_news(days_back=365)
    print("\n── Sample output ──")
    print(df[df["data_source"] == "finnhub"][[
        "ticker", "headline", "published_date",
        "headline_sentiment_label", "relevance_score", "source_name"
    ]].head(20).to_string(index=False))

    print("\n── Data source breakdown ──")
    print(df["data_source"].value_counts().to_string())