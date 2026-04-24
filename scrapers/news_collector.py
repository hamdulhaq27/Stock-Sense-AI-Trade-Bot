"""
StockSense AI — News Data Collector
CS4063 NLP Project | Mohammad Haider 23i-2558
Fetches financial news from NewsAPI with maximum columns for NLP analysis.
"""

import os
import sqlite3
import hashlib
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from textblob import TextBlob   # pip install textblob
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "2336ad9efa51473287444ceb5a27dfeb")
NEWS_API_URL  = "https://newsapi.org/v2/everything"
DB_PATH       = "stocksense.db"

# US market tickers we care about
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
# Trusted financial news sources
TRUSTED_SOURCES = (
    "bloomberg.com,reuters.com,wsj.com,ft.com,cnbc.com,"
    "marketwatch.com,barrons.com,seekingalpha.com,"
    "fool.com,investopedia.com,yahoo.com"
)

FINANCIAL_KEYWORDS = [
    "earnings", "revenue", "profit", "loss", "guidance", "forecast",
    "acquisition", "merger", "IPO", "dividend", "buyback", "stock split",
    "SEC", "analyst", "upgrade", "downgrade", "price target",
    "bull", "bear", "rally", "selloff", "volatility"
]

# ── Database setup ──────────────────────────────────────────────────────────────
def init_db(db_path: str = DB_PATH):
    """Create the news table with all columns if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            -- Identity & deduplication
            id                  TEXT PRIMARY KEY,   -- SHA-256 of URL
            url                 TEXT UNIQUE NOT NULL,

            -- Core content
            ticker              TEXT,               -- e.g. AAPL, TSLA
            headline            TEXT,
            description         TEXT,
            content             TEXT,               -- truncated body (NewsAPI free tier)
            full_content_length INTEGER,            -- char length of content

            -- Source metadata
            source_name         TEXT,
            source_id           TEXT,               -- newsapi source id
            author              TEXT,
            language            TEXT,

            -- Temporal
            published_at        TEXT,               -- ISO-8601 from API
            published_date      TEXT,               -- YYYY-MM-DD (for grouping)
            published_hour      INTEGER,            -- 0-23 (market open/close context)
            collected_at        TEXT,               -- when we inserted this row

            -- NLP signals (pre-computed lightweight signals)
            headline_word_count INTEGER,
            content_word_count  INTEGER,
            has_numbers         INTEGER,            -- 1 if headline contains digits
            has_percent         INTEGER,            -- 1 if headline contains %
            financial_kw_count  INTEGER,            -- count of financial keywords in headline+desc
            headline_sentiment_polarity   REAL,    -- TextBlob polarity  (-1 to 1)
            headline_sentiment_subjectivity REAL,  -- TextBlob subjectivity (0 to 1)
            headline_sentiment_label TEXT,          -- positive / negative / neutral

            -- Relevance signals
            ticker_in_headline  INTEGER,            -- 1 if ticker symbol in headline
            ticker_in_desc      INTEGER,
            ticker_in_content   INTEGER,
            relevance_score     REAL,               -- 0-1 composite relevance

            -- Market context flags
            is_earnings_news    INTEGER DEFAULT 0,
            is_merger_news      INTEGER DEFAULT 0,
            is_analyst_news     INTEGER DEFAULT 0,
            is_macro_news       INTEGER DEFAULT 0,

            -- API metadata
            query_used          TEXT,               -- what query fetched this article
            api_page            INTEGER
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", db_path)


# ── Helpers ─────────────────────────────────────────────────────────────────────
def make_article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def compute_sentiment(text: str) -> dict:
    """Lightweight sentiment via TextBlob. FinBERT will run later in the pipeline."""
    if not text:
        return {"polarity": None, "subjectivity": None, "label": "neutral"}
    blob = TextBlob(text)
    pol  = round(blob.sentiment.polarity, 4)
    sub  = round(blob.sentiment.subjectivity, 4)
    label = "positive" if pol > 0.05 else ("negative" if pol < -0.05 else "neutral")
    return {"polarity": pol, "subjectivity": sub, "label": label}


def count_financial_keywords(text: str) -> int:
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in FINANCIAL_KEYWORDS if kw in text_lower)


def compute_relevance(ticker: str, headline: str, desc: str, content: str) -> float:
    """Score 0-1 how relevant the article is to the ticker."""
    keywords = TARGET_STOCKS.get(ticker, [ticker])
    combined = f"{headline} {desc} {content}".lower()
    hits = sum(1 for kw in keywords if kw.lower() in combined)
    score = min(hits / max(len(keywords), 1), 1.0)
    return round(score, 3)


def classify_news_type(headline: str, desc: str) -> dict:
    """Flag article type based on keyword presence."""
    combined = f"{headline} {desc}".lower()
    return {
        "is_earnings": int(any(w in combined for w in ["earnings", "eps", "revenue beat", "guidance"])),
        "is_merger":   int(any(w in combined for w in ["merger", "acquisition", "deal", "buyout"])),
        "is_analyst":  int(any(w in combined for w in ["analyst", "upgrade", "downgrade", "price target", "rating"])),
        "is_macro":    int(any(w in combined for w in ["fed", "inflation", "interest rate", "gdp", "recession"])),
    }


# ── Core fetcher ────────────────────────────────────────────────────────────────
def fetch_news_for_ticker(ticker: str, days_back: int = 7, max_pages: int = 3) -> list[dict]:
    """Fetch raw articles from NewsAPI for a given ticker."""
    keywords = TARGET_STOCKS.get(ticker, [ticker])
    query    = " OR ".join(f'"{kw}"' for kw in keywords)
    from_dt  = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_articles = []
    for page in range(1, max_pages + 1):
        params = {
            "q":          query,
            "from":       from_dt,
            "language":   "en",
            "sortBy":     "publishedAt",
            "domains":    TRUSTED_SOURCES,
            "pageSize":   100,
            "page":       page,
            "apiKey":     NEWS_API_KEY,
        }
        try:
            resp = requests.get(NEWS_API_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("articles", [])
            if not articles:
                break
            for art in articles:
                art["_ticker"]     = ticker
                art["_query"]      = query
                art["_page"]       = page
            all_articles.extend(articles)
            logger.info("  [%s] page %d → %d articles", ticker, page, len(articles))
            if len(articles) < 100:
                break
        except requests.RequestException as e:
            logger.error("NewsAPI error for %s page %d: %s", ticker, page, e)
            break

    return all_articles


def parse_article(raw: dict) -> Optional[dict]:
    """Transform a raw NewsAPI article dict into a fully-featured flat row."""
    url = raw.get("url", "")
    if not url or url == "https://removed.com":
        return None

    headline = raw.get("title", "") or ""
    desc     = raw.get("description", "") or ""
    content  = raw.get("content", "") or ""
    ticker   = raw.get("_ticker", "")

    # Temporal
    pub_raw  = raw.get("publishedAt", "")
    try:
        pub_dt   = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
        pub_date = pub_dt.strftime("%Y-%m-%d")
        pub_hour = pub_dt.hour
    except Exception:
        pub_date = None
        pub_hour = None

    # Sentiment on headline
    sentiment = compute_sentiment(headline)

    # Financial classification
    news_type = classify_news_type(headline, desc)

    return {
        "id":                   make_article_id(url),
        "url":                  url,
        "ticker":               ticker,
        "headline":             headline,
        "description":          desc,
        "content":              content,
        "full_content_length":  len(content),

        "source_name":          (raw.get("source") or {}).get("name"),
        "source_id":            (raw.get("source") or {}).get("id"),
        "author":               raw.get("author"),
        "language":             "en",

        "published_at":         pub_raw,
        "published_date":       pub_date,
        "published_hour":       pub_hour,
        "collected_at":         datetime.utcnow().isoformat(),

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

        "query_used":           raw.get("_query"),
        "api_page":             raw.get("_page"),
    }


# ── DB writer ───────────────────────────────────────────────────────────────────
def save_articles(articles: list[dict], db_path: str = DB_PATH) -> int:
    """Upsert parsed articles into SQLite. Returns number of new rows inserted."""
    if not articles:
        return 0
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()
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
                    :query_used, :api_page
                )
            """, row)
            inserted += cursor.rowcount
        except sqlite3.Error as e:
            logger.warning("DB insert error: %s", e)
    conn.commit()
    conn.close()
    return inserted


