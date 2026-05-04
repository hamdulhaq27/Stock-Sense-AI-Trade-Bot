# Quick Verification Checklist

Follow these steps to verify the automated pipeline is working correctly.

## Pre-Flight Checks

- [ ] Python 3.8+ installed: `python --version`
- [ ] Trained models exist: `ls -lh models/` (should show 15+ files)
- [ ] Data files exist: `ls -lh backend/data/*.csv` (should show 4 CSV files)
- [ ] Git repo is clean: `git status` (no uncommitted changes needed)

## Installation

```bash
# Step 1: Install dependencies
cd backend
pip install -r requirements.txt

# Step 2: Verify key packages installed
pip show apscheduler
pip show torch
pip show catboost

# Step 3: Go back to root
cd ..
```

## Starting the Backend

```bash
# Terminal 1: Start the backend server
cd backend
uvicorn main:app --reload --port 8000

# You should see:
# ⏳  Loading datasets…
# ✅  Loaded 153 symbols in 2.3s
# ⏳  Initializing predictions database…
# ✅  Predictions database ready (X existing predictions)
# ⏳  Starting daily prediction scheduler…
# ✅  Scheduler started successfully
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

## API Verification

```bash
# Terminal 2: Test the API endpoints

# Test 1: Health check
curl http://localhost:8000/health
# Expected: 200 OK with status: "ok"

# Test 2: Get latest prediction for AAPL
curl http://localhost:8000/predictions/AAPL
# Expected: 200 OK with prediction data

# Test 3: Get all latest predictions (limited to first few)
curl http://localhost:8000/predictions/ | jq '.predictions[:3]'
# Expected: Array of 3 predictions

# Test 4: Get statistics
curl http://localhost:8000/predictions/stats/summary
# Expected: Statistics with counts and confidence average

# Test 5: API documentation
# Expected: Open http://localhost:8000/docs in browser
# You should see: Swagger UI with all endpoints documented
```

## Manual Pipeline Trigger (Testing)

```bash
# Trigger the pipeline immediately (don't wait for 4 PM)
curl -X POST http://localhost:8000/predictions/trigger-manual

# Expected response:
# {
#   "status": "success",
#   "duration_seconds": 18.5,
#   "predictions_saved": 152,
#   "errors": []
# }

# This will:
# 1. Fetch today's stock data
# 2. Run ML inference
# 3. Save predictions to database
# 4. Export CSV backup
```

## Log Verification

```bash
# Check if logs were created
ls -lh backend/logs/
# Expected: scheduler_YYYY-MM-DD.log, scraper_YYYY-MM-DD.log, predictor_YYYY-MM-DD.log

# View recent logs
tail -20 backend/logs/scheduler_*.log
tail -20 backend/logs/scraper_*.log
tail -20 backend/logs/predictor_*.log

# Search for errors
grep ERROR backend/logs/*.log
# Should return nothing or only recoverable warnings
```

## Database Verification

```bash
# Check database exists
ls -lh backend/data/predictions.db

# Count predictions
sqlite3 backend/data/predictions.db "SELECT COUNT(*) as total, COUNT(DISTINCT date) as unique_dates FROM daily_predictions;"
# Expected: Shows total predictions and number of distinct dates

# Check latest predictions
sqlite3 backend/data/predictions.db "SELECT symbol, date, direction, confidence FROM daily_predictions ORDER BY date DESC LIMIT 5;"
# Expected: Shows 5 most recent predictions with UP/DOWN/STABLE
```

## Configuration Check

```bash
# Verify config is correct
grep SCHEDULER_TIME backend/config.py
# Expected: SCHEDULER_TIME = "16:00"

grep TIMEZONE backend/config.py
# Expected: TIMEZONE = "US/Eastern"

grep USE_ML_MODELS backend/config.py
# Expected: USE_ML_MODELS = True
```

## Scheduler Verification

```bash
# The scheduler should be active and scheduled
# If running Python, check with:
python -c "
import sys
sys.path.insert(0, 'backend')
from scheduler.daily_scheduler import get_scheduler
scheduler = get_scheduler()
if scheduler:
    print('✅ Scheduler is running')
    for job in scheduler.get_jobs():
        print(f'   Job: {job.name}')
        print(f'   Next run: {job.next_run_time}')
else:
    print('❌ Scheduler not running')
"
```

## Full Integration Test

```bash
# 1. Get a prediction BEFORE manual trigger
curl http://localhost:8000/predictions/AAPL | jq '.created_at'
# Note the created_at timestamp

# 2. Trigger pipeline manually
curl -X POST http://localhost:8000/predictions/trigger-manual

# 3. Wait 5 seconds for pipeline to complete
sleep 5

# 4. Get prediction AFTER manual trigger
curl http://localhost:8000/predictions/AAPL | jq '.created_at'
# Should have a NEW (more recent) timestamp

# 5. Verify statistics updated
curl http://localhost:8000/predictions/stats/summary | jq '.latest_predictions_count'
# Should show 153 (all stocks have predictions)
```

## Frontend Integration Ready Check

```bash
# Your Next.js frontend can now make requests to:
# - http://localhost:8000/predictions/{symbol}
# - http://localhost:8000/predictions/
# - http://localhost:8000/predictions/{symbol}/history
# - http://localhost:8000/predictions/stats/summary

# Example fetch from frontend:
curl -H "Accept: application/json" \
  http://localhost:8000/predictions/AAPL | jq '.'
```

## Success Criteria

✅ All checks below should pass:

- [ ] Backend starts without errors
- [ ] Scheduler initialization shows "✅ Scheduler started"
- [ ] /health endpoint returns 200
- [ ] /predictions/AAPL returns valid prediction data
- [ ] /predictions/ returns array of predictions
- [ ] /predictions/stats/summary returns statistics
- [ ] /docs endpoint shows API documentation
- [ ] Manual trigger completes successfully
- [ ] Database contains predictions
- [ ] Log files are created with content
- [ ] Latest predictions can be retrieved

## What Now?

1. **Start Backend**: `uvicorn backend/main:app --reload --port 8000`
2. **Leave Running**: Backend will automatically run pipeline at 4:00 PM daily
3. **Connect Frontend**: Have Next.js app call prediction endpoints
4. **Monitor Logs**: Check `backend/logs/` daily for any issues
5. **View Predictions**: Use API endpoints to fetch and display predictions

## Troubleshooting

If any check fails:

1. **Backend won't start**: Check Python version, reinstall dependencies
2. **Scheduler not running**: Check `backend/config.py` for syntax errors
3. **No predictions**: Run manual trigger, check logs for errors
4. **Models not loading**: Verify `models/` directory has files
5. **Database errors**: Check `backend/data/` has write permissions

See `PIPELINE_GUIDE.md` for detailed troubleshooting.

---

Once all checks pass: ✅ **System is ready for production use!**

The pipeline will automatically execute daily at 4:00 PM ET without any manual intervention.
