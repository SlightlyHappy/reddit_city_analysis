# Reddit Sentiment Analysis - Deployment Guide

## 🚀 Streamlit Cloud Deployment (Recommended)

This application is optimized for Streamlit Cloud with built-in background scheduling!

### Quick Deploy Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repository
   - Main file path: `dashboard/app.py`
   - Click "Deploy"!

3. **That's it!** The app will:
   - ✅ Collect data from all cities immediately
   - ✅ Start background scheduler (updates every 6 hours)
   - ✅ Display live dashboard with all features

### How It Works on Streamlit Cloud

- The dashboard automatically starts a background scheduler using `@st.cache_resource`
- Data collection happens in the background without blocking the UI
- Updates occur every 6 hours automatically
- SQLite database persists between app restarts

### Configuration (Optional)

Add these secrets in Streamlit Cloud settings if you want to customize:

```toml
# .streamlit/secrets.toml
COLLECTION_INTERVAL_HOURS = "6"  # Change collection frequency
```

## 🌐 Alternative Deployment Options

### Replit

1. **Import project** to Replit
2. **Configuration is already set** in `.replit` file
3. **Click Run** - That's it!
   - The app launches Streamlit with background scheduler
   - Dashboard opens automatically

### Railway

1. Create new project on Railway.app
2. Connect GitHub repo
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
5. Deploy!

### Render

1. Create new "Web Service"  
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
4. Auto-deploys on git push

### Heroku

1. Create `Procfile`:
   ```
   web: streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Dockestreamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
   ```

2. Build and run:
   ```bash
   docker build -t reddit-sentiment .
   docker run -p 8501:8501 reddit-sentiment
   ```

## ⚙️ Configuration

### Adjust Collection Frequency

Set environment variable:
```bash
export COLLECTION_INTERVAL_HOURS=12  # Change from default 6 hours
```

Or in Streamlit Cloud, add to `.streamlit/secrets.toml`:
```toml
COLLECTION_INTERVAL_HOURS = "12"

Edit `run.py` line 27:
```python
interval_hours = 6  # Change to your preferred interval
```

Or set environment variable:
```bash
export COLLECTION_INTERVAL_HOURS=12
```

### Change Cities

Edit `config/config.py`:
```python
CITIES = {
    'London': 'london',
    'Sydney': 'sydney',
    # Add more cities...
}
```

### Disable Comment Collection

In `config/config.py`, add:
```python
FETCH_COMMENTS = False
```

## 🔧 Local Development

Run the app locally:

```bash
# Single command - starts everything
streamlit run dashboard/app.py
```

This will:
- Start the Streamlit dashboard
- Automatically initialize background scheduler
- Collect data from all cities immediately
- Schedule updates every 6 hours

**Alternative - Manual data collection:**
```bash
# Collect data manually
python collect_cities.py
browser console in Streamlit Cloud logs
- Database grows automatically with each collection
- Dashboard reflects new data immediately after each collection cycle

## 🐛 Troubleshooting

**Issue**: No data showing in dashboard
- Wait 2-3 minutes for initial data collection to complete
- Check Streamlit Cloud logs for errors
- Verify Reddit API credentials in `config/config.py`

**Issue**: Scheduler not running
- The scheduler starts automatically when the app loads
- Uses `@st.cache_resource` to run once per app instance
- Check logs for "Background scheduler started successfully"

**Issue**: App showing "Port 8501 already in use"
- This error should NOT appear with current setup
- If it does, ensure you're running `streamlit run dashboard/app.py` not `python run.py`

**Issue**: Out of memory
- Reduce collection interval (set COLLECTION_INTERVAL_HOURS to higher value)
- Disable comment collection in `config/config.py`: `FETCH_COMMENTS = False`
- Clear old database records periodically

## 📝 Architecture Notes

### How Background Scheduling Works

The app uses Streamlit's `@st.cache_resource` decorator to create a singleton scheduler:

```python
@st.cache_resource
def start_background_scheduler():
    scheduler = DataCollectionScheduler(interval_hours=6)
    scheduler.start()
    return scheduler
```

This ensures:
- Scheduler starts once when app loads
- Runs in background thread
- Persists across page refreshes
- Works on all deployment platforms

### Why Not `run.py`?

For Streamlit Cloud and similar platforms:
- They manage the Streamlit process
- Running Streamlit manually causes port conflicts
- Integrating scheduler into the app is cleaner and more reliable

The `run.py` file is kept for backward compatibility but not recommended for cloud deployments.oad
- Ensure port 8501 is accessible
- Check for port conflicts
- Verify Streamlit is installed

**Issue**: Out of memory on Replit
- Reduce collection interval
- Disable comment collection
- Clear old database records

## 📝 Notes

- First run fetches data immediately
- Subsequent collections happen automatically
- Database persists between restarts
- Dashboard updates in real-time as data arrives

For support, check the logs or run components separately to isolate issues.
