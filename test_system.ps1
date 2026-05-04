param(
    [int]$RepeatCount = 1,
    [int]$DelaySeconds = 300
)

$BaseUrl = "http://localhost:8000"
$PassedTests = 0
$FailedTests = 0

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     StockSense AI - Complete System Verification           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

for ($run = 1; $run -le $RepeatCount; $run++) {
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║  Test Run $run of $RepeatCount - $(Get-Date -Format 'HH:mm:ss')                        ║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Blue

    # Test 1: Backend Health
    Write-Host "`n[1/8] Testing Backend Health..." -ForegroundColor Yellow
    try {
        $health = Invoke-WebRequest -Uri "$BaseUrl/health" -TimeoutSec 5 | ConvertFrom-Json
        Write-Host "✅ Backend running - $($health.symbols_loaded) symbols loaded" -ForegroundColor Green
        $PassedTests++
    }
    catch {
        Write-Host "❌ Backend not responding" -ForegroundColor Red
        $FailedTests++
    }

    # Test 2: Stocks Endpoint
    Write-Host "[2/8] Testing /stocks endpoint..." -ForegroundColor Yellow
    try {
        $stocks = Invoke-WebRequest -Uri "$BaseUrl/stocks" -TimeoutSec 5 | ConvertFrom-Json
        Write-Host "✅ Stocks endpoint working - $($stocks.total) stocks found" -ForegroundColor Green
        $PassedTests++
    }
    catch {
        Write-Host "❌ Stocks endpoint failed" -ForegroundColor Red
        $FailedTests++
    }

    # Test 3: Predictions Endpoint
    Write-Host "[3/8] Testing /predictions endpoint..." -ForegroundColor Yellow
    try {
        $preds = Invoke-WebRequest -Uri "$BaseUrl/predictions/" -TimeoutSec 5 | ConvertFrom-Json
        Write-Host "✅ Predictions endpoint working - $($preds.total) predictions" -ForegroundColor Green
        $PassedTests++
    }
    catch {
        Write-Host "⚠️  No predictions yet (first run)" -ForegroundColor Yellow
    }

    # Test 4: Specific Stock
    Write-Host "[4/8] Testing /predict/AAPL..." -ForegroundColor Yellow
    try {
        $pred = Invoke-WebRequest -Uri "$BaseUrl/predict/AAPL" -TimeoutSec 5 | ConvertFrom-Json
        Write-Host "✅ AAPL prediction: $($pred.direction) (confidence: $($pred.confidence))" -ForegroundColor Green
        $PassedTests++
    }
    catch {
        Write-Host "⚠️  No prediction for AAPL yet" -ForegroundColor Yellow
    }

    # Test 5: Pipeline Execution
    Write-Host "[5/8] Testing Pipeline (This may take 5-10 seconds)..." -ForegroundColor Yellow
    try {
        Write-Host "⏳ Running pipeline..." -ForegroundColor Cyan
        $result = Invoke-WebRequest -Uri "$BaseUrl/predictions/trigger-manual" -Method POST -TimeoutSec 120 | ConvertFrom-Json
        Write-Host "✅ Pipeline executed - Status: $($result.status)" -ForegroundColor Green
        Write-Host "   - Predictions saved: $($result.predictions_saved)" -ForegroundColor Green
        Write-Host "   - Duration: $($result.duration_seconds)s" -ForegroundColor Green
        if ($result.errors -and $result.errors.Count -gt 0) {
            Write-Host "   - Warnings: $($result.errors[0])" -ForegroundColor Yellow
        }
        $PassedTests++
    }
    catch {
        Write-Host "❌ Pipeline execution failed: $_" -ForegroundColor Red
        $FailedTests++
    }

    # Test 6: Database
    Write-Host "[6/8] Testing Database..." -ForegroundColor Yellow
    $DbPath = "C:\Users\PC\Desktop\website\backend\data\predictions.db"
    if (Test-Path $DbPath) {
        $Size = (Get-Item $DbPath).Length / 1024
        Write-Host "✅ Database exists - Size: $($Size)KB" -ForegroundColor Green
        $PassedTests++
    }
    else {
        Write-Host "❌ Database not found" -ForegroundColor Red
        $FailedTests++
    }

    # Test 7: Logs
    Write-Host "[7/8] Checking Logs..." -ForegroundColor Yellow
    $LogDir = "C:\Users\PC\Desktop\website\backend\logs"
    if (Test-Path $LogDir) {
        $Logs = @(Get-ChildItem $LogDir -Filter "*.log" -ErrorAction SilentlyContinue)
        Write-Host "✅ Log files found: $($Logs.Count)" -ForegroundColor Green
        $PassedTests++
    }
    else {
        Write-Host "⚠️  Log directory not found" -ForegroundColor Yellow
    }

    # Test 8: Frontend
    Write-Host "[8/8] Testing Frontend..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -ErrorAction SilentlyContinue
        Write-Host "✅ Frontend running at http://localhost:3000" -ForegroundColor Green
        $PassedTests++
    }
    catch {
        Write-Host "⚠️  Frontend not running (start with: npm run dev)" -ForegroundColor Yellow
    }

    # Summary
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "📊 Test Summary - Run $run" -ForegroundColor Green
    Write-Host "   ✅ Passed: $PassedTests" -ForegroundColor Green
    Write-Host "   ❌ Failed: $FailedTests" -ForegroundColor Red
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

    if ($run -lt $RepeatCount) {
        Write-Host "`n⏳ Next test in $DelaySeconds seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds $DelaySeconds
    }
}

Write-Host "`n✅ All tests completed!" -ForegroundColor Green
Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   • Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   • API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   • Backend: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
