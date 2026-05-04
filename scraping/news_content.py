"""
StockSense AI — News Data Collector v5
CS4063 NLP Project | Mohammad Haider, Hamd ul Haq, Ayesha Ikram

FIXES IN v5:
  - 80 most important tickers
  - Phase 1 results saved to articles_cache.json after EVERY ticker
  - Phase 2 tracks scraped URLs in scraped_urls.json
  - Ctrl+C at ANY point = zero data loss, resume exactly where you stopped
"""

import asyncio
import aiohttp
import time
import csv
import re
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

import finnhub
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

FINNHUB_API_KEY    = "d7luthpr01qk7lvugjp0d7luthpr01qk7lvugjpg"
OUTPUT_CSV         = "news_final.csv"
ARTICLES_CACHE     = "articles_cache.json"
SCRAPED_URLS_FILE  = "scraped_urls.json"

DATE_END           = datetime.today()
DATE_START         = DATE_END - timedelta(days=365)

MIN_TEXT_LENGTH    = 300

MAX_CONCURRENT_SCRAPES   = 15
MAX_REQUESTS_PER_DOMAIN  = 3
FINNHUB_CALLS_PER_MIN    = 55
SCRAPE_TIMEOUT_SEC       = 12
SAVE_INTERVAL            = 500


# ─────────────────────────────────────────────────────────────────────────────
# TOP 80 TICKERS
# ─────────────────────────────────────────────────────────────────────────────

