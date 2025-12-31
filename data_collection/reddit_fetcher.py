"""
Reddit data fetcher using PRAW library.
Fetches posts from specified subreddit.
"""
import praw
from datetime import datetime
from typing import List, Dict, Optional
from config.config import Config


class RedditFetcher:
    """Fetch posts from Reddit using PRAW."""
    
    def __init__(self, subreddit_name=None):
        """Initialize Reddit API connection.
        
        Args:
            subreddit_name: Name of subreddit to fetch from. If None, uses Config.SUBREDDIT
        """
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT
        )
        self.subreddit_name = subreddit_name or Config.SUBREDDIT
        self.subreddit = self.reddit.subreddit(self.subreddit_name)
        
    def fetch_posts(self, limit: int = None, time_filter: str = None) -> List[Dict]:
        """
        Fetch posts from the subreddit.
        
        Args:
            limit: Maximum number of posts to fetch (default: Config.MAX_POSTS_PER_FETCH)
            time_filter: Time filter for top posts (default: Config.FETCH_TIME_FILTER)
            
        Returns:
            List of dictionaries containing post data
        """
        if limit is None:
            limit = Config.MAX_POSTS_PER_FETCH
        if time_filter is None:
            time_filter = Config.FETCH_TIME_FILTER
            
        posts_data = []
        
        try:
            # Fetch from multiple sources for better coverage
            sources = [
                ('hot', self.subreddit.hot(limit=limit // 3)),
                ('new', self.subreddit.new(limit=limit // 3)),
                ('top', self.subreddit.top(time_filter=time_filter, limit=limit // 3))
            ]
            
            seen_ids = set()
            
            for source_name, posts in sources:
                for post in posts:
                    if post.id in seen_ids:
                        continue
                    seen_ids.add(post.id)
                    
                    # Only process text posts (with selftext) or titles
                    text_content = post.selftext if post.selftext else post.title
                    
                    # Skip if text is too short
                    if len(text_content) < Config.MIN_TEXT_LENGTH:
                        continue
                    
                    post_data = {
                        'post_id': post.id,
                        'title': post.title,
                        'text': post.selftext if post.selftext else '',
                        'full_text': f"{post.title}. {post.selftext}" if post.selftext else post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'created_utc': datetime.fromtimestamp(post.created_utc),
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'url': post.url,
                        'permalink': f"https://reddit.com{post.permalink}",
                        'source': source_name,
                        'subreddit': self.subreddit_name,
                        'fetched_at': datetime.now()
                    }
                    
                    posts_data.append(post_data)
            
            print(f"✓ Fetched {len(posts_data)} posts from r/{self.subreddit_name}")
            return posts_data
            
        except Exception as e:
            print(f"✗ Error fetching posts from r/{self.subreddit_name}: {str(e)}")
            return []

    def fetch_comments_for_posts(
        self,
        posts: List[Dict],
        max_comments_per_post: Optional[int] = None,
        comment_sort: Optional[str] = None,
        min_comment_length: Optional[int] = None,
    ) -> List[Dict]:
        """Fetch comments for the given posts (by post_id)."""
        if max_comments_per_post is None:
            max_comments_per_post = Config.MAX_COMMENTS_PER_POST
        if comment_sort is None:
            comment_sort = Config.COMMENT_SORT
        if min_comment_length is None:
            min_comment_length = Config.MIN_COMMENT_LENGTH

        comments: List[Dict] = []
        if not posts:
            return comments

        for post in posts:
            post_id = post.get('post_id')
            if not post_id:
                continue

            try:
                submission = self.reddit.submission(id=post_id)
                submission.comment_sort = comment_sort
                submission.comments.replace_more(limit=0)

                all_comments = submission.comments.list()
                # Prefer higher score comments; fall back to existing order if score missing
                all_comments.sort(key=lambda c: getattr(c, 'score', 0), reverse=True)

                taken = 0
                for c in all_comments:
                    if taken >= max_comments_per_post:
                        break

                    body = getattr(c, 'body', '') or ''
                    if len(body.strip()) < min_comment_length:
                        continue

                    comments.append({
                        'comment_id': c.id,
                        'post_id': post_id,
                        'subreddit': Config.SUBREDDIT,
                        'author': str(c.author) if c.author else '[deleted]',
                        'body': body,
                        'score': getattr(c, 'score', 0),
                        'created_utc': datetime.fromtimestamp(getattr(c, 'created_utc', 0)),
                        'permalink': f"https://reddit.com{c.permalink}",
                        'depth': getattr(c, 'depth', 0),
                        'fetched_at': datetime.now(),
                    })
                    taken += 1
            except Exception as e:
                print(f"✗ Error fetching comments for post {post_id}: {str(e)}")

        print(f"✓ Fetched {len(comments)} comments (up to {max_comments_per_post} per post)")
        return comments
    
    def test_connection(self) -> bool:
        """Test if Reddit API connection is working."""
        try:
            subreddit_info = self.subreddit.display_name
            print(f"✓ Successfully connected to r/{subreddit_info}")
            print(f"  Subscribers: {self.subreddit.subscribers:,}")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            return False


if __name__ == "__main__":
    # Test the fetcher
    fetcher = RedditFetcher()
    if fetcher.test_connection():
        posts = fetcher.fetch_posts(limit=10)
        print(f"\nSample post:")
        if posts:
            print(f"Title: {posts[0]['title']}")
            print(f"Score: {posts[0]['score']}")
            print(f"Text length: {len(posts[0]['full_text'])} characters")
