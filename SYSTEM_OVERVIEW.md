# StockSense AI - Complete System Overview & Setup Guide

## 🎯 What This System Does

Your **StockSense AI** is a real-time stock prediction platform that:

### Core Functionality
1. **Predicts Stock Direction** (UP/DOWN/STABLE) for 144 major stocks
2. **Combines Multiple Signals:**
   - Technical Indicators (RSI, MACD, SMA, Bollinger Bands)
   - News Sentiment (FinBERT analysis)
   - Social Media (Reddit, StockTwits)
3. **Runs Automatically Every Day** at 4:00 PM (market close)
4. **Stores Predictions** in SQLite database
5. **Serves via REST API** with interactive docs

### Output Example
```json
{
  "symbol": "AAPL",
  "direction": "UP",
  "confidence": 0.78,
  "raw_score": 0.452,
  "technical": {
    "rsi_14": 62.5,
    "macd": 0.15,
    "sma_20": 185.32
  },
  "sentiment": {
    "news_score": 0.65,
    "reddit_score": 0.42,
    "composite": 0.58
  }
}
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────┐
│           Next.js Frontend (React)                   │
│  - Dashboard with stock predictions                 │
│  - Real-time charts and sentiment                   │
│  - Portfolio tracking                               │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────────────┐
│         FastAPI Backend (Python)                     │
│  - /predict/{symbol}      - Get prediction          │
│  - /sentiment/{symbol}    - Get sentiment           │
│  - /stocks/               - List stocks             │
│  - /batch/predict         - Batch predictions       │
│  - /predictions/          - Stored predictions      │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┬─────────────┐
        │                     │             │
┌───────▼────────┐  ┌────────▼────────┐  ┌─▼──────────────┐
│   Data Loader  │  │ Daily Scheduler │  │ ML Predictor   │
│ - Stock data   │  │ APScheduler     │  │ (Rule-based)   │
│ - News data    │  │ 4:00 PM daily   │  │ - Technical    │
│ - Sentiment    │  │                 │  │ - Sentiment    │
└────────────────┘  └─────────────────┘  └────────────────┘
        │                     │                    │
        └─────────────────────┼────────────────────┘
                              │
                      ┌───────▼────────┐
                      │  SQLite DB     │
                      │ predictions.db │
                      └────────────────┘
```

---

## 🚀 Complete Setup & Running

### Step 1: Install Frontend Dependencies

```powershell
cd C:\Users\PC\Desktop\website
npm install
```

### Step 2: Start Backend

```powershell
cd backend
uvicorn main:app --port 8000
```

Backend will be at: `http://localhost:8000/docs`

### Step 3: Start Frontend

```powershell
# In a new PowerShell window
cd C:\Users\PC\Desktop\website
npm run dev
```

Frontend will be at: `http://localhost:3000`

### Step 4: Access the System

- **Frontend Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Manual Pipeline Trigger:** See automation section below

---

## 🤖 Automation & Verification

### Option 1: Manual Trigger Testing

```powershell
# Trigger pipeline manually
Invoke-WebRequest -Uri "http://localhost:8000/predictions/trigger-manual" -Method POST | Select-Object -ExpandProperty Content

# Expected output:
# {
#   "status": "success",
#   "duration_seconds": 3.8,
#   "predictions_saved": 141,
#   "errors": []
# }
```

### Option 2: Automated Testing Script

Create `test_system.ps1`:

```powershell
param(
    [int]$RepeatCount = 1,
    [int]$DelaySeconds = 300
)

$BaseUrl = "http://localhost:8000"
$FailedTests = @()

function Test-Backend {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Testing Backend Health"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    try {
        $health = Invoke-WebRequest -Uri "$BaseUrl/health" | ConvertFrom-Json
        Write-Host "✅ Backend Health: $($health.status)"
        Write-Host "   Symbols Loaded: $($health.symbols_loaded)"
    } catch {
        Write-Host "❌ Backend health check failed"
        $FailedTests += "Backend health"
        return $false
    }
    return $true
}

function Test-API {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Testing API Endpoints"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Test /stocks
    try {
        $stocks = Invoke-WebRequest -Uri "$BaseUrl/stocks" | ConvertFrom-Json
        Write-Host "✅ /stocks endpoint: $($stocks.total) symbols"
    } catch {
        Write-Host "❌ /stocks endpoint failed"
        $FailedTests += "/stocks"
    }
    
    # Test /predictions
    try {
        $preds = Invoke-WebRequest -Uri "$BaseUrl/predictions/" | ConvertFrom-Json
        Write-Host "✅ /predictions endpoint: $($preds.total) predictions"
    } catch {
        Write-Host "❌ /predictions endpoint failed"
        $FailedTests += "/predictions"
    }
    
    # Test specific stock
    try {
        $pred = Invoke-WebRequest -Uri "$BaseUrl/predictions/AAPL" | ConvertFrom-Json
        Write-Host "✅ /predictions/AAPL: $($pred.direction) (confidence: $($pred.confidence))"
    } catch {
        Write-Host "⚠️  No prediction yet for AAPL"
    }
}

function Test-Pipeline {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Testing Pipeline Execution"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    try {
        $result = Invoke-WebRequest -Uri "$BaseUrl/predictions/trigger-manual" -Method POST | ConvertFrom-Json
        Write-Host "✅ Pipeline Status: $($result.status)"
        Write-Host "   Duration: $($result.duration_seconds)s"
        Write-Host "   Predictions Saved: $($result.predictions_saved)"
        
        if ($result.errors.Count -gt 0) {
            Write-Host "   ⚠️  Errors: $($result.errors -join ', ')"
        }
    } catch {
        Write-Host "❌ Pipeline trigger failed"
        $FailedTests += "Pipeline execution"
    }
}

function Test-Database {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Testing Database"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    $DbPath = "C:\Users\PC\Desktop\website\backend\data\predictions.db"
    
    if (Test-Path $DbPath) {
        $Size = (Get-Item $DbPath).Length / 1024
        Write-Host "✅ Database exists: $($Size)KB"
        
        try {
            $Count = sqlite3 $DbPath "SELECT COUNT(*) FROM daily_predictions;" 2>$null
            Write-Host "   Total Predictions: $Count"
        } catch {
            Write-Host "   ⚠️  Could not read prediction count"
        }
    } else {
        Write-Host "❌ Database not found"
        $FailedTests += "Database"
    }
}

function Test-Frontend {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "Testing Frontend"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Frontend is running"
        }
    } catch {
        Write-Host "⚠️  Frontend not detected (may not be running)"
    }
}

# Main loop
for ($i = 1; $i -le $RepeatCount; $i++) {
    Write-Host "`n`n╔═══════════════════════════════════════════════════════╗"
    Write-Host "║  StockSense AI - System Verification (Run $i/$RepeatCount)      ║"
    Write-Host "║  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                              ║"
    Write-Host "╚═══════════════════════════════════════════════════════╝"
    
    Test-Backend
    Test-API
    Test-Pipeline
    Test-Database
    Test-Frontend
    
    if ($i -lt $RepeatCount) {
        Write-Host "`n⏳ Waiting $DelaySeconds seconds before next test..."
        Start-Sleep -Seconds $DelaySeconds
    }
}

