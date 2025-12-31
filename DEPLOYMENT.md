# Reddit Sentiment Analysis - Deployment Guide

## 🚀 Replit Deployment

This application is ready to deploy on Replit! It runs both data collection and dashboard simultaneously.

### Quick Deploy Steps

1. **Import to Replit**
   - Go to https://replit.com
   - Click "Create Repl" → "Import from GitHub"
   - Or upload this folder directly

2. **Set Environment Variables** (Optional)
   - `COLLECTION_INTERVAL_HOURS=6` - How often to collect data (default: 6 hours)
   - `PORT=8501` - Port for Streamlit (Replit will override this)

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python run.py
   ```
   
   Or simply click the "Run" button in Replit!

### What Happens When You Run

1. **Background Scheduler Starts**
   - Collects data from all cities immediately
   - Schedules automatic collection every 6 hours
   - Runs silently in background

2. **Streamlit Dashboard Launches**
   - Opens in your browser
   - Shows real-time sentiment data
   - Auto-updates as new data is collected

### Application Structure

```
run.py                 # Main entry point (starts everything)
├── scheduler.py       # Background data collection (runs every 6h)
└── dashboard/app.py   # Streamlit web interface
```

## 🌐 Alternative Deployment Options

### Railway

1. Create new project on Railway.app
2. Connect GitHub repo or upload files
3. Add environment variables (optional)
4. Deploy with command: `python run.py`

### Render

1. Create new "Web Service" on Render.com
2. Build command: `pip install -r requirements.txt`
3. Start command: `python run.py`
4. Auto-deploys on git push

### Heroku

1. Create `Procfile`:
   ```
   web: python run.py
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Docker

1. Create `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 8501
   CMD ["python", "run.py"]
   ```

2. Build and run:
   ```bash
   docker build -t reddit-sentiment .
   docker run -p 8501:8501 reddit-sentiment
   ```

## ⚙️ Configuration

### Adjust Collection Frequency

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

Run separately for development:

**Terminal 1 - Data Collection:**
```bash
python collect_cities.py  # One-time collection
# or
python scheduler.py       # Continuous scheduled collection
```

**Terminal 2 - Dashboard:**
```bash
python -m streamlit run dashboard/app.py
```

## 📊 Monitoring

The scheduler logs all collection activities:
- Check console/logs for collection status
- Database grows automatically with each collection
- Dashboard reflects new data immediately

## 🐛 Troubleshooting

**Issue**: Scheduler not collecting data
- Check Reddit API credentials in `config/config.py`
- Verify rate limits aren't exceeded
- Check logs for error messages

**Issue**: Dashboard won't load
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