# ── Export helper ────────────────────────────────────────────────────────────────
def export_to_csv(db_path: str = DB_PATH, output: str = "news_data.csv"):
    conn = sqlite3.connect(db_path)
    df   = pd.read_sql("SELECT * FROM news_articles ORDER BY published_at DESC", conn)
    conn.close()
    df.to_csv(output, index=False)
    logger.info("Exported %d rows to %s", len(df), output)
    return df


# ── Main runner ─────────────────────────────────────────────────────────────────
def collect_all_news(days_back: int = 30):
    init_db()
    total = 0
    for ticker in TARGET_STOCKS:
        logger.info("Collecting news for %s ...", ticker)
        raw_articles    = fetch_news_for_ticker(ticker, days_back=days_back)
        parsed          = [parse_article(a) for a in raw_articles]
        parsed          = [p for p in parsed if p is not None]
        inserted        = save_articles(parsed)
        total          += inserted
        logger.info("  → %d new articles saved for %s", inserted, ticker)
    logger.info("Done. Total new articles: %d", total)
    return export_to_csv()


if __name__ == "__main__":
    df = collect_all_news(days_back=30)
    print(df[["ticker", "headline", "published_date",
              "headline_sentiment_label", "relevance_score",
              "is_earnings_news"]].head(20).to_string(index=False))
