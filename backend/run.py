#!/usr/bin/env python3
"""
python run.py               — dev server with auto-reload
python run.py --prod        — production server (4 workers)
python run.py --test AAPL   — print a prediction to the terminal
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="StockSense AI runner")
    parser.add_argument("--prod", action="store_true", help="Run in production mode")
    parser.add_argument("--test", metavar="SYMBOL", help="Print prediction for SYMBOL and exit")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.test:
        # CLI smoke-test
        sys.path.insert(0, ".")
        from core.predictor import predict
        sym = args.test.upper()
        result = predict(sym)
        if result is None:
            print(f"❌  No data for {sym}")
            sys.exit(1)
        print(f"\n{'='*60}")
        print(f"  StockSense AI — {sym}")
        print(f"{'='*60}")
        print(f"  Direction  : {result.direction}")
        print(f"  Confidence : {result.confidence:.1%}")
        print(f"  Raw Score  : {result.raw_score:+.4f}")
        print(f"  As of      : {result.as_of_date}")
        print(f"\n  Technical")
        t = result.technical
        print(f"    RSI-14   : {t.rsi_14}")
        print(f"    MACD     : {t.macd}")
        print(f"    SMA-20   : {t.sma_20}")
        print(f"    SMA-50   : {t.sma_50}")
        print(f"\n  Sentiment  (composite {result.sentiment.composite:+.4f})")
        print(f"    News     : {result.sentiment.news_score:+.4f}  ({result.sentiment.news_count} articles)")
        print(f"    Reddit   : {result.sentiment.reddit_score:+.4f}  ({result.sentiment.reddit_count} posts)")
        print(f"    Twits    : {result.sentiment.twit_score:+.4f}  ({result.sentiment.twit_count} posts)")
        print(f"\n  {result.explanation}")
        print(f"{'='*60}\n")
        return

    import uvicorn
    if args.prod:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            workers=4,
        )
    else:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=True,
        )

if __name__ == "__main__":
    main()
