"""
StockSense AI — GDELT News Collector
CS4063 NLP Project | Mohammad Haider 23i-2558
Fetches US stock news from GDELT Project — FREE, no API key, goes back 5+ years.
Saves into the same stocksense.db as other collectors.
"""

import sqlite3
import hashlib
import logging
import requests
import pandas as pd
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from textblob import TextBlob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
GDELT_URL  = "https://api.gdeltproject.org/api/v2/doc/doc"
DB_PATH    = "stocksense.db"

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
    Creates or reuses the same news_articles table.
    Safe to run even if table already exists from NewsAPI/Finnhub runs.
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

    # Add data_source column if table already exists from previous runs
    try:
        conn.execute("ALTER TABLE news_articles ADD COLUMN data_source TEXT DEFAULT 'newsapi'")
        logger.info("Added data_source column to existing table")
    except sqlite3.OperationalError:
        pass  # Already exists, fine

    conn.commit()
    conn.close()
    logger.info("Database ready at %s", db_path)


# ── Helpers ─────────────────────────────────────────────────────────────────────
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
    return sum(1 for kw in FINANCIAL_KEYWORDS if kw in text.lower())


def compute_relevance(ticker: str, headline: str, desc: str, content: str) -> float:
    keywords = TARGET_STOCKS.get(ticker, [ticker])
    combined = f"{headline} {desc} {content}".lower()
    hits     = sum(1 for kw in keywords if kw.lower() in combined)
    return round(min(hits / max(len(keywords), 1), 1.0), 3)


def classify_news_type(headline: str, desc: str) -> dict:
    combined = f"{headline} {desc}".lower()
    return {
        "is_earnings": int(any(w in combined for w in ["earnings", "eps", "revenue beat", "guidance"])),
        "is_merger":   int(any(w in combined for w in ["merger", "acquisition", "deal", "buyout"])),
        "is_analyst":  int(any(w in combined for w in ["analyst", "upgrade", "downgrade", "price target", "rating"])),
        "is_macro":    int(any(w in combined for w in ["fed", "inflation", "interest rate", "gdp", "recession"])),
    }


def extract_source_from_url(url: str) -> str:
    """Extract domain name as source from URL."""
    try:
        domain = url.split("//")[-1].split("/")[0]
        domain = domain.replace("www.", "")
        return domain
    except Exception:
        return "unknown"


# ── GDELT fetcher ───────────────────────────────────────────────────────────────
def build_gdelt_query(ticker: str) -> str:
    """
    Build GDELT query for a ticker.
    GDELT works best with simple keyword OR combinations.
    We use the first 2 keywords to keep query focused and avoid timeouts.
    """
    keywords = TARGET_STOCKS.get(ticker, [ticker])
    # Use first 2 keywords only — GDELT times out on long queries
    top_keywords = keywords[:2]
    # Wrap multi-word keywords in quotes
    quoted = [f'"{kw}"' if " " in kw else kw for kw in top_keywords]
    return " OR ".join(quoted)


