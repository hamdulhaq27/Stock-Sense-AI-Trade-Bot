"""
/predict routes
"""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query

from api.schemas import PredictionResponse, SentimentResponse, TechnicalOut, SentimentOut, HeadlineOut
from core.predictor import predict, _extract_sentiment
from data.loader import symbol_exists
from utils.cache import prediction_cache, sentiment_cache

router = APIRouter(prefix="/predict", tags=["Prediction"])


def _to_response(result) -> PredictionResponse:
    t = result.technical
    s = result.sentiment
    return PredictionResponse(
        symbol=result.symbol,
        direction=result.direction,
        confidence=result.confidence,
        raw_score=result.raw_score,
        as_of_date=result.as_of_date,
        explanation=result.explanation,
        technical=TechnicalOut(
            rsi_14=t.rsi_14,
            macd=t.macd,
            macd_signal=t.macd_signal,
            macd_histogram=t.macd_histogram,
            sma_20=t.sma_20,
            sma_50=t.sma_50,
            close=t.close,
            bb_pct=t.bb_pct,
            volume_ratio=t.volume_ratio,
            rsi_signal=t.rsi_signal,
            macd_cross=t.macd_cross,
            trend_signal=t.trend_signal,
        ),
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


@router.get("/{symbol}", response_model=PredictionResponse, summary="Get directional prediction for a stock")
async def get_prediction(
    symbol: str,
    refresh: bool = Query(False, description="Force bypass cache"),
):
    """
    Returns UP / DOWN / STABLE prediction with confidence score,
    composite sentiment, and technical indicator summary.
    """
    symbol = symbol.upper()
    if not symbol_exists(symbol):
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in dataset.")

    cache_key = f"pred:{symbol}"
    if not refresh:
        cached = prediction_cache.get(cache_key)
        if cached:
            return cached

    result = predict(symbol)
    if result is None:
        raise HTTPException(status_code=422, detail=f"Insufficient data to predict '{symbol}'.")

    response = _to_response(result)
    prediction_cache.set(cache_key, response)
    return response
