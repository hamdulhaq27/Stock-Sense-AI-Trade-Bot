"""
Daily Pipeline Orchestrator
===========================
Coordinates the entire daily prediction pipeline:
1. Scrape new data (stocks, news, social)
2. Preprocess cleaned data
3. Run ML inference
4. Store predictions
5. Log results
"""

import time
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_DIR, TARGET_TICKERS
from logging_config import get_logger
from data.predictions_db import init_predictions_table, save_prediction, export_predictions_csv
from data.loader import get_stock_data

logger = get_logger("scheduler")


class PipelineResult:
    """Container for pipeline execution results."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.status = "pending"  # pending, running, success, failed
        self.total_stocks_scraped = 0
        self.total_stocks_predicted = 0
        self.total_predictions_saved = 0
        self.errors: List[str] = []
        self.failed_tickers: List[str] = []
        self.warnings: List[str] = []

    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def summary(self) -> str:
        duration = self.duration_seconds()
        return (
            f"Pipeline {self.status.upper()} in {duration:.1f}s\n"
            f"  Stocks scraped: {self.total_stocks_scraped}\n"
            f"  Predictions made: {self.total_stocks_predicted}\n"
            f"  Predictions saved: {self.total_predictions_saved}\n"
            f"  Errors: {len(self.errors)}\n"
            f"  Warnings: {len(self.warnings)}"
        )


def run_daily_pipeline() -> PipelineResult:
    """
    Execute the complete daily prediction pipeline.

    Steps:
    1. Initialize
    2. Scrape new data
    3. Preprocess
    4. Predict
    5. Store
    6. Finalize
    """
    result = PipelineResult()
    result.start_time = datetime.now()
    result.status = "running"

    logger.info("=" * 80)
    logger.info("Starting daily prediction pipeline at %s", result.start_time.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 80)

    try:
        # Step 1: Initialize database
        logger.info("[1/5] Initializing database...")
        init_predictions_table()

        # Step 2: Scrape new data
        logger.info("[2/5] Scraping new stock data...")
        try:
            import importlib.util
            scraping_file = Path(__file__).parent.parent.parent / "scraping" / "stock_collector_daily.py"
            spec = importlib.util.spec_from_file_location("stock_collector_daily", scraping_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            collect_stocks_incremental = module.collect_stocks_incremental
            scraped_rows, error_tickers = collect_stocks_incremental()
            result.total_stocks_scraped = scraped_rows
            if error_tickers:
                result.warnings.append(f"Stock scraper errors: {', '.join(error_tickers)}")
                logger.warning("Stock scraper had errors for: %s", ", ".join(error_tickers))
        except Exception as e:
            msg = f"Stock scraping failed: {e}"
            result.errors.append(msg)
            logger.error(msg)

        # Step 3: Load fresh data
        logger.info("[3/5] Loading data for prediction...")
        try:
            # Reload data loader cache to get new data
            import sys
            if 'backend.data.loader' in sys.modules:
                del sys.modules['backend.data.loader']
            from data.loader import get_stock_data
            stock_df = get_stock_data()
            logger.info("Loaded %d stock records", len(stock_df))
        except Exception as e:
            msg = f"Data loading failed: {e}"
            result.errors.append(msg)
            logger.error(msg)
            stock_df = None

        # Step 4: Run predictions
        logger.info("[4/5] Running predictions...")
        predictions_saved = 0

        if stock_df is not None and not stock_df.empty:
            try:
                from core.predictor import predict
                today = datetime.now().strftime("%Y-%m-%d")

                # Get unique symbols
                symbols = stock_df["symbol"].unique()

                for symbol in symbols:
                    try:
                        # Run rule-based prediction
                        pred_result = predict(symbol)

                        if pred_result:
                            # Save to database
                            saved = save_prediction(
                                symbol=pred_result.symbol,
                                date=today,
                                direction=pred_result.direction,
                                confidence=pred_result.confidence,
                                raw_score=pred_result.raw_score,
                                technical_features={
                                    "rsi_14": pred_result.technical.rsi_14,
                                    "macd": pred_result.technical.macd,
                                    "sma_20": pred_result.technical.sma_20,
                                },
                                sentiment_features={
                                    "composite_sentiment": pred_result.sentiment.composite,
                                },
                                model_version="rule-based-1.0",
                            )
                            if saved:
                                predictions_saved += 1
                            else:
                                result.warnings.append(f"Failed to save prediction for {symbol}")

                            # Count prediction attempt
                            result.total_stocks_predicted += 1
                        else:
                            result.failed_tickers.append(symbol)
                            result.warnings.append(f"Insufficient data for {symbol}")

                    except Exception as e:
                        logger.error("Error predicting %s: %s", symbol, e)
                        result.failed_tickers.append(symbol)
                        result.errors.append(f"Prediction error for {symbol}: {e}")

                result.total_predictions_saved = predictions_saved
                logger.info("Saved %d predictions", predictions_saved)

            except Exception as e:
                msg = f"Prediction phase failed: {e}"
                result.errors.append(msg)
                logger.error(msg)
        else:
            logger.warning("No stock data available for prediction")

        # Step 5: Export backup
        logger.info("[5/5] Exporting backup...")
        try:
            export_path = DATA_DIR / f"predictions_backup_{datetime.now().strftime('%Y-%m-%d')}.csv"
            export_predictions_csv(str(export_path))
            logger.info("Exported predictions to %s", export_path)
        except Exception as e:
            logger.warning("Failed to export backup: %s", e)

        # Success
        result.status = "success"

    except Exception as e:
        result.status = "failed"
        result.errors.append(f"Pipeline failed: {e}")
        logger.error("Pipeline failed: %s", e)

    finally:
        result.end_time = datetime.now()
        logger.info("=" * 80)
        logger.info(result.summary())
        logger.info("=" * 80)

    return result


if __name__ == "__main__":
    result = run_daily_pipeline()
    print(result.summary())
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
