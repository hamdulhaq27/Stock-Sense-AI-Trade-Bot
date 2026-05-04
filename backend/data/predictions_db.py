"""
Database handler for storing and retrieving daily predictions.
Uses SQLite with a simple schema for daily_predictions table.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import PREDICTIONS_DB, STOCK_DB
from logging_config import get_logger

logger = get_logger("database")


def init_predictions_table(db_path: str = str(PREDICTIONS_DB)) -> None:
    """Initialize the predictions database and tables if they don't exist."""
    PREDICTIONS_DB.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Main predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_predictions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol              TEXT NOT NULL,
            date                TEXT NOT NULL,
            direction           TEXT NOT NULL,
            confidence          REAL,
            raw_score           REAL,
            technical_features  TEXT,
            sentiment_features  TEXT,
            model_version       TEXT DEFAULT '1.0.0',
            created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    """)

    # Index for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_symbol_date
        ON daily_predictions(symbol, date DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_date
        ON daily_predictions(date DESC)
    """)

    conn.commit()
    conn.close()
    logger.info("Predictions table initialized in %s", db_path)


def save_prediction(
    symbol: str,
    date: str,
    direction: str,
    confidence: float,
    raw_score: float,
    technical_features: Optional[Dict[str, Any]] = None,
    sentiment_features: Optional[Dict[str, Any]] = None,
    model_version: str = "1.0.0",
    db_path: str = str(PREDICTIONS_DB),
) -> bool:
    """Save a prediction to the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        technical_json = json.dumps(technical_features) if technical_features else None
        sentiment_json = json.dumps(sentiment_features) if sentiment_features else None

        cursor.execute("""
            INSERT OR REPLACE INTO daily_predictions
            (symbol, date, direction, confidence, raw_score, technical_features, sentiment_features, model_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (symbol, date, direction, confidence, raw_score, technical_json, sentiment_json, model_version))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error("Failed to save prediction for %s on %s: %s", symbol, date, e)
        return False


def get_latest_prediction(symbol: str, db_path: str = str(PREDICTIONS_DB)) -> Optional[Dict]:
    """Get the latest prediction for a symbol."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM daily_predictions
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 1
        """, (symbol.upper(),))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error("Failed to get latest prediction for %s: %s", symbol, e)
        return None


def get_predictions_by_date(date: str, db_path: str = str(PREDICTIONS_DB)) -> List[Dict]:
    """Get all predictions for a specific date."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM daily_predictions
            WHERE date = ?
            ORDER BY symbol ASC
        """, (date,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to get predictions for date %s: %s", date, e)
        return []


def get_predictions_history(
    symbol: str,
    days: int = 30,
    db_path: str = str(PREDICTIONS_DB),
) -> List[Dict]:
    """Get prediction history for a symbol over N days."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT * FROM daily_predictions
            WHERE symbol = ? AND date >= ?
            ORDER BY date DESC
        """, (symbol.upper(), cutoff_date))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to get history for %s: %s", symbol, e)
        return []


def get_latest_predictions_all(db_path: str = str(PREDICTIONS_DB)) -> List[Dict]:
    """Get the latest prediction for each symbol."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM daily_predictions dp
            WHERE date = (
                SELECT MAX(date) FROM daily_predictions
                WHERE symbol = dp.symbol
            )
            ORDER BY symbol ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Failed to get all latest predictions: %s", e)
        return []


def get_prediction_count(db_path: str = str(PREDICTIONS_DB)) -> int:
    """Get total count of predictions in the database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_predictions")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.error("Failed to get prediction count: %s", e)
        return 0


def export_predictions_csv(
    output_path: str,
    db_path: str = str(PREDICTIONS_DB),
) -> bool:
    """Export all predictions to CSV for backup."""
    try:
        import pandas as pd

        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM daily_predictions ORDER BY date DESC, symbol ASC", conn)
        conn.close()

        df.to_csv(output_path, index=False)
        logger.info("Exported %d predictions to %s", len(df), output_path)
        return True
    except Exception as e:
        logger.error("Failed to export predictions to CSV: %s", e)
        return False


def cleanup_old_predictions(
    days_to_keep: int = 365,
    db_path: str = str(PREDICTIONS_DB),
) -> int:
    """Delete predictions older than N days."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

        cursor.execute("DELETE FROM daily_predictions WHERE date < ?", (cutoff_date,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info("Cleaned up %d old predictions (older than %d days)", deleted, days_to_keep)
        return deleted
    except Exception as e:
        logger.error("Failed to cleanup old predictions: %s", e)
        return 0
