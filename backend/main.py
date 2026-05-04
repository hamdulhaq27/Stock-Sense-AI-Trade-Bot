"""
StockSense AI — FastAPI Backend
================================
Start with:  uvicorn main:app --reload --port 8000
Docs at:     http://localhost:8000/docs
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import predict, sentiment, stocks, batch, predictions
from api.schemas import HealthResponse
from data.loader import get_all_symbols, get_news_data, get_reddit_data, get_stock_data, get_stocktwits_data
from data.predictions_db import init_predictions_table, get_prediction_count
from scheduler.daily_scheduler import init_scheduler, stop_scheduler, is_scheduler_running


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load all DataFrames into memory so first requests are fast
    print("⏳  Loading datasets…")
    t0 = time.monotonic()
    get_stock_data()
    get_news_data()
    get_reddit_data()
    get_stocktwits_data()
    n = len(get_all_symbols())
    print(f"✅  Loaded {n} symbols in {time.monotonic() - t0:.1f}s")

    # Initialize predictions database
    print("⏳  Initializing predictions database…")
    init_predictions_table()
    pred_count = get_prediction_count()
    print(f"✅  Predictions database ready ({pred_count} existing predictions)")

    # Initialize and start the daily scheduler
    print("⏳  Starting daily prediction scheduler…")
    try:
        init_scheduler()
        if is_scheduler_running():
            print("✅  Scheduler started successfully")
        else:
            print("⚠️  Scheduler failed to start")
    except Exception as e:
        print(f"⚠️  Scheduler initialization failed: {e}")

    yield

    # Shutdown
    print("👋  Shutting down StockSense AI")
    print("⏳  Stopping scheduler…")
    stop_scheduler()
    print("✅  Scheduler stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="StockSense AI",
    description=(
        "Multi-signal stock direction prediction API.\n\n"
        "Combines FinBERT news sentiment, Reddit/StockTwits social sentiment, "
        "and technical indicators (RSI, MACD, SMA) into a single directional "
        "forecast (UP / DOWN / STABLE) with a confidence score."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the Next.js frontend (localhost:3000) and any Vercel preview
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
        "https://stocksense-ai-trader.vercel.app/", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
    return response

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(predict.router)
app.include_router(sentiment.router)
app.include_router(stocks.router)
app.include_router(batch.router)
app.include_router(predictions.router)

# ---------------------------------------------------------------------------
# Root & health
# ---------------------------------------------------------------------------

@app.get("/", tags=["Meta"])
async def root():
    return {
        "name": "StockSense AI",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "GET  /predict/{symbol}",
            "GET  /sentiment/{symbol}",
            "GET  /stocks/",
            "GET  /stocks/{symbol}",
            "GET  /stocks/{symbol}/history",
            "POST /batch/predict",
            "GET  /batch/top",
            "GET  /health",
        ],
    }


@app.get("/health", response_model=HealthResponse, tags=["Meta"])
async def health():
    return HealthResponse(
        status="ok",
        symbols_loaded=len(get_all_symbols()),
        version="1.0.0",
    )
