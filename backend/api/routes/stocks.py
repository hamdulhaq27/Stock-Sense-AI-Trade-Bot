"""
/stocks routes — historical price data and latest snapshot
"""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Query

from api.schemas import StockResponse, HistoryResponse, HistoryPoint, SymbolsResponse
from data.loader import get_stock_data, get_all_symbols, symbol_exists

router = APIRouter(prefix="/stocks", tags=["Stock Data"])


def _clean_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _clean_int(val) -> int | None:
    f = _clean_float(val)
    return int(f) if f is not None else None


@router.get("/", response_model=SymbolsResponse, summary="List all available symbols")
async def list_symbols(
    search: str | None = Query(None, description="Filter by prefix, e.g. 'AA'"),
):
    syms = get_all_symbols()
    if search:
        syms = [s for s in syms if s.startswith(search.upper())]
    return SymbolsResponse(total=len(syms), symbols=syms)


@router.get("/{symbol}", response_model=StockResponse, summary="Latest snapshot for a symbol")
async def get_latest(symbol: str):
    symbol = symbol.upper()
    if not symbol_exists(symbol):
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found.")

    df = get_stock_data()
    sym_df = df[df["symbol"] == symbol].sort_values("date")
    if sym_df.empty:
        raise HTTPException(status_code=404, detail="No stock data available.")

    row = sym_df.iloc[-1]
    return StockResponse(
        symbol=symbol,
        company_name=row.get("company_name"),
        sector=row.get("sector"),
        latest_close=_clean_float(row.get("close")),
        as_of_date=str(row.get("date", ""))[:10],
        daily_return_pct=_clean_float(row.get("daily_return_pct")),
        rsi_14=_clean_float(row.get("rsi_14")),
        macd=_clean_float(row.get("macd")),
        sma_20=_clean_float(row.get("sma_20")),
        sma_50=_clean_float(row.get("sma_50")),
        volume_ratio=_clean_float(row.get("volume_ratio")),
        price_direction_3class=_clean_int(row.get("price_direction_3class")),
    )


@router.get("/{symbol}/history", response_model=HistoryResponse, summary="OHLCV + indicator history")
async def get_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of trading days to return"),
):
    symbol = symbol.upper()
    if not symbol_exists(symbol):
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found.")

    df = get_stock_data()
    sym_df = df[df["symbol"] == symbol].sort_values("date").tail(days)

    if sym_df.empty:
        raise HTTPException(status_code=404, detail="No history available.")

    points = []
    for _, row in sym_df.iterrows():
        points.append(HistoryPoint(
            date=str(row.get("date", ""))[:10],
            open=_clean_float(row.get("open")),
            high=_clean_float(row.get("high")),
            low=_clean_float(row.get("low")),
            close=_clean_float(row.get("close")),
            volume=_clean_int(row.get("volume")),
            rsi_14=_clean_float(row.get("rsi_14")),
            macd=_clean_float(row.get("macd")),
            sma_20=_clean_float(row.get("sma_20")),
            sma_50=_clean_float(row.get("sma_50")),
            daily_return_pct=_clean_float(row.get("daily_return_pct")),
        ))

    return HistoryResponse(symbol=symbol, period_days=days, data=points)
