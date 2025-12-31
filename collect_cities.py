"""
Multi-city data collection script.
Collects data from all configured cities.
"""
from data_collection.reddit_fetcher import RedditFetcher
from analysis.sentiment_analyzer import SentimentAnalyzer
from database.db_handler import DatabaseHandler
from config.config import Config
from datetime import datetime


def collect_all_cities():
    """Collect data from all cities."""
    print("=" * 60)
    print("Reddit Sentiment Analysis - Multi-City Data Collection")
    print("=" * 60)
    print(f"Cities: {', '.join(Config.CITIES.keys())}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Initialize shared components
    print("🔧 Initializing components...")
    analyzer = SentimentAnalyzer()
    db = DatabaseHandler()
    print()
    
    total_fetched = 0
    total_comments = 0
    
    # Loop through each city
    for city_name, subreddit_name in Config.CITIES.items():
        print(f"\n{'='*60}")
        print(f"🌆 Processing: {city_name} (r/{subreddit_name})")
        print(f"{'='*60}")
        
        # Create fetcher for this city
        fetcher = RedditFetcher(subreddit_name)
        
        # Test connection
        print(f"🔌 Testing connection to r/{subreddit_name}...")
        if not fetcher.test_connection():
            print(f"❌ Failed to connect to r/{subreddit_name}. Skipping...")
            continue
        print()
        
        # Fetch posts
        print(f"📥 Fetching posts from r/{subreddit_name}...")
        posts = fetcher.fetch_posts()
        
        if not posts:
            print(f"⚠️  No posts fetched from r/{subreddit_name}")
            continue
        
        total_fetched += len(posts)
        print(f"✅ Fetched {len(posts)} posts from {city_name}")
        
        # Analyze sentiment
        print(f"🧠 Analyzing sentiment for {city_name}...")
        analyzed_posts = analyzer.analyze_posts(posts)
        
        # Show summary for this city
        summary = analyzer.get_summary_stats(analyzed_posts)
        print(f"✅ {city_name} Analysis:")
        print(f"   Positive: {summary['positive_count']} ({summary['positive_pct']}%)")
        print(f"   Negative: {summary['negative_count']} ({summary['negative_pct']}%)")
        print(f"   Neutral:  {summary['neutral_count']} ({summary['neutral_pct']}%)")
        print(f"   Avg Sentiment: {summary['avg_compound_score']}")
        
        # Store in database
        print(f"💾 Storing {city_name} posts...")
        inserted = db.insert_posts(analyzed_posts)
        print(f"✅ Stored {inserted} posts from {city_name}")
        
        # Fetch + analyze + store comments (if enabled)
        if hasattr(Config, 'FETCH_COMMENTS') and Config.FETCH_COMMENTS:
            print(f"💬 Fetching comments for {city_name}...")
            if hasattr(fetcher, 'fetch_comments_for_posts'):
                comments = fetcher.fetch_comments_for_posts(analyzed_posts)

                if comments:
                    print(f"🧠 Analyzing comment sentiment for {city_name}...")
                    if hasattr(analyzer, 'analyze_items'):
                        analyzed_comments = analyzer.analyze_items(comments, text_key='body')
                    else:
                        analyzed_comments = comments
                    stored_comments = db.insert_comments(analyzed_comments)
                    print(f"✅ Stored {stored_comments} comments from {city_name}")
                    total_comments += stored_comments
                else:
                    print(f"⚠️  No comments fetched from {city_name}")
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 Overall Statistics")
    print(f"{'='*60}")
    print(f"   Total posts fetched: {total_fetched}")
    if total_comments > 0:
        print(f"   Total comments fetched: {total_comments}")
    print(f"   Cities processed: {len(Config.CITIES)}")
    
    db_stats = db.get_database_stats()
    print(f"   Total posts in DB: {db_stats['total_posts']}")
    if 'total_comments' in db_stats:
        print(f"   Total comments in DB: {db_stats['total_comments']}")
    print(f"   Subreddits tracked: {db_stats['subreddit_count']}")
    if db_stats.get('latest_post'):
        print(f"   Latest update: {db_stats['latest_post'][:16]}")
    print()
    
    print("=" * 60)
    print("✨ Multi-city collection completed!")
    print("=" * 60)
    print()
    print("🚀 Next steps:")
    print("   1. Run the dashboard: python -m streamlit run dashboard/app.py")
    print("   2. Compare sentiment across cities")
    print()


if __name__ == "__main__":
    try:
        collect_all_cities()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
