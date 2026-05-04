# Deployment Guide: Render + Vercel

## 🚀 Complete Deployment Steps (30 minutes)

---

## **PART 1: Prepare for Deployment**

### Step 1.1: Commit Code to GitHub

```powershell
cd C:\Users\PC\Desktop\website

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial StockSense AI deployment setup"

# Create GitHub repo and push
# Then run:
git remote add origin https://github.com/YOUR_USERNAME/stocksense-ai.git
git branch -M main
git push -u origin main
```

✅ **Result:** Code on GitHub

---

## **PART 2: Deploy Backend to Render**

### Step 2.1: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub (easiest)
3. Click "New +" → "Web Service"
4. Connect GitHub repo

### Step 2.2: Configure Backend Service

| Setting | Value |
|---------|-------|
| **Name** | stocksense-api |
| **Environment** | Python 3 |
| **Build Command** | `pip install -r backend/requirements.txt` |
| **Start Command** | `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free (or $7/month Starter) |
| **Auto-deploy** | Yes |

### Step 2.3: Set Environment Variables

In Render dashboard → Environment:

```
API_HOST=0.0.0.0
API_PORT=8000
SCHEDULER_TIME=16:00
TIMEZONE=US/Eastern
```

✅ **Result:** Backend deployed at `https://stocksense-api.onrender.com`

---

## **PART 3: Deploy Frontend to Vercel**

### Step 3.1: Create Vercel Account

1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Add New Project"
4. Select your GitHub repo

### Step 3.2: Configure Frontend

| Setting | Value |
|---------|-------|
| **Framework** | Next.js |
| **Root Directory** | ./ |
| **Build Command** | `npm run build` |
| **Output Directory** | .next |

### Step 3.3: Set Environment Variables

In Vercel → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://stocksense-api.onrender.com
```

### Step 3.4: Deploy

Click "Deploy" and wait 2-3 minutes.

✅ **Result:** Frontend deployed at `https://your-project.vercel.app`

---

## **PART 4: Verify Deployment**

### Test Backend

```powershell
# Get your Render URL from dashboard
$BACKEND_URL = "https://stocksense-api.onrender.com"

# Test health
Invoke-WebRequest -Uri "$BACKEND_URL/health" | ConvertFrom-Json

# Should return:
# status: "ok"
# symbols_loaded: 144
```

### Test Frontend

```powershell
# Open in browser
Start-Process "https://your-project.vercel.app"
```

---

## **PART 5: Enable Auto-Scaling (Keep Backend Awake)**

### Option A: Render (Free Plan Issue)
Free tier sleeps after 15 mins of inactivity. To keep it awake:

**Solution:** Upgrade to $7/month or use UptimeRobot (free)

### Option B: UptimeRobot (Recommended for Free)

1. Go to https://uptimerobot.com (free)
2. Sign up
3. Create monitor → HTTP(s)
4. URL: `https://stocksense-api.onrender.com/health`
5. Interval: 5 minutes
6. ✅ This will ping every 5 minutes and keep it alive!

---

## **PART 6: Daily Pipeline Verification**

Your pipeline runs automatically at **4:00 PM ET daily**.

### Check if Running

```powershell
# Check in the morning
$BACKEND_URL = "https://stocksense-api.onrender.com"

$result = Invoke-WebRequest -Uri "$BACKEND_URL/predictions/trigger-manual" -Method POST | ConvertFrom-Json
Write-Host "Status: $($result.status)"
Write-Host "Predictions saved: $($result.predictions_saved)"
```

### Monitor via Logs

In Render Dashboard → Logs (real-time)

```
Look for:
✅ [1/5] Initializing database...
✅ [2/5] Scraping new stock data...
✅ [3/5] Loading data for prediction...
✅ [4/5] Running predictions...
✅ [5/5] Exporting backup...
```

---

## **Deployment Summary**

```
Frontend: https://your-project.vercel.app
Backend: https://stocksense-api.onrender.com

Daily Schedule: 4:00 PM ET

Automatic:
✅ Stock scraping
✅ Predictions generation
✅ Database storage
✅ API available 24/7
```

---

## **Cost Breakdown**

| Service | Free Tier | Starter |
|---------|-----------|---------|
| **Vercel** | ✅ Free | - |
| **Render** | ✅ Free (sleeps) | $7/month |
| **UptimeRobot** | ✅ Free | - |
| **Total** | **$0/month** | **$7/month** |

**Recommendation:** Free tier with UptimeRobot = Fully operational 24/7 at $0/month

---

## **Quick Links After Deployment**

```
Frontend Dashboard: https://your-project.vercel.app
API Docs: https://stocksense-api.onrender.com/docs
Health Check: https://stocksense-api.onrender.com/health
```

---

## **Troubleshooting**

### Backend won't start on Render

Check logs for:
- Missing dependencies → Fix `requirements.txt`
- Port issues → Render sets `$PORT` automatically
- Module imports → Ensure all files included

### Frontend can't reach backend

- Verify `NEXT_PUBLIC_API_URL` is set in Vercel
- Check CORS in backend (`main.py` line 88-94)
- Should allow `https://*.vercel.app`

### Predictions not running

- Check Render logs at 4:00 PM ET
- Verify scheduler is enabled
- UptimeRobot should ping health endpoint every 5 min

---

## **Next: Automated Monitoring**

Set up alerts:
1. **UptimeRobot**: Get notified if backend goes down
2. **Render**: Email on deployment failure
3. **Vercel**: Email on build failures

---

## **Post-Deployment Checklist**

- [ ] GitHub repo created and pushed
- [ ] Render backend deployed
- [ ] Vercel frontend deployed
- [ ] Environment variables set in both
- [ ] UptimeRobot monitoring health endpoint
- [ ] Tested `/health` endpoint working
- [ ] Tested `/predict/AAPL` returns predictions
- [ ] Frontend displays predictions
- [ ] Scheduler running (check 4:00 PM ET)
- [ ] Database growing with predictions
