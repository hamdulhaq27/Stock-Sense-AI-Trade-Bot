"""
/batch routes — predict multiple symbols in one call
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.schemas import PredictionResponse, TechnicalOut, SentimentOut, HeadlineOut
from core.predictor import predict
from data.loader import symbol_exists, get_all_symbols
from utils.cache import prediction_cache

router = APIRouter(prefix="/batch", tags=["Batch"])

MAX_SYMBOLS = 20


class BatchRequest(BaseModel):
    symbols: list[str] = Field(..., min_length=1, max_length=MAX_SYMBOLS)


class BatchItem(BaseModel):
    symbol: str
    success: bool
    error: str | None = None
    prediction: PredictionResponse | None = None


class BatchResponse(BaseModel):
    requested: int
    succeeded: int
    failed: int
    results: list[BatchItem]


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
            rsi_14=t.rsi_14, macd=t.macd, macd_signal=t.macd_signal,
            macd_histogram=t.macd_histogram, sma_20=t.sma_20, sma_50=t.sma_50,
            close=t.close, bb_pct=t.bb_pct, volume_ratio=t.volume_ratio,
            rsi_signal=t.rsi_signal, macd_cross=t.macd_cross, trend_signal=t.trend_signal,
        ),
        sentiment=SentimentOut(
            news_score=s.news_score, news_count=s.news_count,
            reddit_score=s.reddit_score, reddit_count=s.reddit_count,
            twit_score=s.twit_score, twit_count=s.twit_count,
            composite=s.composite,
            top_headlines=[HeadlineOut(**h) for h in s.top_headlines],
        ),
    )


@router.post("/predict", response_model=BatchResponse, summary="Predict multiple symbols at once")
async def batch_predict(body: BatchRequest):
    """
    Accepts up to 20 symbols. Each is predicted independently.
    Cached results are returned instantly; fresh predictions are computed inline.
    """
    results = []
    ok = 0
    fail = 0

    for sym in body.symbols:
        sym = sym.upper()
        if not symbol_exists(sym):
            results.append(BatchItem(symbol=sym, success=False, error="Symbol not found"))
            fail += 1
            continue

        cache_key = f"pred:{sym}"
        cached = prediction_cache.get(cache_key)
        if cached:
            results.append(BatchItem(symbol=sym, success=True, prediction=cached))
            ok += 1
            continue

        try:
            result = predict(sym)
            if result is None:
                raise ValueError("Insufficient data")
            resp = _to_response(result)
            prediction_cache.set(cache_key, resp)
            results.append(BatchItem(symbol=sym, success=True, prediction=resp))
            ok += 1
        except Exception as exc:
            results.append(BatchItem(symbol=sym, success=False, error=str(exc)))
            fail += 1

    return BatchResponse(
        requested=len(body.symbols),
        succeeded=ok,
        failed=fail,
        results=results,
    )


@router.get("/top", response_model=BatchResponse, summary="Top-N predictions across all symbols")
async def top_predictions(
    n: int = 10,
    direction: str | None = None,
):
    """
    Runs predictions for all symbols and returns the top-N by confidence.
    Optionally filter by direction: UP / DOWN / STABLE.
    """
    if n > 50:
        raise HTTPException(status_code=400, detail="n must be ≤ 50")

    all_syms = get_all_symbols()
    results = []

    for sym in all_syms:
        cache_key = f"pred:{sym}"
        cached = prediction_cache.get(cache_key)
        if cached:
            results.append(BatchItem(symbol=sym, success=True, prediction=cached))
            continue
        try:
            result = predict(sym)
            if result:
                resp = _to_response(result)
                prediction_cache.set(cache_key, resp)
                results.append(BatchItem(symbol=sym, success=True, prediction=resp))
        except Exception:
            pass

    # Filter
    if direction:
        direction = direction.upper()
        results = [r for r in results if r.prediction and r.prediction.direction == direction]

    # Sort by confidence desc
    results.sort(key=lambda r: r.prediction.confidence if r.prediction else 0, reverse=True)
    results = results[:n]

    return BatchResponse(
        requested=len(all_syms),
        succeeded=len(results),
        failed=0,
        results=results,
    )
