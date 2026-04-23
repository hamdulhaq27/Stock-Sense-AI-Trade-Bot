import cloudscraper
import time
import random
import csv
from datetime import datetime

########
# CONFIG
########

TARGET_STOCKS = {
    "AAPL":  ["Apple", "AAPL", "iPhone", "Tim Cook"],
    "TSLA":  ["Tesla", "TSLA", "Elon Musk", "electric vehicle"],
    "AMZN":  ["Amazon", "AMZN", "AWS", "Andy Jassy"],
    "MSFT":  ["Microsoft", "MSFT", "Azure", "Satya Nadella"],
    "NVDA":  ["Nvidia", "NVDA", "GPU", "Jensen Huang"],
    "GOOGL": ["Google", "Alphabet", "GOOGL", "Sundar Pichai"],
    "META":  ["Meta", "Facebook", "META", "Zuckerberg"],
    "JPM":   ["JPMorgan", "JPM", "Jamie Dimon"],
    "NFLX":  ["Netflix", "NFLX", "streaming"],
    "AMD":   ["AMD", "Advanced Micro Devices", "Lisa Su"],
    "UBER":  ["Uber", "UBER", "rideshare"],
    "DIS":   ["Disney", "DIS", "Walt Disney"],
}

# StockTwits API endpoint
BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
OUTPUT_FILE = f"stocktwits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


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

        time.sleep(random.uniform(1.5, 3.5))

    print("\n🚀 TOTAL RECORDS:", len(all_data))

    save_csv(all_data)

    print("\n📌 SAMPLE:")
    for item in all_data[:5]:
        print(item)


if __name__ == "__main__":
    main()