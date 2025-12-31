"""
Main script to orchestrate Reddit data collection, sentiment analysis, and storage.
Run this script to fetch posts, analyze sentiment, and store in database.
"""
from data_collection.reddit_fetcher import RedditFetcher
from analysis.sentiment_analyzer import SentimentAnalyzer
from database.db_handler import DatabaseHandler
from config.config import Config
from datetime import datetime


def main():
    """Main execution function."""
    print("=" * 60)
    print("Reddit Sentiment Analysis - Data Collection Pipeline")
    print("=" * 60)
    print(f"Target: r/{Config.SUBREDDIT}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Step 1: Initialize components
    print("🔧 Initializing components...")
    fetcher = RedditFetcher()
    analyzer = SentimentAnalyzer()
    db = DatabaseHandler()
    print()
    
    # Step 2: Test Reddit connection
    print("🔌 Testing Reddit API connection...")
    if not fetcher.test_connection():
        print("❌ Failed to connect to Reddit API. Please check credentials.")
        return
    print()
    
    # Step 3: Fetch posts
    print(f"📥 Fetching posts from r/{Config.SUBREDDIT}...")
    posts = fetcher.fetch_posts()
    
    if not posts:
        print("⚠️  No posts fetched. Exiting.")
        return
    
    print(f"✅ Fetched {len(posts)} posts")
    print()
    
    # Step 4: Analyze sentiment
    print("🧠 Analyzing sentiment...")
    analyzed_posts = analyzer.analyze_posts(posts)
    
    # Show summary
    summary = analyzer.get_summary_stats(analyzed_posts)
    print(f"✅ Analysis complete!")
    print(f"   Positive: {summary['positive_count']} ({summary['positive_pct']}%)")
    print(f"   Negative: {summary['negative_count']} ({summary['negative_pct']}%)")
    print(f"   Neutral:  {summary['neutral_count']} ({summary['neutral_pct']}%)")
    print(f"   Avg Sentiment Score: {summary['avg_compound_score']}")
    print()
    
    # Step 5: Store in database
    print("💾 Storing in database...")
    inserted = db.insert_posts(analyzed_posts)
    print(f"✅ Stored {inserted} posts")
    print()

    # Step 5b: Fetch + analyze + store comments (optional)
    if Config.FETCH_COMMENTS:
        print("💬 Fetching comments...")
        comments = fetcher.fetch_comments_for_posts(analyzed_posts)

        if comments:
            print("🧠 Analyzing comment sentiment...")
            analyzed_comments = analyzer.analyze_items(comments, text_key='body')
            stored_comments = db.insert_comments(analyzed_comments)
            print(f"✅ Stored {stored_comments} comments")
        else:
            print("⚠️  No comments fetched")
        print()
    
    # Step 6: Show database stats
    print("📊 Database Statistics:")
    db_stats = db.get_database_stats()
    print(f"   Total posts in DB: {db_stats['total_posts']}")
    print(f"   Total comments in DB: {db_stats.get('total_comments', 0)}")
    print(f"   Date range: {db_stats['earliest_post']} to {db_stats['latest_post']}")
    print()
    
    # Final message
    print("=" * 60)
    print("✨ Pipeline completed successfully!")
    print("=" * 60)
    print()
    print("🚀 Next steps:")
    print("   1. Run the dashboard: python -m streamlit run dashboard/app.py")
    print("   2. Schedule this script to run periodically for live updates")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
