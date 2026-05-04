"""
APScheduler Setup for Daily Pipeline
====================================
Schedules the daily prediction pipeline to run at 4:00 PM (16:00) every day.
Runs within the FastAPI lifespan.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SCHEDULER_TIME, TIMEZONE
from logging_config import get_logger

logger = get_logger("scheduler")

_scheduler: Optional[BackgroundScheduler] = None


def init_scheduler() -> BackgroundScheduler:
    """Initialize and start the APScheduler."""
    global _scheduler

    if _scheduler is not None:
        return _scheduler

    logger.info("Initializing APScheduler...")

    _scheduler = BackgroundScheduler(timezone=TIMEZONE)

    # Parse schedule time (HH:MM format)
    hour, minute = map(int, SCHEDULER_TIME.split(":"))

    # Add job: daily at specified time
    _scheduler.add_job(
        func=_run_pipeline,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=TIMEZONE),
        id="daily_prediction_pipeline",
        name="Daily Prediction Pipeline",
        replace_existing=True,
        max_instances=1,  # Prevent concurrent runs
    )

    _scheduler.start()
    logger.info("APScheduler started. Pipeline scheduled daily at %02d:%02d %s", hour, minute, TIMEZONE)

    return _scheduler


def stop_scheduler() -> None:
    """Stop the scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("APScheduler stopped")


def _run_pipeline() -> None:
    """Wrapper function to run the pipeline."""
    logger.info("=" * 80)
    logger.info("Scheduled pipeline execution triggered")
    logger.info("=" * 80)

    try:
        from core.pipeline_orchestrator import run_daily_pipeline
        result = run_daily_pipeline()

        if result.status == "success":
            logger.info("✅ Pipeline executed successfully")
        else:
            logger.warning("⚠️  Pipeline completed with status: %s", result.status)
            if result.errors:
                for error in result.errors:
                    logger.error("  Error: %s", error)

    except Exception as e:
        logger.error("Failed to execute pipeline: %s", e)


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the current scheduler instance."""
    return _scheduler


def is_scheduler_running() -> bool:
    """Check if scheduler is running."""
    global _scheduler
    return _scheduler is not None and _scheduler.running


def trigger_manual_run() -> dict:
    """Manually trigger the pipeline (for testing)."""
    logger.info("Manual pipeline trigger requested")
    try:
        from core.pipeline_orchestrator import run_daily_pipeline
        result = run_daily_pipeline()
        return {
            "status": result.status,
            "duration_seconds": result.duration_seconds(),
            "predictions_saved": result.total_predictions_saved,
            "errors": result.errors,
        }
    except Exception as e:
        logger.error("Manual trigger failed: %s", e)
        return {
            "status": "failed",
            "error": str(e),
        }
