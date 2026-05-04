"""
/sentiment routes — raw sentiment breakdown without price prediction
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas import SentimentOut, HeadlineOut, SentimentResponse
from core.predictor import _extract_sentiment
from data.loader import symbol_exists, get_news_data
from utils.cache import sentiment_cache

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.get("/{symbol}", response_model=SentimentResponse, summary="Sentiment breakdown for a symbol")
async def get_sentiment(
    symbol: str,
    window_days: int = Query(7, ge=1, le=90, description="Look-back window in days"),
):
    symbol = symbol.upper()
    if not symbol_exists(symbol):
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found.")

    cache_key = f"sent:{symbol}:{window_days}"
    cached = sentiment_cache.get(cache_key)
    if cached:
        return cached

    s = _extract_sentiment(symbol, window_days=window_days)

    # Latest date with news coverage
    news_df = get_news_data()
    sym_news = news_df[news_df["symbol"] == symbol]
    as_of = str(sym_news["date"].max())[:10] if not sym_news.empty else "N/A"

    response = SentimentResponse(
        symbol=symbol,
        as_of_date=as_of,
        sentiment=SentimentOut(
            news_score=s.news_score,
            news_count=s.news_count,
            reddit_score=s.reddit_score,
            reddit_count=s.reddit_count,
            twit_score=s.twit_score,
            twit_count=s.twit_count,
            composite=s.composite,
            top_headlines=[HeadlineOut(**h) for h in s.top_headlines],
        ),
    )
    sentiment_cache.set(cache_key, response)
    return response
