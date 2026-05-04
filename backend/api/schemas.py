"""
Pydantic schemas for all API request/response bodies.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class TechnicalOut(BaseModel):
    rsi_14: float | None = Field(None, description="14-period RSI (0–100)")
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    close: float | None = None
    bb_pct: float | None = Field(None, description="Bollinger Band %B (0–1)")
    volume_ratio: float | None = Field(None, description="Current vol / 10-day avg vol")
    rsi_signal: int = Field(0, description="+1 oversold, -1 overbought, 0 neutral")
    macd_cross: int = Field(0, description="+1 bull cross, -1 bear cross, 0 none")
    trend_signal: int = Field(0, description="+1 uptrend, -1 downtrend, 0 sideways")


class HeadlineOut(BaseModel):
    headline: str
    source: str
    date: str
    sentiment: int = Field(description="+1 positive, -1 negative, 0 neutral")
    score: float


class SentimentOut(BaseModel):
    news_score: float = Field(description="Weighted FinBERT score (-1 to +1)")
    news_count: int
    reddit_score: float
    reddit_count: int
    twit_score: float
    twit_count: int
    composite: float = Field(description="Overall composite sentiment (-1 to +1)")
    top_headlines: list[HeadlineOut] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    symbol: str
    direction: str = Field(description="'UP', 'DOWN', or 'STABLE'")
    confidence: float = Field(description="0.0 – 1.0")
    raw_score: float = Field(description="-1.0 – +1.0 composite signal")
    as_of_date: str
    technical: TechnicalOut
    sentiment: SentimentOut
    explanation: str


class SentimentResponse(BaseModel):
    symbol: str
    sentiment: SentimentOut
    as_of_date: str


class StockResponse(BaseModel):
    symbol: str
    company_name: str | None = None
    sector: str | None = None
    latest_close: float | None = None
    as_of_date: str | None = None
    daily_return_pct: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    volume_ratio: float | None = None
    price_direction_3class: int | None = None   # -1 / 0 / +1


class HistoryPoint(BaseModel):
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None
    rsi_14: float | None = None
    macd: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    daily_return_pct: float | None = None


class HistoryResponse(BaseModel):
    symbol: str
    period_days: int
    data: list[HistoryPoint]


class SymbolsResponse(BaseModel):
    total: int
    symbols: list[str]


class HealthResponse(BaseModel):
    status: str
    symbols_loaded: int
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    detail: str