TARGET_STOCKS = {
    # ── Big Tech (9) ──────────────────────────────────────────────────────────
    "AAPL":  ["Apple", "AAPL", "iPhone", "Tim Cook"],
    "TSLA":  ["Tesla", "TSLA", "Elon Musk", "electric vehicle"],
    "AMZN":  ["Amazon", "AMZN", "AWS", "Andy Jassy"],
    "MSFT":  ["Microsoft", "MSFT", "Azure", "Satya Nadella"],
    "NVDA":  ["Nvidia", "NVDA", "GPU", "Jensen Huang"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "Sundar Pichai"],
    "META":  ["Meta", "Facebook", "META", "Zuckerberg"],
    "AMD":   ["AMD", "Advanced Micro Devices", "Lisa Su"],
    "INTC":  ["Intel", "INTC", "Pat Gelsinger"],

    # ── Semiconductors & Hardware (9) ─────────────────────────────────────────
    "QCOM":  ["Qualcomm", "QCOM", "Snapdragon"],
    "AVGO":  ["Broadcom", "AVGO"],
    "TSM":   ["TSMC", "TSM", "Taiwan Semiconductor"],
    "ASML":  ["ASML", "lithography", "EUV"],
    "MU":    ["Micron", "MU", "memory chip", "DRAM"],
    "AMAT":  ["Applied Materials", "AMAT", "semiconductor equipment"],
    "KLAC":  ["KLA Corporation", "KLAC", "chip inspection"],
    "LRCX":  ["Lam Research", "LRCX"],
    "ARM":   ["ARM Holdings", "ARM", "chip architecture"],

    # ── Software & SaaS (9) ───────────────────────────────────────────────────
    "CRM":   ["Salesforce", "CRM", "Marc Benioff"],
    "NOW":   ["ServiceNow", "NOW"],
    "WDAY":  ["Workday", "WDAY"],
    "SNOW":  ["Snowflake", "SNOW", "data cloud"],
    "PLTR":  ["Palantir", "PLTR", "Alex Karp"],
    "ADBE":  ["Adobe", "ADBE", "Photoshop"],
    "ORCL":  ["Oracle", "ORCL", "Larry Ellison"],
    "INTU":  ["Intuit", "INTU", "TurboTax", "QuickBooks"],
    "DDOG":  ["Datadog", "DDOG", "observability"],

    # ── E-Commerce & Consumer Internet (9) ────────────────────────────────────
    "SHOP":  ["Shopify", "SHOP"],
    "PYPL":  ["PayPal", "PYPL"],
    "SQ":    ["Block", "Square", "SQ", "Jack Dorsey"],
    "NFLX":  ["Netflix", "NFLX", "streaming"],
    "SPOT":  ["Spotify", "SPOT", "podcast"],
    "UBER":  ["Uber", "UBER", "rideshare"],
    "ABNB":  ["Airbnb", "ABNB"],
    "BKNG":  ["Booking Holdings", "BKNG", "Booking.com"],
    "DASH":  ["DoorDash", "DASH", "food delivery"],

    # ── Finance & Banking (9) ─────────────────────────────────────────────────
    "JPM":   ["JPMorgan", "JPM", "Jamie Dimon"],
    "GS":    ["Goldman Sachs", "GS", "Goldman"],
    "BAC":   ["Bank of America", "BAC"],
    "MS":    ["Morgan Stanley", "MS"],
    "C":     ["Citigroup", "Citi", "C"],
    "WFC":   ["Wells Fargo", "WFC"],
    "BLK":   ["BlackRock", "BLK", "Larry Fink"],
    "AXP":   ["American Express", "AXP", "Amex"],
    "SCHW":  ["Charles Schwab", "SCHW"],

    # ── Insurance & Asset Management (9) ──────────────────────────────────────
    "BRK.B": ["Berkshire Hathaway", "BRK.B", "Warren Buffett", "Charlie Munger"],
    "CB":    ["Chubb", "CB", "insurance"],
    "MET":   ["MetLife", "MET", "life insurance"],
    "PRU":   ["Prudential", "PRU"],
    "ALL":   ["Allstate", "ALL"],
    "PGR":   ["Progressive", "PGR", "auto insurance"],
    "AFL":   ["Aflac", "AFL"],
    "AIG":   ["AIG", "American International Group"],
    "TRV":   ["Travelers", "TRV"],

    # ── Oil & Gas / Energy (9) ────────────────────────────────────────────────
    "XOM":   ["ExxonMobil", "Exxon", "XOM"],
    "CVX":   ["Chevron", "CVX"],
    "COP":   ["ConocoPhillips", "COP"],
    "BP":    ["BP", "British Petroleum", "BP plc"],
    "SHEL":  ["Shell", "SHEL", "Royal Dutch Shell"],
    "SLB":   ["Schlumberger", "SLB", "oilfield services"],
    "OXY":   ["Occidental", "OXY", "Occidental Petroleum", "Warren Buffett"],
    "PSX":   ["Phillips 66", "PSX", "refining"],
    "HAL":   ["Halliburton", "HAL"],

    # ── Renewable Energy & Utilities (9) ──────────────────────────────────────
    "NEE":   ["NextEra Energy", "NEE", "renewable energy"],
    "ENPH":  ["Enphase Energy", "ENPH", "solar"],
    "SEDG":  ["SolarEdge", "SEDG", "solar inverter"],
    "FSLR":  ["First Solar", "FSLR"],
    "RUN":   ["Sunrun", "RUN", "residential solar"],
    "BE":    ["Bloom Energy", "BE", "fuel cell"],
    "CEG":   ["Constellation Energy", "CEG", "nuclear"],
    "VST":   ["Vistra", "VST", "power generation"],
    "AEP":   ["American Electric Power", "AEP", "utility"],

    # ── Healthcare & Pharma (9) ───────────────────────────────────────────────
    "JNJ":   ["Johnson Johnson", "JNJ"],
    "PFE":   ["Pfizer", "PFE"],
    "MRK":   ["Merck", "MRK"],
    "ABBV":  ["AbbVie", "ABBV", "Humira"],
    "LLY":   ["Eli Lilly", "LLY", "Ozempic", "GLP-1"],
    "UNH":   ["UnitedHealth", "UNH", "United Health Group"],
    "CVS":   ["CVS Health", "CVS"],
    "BMY":   ["Bristol Myers Squibb", "BMY"],
    "AMGN":  ["Amgen", "AMGN"],

    # ── Biotech & Medical Devices (9) ─────────────────────────────────────────
    "GILD":  ["Gilead Sciences", "GILD"],
    "REGN":  ["Regeneron", "REGN"],
    "VRTX":  ["Vertex Pharmaceuticals", "VRTX", "cystic fibrosis"],
    "MRNA":  ["Moderna", "MRNA", "mRNA vaccine"],
    "ISRG":  ["Intuitive Surgical", "ISRG", "da Vinci robot"],
    "BSX":   ["Boston Scientific", "BSX"],
    "MDT":   ["Medtronic", "MDT"],
    "SYK":   ["Stryker", "SYK"],
    "EW":    ["Edwards Lifesciences", "EW", "heart valve"],

    # ── Consumer Staples (9) ──────────────────────────────────────────────────
    "KO":    ["Coca-Cola", "KO", "Coke"],
    "PEP":   ["PepsiCo", "PEP", "Pepsi"],
    "PG":    ["Procter Gamble", "PG", "P&G"],
    "COST":  ["Costco", "COST"],
    "WMT":   ["Walmart", "WMT"],
    "MCD":   ["McDonald's", "MCD", "McDonalds"],
    "MDLZ":  ["Mondelez", "MDLZ", "Oreo", "snacks"],
    "CL":    ["Colgate-Palmolive", "CL", "Colgate"],
    "GIS":   ["General Mills", "GIS", "Cheerios"],

    # ── Consumer Discretionary & Retail (9) ───────────────────────────────────
    "NKE":   ["Nike", "NKE"],
    "SBUX":  ["Starbucks", "SBUX", "Brian Niccol"],
    "TGT":   ["Target", "TGT"],
    "HD":    ["Home Depot", "HD"],
    "DIS":   ["Disney", "DIS", "Walt Disney"],
    "RIVN":  ["Rivian", "RIVN"],
    "GM":    ["General Motors", "GM", "Mary Barra"],
    "F":     ["Ford", "F", "Ford Motor", "Jim Farley"],
    "LOW":   ["Lowe's", "LOW"],

    # ── Industrials & Aerospace (9) ───────────────────────────────────────────
    "BA":    ["Boeing", "BA", "airplane", "aircraft"],
    "CAT":   ["Caterpillar", "CAT"],
    "GE":    ["GE Aerospace", "GE", "General Electric"],
    "RTX":   ["RTX", "Raytheon", "defense"],
    "LMT":   ["Lockheed Martin", "LMT", "defense contractor"],
    "HON":   ["Honeywell", "HON"],
    "UPS":   ["UPS", "United Parcel Service", "shipping"],
    "FDX":   ["FedEx", "FDX", "freight"],
    "DE":    ["Deere", "DE", "John Deere", "agriculture"],

    # ── Materials & Mining (9) ────────────────────────────────────────────────
    "NEM":   ["Newmont", "NEM", "gold mining"],
    "FCX":   ["Freeport-McMoRan", "FCX", "copper"],
    "BHP":   ["BHP", "BHP Group", "mining"],
    "RIO":   ["Rio Tinto", "RIO"],
    "AA":    ["Alcoa", "AA", "aluminum"],
    "NUE":   ["Nucor", "NUE", "steel"],
    "X":     ["US Steel", "X", "steel"],
    "LIN":   ["Linde", "LIN", "industrial gas"],
    "APD":   ["Air Products", "APD", "hydrogen"],

    # ── Real Estate (REITs) (9) ───────────────────────────────────────────────
    "PLD":   ["Prologis", "PLD", "logistics REIT"],
    "AMT":   ["American Tower", "AMT", "cell tower REIT"],
    "EQIX":  ["Equinix", "EQIX", "data center REIT"],
    "CCI":   ["Crown Castle", "CCI", "tower REIT"],
    "SPG":   ["Simon Property", "SPG", "mall REIT"],
    "WELL":  ["Welltower", "WELL", "healthcare REIT"],
    "AVB":   ["AvalonBay", "AVB", "apartment REIT"],
    "EQR":   ["Equity Residential", "EQR"],
    "DLR":   ["Digital Realty", "DLR", "data center"],

    # ── Telecommunications (9) ────────────────────────────────────────────────
    "T":     ["AT&T", "T", "telecom"],
    "VZ":    ["Verizon", "VZ"],
    "TMUS":  ["T-Mobile", "TMUS"],
    "LUMN":  ["Lumen Technologies", "LUMN", "fiber"],
    "DISH":  ["DISH Network", "DISH", "satellite"],
    "CHTR":  ["Charter Communications", "CHTR", "Spectrum"],
    "CMCSA": ["Comcast", "CMCSA", "NBCUniversal", "Xfinity"],
    "VOD":   ["Vodafone", "VOD"],
    "SATS":  ["EchoStar", "SATS", "satellite internet"],
}
# ─────────────────────────────────────────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_articles_cache() -> dict:
    if os.path.exists(ARTICLES_CACHE):
        with open(ARTICLES_CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_articles_cache(data: dict):
    with open(ARTICLES_CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def load_scraped_urls() -> set:
    if os.path.exists(SCRAPED_URLS_FILE):
        with open(SCRAPED_URLS_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_scraped_urls(urls: set):
    with open(SCRAPED_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(urls), f)


# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN RATE LIMITER
# ─────────────────────────────────────────────────────────────────────────────

class DomainRateLimiter:
    def __init__(self, max_per_sec: float = 2.0):
        self.interval = 1.0 / max_per_sec
        self.last_hit: dict[str, float] = defaultdict(float)
        self.locks:    dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _domain(self, url: str) -> str:
        try:
            return url.split("/")[2]
        except Exception:
            return url

    async def wait(self, url: str):
        domain = self._domain(url)
        async with self.locks[domain]:
            now     = asyncio.get_event_loop().time()
            elapsed = now - self.last_hit[domain]
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self.last_hit[domain] = asyncio.get_event_loop().time()


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SOURCE_SELECTORS = {
    "reuters.com":       ("div",  {"data-testid": "ArticleBody"}),
    "finance.yahoo.com": ("div",  {"class": re.compile(r"caas-body")}),
    "marketwatch.com":   ("div",  {"class": re.compile(r"article__body")}),
    "benzinga.com":      ("div",  {"class": re.compile(r"article-content-body")}),
    "businesswire.com":  ("div",  {"class": re.compile(r"bw-release-story")}),
    "prnewswire.com":    ("div",  {"class": re.compile(r"release-body")}),
    "cnbc.com":          ("div",  {"class": re.compile(r"ArticleBody")}),
    "fool.com":          ("div",  {"class": re.compile(r"article-body")}),
    "investopedia.com":  ("div",  {"id":    re.compile(r"article-body")}),
}

PAYWALLED = {"wsj.com", "ft.com", "bloomberg.com", "barrons.com", "economist.com"}


def extract_text(html: str, url: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for domain, (tag, attrs) in SOURCE_SELECTORS.items():
        if domain in url:
            container = soup.find(tag, attrs)
            if container:
                text = " ".join(
                    p.get_text(strip=True)
                    for p in container.find_all("p")
                    if len(p.get_text(strip=True)) > 30
                )
                if len(text) >= MIN_TEXT_LENGTH:
                    return text, "specific"
    text = " ".join(
        p.get_text(strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 40
    )
    return (text, "generic") if len(text) >= MIN_TEXT_LENGTH else ("", "stub")


async def scrape_one(session, url, limiter, semaphore):
    if not url or not url.startswith("http"):
        return "", "no_url"
    for d in PAYWALLED:
        if d in url:
            return "", "paywalled"
    async with semaphore:
        await limiter.wait(url)
        try:
            timeout = aiohttp.ClientTimeout(total=SCRAPE_TIMEOUT_SEC)
            async with session.get(url, headers=HEADERS, timeout=timeout) as resp:
                if resp.status != 200:
                    return "", f"http_{resp.status}"
                html = await resp.text(errors="replace")
                return extract_text(html, url)
        except asyncio.TimeoutError:
            return "", "timeout"
        except Exception:
            return "", "failed"


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1
# ─────────────────────────────────────────────────────────────────────────────

def fetch_all_finnhub(tickers: list[str], cache: dict) -> dict:
    remaining = [t for t in tickers if t not in cache]

    if not remaining:
        print(f"\n[Phase 1] All {len(tickers)} tickers cached — skipping!")
        return cache

    print(f"\n[Phase 1] Fetching Finnhub metadata...")
    print(f"          Cached: {len(cache)} | Remaining: {len(remaining)}")

    client   = finnhub.Client(api_key=FINNHUB_API_KEY)
    interval = 60.0 / FINNHUB_CALLS_PER_MIN

    for ticker in tqdm(remaining, desc="Finnhub fetch"):
        articles    = []
        chunk_start = DATE_START

        while chunk_start < DATE_END:
            chunk_end = min(chunk_start + timedelta(days=30), DATE_END)
            try:
                raw = client.company_news(
                    ticker,
                    _from=chunk_start.strftime("%Y-%m-%d"),
                    to=chunk_end.strftime("%Y-%m-%d")
                )
                for item in raw:
                    articles.append({
                        "ticker":         ticker,
                        "company":        TARGET_STOCKS[ticker][0],
                        "headline":       item.get("headline", "").strip(),
                        "url":            item.get("url", "").strip(),
                        "summary":        item.get("summary", "").strip(),
                        "source":         item.get("source", "").strip(),
                        "published_date": datetime.fromtimestamp(
                                              item.get("datetime", 0)
                                          ).strftime("%Y-%m-%d %H:%M:%S"),
                        "full_text":      "",
                        "text_source":    "finnhub_pending"
                    })
            except Exception as e:
                print(f"  [!] Finnhub {ticker}: {e}")

            chunk_start = chunk_end + timedelta(days=1)
            time.sleep(interval)

        seen, unique = set(), []
        for a in articles:
            if a["url"] and a["url"] not in seen:
                seen.add(a["url"])
                unique.append(a)

        cache[ticker] = unique
        print(f"  {ticker}: {len(unique)} articles")
        save_articles_cache(cache)   # saved after every ticker — Ctrl+C safe

    return cache


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2
# ─────────────────────────────────────────────────────────────────────────────

async def scrape_all_articles(all_articles: dict, scraped_urls: set):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCRAPES)
    limiter   = DomainRateLimiter(max_per_sec=MAX_REQUESTS_PER_DOMAIN)

    all_flat  = [a for articles in all_articles.values() for a in articles]
    todo      = [a for a in all_flat if a["url"] not in scraped_urls]
    total     = len(all_flat)
    already   = len(scraped_urls)

    print(f"\n[Phase 2] Scraping...")
    print(f"          Total: {total} | Already done: {already} | Remaining: {len(todo)}")
    print(f"          Concurrency: {MAX_CONCURRENT_SCRAPES} | Per-domain: {MAX_REQUESTS_PER_DOMAIN} req/sec")

    if not todo:
        print("  All articles already scraped!")
        return

    stats       = {"saved": 0, "full_text": 0, "paywalled": 0}
    file_exists = os.path.exists(OUTPUT_CSV)
    fieldnames  = ["ticker", "company", "headline", "url", "summary",
                   "full_text", "published_date", "source", "text_source"]

    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_SCRAPES, ssl=False)

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        async with aiohttp.ClientSession(connector=connector) as session:

            async def process_one(article: dict):
                text, label = await scrape_one(session, article["url"], limiter, semaphore)
                article["full_text"]   = text
                article["text_source"] = f"finnhub_{label}"
                writer.writerow(article)
                csvfile.flush()
                scraped_urls.add(article["url"])
                stats["saved"] += 1
                if len(text) >= MIN_TEXT_LENGTH:
                    stats["full_text"] += 1
                if label == "paywalled":
                    stats["paywalled"] += 1
                if stats["saved"] % SAVE_INTERVAL == 0:
                    save_scraped_urls(scraped_urls)

            batch_size = 200
            for i in range(0, len(todo), batch_size):
                batch = todo[i : i + batch_size]
                await asyncio.gather(*[process_one(a) for a in batch])
                done_total = already + stats["saved"]
                pct = 100 * done_total // total
                print(f"  Progress: {done_total}/{total} ({pct}%) | "
                      f"Full text: {stats['full_text']} | "
                      f"Paywalled: {stats['paywalled']}")

    save_scraped_urls(scraped_urls)
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 65)
    print("  StockSense AI — Collector v5")
    print(f"  Date range   : {DATE_START.date()} -> {DATE_END.date()}")
    print(f"  Total tickers: {len(TARGET_STOCKS)}")
    print(f"  Output       : {OUTPUT_CSV}")
    print("=" * 65)

    # Phase 1
    cache = load_articles_cache()
    if cache:
        print(f"\n  Phase 1 cache found: {len(cache)}/{len(TARGET_STOCKS)} tickers already fetched")

    try:
        all_articles = fetch_all_finnhub(list(TARGET_STOCKS.keys()), cache)
    except KeyboardInterrupt:
        print("\n  Interrupted in Phase 1. Progress saved to articles_cache.json")
        print("   Re-run to continue from where you stopped.")
        sys.exit(0)

    total_found = sum(len(v) for v in all_articles.values())
    print(f"\n  Total articles: {total_found}")

    # Phase 2
    scraped_urls = load_scraped_urls()
    if scraped_urls:
        print(f"  Phase 2 progress found: {len(scraped_urls)} URLs already scraped")

    try:
        await scrape_all_articles(all_articles, scraped_urls)
    except KeyboardInterrupt:
        print(f"\n  Interrupted in Phase 2. Saving progress...")
        save_scraped_urls(scraped_urls)
        print(f"   Re-run to continue. No data lost.")
        sys.exit(0)

    # Final summary
    print("\n" + "=" * 65)
    print("  COLLECTION COMPLETE")
    df       = pd.read_csv(OUTPUT_CSV)
    df       = df.drop_duplicates(subset="url")
    has_text = (df["full_text"].str.len() > MIN_TEXT_LENGTH).sum()
    print(f"  Total rows       : {len(df)}")
    print(f"  With full text   : {has_text} ({100*has_text//max(len(df),1)}%)")
    print(f"  No text / stubs  : {len(df) - has_text}")
    print(f"\n  Top 10 tickers:")
    print(df.groupby("ticker")["headline"].count()
            .sort_values(ascending=False).head(10).to_string())
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())