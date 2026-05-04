"""
ML Prediction Service
====================
Loads trained models (CatBoost, LightGBM, XGBoost, Transformer) and runs inference.
Provides ensemble predictions for stock direction (UP/DOWN/STABLE).
"""

import pickle
import json
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MODEL_CATBOOST_PATH,
    MODEL_LGB_PATH,
    MODEL_XGB_PATH,
    MODEL_TRANSFORMER_PATH,
    MODEL_CONFIG_PATH,
    MODEL_NORM_STATS_PATH,
    MODEL_SECTOR_ENCODER_PATH,
    FEATURE_COLUMNS,
)
from logging_config import get_logger

logger = get_logger("predictor")


@dataclass
class PredictionResult:
    """Result of ML prediction."""
    symbol: str
    direction: str  # UP, DOWN, STABLE
    confidence: float  # 0.0 - 1.0
    raw_score: float  # -1.0 to +1.0
    model_version: str = "1.0.0"
    feature_count: int = 0
    inference_time_ms: float = 0.0


class MLPredictor:
    """ML-based stock prediction using ensemble of multiple models."""

    def __init__(self):
        """Initialize and load all trained models."""
        logger.info("Initializing ML Predictor...")
        self.models = {}
        self.norm_stats = None
        self.config = None
        self.sector_encoder = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        try:
            self._load_models()
            logger.info("ML Predictor initialized successfully (device: %s)", self.device)
        except Exception as e:
            logger.error("Failed to initialize ML Predictor: %s", e)
            raise

    def _load_models(self) -> None:
        """Load all trained models from disk."""
        import time

        start = time.time()

        # Load normalization stats
        if MODEL_NORM_STATS_PATH.exists():
            with open(MODEL_NORM_STATS_PATH, "rb") as f:
                self.norm_stats = pickle.load(f)
                logger.info("Loaded normalization stats")
        else:
            logger.warning("Normalization stats not found at %s", MODEL_NORM_STATS_PATH)

        # Load config
        if MODEL_CONFIG_PATH.exists():
            with open(MODEL_CONFIG_PATH, "rb") as f:
                self.config = pickle.load(f)
                logger.info("Loaded model config")

        # Load CatBoost
        if MODEL_CATBOOST_PATH.exists():
            try:
                from catboost import CatBoostClassifier
                self.models["catboost"] = CatBoostClassifier()
                self.models["catboost"].load_model(str(MODEL_CATBOOST_PATH))
                logger.info("Loaded CatBoost model (%s)", MODEL_CATBOOST_PATH.stat().st_size / 1024 / 1024)
            except Exception as e:
                logger.error("Failed to load CatBoost: %s", e)

        # Load LightGBM
        if MODEL_LGB_PATH.exists():
            try:
                import lightgbm as lgb
                self.models["lgb"] = lgb.Booster(model_file=str(MODEL_LGB_PATH))
                logger.info("Loaded LightGBM model (%s)", MODEL_LGB_PATH.stat().st_size / 1024 / 1024)
            except Exception as e:
                logger.error("Failed to load LightGBM: %s", e)

        # Load XGBoost
        if MODEL_XGB_PATH.exists():
            try:
                import xgboost as xgb
                self.models["xgboost"] = xgb.Booster()
                self.models["xgboost"].load_model(str(MODEL_XGB_PATH))
                logger.info("Loaded XGBoost model (%s)", MODEL_XGB_PATH.stat().st_size / 1024 / 1024)
            except Exception as e:
                logger.error("Failed to load XGBoost: %s", e)

        # Load Transformer (PyTorch)
        if MODEL_TRANSFORMER_PATH.exists():
            try:
                # Load transformer checkpoint
                checkpoint = torch.load(str(MODEL_TRANSFORMER_PATH), map_location=self.device)
                logger.info("Loaded Transformer checkpoint (%s)", MODEL_TRANSFORMER_PATH.stat().st_size / 1024 / 1024)
                self.models["transformer"] = checkpoint
            except Exception as e:
                logger.error("Failed to load Transformer: %s", e)

        # Load sector encoder
        if MODEL_SECTOR_ENCODER_PATH.exists():
            try:
                with open(MODEL_SECTOR_ENCODER_PATH, "rb") as f:
                    self.sector_encoder = pickle.load(f)
                    logger.info("Loaded sector encoder")
            except Exception as e:
                logger.warning("Failed to load sector encoder: %s", e)

        elapsed = time.time() - start
        logger.info("Model loading completed in %.2f seconds", elapsed)

        if not self.models:
            raise RuntimeError("No models were loaded successfully!")

    def _normalize_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Normalize features using training data statistics."""
        if self.norm_stats is None:
            return features

        try:
            features_norm = features.copy()

            if isinstance(self.norm_stats, dict):
                for col in features_norm.columns:
                    if col in self.norm_stats and "mean" in self.norm_stats[col]:
                        mean = self.norm_stats[col]["mean"]
                        std = self.norm_stats[col]["std"]
                        if std > 0:
                            features_norm[col] = (features_norm[col] - mean) / std

            return features_norm
        except Exception as e:
            logger.warning("Feature normalization failed: %s", e)
            return features

    def _prepare_features(self, features: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Validate and prepare features for model inference."""
        try:
            # Select only required features
            required_cols = [col for col in FEATURE_COLUMNS if col in features.columns]

            if len(required_cols) < len(FEATURE_COLUMNS) * 0.8:
                logger.warning("Only %d/%d features available", len(required_cols), len(FEATURE_COLUMNS))

            X = features[required_cols].copy()

            # Fill any remaining NaN
            X = X.fillna(X.mean())

            # Normalize
            X = self._normalize_features(X)

            return X
        except Exception as e:
            logger.error("Feature preparation failed: %s", e)
            return None

    def predict(self, symbol: str, features: pd.DataFrame) -> Optional[PredictionResult]:
        """
        Run ML inference on stock features.

        Args:
            symbol: Stock ticker symbol
            features: DataFrame with technical features (single row)

        Returns:
            PredictionResult with direction and confidence, or None if failed
        """
        import time

        if features.empty:
            logger.warning("Empty features for %s", symbol)
            return None

        start_time = time.time()

        try:
            # Prepare features
            X = self._prepare_features(features.iloc[[0]])
            if X is None or X.empty:
                logger.warning("Feature preparation failed for %s", symbol)
                return None

            # Run ensemble predictions
            predictions = []

            # CatBoost prediction
            if "catboost" in self.models:
                try:
                    pred = self.models["catboost"].predict_proba(X)[0]
                    prob_up = pred[1] if len(pred) > 1 else 0.5
                    score = 2 * (prob_up - 0.5)  # Convert to -1 to 1
                    predictions.append(score)
                except Exception as e:
                    logger.debug("CatBoost prediction failed for %s: %s", symbol, e)

            # LightGBM prediction
            if "lgb" in self.models:
                try:
                    pred = self.models["lgb"].predict(X)[0]
                    prob_up = pred if isinstance(pred, (int, float)) else pred[1]
                    score = 2 * (prob_up - 0.5)
                    predictions.append(score)
                except Exception as e:
                    logger.debug("LightGBM prediction failed for %s: %s", symbol, e)

            # XGBoost prediction
            if "xgboost" in self.models:
                try:
                    pred = self.models["xgboost"].predict(X)[0]
                    prob_up = pred if isinstance(pred, (int, float)) else pred[1]
                    score = 2 * (prob_up - 0.5)
                    predictions.append(score)
                except Exception as e:
                    logger.debug("XGBoost prediction failed for %s: %s", symbol, e)

            if not predictions:
                logger.warning("No model predictions for %s", symbol)
                return None

            # Ensemble: average predictions
            raw_score = float(np.mean(predictions))
            raw_score = np.clip(raw_score, -1.0, 1.0)

            # Direction and confidence
            UP_THRESH = 0.10
            DOWN_THRESH = -0.10

            if raw_score >= UP_THRESH:
                direction = "UP"
            elif raw_score <= DOWN_THRESH:
                direction = "DOWN"
            else:
                direction = "STABLE"

            # Confidence: sigmoid-like mapping
            confidence = 0.5 + 0.5 * (1 - np.exp(-3 * abs(raw_score)))
            confidence = float(np.clip(confidence, 0.0, 1.0))

            elapsed_ms = (time.time() - start_time) * 1000

            result = PredictionResult(
                symbol=symbol.upper(),
                direction=direction,
                confidence=round(confidence, 4),
                raw_score=round(raw_score, 4),
                model_version="1.0.0",
                feature_count=len(X),
                inference_time_ms=round(elapsed_ms, 2),
            )

            logger.debug(
                "Predicted %s: %s (conf=%.2f, score=%.3f, time=%.1fms)",
                symbol, direction, confidence, raw_score, elapsed_ms
            )

            return result

        except Exception as e:
            logger.error("ML prediction failed for %s: %s", symbol, e)
            return None


# Global predictor instance
_predictor = None


def get_ml_predictor() -> MLPredictor:
    """Get or create the global ML predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = MLPredictor()
    return _predictor


def predict_stock(symbol: str, features: pd.DataFrame) -> Optional[PredictionResult]:
    """Convenience function for prediction."""
    predictor = get_ml_predictor()
    return predictor.predict(symbol, features)