# Summary
Write-Host "`n`n╔═══════════════════════════════════════════════════════╗"
Write-Host "║  Test Summary                                         ║"
Write-Host "╚═══════════════════════════════════════════════════════╝"

if ($FailedTests.Count -eq 0) {
    Write-Host "✅ All tests passed!"
} else {
    Write-Host "❌ Failed tests: $($FailedTests -join ', ')"
}
```

Run it:
```powershell
.\test_system.ps1 -RepeatCount 3 -DelaySeconds 120
```

### Option 3: Scheduled Verification

Create `verify_daily.ps1` for daily checks:

```powershell
$LogFile = "C:\Users\PC\Desktop\website\backend\logs\verification_$(Get-Date -Format 'yyyy-MM-dd').log"

Add-Content $LogFile "═══ Verification Run: $(Get-Date) ═══"

$result = Invoke-WebRequest -Uri "http://localhost:8000/predictions/trigger-manual" -Method POST | ConvertFrom-Json
Add-Content $LogFile "Status: $($result.status)"
Add-Content $LogFile "Predictions Saved: $($result.predictions_saved)"
Add-Content $LogFile "Duration: $($result.duration_seconds)s"

if ($result.errors.Count -gt 0) {
    Add-Content $LogFile "Errors: $($result.errors -join ', ')"
}
```

---

## 📈 Expected Daily Flow

```
4:00 PM (16:00) Eastern Time
    ↓
APScheduler triggers pipeline
    ↓
1. Check/initialize database
2. Scrape new stock data (optional if yfinance installed)
3. Load 176,029 stock records
4. Generate 141-143 predictions using:
   - Technical indicators (RSI, MACD, SMA)
   - News sentiment
   - Social media sentiment
5. Save predictions to SQLite
6. Export backup CSV
    ↓
Frontend can now display latest predictions
API users can fetch predictions
    ↓
Next day at 4:00 PM: repeat
```

---

## 🔍 Monitoring & Logs

### View Real-time Logs
```powershell
# Scheduler logs
Get-Content -Wait backend/logs/scheduler_*.log

# Scraper logs
Get-Content -Wait backend/logs/scraper_*.log

# Predictor logs
Get-Content -Wait backend/logs/predictor_*.log
```

### Check Database Size
```powershell
$DbSize = (Get-Item backend/data/predictions.db).Length / 1024 / 1024
Write-Host "Database size: $($DbSize)MB"
```

---

## ✅ Quick Verification Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] API docs available at http://localhost:8000/docs
- [ ] Manual pipeline trigger returns 141+ predictions
- [ ] Database file grows after each run
- [ ] Predictions appear in API responses
- [ ] Scheduler confirms it's running at startup
- [ ] Logs show successful execution

---

## 📊 Key Metrics to Monitor

| Metric | Expected | Warning |
|--------|----------|---------|
| Pipeline Duration | 3-5 seconds | > 30 seconds |
| Predictions Saved | 141-143 | < 100 |
| API Response Time | < 100ms | > 1000ms |
| Database Growth | +141 rows/day | 0 rows |
| Scraper Errors | 0-2 | > 5 |

---

## 🛠️ Troubleshooting

### "Connection refused" on :8000
```powershell
# Kill all Python processes
Get-Process python | Stop-Process -Force
# Wait and restart
```

### "Module not found" errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt
```

### No predictions showing
```powershell
# Check if data files exist
ls backend/data/stock_data_clean.csv
ls backend/data/news_clean.csv

# Check database
sqlite3 backend/data/predictions.db "SELECT COUNT(*) FROM daily_predictions;"
```

---

## 📝 Next Steps

1. **Install yfinance** for daily scraping:
   ```powershell
   pip install yfinance
   ```

2. **Run complete system:**
   ```powershell
   # Terminal 1: Backend
   cd backend
   uvicorn main:app --port 8000
   
   # Terminal 2: Frontend
   npm run dev
   
   # Terminal 3: Monitor
   .\test_system.ps1 -RepeatCount 1
   ```

3. **Set up Windows Task Scheduler** for automated verification (optional)

4. **Monitor logs daily** for errors and performance
