"""
/predictions endpoints
======================
Expose ML predictions to the frontend API.
Includes routes for latest predictions, history, and manual triggers.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.predictions_db import (
    get_latest_prediction,
    get_latest_predictions_all,
    get_predictions_history,
    get_predictions_by_date,
)
from scheduler.daily_scheduler import trigger_manual_run
from logging_config import get_logger

logger = get_logger("api")

router = APIRouter(prefix="/predictions", tags=["ML Predictions"])


class PredictionOut(dict):
    """Prediction response model."""
    pass


@router.get("/{symbol}", summary="Get latest ML prediction for a stock")
async def get_latest_prediction_endpoint(symbol: str) -> dict:
    """
    Get the latest ML-generated prediction for a stock symbol.

    Returns direction (UP/DOWN/STABLE), confidence score, and model info.
    """
    symbol = symbol.upper()

    prediction = get_latest_prediction(symbol)
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for {symbol}"
        )

    return {
        "symbol": prediction["symbol"],
        "date": prediction["date"],
        "direction": prediction["direction"],
        "confidence": prediction["confidence"],
        "raw_score": prediction["raw_score"],
        "model_version": prediction.get("model_version", "1.0.0"),
        "created_at": prediction["created_at"],
    }


@router.get("/", summary="Get all latest predictions")
async def get_all_latest_predictions() -> dict:
    """
    Get the latest prediction for each stock symbol.
    Useful for displaying a dashboard with all stocks.
    """
    predictions = get_latest_predictions_all()

    return {
        "total": len(predictions),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "predictions": [
            {
                "symbol": p["symbol"],
                "direction": p["direction"],
                "confidence": p["confidence"],
                "raw_score": p["raw_score"],
                "date": p["date"],
            }
            for p in predictions
        ],
    }


@router.get("/{symbol}/history", summary="Get prediction history for a stock")
async def get_prediction_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
) -> dict:
    """Get prediction history for a symbol over N days."""
    symbol = symbol.upper()

    predictions = get_predictions_history(symbol, days=days)
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No prediction history found for {symbol}",
        )

    return {
        "symbol": symbol,
        "days": days,
        "total": len(predictions),
        "predictions": [
            {
                "date": p["date"],
                "direction": p["direction"],
                "confidence": p["confidence"],
                "raw_score": p["raw_score"],
            }
            for p in predictions
        ],
    }


@router.get("/date/{date}", summary="Get all predictions for a specific date")
async def get_predictions_for_date(date: str) -> dict:
    """Get all predictions for a specific date (YYYY-MM-DD format)."""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Date must be in YYYY-MM-DD format"
        )

    predictions = get_predictions_by_date(date)
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for {date}"
        )

    # Count by direction
    directions = {"UP": 0, "DOWN": 0, "STABLE": 0}
    for p in predictions:
        directions[p["direction"]] += 1

    return {
        "date": date,
        "total": len(predictions),
        "by_direction": directions,
        "predictions": [
            {
                "symbol": p["symbol"],
                "direction": p["direction"],
                "confidence": p["confidence"],
                "raw_score": p["raw_score"],
            }
            for p in predictions
        ],
    }


@router.post("/trigger-manual", summary="Manually trigger the pipeline (testing)")
async def trigger_manual_pipeline() -> dict:
    """
    Manually trigger the daily prediction pipeline.
    Useful for testing. Requires admin access in production.
    """
    logger.info("Manual pipeline trigger requested via API")

    result = trigger_manual_run()
    return result


@router.get("/stats/summary", summary="Get prediction statistics")
async def get_prediction_summary() -> dict:
    """Get summary statistics on predictions."""
    from data.predictions_db import get_prediction_count

    total_predictions = get_prediction_count()
    latest_predictions = get_latest_predictions_all()

    up_count = sum(1 for p in latest_predictions if p["direction"] == "UP")
    down_count = sum(1 for p in latest_predictions if p["direction"] == "DOWN")
    stable_count = sum(1 for p in latest_predictions if p["direction"] == "STABLE")

    avg_confidence = (
        sum(p["confidence"] for p in latest_predictions) / len(latest_predictions)
        if latest_predictions
        else 0
    )

    return {
        "total_predictions_in_db": total_predictions,
        "latest_predictions_count": len(latest_predictions),
        "directions": {
            "UP": up_count,
            "DOWN": down_count,
            "STABLE": stable_count,
        },
        "average_confidence": round(avg_confidence, 3),
    }
