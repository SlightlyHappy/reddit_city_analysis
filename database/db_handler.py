"""
SQLite database handler for storing Reddit posts and sentiment analysis.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from config.config import Config
import pandas as pd


class DatabaseHandler:
    """Handle SQLite database operations."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or Config.DB_PATH
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE NOT NULL,
                subreddit TEXT NOT NULL,
                title TEXT NOT NULL,
                text TEXT,
                full_text TEXT,
                author TEXT,
                created_utc TIMESTAMP,
                score INTEGER,
                upvote_ratio REAL,
                num_comments INTEGER,
                url TEXT,
                permalink TEXT,
                source TEXT,
                fetched_at TIMESTAMP,
                
                -- Sentiment fields
                positive REAL,
                neutral REAL,
                negative REAL,
                compound REAL,
                sentiment TEXT,
                sentiment_bucket TEXT,
                text_length INTEGER,
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE NOT NULL,
                post_id TEXT NOT NULL,
                subreddit TEXT NOT NULL,
                author TEXT,
                body TEXT,
                score INTEGER,
                created_utc TIMESTAMP,
                permalink TEXT,
                depth INTEGER,
                fetched_at TIMESTAMP,

                -- Sentiment fields
                positive REAL,
                neutral REAL,
                negative REAL,
                compound REAL,
                sentiment TEXT,
                sentiment_bucket TEXT,
                text_length INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Lightweight schema evolution for existing DBs
        self._ensure_column(conn, 'posts', 'sentiment_bucket', 'TEXT')
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_post_id ON posts(post_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_utc ON posts(created_utc DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sentiment ON posts(sentiment)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_subreddit ON posts(subreddit)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_comment_id ON comments(comment_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_comment_created_utc ON comments(created_utc DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_comment_post_id ON comments(post_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_comment_sentiment ON comments(sentiment)
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized at {self.db_path}")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
        """Add a missing column to a table (best-effort, SQLite-safe)."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if column in existing_cols:
            return
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
    
    def insert_posts(self, posts: List[Dict]) -> int:
        """
        Insert or update posts in the database.
        
        Args:
            posts: List of post dictionaries with sentiment data
            
        Returns:
            Number of posts inserted/updated
        """
        if not posts:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        
        for post in posts:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO posts (
                        post_id, subreddit, title, text, full_text, author,
                        created_utc, score, upvote_ratio, num_comments,
                        url, permalink, source, fetched_at,
                        positive, neutral, negative, compound, sentiment, sentiment_bucket, text_length,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    post['post_id'],
                    post['subreddit'],
                    post['title'],
                    post.get('text', ''),
                    post['full_text'],
                    post['author'],
                    post['created_utc'],
                    post['score'],
                    post['upvote_ratio'],
                    post['num_comments'],
                    post['url'],
                    post['permalink'],
                    post['source'],
                    post['fetched_at'],
                    post.get('positive', 0),
                    post.get('neutral', 0),
                    post.get('negative', 0),
                    post.get('compound', 0),
                    post.get('sentiment', 'Neutral'),
                    post.get('sentiment_bucket', 'Neutral'),
                    post.get('text_length', 0)
                ))
                inserted_count += 1
            except Exception as e:
                print(f"✗ Error inserting post {post.get('post_id')}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        print(f"✓ Inserted/updated {inserted_count} posts")
        return inserted_count

    def insert_comments(self, comments: List[Dict]) -> int:
        """Insert or update comments in the database."""
        if not comments:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        inserted_count = 0

        for c in comments:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO comments (
                        comment_id, post_id, subreddit, author, body, score,
                        created_utc, permalink, depth, fetched_at,
                        positive, neutral, negative, compound, sentiment, sentiment_bucket, text_length,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    c['comment_id'],
                    c['post_id'],
                    c['subreddit'],
                    c.get('author', '[deleted]'),
                    c.get('body', ''),
                    c.get('score', 0),
                    c.get('created_utc'),
                    c.get('permalink', ''),
                    c.get('depth', 0),
                    c.get('fetched_at'),
                    c.get('positive', 0),
                    c.get('neutral', 0),
                    c.get('negative', 0),
                    c.get('compound', 0),
                    c.get('sentiment', 'Neutral'),
                    c.get('sentiment_bucket', 'Neutral'),
                    c.get('text_length', 0),
                ))
                inserted_count += 1
            except Exception as e:
                print(f"✗ Error inserting comment {c.get('comment_id')}: {str(e)}")

        conn.commit()
        conn.close()
        print(f"✓ Inserted/updated {inserted_count} comments")
        return inserted_count
    
    def get_all_posts(self, limit: int = None) -> pd.DataFrame:
        """Get all posts as a pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM posts ORDER BY created_utc DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df

    def get_all_comments(self, limit: int = None) -> pd.DataFrame:
        """Get all comments as a pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM comments ORDER BY created_utc DESC"
        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_sentiment_summary(self) -> Dict:
        """Get summary statistics of sentiment."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_posts,
                SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) as neutral_count,
                AVG(compound) as avg_compound,
                AVG(score) as avg_score
            FROM posts
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            total = row[0]
            return {
                'total_posts': total,
                'positive_count': row[1],
                'negative_count': row[2],
                'neutral_count': row[3],
                'positive_pct': round(row[1] / total * 100, 1) if total > 0 else 0,
                'negative_pct': round(row[2] / total * 100, 1) if total > 0 else 0,
                'neutral_pct': round(row[3] / total * 100, 1) if total > 0 else 0,
                'avg_compound': round(row[4], 3) if row[4] else 0,
                'avg_score': round(row[5], 1) if row[5] else 0
            }
        
        return {}
    
    def get_posts_by_timeframe(self, days: int = 7) -> pd.DataFrame:
        """Get posts from the last N days."""
        conn = sqlite3.connect(self.db_path)
        
        query = f"""
            SELECT * FROM posts 
            WHERE created_utc >= datetime('now', '-{days} days')
            ORDER BY created_utc DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df

    def get_comments_by_timeframe(self, days: int = 7) -> pd.DataFrame:
        """Get comments from the last N days."""
        conn = sqlite3.connect(self.db_path)

        query = f"""
            SELECT * FROM comments
            WHERE created_utc >= datetime('now', '-{days} days')
            ORDER BY created_utc DESC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(created_utc), MAX(created_utc) FROM posts")
        date_range = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(DISTINCT subreddit) FROM posts")
        subreddit_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM comments")
        total_comments = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'earliest_post': date_range[0] if date_range[0] else None,
            'latest_post': date_range[1] if date_range[1] else None,
            'subreddit_count': subreddit_count
        }


if __name__ == "__main__":
    # Test the database
    db = DatabaseHandler()
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")
