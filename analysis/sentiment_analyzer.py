"""
Sentiment analysis using VADER (Valence Aware Dictionary and sEntiment Reasoner).
VADER is optimized for social media text and doesn't require training.
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List
import re

from config.config import Config


class SentimentAnalyzer:
    """Analyze sentiment of text using VADER."""
    
    def __init__(self):
        """Initialize VADER sentiment analyzer."""
        self.analyzer = SentimentIntensityAnalyzer()
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores and classification
        """
        if not text or len(text.strip()) == 0:
            return self._empty_sentiment()
        
        # Clean text (remove URLs, special chars)
        cleaned_text = self._clean_text(text)
        
        # Get VADER scores
        scores = self.analyzer.polarity_scores(cleaned_text)
        
        # Classify sentiment based on compound score
        sentiment_label = self._classify_sentiment(scores['compound'])
        bucket = self._bucket_sentiment(scores['compound'])
        
        return {
            'positive': round(scores['pos'], 3),
            'neutral': round(scores['neu'], 3),
            'negative': round(scores['neg'], 3),
            'compound': round(scores['compound'], 3),
            'sentiment': sentiment_label,
            'sentiment_bucket': bucket,
            'text_length': len(text)
        }
    
    def analyze_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for multiple posts.
        
        Args:
            posts: List of post dictionaries with 'full_text' key
            
        Returns:
            List of posts with added sentiment data
        """
        analyzed_posts = []
        
        for post in posts:
            text = post.get('full_text', '')
            sentiment = self.analyze_text(text)
            
            # Add sentiment data to post
            post_with_sentiment = {**post, **sentiment}
            analyzed_posts.append(post_with_sentiment)
        
        print(f"✓ Analyzed sentiment for {len(analyzed_posts)} posts")
        return analyzed_posts

    def analyze_items(self, items: List[Dict], text_key: str) -> List[Dict]:
        """Analyze sentiment for a list of dicts using a specific text key."""
        analyzed = []
        for item in items:
            text = item.get(text_key, '')
            sentiment = self.analyze_text(text)
            analyzed.append({**item, **sentiment})
        return analyzed
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis."""
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _classify_sentiment(self, compound_score: float) -> str:
        """
        Classify sentiment based on compound score.
        
        VADER compound score ranges from -1 (most negative) to +1 (most positive)
        """
        if compound_score >= 0.05:
            return 'Positive'
        elif compound_score <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
    
    def _empty_sentiment(self) -> Dict:
        """Return empty sentiment for invalid input."""
        return {
            'positive': 0.0,
            'neutral': 1.0,
            'negative': 0.0,
            'compound': 0.0,
            'sentiment': 'Neutral',
            'sentiment_bucket': 'Neutral',
            'text_length': 0
        }

    def _bucket_sentiment(self, compound_score: float) -> str:
        """Bucket sentiment into 5 levels for breakdown charts."""
        if compound_score >= Config.VERY_POSITIVE_THRESHOLD:
            return 'Very Positive'
        if compound_score >= 0.05:
            return 'Positive'
        if compound_score <= Config.VERY_NEGATIVE_THRESHOLD:
            return 'Very Negative'
        if compound_score <= -0.05:
            return 'Negative'
        return 'Neutral'
    
    def get_summary_stats(self, analyzed_posts: List[Dict]) -> Dict:
        """
        Get summary statistics of sentiment analysis.
        
        Args:
            analyzed_posts: List of posts with sentiment data
            
        Returns:
            Dictionary with summary statistics
        """
        if not analyzed_posts:
            return {}
        
        sentiments = [p['sentiment'] for p in analyzed_posts]
        compounds = [p['compound'] for p in analyzed_posts]
        
        total = len(analyzed_posts)
        positive_count = sentiments.count('Positive')
        negative_count = sentiments.count('Negative')
        neutral_count = sentiments.count('Neutral')
        
        avg_compound = sum(compounds) / total if total > 0 else 0
        
        return {
            'total_posts': total,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_pct': round(positive_count / total * 100, 1),
            'negative_pct': round(negative_count / total * 100, 1),
            'neutral_pct': round(neutral_count / total * 100, 1),
            'avg_compound_score': round(avg_compound, 3)
        }


if __name__ == "__main__":
    # Test the analyzer
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "I absolutely love living in Gurgaon! The infrastructure is amazing.",
        "The traffic in Gurgaon is terrible and getting worse every day.",
        "Just another day at the office.",
        "Gurgaon has great restaurants but the air quality is concerning."
    ]
    
    print("Testing sentiment analyzer:\n")
    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"Text: {text}")
        print(f"Sentiment: {result['sentiment']} (compound: {result['compound']})")
        print(f"Scores - Pos: {result['positive']}, Neu: {result['neutral']}, Neg: {result['negative']}\n")
