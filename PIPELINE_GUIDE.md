# StockSense AI — Daily Automated Pipeline

Complete guide to the automated daily prediction pipeline.

## Overview

The system now runs a fully automated daily pipeline that:
1. **Scrapes** new stock data every day after market close
2. **Preprocesses** the data (indicators, cleaning)
3. **Predicts** using trained ML models (ensemble of 4 models)
4. **Stores** predictions in SQLite database
5. **Exposes** results via REST API to frontend

**Execution Time**: 4:00 PM ET (16:00) every trading day
**Duration**: ~15-20 minutes per run
**Status**: Automatic background execution via APScheduler

---

## Architecture

### Components

```
Backend (FastAPI)
├── Logging         → logs/ directory with dated files
├── Scheduler       → APScheduler (runs at 16:00 daily)
├── Pipeline Orchestrator → Coordinates all steps
├── Scraping Service    → Fetches today's data only
├── Preprocessing       → Cleans & preputes features
├── ML Predictor        → Ensemble of 4 ML models
├── Database            → SQLite predictions.db
└── API Routes          → /predictions/* endpoints
```

### Models

The system uses an **ensemble** of 4 trained models:
- **CatBoost** (main classifier) - 7.9 MB
- **LightGBM** (fast gradient boosting) - 87 KB  
- **XGBoost** (gradient boosting) - 247 KB
- **Transformer** (deep learning) - 6.7 MB

Predictions are **averaged** across models for robustness.

---

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Verify Models Exist

Check that trained models are present:
```bash
ls -lh ../models/
# Should show: catboost.pkl, lgb.pkl, xgboost.pkl, transformer.pt, etc.
```

### 3. Verify Data Files

Existing data files should be in `backend/data/`:
```bash
ls -lh data/
# Should show: stock_data_clean.csv, news_clean.csv, agg_reddit.csv, agg_stocktwits.csv
```

---

## Running the Backend

### Start the FastAPI Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Output**:
```
⏳  Loading datasets…
✅  Loaded 153 symbols in 2.3s
⏳  Initializing predictions database…
✅  Predictions database ready (42 existing predictions)
⏳  Starting daily prediction scheduler…
✅  Scheduler started successfully
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Verify Scheduler is Running

Check API health:
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "symbols_loaded": 153,
  "version": "1.0.0"
}
```

---

## API Endpoints

All endpoints are documented at: **http://localhost:8000/docs**

### Get Latest Predictions

```bash
# Get latest prediction for a stock
curl http://localhost:8000/predictions/AAPL

# Response:
{
  "symbol": "AAPL",
  "date": "2026-05-04",
  "direction": "UP",
  "confidence": 0.78,
  "raw_score": 0.452,
  "model_version": "1.0.0",
  "created_at": "2026-05-04T16:45:23"
}
```

### Get All Latest Predictions

```bash
curl http://localhost:8000/predictions/

# Response:
{
  "total": 153,
  "date": "2026-05-04",
  "predictions": [
    {
      "symbol": "AAPL",
      "direction": "UP",
      "confidence": 0.78,
      "raw_score": 0.452,
      "date": "2026-05-04"
    },
    ...
  ]
}
```

### Get Prediction History

```bash
# Get last 30 days of predictions
curl "http://localhost:8000/predictions/AAPL/history?days=30"

# Get last 7 days
curl "http://localhost:8000/predictions/AAPL/history?days=7"

# Response:
{
  "symbol": "AAPL",
  "days": 30,
  "total": 22,
  "predictions": [
    {
      "date": "2026-05-04",
      "direction": "UP",
      "confidence": 0.78,
      "raw_score": 0.452
    },
    ...
  ]
}
```

### Get Predictions by Date

```bash
curl http://localhost:8000/predictions/date/2026-05-04

# Response:
{
  "date": "2026-05-04",
  "total": 153,
  "by_direction": {
    "UP": 52,
    "DOWN": 48,
    "STABLE": 53
  },
  "predictions": [...]
}
```

### Get Statistics

```bash
curl http://localhost:8000/predictions/stats/summary

# Response:
{
  "total_predictions_in_db": 2847,
  "latest_predictions_count": 153,
  "directions": {
    "UP": 52,
    "DOWN": 48,
    "STABLE": 53
  },
  "average_confidence": 0.612
}
```