def fetch_gdelt_chunk(ticker: str, start_date: str, end_date: str) -> list[dict]:
    """
    Fetch one chunk of GDELT data for a ticker between two dates.
    GDELT format: YYYYMMDDHHMMSS
    Returns list of raw article dicts.
    """
    query = build_gdelt_query(ticker)

    # Convert YYYY-MM-DD to GDELT format YYYYMMDDHHMMSS
    start_gdelt = start_date.replace("-", "") + "000000"
    end_gdelt   = end_date.replace("-", "") + "235959"

    params = {
        "query":         f"{query} sourcelang:english",
        "mode":          "artlist",
        "maxrecords":    250,        # max per request on free tier
        "format":        "json",
        "startdatetime": start_gdelt,
        "enddatetime":   end_gdelt,
        "sort":          "DateDesc",
    }

    try:
        resp = requests.get(GDELT_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        for art in articles:
            art["_ticker"] = ticker
            art["_query"]  = query
        return articles
    except requests.exceptions.Timeout:
        logger.warning("GDELT timeout for %s (%s to %s) — skipping chunk", ticker, start_date, end_date)
        return []
    except requests.exceptions.JSONDecodeError:
        logger.warning("GDELT returned non-JSON for %s — skipping chunk", ticker)
        return []
    except requests.RequestException as e:
        logger.error("GDELT error for %s: %s", ticker, e)
        return []


def fetch_gdelt_for_ticker(ticker: str, years_back: int = 5) -> list[dict]:
    """
    Fetch GDELT news for a ticker going back `years_back` years.
    Splits into 6-month chunks to avoid GDELT query limits.
    Adds a small delay between requests to be respectful of the free service.
    """
    all_articles = []
    end_date     = datetime.now(timezone.utc)

    # Split into 6-month chunks going backwards
    chunk_months = 6
    num_chunks   = years_back * 2  # 2 chunks per year

    for i in range(num_chunks):
        chunk_end   = end_date - timedelta(days=i * 30 * chunk_months)
        chunk_start = chunk_end - timedelta(days=30 * chunk_months)

        start_str = chunk_start.strftime("%Y-%m-%d")
        end_str   = chunk_end.strftime("%Y-%m-%d")

        logger.info("    [%s] chunk %d/%d: %s → %s", ticker, i+1, num_chunks, start_str, end_str)

        articles = fetch_gdelt_chunk(ticker, start_str, end_str)
        all_articles.extend(articles)

        # Be respectful — GDELT is a free public service
        time.sleep(1)

    logger.info("  [%s] Total from GDELT: %d articles", ticker, len(all_articles))
    return all_articles


# ── Parser ───────────────────────────────────────────────────────────────────────
def parse_gdelt_article(raw: dict) -> Optional[dict]:
    """
    GDELT article fields:
      url, title, seendate, socialimage, domain, language, sourcecountry
    Map to our standard DB columns.
    """
    url = raw.get("url", "")
    if not url:
        return None

    headline = raw.get("title", "") or ""
    desc     = ""    # GDELT free tier doesn't provide article body
    content  = ""
    ticker   = raw.get("_ticker", "")

    # GDELT date format: 20210415T120000Z
    seen_raw = raw.get("seendate", "")
    try:
        # Handle both formats GDELT uses
        seen_raw_clean = seen_raw.replace("T", "").replace("Z", "")
        pub_dt   = datetime.strptime(seen_raw_clean, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        pub_raw  = pub_dt.isoformat()
        pub_date = pub_dt.strftime("%Y-%m-%d")
        pub_hour = pub_dt.hour
    except Exception:
        pub_raw  = seen_raw
        pub_date = None
        pub_hour = None

    source_domain = raw.get("domain", extract_source_from_url(url))
    sentiment     = compute_sentiment(headline)
    news_type     = classify_news_type(headline, desc)

    return {
        "id":                   make_article_id(url),
        "url":                  url,
        "ticker":               ticker,
        "headline":             headline,
        "description":          desc,
        "content":              content,
        "full_content_length":  len(content),

        "source_name":          source_domain,
        "source_id":            source_domain.replace(".", "-"),
        "author":               None,
        "language":             raw.get("language", "en"),

        "published_at":         pub_raw,
        "published_date":       pub_date,
        "published_hour":       pub_hour,
        "collected_at":         datetime.now(timezone.utc).isoformat(),

        "headline_word_count":  len(headline.split()),
        "content_word_count":   0,
        "has_numbers":          int(bool(re.search(r"\d", headline))),
        "has_percent":          int("%" in headline),
        "financial_kw_count":   count_financial_keywords(headline),

        "headline_sentiment_polarity":     sentiment["polarity"],
        "headline_sentiment_subjectivity": sentiment["subjectivity"],
        "headline_sentiment_label":        sentiment["label"],

        "ticker_in_headline":   int(ticker.upper() in headline.upper()),
        "ticker_in_desc":       0,
        "ticker_in_content":    0,
        "relevance_score":      compute_relevance(ticker, headline, desc, content),

        "is_earnings_news":     news_type["is_earnings"],
        "is_merger_news":       news_type["is_merger"],
        "is_analyst_news":      news_type["is_analyst"],
        "is_macro_news":        news_type["is_macro"],

        "query_used":           f"gdelt:{raw.get('_query', '')}",
        "api_page":             1,
        "data_source":          "gdelt",
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
def collect_all_gdelt_news(years_back: int = 5):
    """
    Collect 5 years of news from GDELT for all 27 tickers.
    No API key needed — completely free.
    Saves into same stocksense.db alongside NewsAPI and Finnhub data.
    WARNING: This will take 20-40 minutes due to 27 tickers x 10 chunks each.
    """
    init_db()
    total = 0

    logger.info("Starting GDELT collection for %d tickers, %d years back...", len(TARGET_STOCKS), years_back)
    logger.info("Estimated time: 20-40 minutes. Do not close the terminal.")

    for i, ticker in enumerate(TARGET_STOCKS, 1):
        logger.info("── [%d/%d] Collecting GDELT news for %s ──", i, len(TARGET_STOCKS), ticker)
        raw_articles = fetch_gdelt_for_ticker(ticker, years_back=years_back)
        parsed       = [parse_gdelt_article(a) for a in raw_articles]
        parsed       = [p for p in parsed if p is not None]
        inserted     = save_articles(parsed)
        total       += inserted
        logger.info("  → %d new articles saved for %s", inserted, ticker)
        # Small pause between tickers
        time.sleep(2)

    logger.info("GDELT collection done. Total new articles: %d", total)
    df = export_to_csv()

    print("\n── Data source breakdown ──")
    print(df["data_source"].value_counts().to_string())

    print("\n── Articles per ticker (GDELT only) ──")
    gdelt_df = df[df["data_source"] == "gdelt"]
    print(gdelt_df["ticker"].value_counts().to_string())

    return df


if __name__ == "__main__":
    df = collect_all_gdelt_news(years_back=5)
    print("\n── Sample GDELT articles ──")
    gdelt_df = df[df["data_source"] == "gdelt"]
    print(gdelt_df[[
        "ticker", "headline", "published_date",
        "headline_sentiment_label", "relevance_score", "source_name"
    ]].head(20).to_string(index=False))