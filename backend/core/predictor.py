"""
Prediction engine: merges technical indicators, news sentiment, Reddit
sentiment, and StockTwits sentiment into a weighted composite signal,
then produces a directional forecast (UP / DOWN / STABLE) with a
confidence score.

No external ML library is required for inference — the logic is a
transparent, rule-based ensemble so the API starts instantly without
loading a PyTorch / TF model. If you train an LSTM (see notebook), drop
in _lstm_predict() and swap it into predict().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

from data.loader import (
    get_news_data,
    get_reddit_data,
    get_stock_data,
    get_stocktwits_data,
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TechnicalSignal:
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    above_sma_20: int | None = None
    above_sma_50: int | None = None
    golden_cross: int | None = None
    bb_pct: float | None = None          # Bollinger Band %B
    close: float | None = None
    volume_ratio: float | None = None
    # Derived interpretation
    rsi_signal: int = 0                  # +1 oversold (bull), -1 overbought (bear), 0 neutral
    macd_cross: int = 0                  # +1 bull cross, -1 bear cross, 0 none
    trend_signal: int = 0                # +1 uptrend, -1 downtrend, 0 sideways


@dataclass
class SentimentSignal:
    news_score: float = 0.0             # -1 to +1
    news_count: int = 0
    reddit_score: float = 0.0
    reddit_count: int = 0
    twit_score: float = 0.0
    twit_count: int = 0
    composite: float = 0.0              # weighted average
    top_headlines: list[dict] = field(default_factory=list)


@dataclass
class PredictionResult:
    symbol: str
    direction: str                       # "UP" | "DOWN" | "STABLE"
    confidence: float                    # 0.0 – 1.0
    raw_score: float                     # -1.0 – +1.0
    as_of_date: str
    technical: TechnicalSignal
    sentiment: SentimentSignal
    explanation: str


# ---------------------------------------------------------------------------
# Technical signal extraction
# ---------------------------------------------------------------------------

def _extract_technical(symbol: str, lookback: int = 5) -> TechnicalSignal | None:
    stock_df = get_stock_data()
    sym_df = stock_df[stock_df["symbol"] == symbol].sort_values("date")
    if sym_df.empty:
        return None

    row = sym_df.iloc[-1]                # most recent row

    sig = TechnicalSignal(
        rsi_14=_safe(row, "rsi_14"),
        macd=_safe(row, "macd"),
        macd_signal=_safe(row, "macd_signal"),
        macd_histogram=_safe(row, "macd_histogram"),
        sma_20=_safe(row, "sma_20"),
        sma_50=_safe(row, "sma_50"),
        above_sma_20=_safe_int(row, "above_sma_20"),
        above_sma_50=_safe_int(row, "above_sma_50"),
        golden_cross=_safe_int(row, "golden_cross"),
        bb_pct=_safe(row, "bb_pct"),
        close=_safe(row, "close"),
        volume_ratio=_safe(row, "volume_ratio"),
    )

    # RSI interpretation
    if sig.rsi_14 is not None:
        if sig.rsi_14 < 30:
            sig.rsi_signal = +1           # oversold → bullish
        elif sig.rsi_14 > 70:
            sig.rsi_signal = -1           # overbought → bearish

    # MACD cross (compare last two rows)
    if len(sym_df) >= 2:
        prev = sym_df.iloc[-2]
        prev_hist = _safe(prev, "macd_histogram")
        curr_hist = sig.macd_histogram
        if prev_hist is not None and curr_hist is not None:
            if prev_hist < 0 and curr_hist > 0:
                sig.macd_cross = +1
            elif prev_hist > 0 and curr_hist < 0:
                sig.macd_cross = -1

    # Trend
    a20 = sig.above_sma_20 if sig.above_sma_20 is not None else 0
    a50 = sig.above_sma_50 if sig.above_sma_50 is not None else 0
    sig.trend_signal = round((a20 + a50 - 1))   # -1 / 0 / +1

    return sig


# ---------------------------------------------------------------------------
# Sentiment extraction
# ---------------------------------------------------------------------------

# Reddit raw scores span roughly -10..+10 (post-weighted compound scores).
# We normalise them to -1..+1 using tanh so the scale matches news/twits.
_REDDIT_SCALE = 3.0   # controls how aggressively tanh compresses the range


def _norm_reddit(score: float) -> float:
    """Normalise a raw Reddit compound score to (-1, +1) via tanh."""
    return math.tanh(score / _REDDIT_SCALE)


def _extract_sentiment(symbol: str, window_days: int = 7) -> SentimentSignal:
    """
    Extract and normalise sentiment from three sources.

    All returned scores are in the range (-1, +1):
      news_score   – confidence-weighted FinBERT mean
      reddit_score – tanh-normalised compound score mean
      twit_score   – already in (-1, +1), used as-is
      composite    – weighted average of the above (news 50%, reddit 25%, twit 25%)

    Window strategy: use the most recent `window_days` of data relative to
    each source's own latest date, not relative to today's wall-clock time.
    This handles datasets that are frozen in time without returning zeros.
    """
    sig = SentimentSignal()

    # --- News ---
    news_df = get_news_data()
    sym_news = news_df[news_df["symbol"] == symbol]
    if not sym_news.empty and "finbert_score" in sym_news.columns and "finbert_sentiment" in sym_news.columns:
        # Use window relative to the dataset's own latest date
        latest_news_date = sym_news["date"].max()
        cutoff_news = latest_news_date - pd.Timedelta(days=window_days)
        ns = sym_news[sym_news["date"] >= cutoff_news]
        if ns.empty:
            ns = sym_news   # fallback: all data for this symbol

        # Confidence-weighted mean of directional scores:
        # finbert_sentiment ∈ {-1, 0, +1}, finbert_score ∈ (0, 1)
        # weighted_score_i = sentiment_i × score_i  →  sum / sum(scores)
        total_conf = ns["finbert_score"].sum()
        if total_conf > 0:
            weighted_sum = (ns["finbert_sentiment"] * ns["finbert_score"]).sum()
            sig.news_score = float(weighted_sum / total_conf)   # in (-1, +1)
        else:
            sig.news_score = float(ns["finbert_sentiment"].mean())

        sig.news_count = len(ns)

        # Top headlines: highest-confidence ones
        top = ns.sort_values("finbert_score", ascending=False).head(5)
        sig.top_headlines = [
            {
                "headline": str(r.get("headline", "")),
                "source": str(r.get("source", "")),
                "date": str(r.get("date", ""))[:10],
                "sentiment": int(r.get("finbert_sentiment", 0)),
                "score": round(float(r.get("finbert_score", 0)), 3),
            }
            for _, r in top.iterrows()
        ]

    # --- Reddit ---
    reddit_df = get_reddit_data()
    sym_reddit = reddit_df[reddit_df["symbol"] == symbol]
    if not sym_reddit.empty:
        latest_reddit_date = sym_reddit["date"].max()
        cutoff_reddit = latest_reddit_date - pd.Timedelta(days=window_days)
        rs = sym_reddit[sym_reddit["date"] >= cutoff_reddit]
        if rs.empty:
            rs = sym_reddit   # fallback

        # Weight each day's score by post count so noisy low-volume days matter less
        post_counts = rs["reddit_post_count"].clip(lower=1)
        raw_weighted = (rs["reddit_sentiment"] * post_counts).sum() / post_counts.sum()
        sig.reddit_score = float(_norm_reddit(raw_weighted))   # normalise to (-1, +1)
        sig.reddit_count = int(rs["reddit_post_count"].sum())

    # --- StockTwits ---
    twit_df = get_stocktwits_data()
    sym_twit = twit_df[twit_df["symbol"] == symbol]
    if not sym_twit.empty:
        latest_twit_date = sym_twit["date"].max()
        cutoff_twit = latest_twit_date - pd.Timedelta(days=window_days)
        ts = sym_twit[sym_twit["date"] >= cutoff_twit]
        if ts.empty:
            ts = sym_twit   # fallback

        # StockTwits scores are already in (-1, +1); weight by post count
        post_counts = ts["twit_post_count"].clip(lower=1)
        sig.twit_score = float(
            (ts["twit_sentiment"] * post_counts).sum() / post_counts.sum()
        )
        sig.twit_count = int(ts["twit_post_count"].sum())

    # --- Composite (news 50%, reddit 25%, twit 25%) ---
    weights: list[float] = []
    scores: list[float] = []
    if sig.news_count > 0:
        weights.append(0.50); scores.append(sig.news_score)
    if sig.reddit_count > 0:
        weights.append(0.25); scores.append(sig.reddit_score)
    if sig.twit_count > 0:
        weights.append(0.25); scores.append(sig.twit_score)

    if weights:
        total_w = sum(weights)
        sig.composite = sum(s * w for s, w in zip(scores, weights)) / total_w
        sig.composite = max(-1.0, min(1.0, sig.composite))   # clamp

    return sig


# ---------------------------------------------------------------------------
# Core prediction logic
# ---------------------------------------------------------------------------

def predict(symbol: str) -> PredictionResult | None:
    symbol = symbol.upper()
    tech = _extract_technical(symbol)
    sent = _extract_sentiment(symbol)

    if tech is None and sent.news_count == 0:
        return None

    # ------------------------------------------------------------------
    # Build composite score (-1 .. +1)
    # ------------------------------------------------------------------
    components: list[tuple[float, float]] = []   # (value, weight)

    # Technical sub-score
    tech_score = 0.0
    tech_weight = 0.0
    if tech is not None:
        # RSI contribution
        if tech.rsi_14 is not None:
            rsi_norm = _rsi_to_score(tech.rsi_14)
            components.append((rsi_norm, 0.15))
            tech_score += rsi_norm * 0.15
            tech_weight += 0.15

        # MACD cross
        if tech.macd_cross != 0:
            components.append((float(tech.macd_cross), 0.15))
            tech_score += tech.macd_cross * 0.15
            tech_weight += 0.15
        elif tech.macd_histogram is not None:
            # use magnitude-normalised histogram direction
            macd_dir = math.copysign(min(abs(tech.macd_histogram) / 2.0, 1.0), tech.macd_histogram)
            components.append((macd_dir, 0.10))
            tech_score += macd_dir * 0.10
            tech_weight += 0.10

        # Trend (SMA)
        components.append((float(tech.trend_signal), 0.10))
        tech_score += tech.trend_signal * 0.10
        tech_weight += 0.10

        # Bollinger band (price near lower band → bullish; near upper → bearish)
        if tech.bb_pct is not None:
            bb_score = -(tech.bb_pct - 0.5) * 2          # maps 0→+1, 0.5→0, 1→-1
            components.append((bb_score, 0.05))
            tech_score += bb_score * 0.05
            tech_weight += 0.05

    # Sentiment contribution (total weight = 0.55)
    if sent.news_count > 0 or sent.reddit_count > 0 or sent.twit_count > 0:
        components.append((sent.composite, 0.55))
        raw_score = tech_score + sent.composite * 0.55
        total_w = tech_weight + 0.55
    else:
        raw_score = tech_score
        total_w = tech_weight

    raw_score = raw_score / total_w if total_w > 0 else 0.0
    raw_score = max(-1.0, min(1.0, raw_score))

    # ------------------------------------------------------------------
    # Direction & confidence
    # ------------------------------------------------------------------
    UP_THRESH = 0.10
    DOWN_THRESH = -0.10

    if raw_score >= UP_THRESH:
        direction = "UP"
    elif raw_score <= DOWN_THRESH:
        direction = "DOWN"
    else:
        direction = "STABLE"

    # Confidence: sigmoid-like mapping of |raw_score| → [0.5, 1.0]
    confidence = 0.5 + 0.5 * (1 - math.exp(-3 * abs(raw_score)))
    confidence = round(confidence, 4)

    explanation = _build_explanation(direction, tech, sent, raw_score)

    # Latest date from stock data
    stock_df = get_stock_data()
    sym_df = stock_df[stock_df["symbol"] == symbol]
    as_of = str(sym_df["date"].max())[:10] if not sym_df.empty else "N/A"

    return PredictionResult(
        symbol=symbol,
        direction=direction,
        confidence=confidence,
        raw_score=round(raw_score, 4),
        as_of_date=as_of,
        technical=tech or TechnicalSignal(),
        sentiment=sent,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rsi_to_score(rsi: float) -> float:
    """Maps RSI (0-100) to a score in (-1, +1)."""
    # oversold (<30) → positive; overbought (>70) → negative; neutral → 0
    if rsi < 30:
        return (30 - rsi) / 30           # 0 to +1
    elif rsi > 70:
        return -(rsi - 70) / 30          # 0 to -1
    else:
        return (50 - rsi) / 40           # slight mean-reversion bias


def _safe(row: pd.Series, col: str) -> float | None:
    val = row.get(col)
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(row: pd.Series, col: str) -> int | None:
    val = _safe(row, col)
    return int(val) if val is not None else None


def _build_explanation(
    direction: str,
    tech: TechnicalSignal | None,
    sent: SentimentSignal,
    score: float,
) -> str:
    parts = []
    if tech:
        if tech.rsi_14 is not None:
            parts.append(f"RSI={tech.rsi_14:.1f} ({'oversold' if tech.rsi_14 < 30 else 'overbought' if tech.rsi_14 > 70 else 'neutral'})")
        if tech.macd_cross == 1:
            parts.append("MACD bullish crossover")
        elif tech.macd_cross == -1:
            parts.append("MACD bearish crossover")
        if tech.trend_signal == 1:
            parts.append("price above both SMAs (uptrend)")
        elif tech.trend_signal == -1:
            parts.append("price below both SMAs (downtrend)")
    if sent.news_count > 0:
        label = "positive" if sent.news_score > 0.05 else "negative" if sent.news_score < -0.05 else "neutral"
        parts.append(f"news sentiment {label} ({sent.news_count} articles)")
    if sent.reddit_count > 0:
        parts.append(f"Reddit sentiment {sent.reddit_score:+.2f} ({sent.reddit_count} posts)")
    if sent.twit_count > 0:
        parts.append(f"StockTwits sentiment {sent.twit_score:+.2f} ({sent.twit_count} posts)")

    body = "; ".join(parts) if parts else "insufficient data"
    return f"Predicted {direction} (composite score {score:+.3f}). Signals: {body}."