### Manually Trigger Pipeline (Testing)

```bash
curl -X POST http://localhost:8000/predictions/trigger-manual

# Response:
{
  "status": "success",
  "duration_seconds": 18.5,
  "predictions_saved": 152,
  "errors": []
}
```

---

## Monitoring the Pipeline

### View Logs

Log files are created daily in `backend/logs/`:

```bash
# View scheduler log
tail -f backend/logs/scheduler_2026-05-04.log

# View scraper log
tail -f backend/logs/scraper_2026-05-04.log

# View predictor log
tail -f backend/logs/predictor_2026-05-04.log
```

### Example Log Output

```
[2026-05-04 16:00:01] [INFO] [scheduler] Starting daily prediction pipeline at 2026-05-04 16:00:01
[2026-05-04 16:00:02] [INFO] [scheduler] Initializing database...
[2026-05-04 16:00:03] [INFO] [scheduler] Scraping new stock data...
[2026-05-04 16:00:05] [INFO] [scraper] Stock collection: 153 new rows in 2.5s
[2026-05-04 16:00:06] [INFO] [scheduler] Loading data for prediction...
[2026-05-04 16:00:08] [INFO] [scheduler] Running ML inference...
[2026-05-04 16:00:25] [INFO] [predictor] Predicted AAPL: UP (conf=0.78, score=0.452, time=85.3ms)
[2026-05-04 16:15:45] [INFO] [scheduler] Saved 152 predictions
[2026-05-04 16:15:50] [INFO] [scheduler] Pipeline success in 910.5s
[2026-05-04 16:15:50] [INFO] [scheduler] Stocks scraped: 153
[2026-05-04 16:15:50] [INFO] [scheduler] Predictions made: 153
[2026-05-04 16:15:50] [INFO] [scheduler] Predictions saved: 152
```

### Check Database Size

```bash
# SQLite database size
ls -lh backend/data/predictions.db

# Example: -rw-r--r-- 1 user group 5.2M 2026-05-04 16:16 predictions.db

# Query prediction count
sqlite3 backend/data/predictions.db "SELECT COUNT(*) as total, COUNT(DISTINCT date) as dates FROM daily_predictions;"

# Example output:
# total|dates
# 2847|18
```

### Export Predictions

Backup CSVs are automatically created:
```bash
ls -lh backend/data/predictions_backup*.csv
# -rw-r--r-- 1 user group 2.1M 2026-05-04 16:16 predictions_backup_2026-05-04.csv
```

---

## Configuration

Edit `backend/config.py` to customize:

```python
# Pipeline execution time (24-hour format)
SCHEDULER_TIME = "16:00"  # 4:00 PM

# Timezone
TIMEZONE = "US/Eastern"

# Model parameters
USE_ML_MODELS = True                    # Use ML or rule-based
BACKUP_TO_RULE_BASED = True            # Fallback if ML fails

# FinBERT batch processing
BATCH_SIZE_FINBERT = 32                # Adjust for GPU memory

# Retry logic
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 300              # 5 minutes between retries
```

---

## Troubleshooting

### Scheduler Not Starting

Check the startup logs:
```bash
# Look for scheduler initialization
grep "Scheduler" backend/logs/scheduler_*.log

# If not found, check main startup output
# Error will be in the uvicorn server output
```

### Pipeline Fails for One Stock

- Check logs: `grep "Error processing" backend/logs/scraper_*.log`
- That stock will be logged but pipeline continues
- Other stocks are unaffected

### No Data for a Date

- Market might be closed (weekends, holidays)
- Check if yfinance returned data: look at scraper log
- Manual trigger will show this in warnings

### Models Not Loading

- Verify model files exist: `ls -lh backend/../models/`
- Check logs: `grep "Failed to load" backend/logs/predictor_*.log`
- If critical, pipeline falls back to rule-based predictor

### Database Locked

```bash
# Check if another process is using it
lsof | grep predictions.db

# Close conflicting processes and retry
```

---

## Performance Metrics

Typical pipeline execution:

