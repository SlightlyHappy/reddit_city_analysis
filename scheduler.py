"""
Background scheduler for periodic data collection.
Runs data collection at specified intervals.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from data_collection.reddit_fetcher import RedditFetcher
from analysis.sentiment_analyzer import SentimentAnalyzer
from database.db_handler import DatabaseHandler
from config.config import Config
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollectionScheduler:
    """Scheduler for automated data collection."""
    
    def __init__(self, interval_hours=6):
        """
        Initialize scheduler.
        
        Args:
            interval_hours: How often to collect data (in hours)
        """
        self.scheduler = BackgroundScheduler()
        self.interval_hours = interval_hours
        self.analyzer = SentimentAnalyzer()
        self.db = DatabaseHandler()
        
    def collect_data(self):
        """Collect data from all cities."""
        logger.info("=" * 60)
        logger.info("Starting scheduled data collection")
        logger.info(f"Cities: {', '.join(Config.CITIES.keys())}")
        logger.info("=" * 60)
        
        total_posts = 0
        total_comments = 0
        
        for city_name, subreddit_name in Config.CITIES.items():
            try:
                logger.info(f"Processing {city_name} (r/{subreddit_name})...")
                
                # Create fetcher
                fetcher = RedditFetcher(subreddit_name)
                
                # Fetch and analyze posts
                posts = fetcher.fetch_posts()
                if not posts:
                    logger.warning(f"No posts fetched from r/{subreddit_name}")
                    continue
                
                analyzed_posts = self.analyzer.analyze_posts(posts)
                inserted = self.db.insert_posts(analyzed_posts)
                total_posts += inserted
                
                logger.info(f"✓ {city_name}: {inserted} posts stored")
                
                # Fetch and analyze comments (if enabled)
                if hasattr(Config, 'FETCH_COMMENTS') and Config.FETCH_COMMENTS:
                    if hasattr(fetcher, 'fetch_comments_for_posts'):
                        comments = fetcher.fetch_comments_for_posts(analyzed_posts)
                        if comments:
                            if hasattr(self.analyzer, 'analyze_items'):
                                analyzed_comments = self.analyzer.analyze_items(comments, text_key='body')
                            else:
                                analyzed_comments = comments
                            stored = self.db.insert_comments(analyzed_comments)
                            total_comments += stored
                            logger.info(f"✓ {city_name}: {stored} comments stored")
                
            except Exception as e:
                logger.error(f"Error processing {city_name}: {str(e)}")
                continue
        
        logger.info("=" * 60)
        logger.info(f"Collection complete: {total_posts} posts, {total_comments} comments")
        logger.info("=" * 60)
    
    def start(self):
        """Start the scheduler."""
        # Run immediately on start
        logger.info(f"Starting scheduler - will collect data every {self.interval_hours} hours")
        self.collect_data()
        
        # Schedule periodic collection
        self.scheduler.add_job(
            self.collect_data,
            'interval',
            hours=self.interval_hours,
            id='data_collection',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    # Test the scheduler
    scheduler = DataCollectionScheduler(interval_hours=1)
    scheduler.start()
    
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()
        print("\nScheduler stopped by user")
