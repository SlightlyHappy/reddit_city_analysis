# Reddit City Sentiment Analysis Dashboard

A real-time sentiment analysis dashboard comparing Reddit sentiment across multiple cities worldwide.

## 🌍 Cities Tracked

- **Gurgaon** (r/gurgaon)
- **New York** (r/nyc)  
- **Paris** (r/paris)
- **Delhi** (r/delhi)
- **Tokyo** (r/tokyo)

## ✨ Features

- 📥 Automated data collection from multiple city subreddits
- 🧠 Sentiment analysis using VADER (optimized for social media)
- 💬 Comment analysis with up to 50 comments per post
- 📊 Interactive Streamlit dashboard with rich visualizations
- 🏙️ Multi-city comparison and rankings
- ☁️ Word clouds and keyword extraction
- 📈 Historical trends and engagement metrics
- 🔄 Background scheduler for automatic updates every 6 hours
- 💾 SQLite database for persistent storage

## 🚀 Quick Start

### For Streamlit Cloud (Recommended)

1. **Fork this repository**
2. **Deploy to Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select this repository
   - Main file: `dashboard/app.py`
   - Click "Deploy"!

The app will automatically:
- Collect initial data from all cities
- Start background scheduler for updates every 6 hours
- Display live dashboard

### For Local Development

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Run the Application

**Option A - Unified App (Recommended):**
```bash
streamlit run dashboard/app.py
```

This automatically starts:
- Background data collection scheduler
- Interactive dashboard
- Updates every 6 hours

**Option B - Manual Collection:**
```bash
# Collect data once
python collect_cities.py

# Then run dashboard
streamlit run dashboard/app.py
```

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Project Structure

```
redditanalysis/
├── config/
│   └── config.py              # Configuration and credentials
├── data_collection/
│   └── reddit_fetcher.py      # Reddit API data fetcher
├── analysis/
│   └── sentiment_analyzer.py  # VADER sentiment analysis
├── database/
│   └── db_handler.py          # SQLite database operations
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── main.py                    # Main orchestrator script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Usage

### Collect Data Regularly

For a live dashboard, run the data collection script periodically:

```bash
# Every hour (example using cron on Linux/Mac)
0 * * * * cd /path/to/redditanalysis && python main.py

# Or use Windows Task Scheduler on Windows
```

### Change Target Subreddit

Edit `config/config.py` and change the `SUBREDDIT` variable:

```python
SUBREDDIT = os.getenv('SUBREDDIT', 'mumbai')  # Change 'gurgaon' to your city
```

### Adjust Fetch Settings

In `config/config.py`:

```python
MAX_POSTS_PER_FETCH = 100        # Number of posts per fetch
FETCH_TIME_FILTER = 'week'       # Options: hour, day, week, month, year, all
MIN_TEXT_LENGTH = 10             # Minimum text length to analyze
```

## Dashboard Features

### Metrics
- Total posts analyzed
- Sentiment distribution (Positive/Negative/Neutral)
- Average sentiment score

### Visualizations
- **Pie Chart**: Sentiment distribution
- **Histogram**: Sentiment score distribution
- **Timeline**: Sentiment trends over time

### Post Explorer
- Most positive posts
- Most negative posts
- Most popular posts (by score)

## How Sentiment Analysis Works

Uses **VADER** (Valence Aware Dictionary and sEntiment Reasoner):
- Optimized for social media text
- No training required
- Provides scores from -1 (very negative) to +1 (very positive)

**Classification**:
- Positive: compound score >= 0.05
- Negative: compound score <= -0.05
- Neutral: compound score between -0.05 and 0.05

## Troubleshooting

### No posts appearing?
- Check Reddit API credentials in `config/config.py`
- Verify subreddit name is correct
- Check rate limits (60 requests/minute for Reddit API)

### Dashboard shows no data?
- Run `python main.py` first to collect data
- Check if `reddit_analysis.db` file exists

### Import errors?
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Ensure you're running from the project root directory

## Next Steps

### Enhancements
- [ ] Add multiple city comparison
- [ ] Topic modeling (what are people talking about?)
- [ ] Word clouds for trending topics
- [ ] Email alerts for sentiment spikes
- [ ] Export data to CSV/JSON
- [ ] Add time-based filters in dashboard
- [ ] Implement caching for faster dashboard loads

## License

MIT License

## Credits

Built with:
- [PRAW](https://praw.readthedocs.io/) - Python Reddit API Wrapper
- [VADER Sentiment](https://github.com/cjhutto/vaderSentiment) - Sentiment Analysis
- [Streamlit](https://streamlit.io/) - Dashboard Framework
- [Plotly](https://plotly.com/) - Interactive Visualizations
# reddit_city_analysis
