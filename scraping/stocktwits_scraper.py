import cloudscraper
import time
import random
import csv
from datetime import datetime

########
# CONFIG
########

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
# StockTwits API endpoint
BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
OUTPUT_FILE = f"SQstocktwits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


######################
# SENTIMENT EXTRACTION
######################

def get_sentiment(msg):
    entities = msg.get("entities")

    if not isinstance(entities, dict):
        return None

    sentiment = entities.get("sentiment")

    if not isinstance(sentiment, dict):
        return None

    return sentiment.get("basic")


#########
# SCRAPER
#########

def fetch_stocktwits(symbol: str, limit: int = 200):
    url = BASE_URL.format(symbol=symbol)

    # cloudscraper for anti bot bypass
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False
        }
    )

    # pagination loop with deduplication
    all_messages = []
    seen_ids = set()
    max_id = None

    print(f"\n🔍 Scraping {symbol}")

    while len(all_messages) < limit:

        params = {}

        if max_id:
            params["max"] = max_id

        try:
            response = scraper.get(url, params=params, timeout=15)

            if response.status_code != 200:
                print(f"❌ Blocked ({response.status_code})")
                break

            data = response.json()

        except Exception as e:
            print(f"❌ Error: {e}")
            break

        messages = data.get("messages")

        if not isinstance(messages, list) or len(messages) == 0:
            break

        for msg in messages:

            text = msg.get("body") or ""
            msg_id = msg.get("id")

            if msg_id in seen_ids:
                continue

            seen_ids.add(msg_id)

            #####################
            # FEATURE ENGINEERING
            #####################

            text_lower = text.lower()

            words = text.split()

            has_url = 1 if "http" in text_lower else 0

            has_cashtag = 1 if "$" in text else 0

            cashtag_count = text.count("$")

            word_count = len(words)

            text_length = len(text)

            is_noise = 1 if word_count <= 5 or text.strip().startswith("$") else 0

            # crude post timing features (no API change needed)
            created_at = msg.get("created_at")
            post_date = created_at.split("T")[0] if created_at else None

            # simple hour bucket (safe fallback)
            post_hour = "unknown"
            if created_at and "T" in created_at:
                hour = int(created_at.split("T")[1][:2])
                if 4 <= hour < 9:
                    post_hour = "pre_market"
                elif 9 <= hour < 16:
                    post_hour = "market"
                else:
                    post_hour = "after_hours"

            all_messages.append({
                # existing
                "symbol": symbol,
                "text": text,
                "created_at": created_at,
                "username": (msg.get("user") or {}).get("username"),
                "sentiment": get_sentiment(msg),

                # new features
                "post_date": post_date,
                "post_hour": post_hour,
                "text_length": text_length,
                "word_count": word_count,
                "has_cashtag": has_cashtag,
                "cashtag_count": cashtag_count,
                "has_url": has_url,
                "is_noise": is_noise,

                # Phase 2 placeholders
                "finbert_sentiment": None,
                "finbert_score": None,
            })

        max_id = messages[-1].get("id", 0) - 1

        time.sleep(1.2)

    print(f"📊 Collected: {len(all_messages)}")
    return all_messages[:limit]

def safe_text(text):
    """
    Cleans encoding issues:
    - HTML entities (&#39; → ')
    - emojis-safe UTF-8 cleanup
    """
    if text is None:
        return ""

    text = str(text)

    # FIX HTML ENTITY
    text = text.replace("&#39;", "'")

    # Optional extra common entities
    text = text.replace("&amp;", "&")
    text = text.replace("&quot;", '"')
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    # UTF-8 safety
    return text.encode("utf-8", "ignore").decode("utf-8")

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
            # sanitize all string fields
            clean_row = {k: safe_text(v) for k, v in row.items()}
            writer.writerow(clean_row)

    print(f"\n💾 Saved → {OUTPUT_FILE}")

###############
# MAIN PIPELINE
###############

def main():
    all_data = []

    for symbol, keywords in TARGET_STOCKS.items():

        data = fetch_stocktwits(symbol, limit=200)

        all_data.extend(data)

        time.sleep(7)

    print("\n🚀 TOTAL RECORDS:", len(all_data))

    save_csv(all_data)

    print("\n📌 SAMPLE:")
    for item in all_data[:5]:
        print(item)


if __name__ == "__main__":
    main()