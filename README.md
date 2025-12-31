# Reddit Sentiment Analysis Dashboard

A real-time sentiment analysis dashboard for Reddit posts from city subreddits. Currently configured for **r/gurgaon**.

## Features

- 📥 Fetch posts from Reddit using PRAW
- 🧠 Sentiment analysis using VADER (optimized for social media)
- 💾 SQLite database for storage
- 📊 Interactive Streamlit dashboard with visualizations
- 📈 Track sentiment over time
- 🔍 View top positive, negative, and popular posts

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials (Optional)

The Reddit API credentials are already configured in `config/config.py` using the credentials from `apicreds.md`.

If you want to use environment variables instead, create a `.env` file:

```bash
cp .env.example .env
```

Then edit `.env` with your credentials (though they're already set in the code).

### 3. Run Data Collection

Fetch posts and analyze sentiment:

```bash
python main.py
```

This will:
- Connect to Reddit API
- Fetch posts from r/gurgaon
- Analyze sentiment using VADER
- Store results in SQLite database (`reddit_analysis.db`)

### 4. Launch Dashboard

View the interactive dashboard:

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
