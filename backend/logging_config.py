"""
Centralized logging configuration for the daily pipeline.
Provides separate loggers for each component with structured formatting and rotation.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Get a configured logger with daily rotation."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    # File handler with daily rotation (max 7 days)
    log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=7,
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Component loggers
scheduler_logger = get_logger("scheduler", logging.INFO)
scraper_logger = get_logger("scraper", logging.INFO)
preprocessor_logger = get_logger("preprocessor", logging.INFO)
predictor_logger = get_logger("predictor", logging.INFO)
