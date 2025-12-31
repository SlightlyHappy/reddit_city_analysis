"""
Configuration loader for Reddit API credentials and app settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    # Reddit API Credentials - MUST be set via environment variables
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'RedditAnalysisBot/1.0')
    
    # Validate credentials
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError(
            "Missing Reddit API credentials! "
            "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
        )
    
    # City Subreddit Mappings
    CITIES = {
        'Gurgaon': 'gurgaon',
        'New York': 'nyc',
        'Paris': 'paris',
        'Delhi': 'delhi',
        'Tokyo': 'tokyo'
    }
    
    # Legacy single subreddit support
    SUBREDDIT = os.getenv('SUBREDDIT', 'gurgaon')
    
    # Database
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reddit_analysis.db')
    
    # Data Collection Settings
    MAX_POSTS_PER_FETCH = 100  # Number of posts to fetch per run
    FETCH_TIME_FILTER = 'week'  # Options: hour, day, week, month, year, all

    # Comment Collection Settings
    FETCH_COMMENTS = os.getenv('FETCH_COMMENTS', 'true').lower() in ('1', 'true', 'yes', 'y')
    MAX_COMMENTS_PER_POST = int(os.getenv('MAX_COMMENTS_PER_POST', '50'))
    COMMENT_SORT = os.getenv('COMMENT_SORT', 'top')  # top | new | best | controversial
    MIN_COMMENT_LENGTH = int(os.getenv('MIN_COMMENT_LENGTH', '10'))
    
    # Analysis Settings
    MIN_TEXT_LENGTH = 10  # Minimum text length to analyze (characters)

    # Sentiment bucket thresholds
    VERY_POSITIVE_THRESHOLD = float(os.getenv('VERY_POSITIVE_THRESHOLD', '0.6'))
    VERY_NEGATIVE_THRESHOLD = float(os.getenv('VERY_NEGATIVE_THRESHOLD', '-0.6'))
    
    @classmethod
    def validate(cls):
        """Validate that required credentials are present."""
        if not cls.REDDIT_CLIENT_ID or cls.REDDIT_CLIENT_ID == 'your_client_id_here':
            raise ValueError("REDDIT_CLIENT_ID not configured")
        if not cls.REDDIT_CLIENT_SECRET or cls.REDDIT_CLIENT_SECRET == 'your_client_secret_here':
            raise ValueError("REDDIT_CLIENT_SECRET not configured")
        return True


# Validate config on import
Config.validate()