| Stage | Duration | Notes |
|-------|----------|-------|
| Scraping | 2-3 min | 153 stocks × yfinance |
| Preprocessing | 1-2 min | Feature engineering |
| Model Loading | 5-10 sec | ~15 MB total |
| Inference | 8-12 min | 153 stocks × 4 models |
| Storage | 1-2 min | DB writes + CSV export |
| **Total** | **15-20 min** | Typically <45 min |

GPU acceleration can reduce inference time by 30-50%.

---

## Data Flow Diagram

```
4:00 PM ET Daily Trigger
    ↓
[Scraper] → Fetch today's AAPL, TSLA, ... (153 stocks)
    ↓ (153 new rows)
[Preprocessor] → Clean, compute indicators
    ↓ (153 rows with features)
[ML Models] → CatBoost + LGB + XGBoost + Transformer
    ↓ (ensemble average)
[Predictions] → direction, confidence, raw_score
    ↓
[Database] → SQLite: daily_predictions table
    ↓
[Backup] → CSV export: predictions_backup_YYYY-MM-DD.csv
    ↓
[Frontend API] → /predictions/{symbol}, /predictions/latest
    ↓
[Frontend] → Display to users
```

---

## Frontend Integration

The frontend Next.js app should call these endpoints:

### Example React Hook

```typescript
// Get latest prediction for a stock
const [prediction, setPrediction] = useState(null);

useEffect(() => {
  fetch(`http://localhost:8000/predictions/AAPL`)
    .then(r => r.json())
    .then(data => setPrediction(data));
}, []);

// Display
{prediction && (
  <div>
    <h3>{prediction.symbol}</h3>
    <p>Direction: {prediction.direction}</p>
    <p>Confidence: {(prediction.confidence * 100).toFixed(1)}%</p>
  </div>
)}
```

### Example Dashboard Endpoint

```typescript
// Get all latest predictions for dashboard
const [predictions, setPredictions] = useState([]);

useEffect(() => {
  fetch(`http://localhost:8000/predictions/`)
    .then(r => r.json())
    .then(data => setPredictions(data.predictions));
}, []);

// Render table of all stocks with latest predictions
```

---

## Maintenance

### Daily Checklist

- [ ] Check logs for errors: `grep ERROR backend/logs/*.log`
- [ ] Verify prediction count: `curl .../predictions/stats/summary`
- [ ] Spot-check a prediction: `curl .../predictions/AAPL`

### Weekly

- [ ] Check database size: `ls -lh backend/data/predictions.db`
- [ ] Verify model inference times: look at logs
- [ ] Review failed tickers (if any)

### Monthly

- [ ] Clean up old logs: `find backend/logs -name "*.log" -mtime +30 -delete`
- [ ] Archive old predictions: export and backup CSV
- [ ] Review performance metrics

### Clean Database (Keep Last 1 Year)

```bash
# From Python
from backend.data.predictions_db import cleanup_old_predictions
cleanup_old_predictions(days_to_keep=365)
```

---

## Deployment Notes

### Production Checklist

- [ ] Disable `/predictions/trigger-manual` endpoint (add auth)
- [ ] Set `SCHEDULER_TIME` to your target timezone
- [ ] Increase `BATCH_SIZE_FINBERT` if running on GPU
- [ ] Enable HTTPS/SSL for API
- [ ] Add authentication to sensitive endpoints
- [ ] Set up log rotation (currently daily, max 7 files)
- [ ] Monitor database growth (consider archiving old predictions)
- [ ] Set up alerts for failed pipeline runs
- [ ] Use environment variables for sensitive config

### Health Check

```bash
# Add this to your monitoring system
curl http://localhost:8000/health

# Should return 200 with json
```

---

## Support

For issues or questions:
1. Check logs in `backend/logs/`
2. Review error messages and timestamps
3. Manually trigger pipeline to test: `POST /predictions/trigger-manual`
4. Check model files exist: `ls backend/../models/`
5. Verify database: `sqlite3 backend/data/predictions.db "SELECT COUNT(*) FROM daily_predictions;"`

---

Last Updated: 2026-05-04
Pipeline Version: 1.0.0
