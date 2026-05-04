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

                time.sleep(7)

    # Save data
    save_csv(all_rows)


if __name__ == "__main__":
    main()