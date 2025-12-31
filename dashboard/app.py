"""
Streamlit dashboard for Reddit sentiment analysis.
Run with: streamlit run dashboard/app.py
"""
import streamlit as st

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="Multi-City Reddit Sentiment Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import sys
import os
import re
from collections import Counter
import logging

try:
    from wordcloud import WordCloud
except Exception:  # pragma: no cover
    WordCloud = None

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_handler import DatabaseHandler
from config.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@st.cache_resource
def start_background_scheduler():
    """Start background data collection scheduler (runs once per app instance)."""
    try:
        from scheduler import DataCollectionScheduler
        
        # Get interval from environment or default to 6 hours
        interval_hours = int(os.getenv('COLLECTION_INTERVAL_HOURS', '6'))
        
        logger.info(f"Starting background scheduler (every {interval_hours} hours)...")
        scheduler = DataCollectionScheduler(interval_hours=interval_hours)
        
        # Start without immediate collection to avoid blocking UI
        # First collection will happen in 1 minute
        scheduler.start(run_immediately=False)
        logger.info("✓ Background scheduler started successfully")
        
        return scheduler
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        return None


# Initialize database
db = DatabaseHandler()

# Start the background scheduler (only runs once due to cache_resource)
# This runs in background and doesn't block UI rendering
try:
    scheduler = start_background_scheduler()
    if scheduler:
        st.sidebar.success("🔄 Auto-update enabled")
        st.sidebar.info("⏱️ First collection in ~1 min, then every 6h")
except Exception as e:
    st.sidebar.warning(f"⚠️ Auto-update disabled: {str(e)}")

# Custom CSS
st.markdown("""
    <style>
    .big-metric {
        font-size: 2rem !important;
        font-weight: bold;
    }
    .positive-text {
        color: #10b981;
    }
    .negative-text {
        color: #ef4444;
    }
    .neutral-text {
        color: #6b7280;
    }
    </style>
""", unsafe_allow_html=True)

# Title  
st.title("🌍 Multi-City Reddit Sentiment Dashboard")
st.markdown("Real-time sentiment analysis across cities worldwide")


STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'from', 'has', 'have',
    'he', 'her', 'his', 'i', 'if', 'in', 'is', 'it', 'its', 'me', 'my', 'no', 'not',
    'of', 'on', 'or', 'our', 'out', 'she', 'so', 'than', 'that', 'the', 'their', 'them',
    'then', 'there', 'they', 'this', 'to', 'up', 'us', 'was', 'we', 'were', 'what',
    'when', 'where', 'which', 'who', 'why', 'will', 'with', 'you', 'your',
    'im', 'dont', 'didnt', 'doesnt', 'cant', 'wont',
}


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r"http\S+|www\.\S+", " ", text.lower())
    tokens = re.findall(r"[a-z']{3,}", text)
    return [t for t in tokens if t not in STOPWORDS]


def top_keywords(texts: list[str], top_n: int = 40) -> Counter:
    counter = Counter()
    for t in texts:
        counter.update(tokenize(t))
    return Counter(dict(counter.most_common(top_n)))


def sentiment_bucket_order() -> list[str]:
    return ['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Refresh button
    if st.button("🔄 Refresh Data", width='stretch'):
        st.rerun()
    
    st.divider()
    
    # City selector
    st.subheader("🌆 Select Cities")
    
    # Get available cities from database
    all_data = db.get_all_posts()
    if not all_data.empty:
        available_cities = sorted(all_data['subreddit'].unique().tolist())
        
        # Map subreddit names to city names
        subreddit_to_city = {v: k for k, v in Config.CITIES.items()}
        city_display_names = [subreddit_to_city.get(s, s.title()) for s in available_cities]
        
        # Multi-select for cities
        selected_city_names = st.multiselect(
            "Cities to Display",
            options=city_display_names,
            default=city_display_names[:3] if len(city_display_names) >= 3 else city_display_names
        )
        
        # Convert back to subreddit names
        city_to_subreddit = {k: v for k, v in Config.CITIES.items()}
        selected_subreddits = [city_to_subreddit.get(c, c.lower()) for c in selected_city_names]
    else:
        selected_subreddits = []
        st.warning("No data available")
    
    st.divider()
    
    # Database stats
    stats = db.get_database_stats()
    st.subheader("📈 Database Stats")
    st.metric("Total Posts", stats.get('total_posts', 0))
    st.metric("Cities", stats.get('subreddit_count', 0))
    
    if stats.get('latest_post'):
        st.caption(f"Latest: {stats['latest_post'][:16]}")
    
    st.divider()
    
    # Time filter
    time_filter = st.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=1
    )
    
    # Convert to days
    time_map = {
        "Last 24 Hours": 1,
        "Last 7 Days": 7,
        "Last 30 Days": 30,
        "All Time": 999999
    }
    days = time_map[time_filter]

    st.divider()
    st.subheader("🔎 Filters")

    include_comments = st.checkbox("Include comment analysis", value=True)

    min_score = st.slider("Min post score", min_value=0, max_value=500, value=0, step=1)
    min_num_comments = st.slider("Min post comment count", min_value=0, max_value=200, value=0, step=1)
    keyword = st.text_input("Keyword contains", value="").strip()

    sentiment_filter = st.multiselect(
        "Sentiment",
        options=["Positive", "Neutral", "Negative"],
        default=["Positive", "Neutral", "Negative"],
    )
    bucket_filter = st.multiselect(
        "Sentiment bucket",
        options=sentiment_bucket_order(),
        default=sentiment_bucket_order(),
    )

    max_top_items = st.slider("Top lists size", min_value=5, max_value=50, value=10, step=5)

# Load data
if days == 999999:
    df = db.get_all_posts()
else:
    df = db.get_posts_by_timeframe(days=days)

# Check if we have data
if df.empty:
    st.warning("⚠️ No posts found in the database. Run the data collection script first!")
    st.info("Run: `python main.py` to fetch and analyze posts")
    st.stop()

# Filter by selected cities
if selected_subreddits:
    df = df[df['subreddit'].isin(selected_subreddits)]
    
    if df.empty:
        st.warning(f"⚠️ No posts found for selected cities: {', '.join(selected_city_names)}")
        st.info("Run: `python main.py` to fetch data for these cities")
        st.stop()

# Convert datetime columns
df['created_utc'] = pd.to_datetime(df['created_utc'])

# Add city display name
subreddit_to_city = {v: k for k, v in Config.CITIES.items()}
df['city'] = df['subreddit'].map(lambda x: subreddit_to_city.get(x, x.title()))

# Apply additional filters
if min_score > 0:
    df = df[df['score'] >= min_score]
if min_num_comments > 0:
    df = df[df['num_comments'] >= min_num_comments]
if keyword:
    df = df[df['full_text'].str.contains(keyword, case=False, na=False)]
if sentiment_filter:
    df = df[df['sentiment'].isin(sentiment_filter)]
if bucket_filter:
    df = df[df['sentiment_bucket'].isin(bucket_filter)]

if df.empty:
    st.warning("⚠️ No posts match the current filters!")
    st.stop()

if include_comments:
    if days == 999999:
        df_comments = db.get_all_comments()
    else:
        df_comments = db.get_comments_by_timeframe(days=days)
    if not df_comments.empty and selected_subreddits:
        df_comments = df_comments[df_comments['subreddit'].isin(selected_subreddits)]
else:
    df_comments = pd.DataFrame()

if not df_comments.empty:
    df_comments['created_utc'] = pd.to_datetime(df_comments['created_utc'])

# Guard for older DBs without sentiment_bucket populated
if 'sentiment_bucket' not in df.columns:
    df['sentiment_bucket'] = df['sentiment']
if not df_comments.empty and 'sentiment_bucket' not in df_comments.columns:
    df_comments['sentiment_bucket'] = df_comments['sentiment']

# Apply filters
df_filtered = df.copy()

df_filtered = df_filtered[df_filtered['score'].fillna(0) >= min_score]
df_filtered = df_filtered[df_filtered['num_comments'].fillna(0) >= min_num_comments]
df_filtered = df_filtered[df_filtered['sentiment'].isin(sentiment_filter)]
df_filtered = df_filtered[df_filtered['sentiment_bucket'].isin(bucket_filter)]

available_sources = sorted([s for s in df_filtered['source'].dropna().unique().tolist()])
with st.sidebar:
    source_filter = st.multiselect("Source", options=available_sources, default=available_sources)

if source_filter:
    df_filtered = df_filtered[df_filtered['source'].isin(source_filter)]

if keyword:
    mask = (
        df_filtered['title'].fillna('').str.contains(keyword, case=False, na=False)
        | df_filtered['text'].fillna('').str.contains(keyword, case=False, na=False)
        | df_filtered['full_text'].fillna('').str.contains(keyword, case=False, na=False)
    )
    df_filtered = df_filtered[mask]

if not df_comments.empty:
    dfc_filtered = df_comments.copy()
    dfc_filtered = dfc_filtered[dfc_filtered['sentiment_bucket'].isin(bucket_filter)]
    if keyword:
        dfc_filtered = dfc_filtered[dfc_filtered['body'].fillna('').str.contains(keyword, case=False, na=False)]
else:
    dfc_filtered = pd.DataFrame()

# Summary metrics
st.header("📊 Overall Sentiment")

col1, col2, col3, col4 = st.columns(4)

total_posts = len(df_filtered)
positive_count = len(df_filtered[df_filtered['sentiment'] == 'Positive'])
negative_count = len(df_filtered[df_filtered['sentiment'] == 'Negative'])
neutral_count = len(df_filtered[df_filtered['sentiment'] == 'Neutral'])

with col1:
    st.metric("Total Posts", total_posts)

with col2:
    positive_pct = (positive_count / total_posts * 100) if total_posts > 0 else 0
    st.metric("😊 Positive", f"{positive_pct:.1f}%", delta=f"{positive_count} posts")

with col3:
    negative_pct = (negative_count / total_posts * 100) if total_posts > 0 else 0
    st.metric("😞 Negative", f"{negative_pct:.1f}%", delta=f"{negative_count} posts")

with col4:
    neutral_pct = (neutral_count / total_posts * 100) if total_posts > 0 else 0
    st.metric("😐 Neutral", f"{neutral_pct:.1f}%", delta=f"{neutral_count} posts")

# City comparison (if multiple cities selected)
if len(selected_city_names) > 1:
    st.header("🏙️ City Comparison")
    
    # Calculate sentiment by city
    city_sentiment = df_filtered.groupby(['city', 'sentiment']).size().reset_index(name='count')
    city_totals = df_filtered.groupby('city').size().reset_index(name='total')
    city_sentiment = city_sentiment.merge(city_totals, on='city')
    city_sentiment['percentage'] = (city_sentiment['count'] / city_sentiment['total'] * 100).round(1)
    
    # Create comparison bar chart
    fig_comparison = px.bar(
        city_sentiment,
        x='city',
        y='percentage',
        color='sentiment',
        color_discrete_map={'Positive': '#10b981', 'Negative': '#ef4444', 'Neutral': '#6b7280'},
        labels={'city': 'City', 'percentage': 'Percentage (%)', 'sentiment': 'Sentiment'},
        title='Sentiment Distribution by City',
        barmode='group'
    )
    
    fig_comparison.update_layout(height=400)
    st.plotly_chart(fig_comparison, width="stretch")
    
    # Average sentiment score by city
    city_avg_sentiment = df_filtered.groupby('city')['compound'].mean().reset_index()
    city_avg_sentiment = city_avg_sentiment.sort_values('compound', ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_avg = px.bar(
            city_avg_sentiment,
            x='city',
            y='compound',
            labels={'city': 'City', 'compound': 'Average Sentiment Score'},
            title='Average Sentiment Score by City',
            color='compound',
            color_continuous_scale=['#ef4444', '#6b7280', '#10b981']
        )
        fig_avg.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_avg, width="stretch")
    
    with col2:
        st.subheader("🏆 City Rankings")
        for idx, row in city_avg_sentiment.iterrows():
            emoji = "😊" if row['compound'] > 0.05 else "😞" if row['compound'] < -0.05 else "😐"
            st.metric(
                f"{emoji} {row['city']}",
                f"{row['compound']:.3f}",
                delta=None
            )

# Sentiment distribution
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Sentiment Distribution")
    
    sentiment_counts = df_filtered['sentiment'].value_counts()
    colors = {'Positive': '#10b981', 'Negative': '#ef4444', 'Neutral': '#6b7280'}
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=sentiment_counts.index,
        values=sentiment_counts.values,
        marker=dict(colors=[colors.get(s, '#6b7280') for s in sentiment_counts.index]),
        hole=0.4
    )])
    
    fig_pie.update_layout(
        showlegend=True,
        height=350,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    
    st.plotly_chart(fig_pie, width='stretch')

with col2:
    st.subheader("Sentiment Score Distribution")
    
    fig_hist = px.histogram(
        df_filtered,
        x='compound',
        nbins=30,
        color='sentiment',
        color_discrete_map=colors,
        labels={'compound': 'Compound Sentiment Score', 'count': 'Number of Posts'}
    )
    
    fig_hist.update_layout(
        showlegend=True,
        height=350,
        margin=dict(t=30, b=40, l=0, r=0)
    )
    
    st.plotly_chart(fig_hist, width='stretch')

# Sentiment bucket breakdown
st.subheader("🧩 Sentiment Breakdown")
bucket_counts = df_filtered['sentiment_bucket'].value_counts().reindex(sentiment_bucket_order(), fill_value=0)
fig_bucket = px.bar(
    x=bucket_counts.index,
    y=bucket_counts.values,
    labels={'x': 'Sentiment bucket', 'y': 'Posts'},
)
fig_bucket.update_layout(height=320, margin=dict(t=30, b=40, l=0, r=0))
st.plotly_chart(fig_bucket, width='stretch')

avg_components = df_filtered[['positive', 'neutral', 'negative']].fillna(0).mean().reset_index()
avg_components.columns = ['component', 'avg']
fig_components = px.bar(
    avg_components,
    x='component',
    y='avg',
    labels={'component': 'VADER component', 'avg': 'Average'},
)
fig_components.update_layout(height=280, margin=dict(t=10, b=30, l=0, r=0))
st.plotly_chart(fig_components, width='stretch')

# Timeline
st.subheader("📈 Sentiment Over Time")

# Daily counts by sentiment
df_filtered['date'] = df_filtered['created_utc'].dt.date
daily_sentiment = df_filtered.groupby(['date', 'sentiment']).size().reset_index(name='count')

fig_timeline = px.line(
    daily_sentiment,
    x='date',
    y='count',
    color='sentiment',
    color_discrete_map=colors,
    labels={'date': 'Date', 'count': 'Number of Posts', 'sentiment': 'Sentiment'}
)
fig_timeline.update_layout(height=380, hovermode='x unified')
st.plotly_chart(fig_timeline, width='stretch')

# Historical trend: avg compound + rolling
daily_avg = (
    df_filtered
    .set_index('created_utc')
    .resample('D')
    .agg(avg_compound=('compound', 'mean'), posts=('post_id', 'count'))
    .reset_index()
)
daily_avg['rolling_7d'] = daily_avg['avg_compound'].rolling(7, min_periods=1).mean()

fig_avg = go.Figure()
fig_avg.add_trace(go.Scatter(x=daily_avg['created_utc'], y=daily_avg['avg_compound'], name='Daily avg', mode='lines'))
fig_avg.add_trace(go.Scatter(x=daily_avg['created_utc'], y=daily_avg['rolling_7d'], name='7d rolling', mode='lines'))
fig_avg.update_layout(height=320, margin=dict(t=30, b=40, l=0, r=0), yaxis_title='Avg compound')
st.plotly_chart(fig_avg, width='stretch')

fig_vol = px.bar(daily_avg, x='created_utc', y='posts', labels={'created_utc': 'Date', 'posts': 'Posts'})
fig_vol.update_layout(height=260, margin=dict(t=10, b=40, l=0, r=0))
st.plotly_chart(fig_vol, width='stretch')

# Engagement metrics
st.subheader("📣 Engagement Metrics")
df_eng = df_filtered.copy()
df_eng['score'] = df_eng['score'].fillna(0)
df_eng['num_comments'] = df_eng['num_comments'].fillna(0)
df_eng['engagement'] = df_eng['score'] + (df_eng['num_comments'] * 2)

col1, col2 = st.columns([1, 1])
with col1:
    fig_scatter = px.scatter(
        df_eng,
        x='compound',
        y='score',
        color='sentiment',
        color_discrete_map=colors,
        size='num_comments',
        hover_data=['title', 'num_comments'],
        labels={'compound': 'Sentiment (compound)', 'score': 'Post score', 'num_comments': 'Comments'}
    )
    fig_scatter.update_layout(height=380, margin=dict(t=30, b=40, l=0, r=0))
    st.plotly_chart(fig_scatter, width='stretch')

with col2:
    fig_eng_hist = px.histogram(df_eng, x='engagement', nbins=30, labels={'engagement': 'Engagement score'})
    fig_eng_hist.update_layout(height=380, margin=dict(t=30, b=40, l=0, r=0))
    st.plotly_chart(fig_eng_hist, width='stretch')

# Better visualizations: day/hour heatmap
st.subheader("🗓️ Time-of-day Sentiment")
df_hm = df_filtered.copy()
df_hm['hour'] = df_hm['created_utc'].dt.hour
df_hm['dow'] = df_hm['created_utc'].dt.day_name()
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

heat = (
    df_hm
    .groupby(['dow', 'hour'])['compound']
    .mean()
    .reset_index()
    .pivot(index='dow', columns='hour', values='compound')
    .reindex(dow_order)
)
fig_heat = px.imshow(
    heat,
    aspect='auto',
    labels=dict(x='Hour', y='Day of week', color='Avg compound'),
)
fig_heat.update_layout(height=360, margin=dict(t=30, b=20, l=0, r=0))
st.plotly_chart(fig_heat, width='stretch')

# Word clouds + top keywords
st.header("☁️ Word Clouds & Top Keywords")

tab_posts, tab_comments = st.tabs(["Posts", "Comments"])
with tab_posts:
    texts = df_filtered['full_text'].fillna('').tolist()
    kw = top_keywords(texts, top_n=40)
    if WordCloud is not None and len(kw) > 0:
        wc = WordCloud(width=900, height=450, background_color='white').generate_from_frequencies(dict(kw))
        st.image(wc.to_array(), caption="Top post keywords")
    else:
        st.info("WordCloud not available; showing keyword bar chart instead.")

    if len(kw) > 0:
        kw_df = pd.DataFrame({'keyword': list(kw.keys()), 'count': list(kw.values())})
        fig_kw = px.bar(kw_df, x='count', y='keyword', orientation='h', labels={'count': 'Frequency', 'keyword': ''})
        fig_kw.update_layout(height=520, margin=dict(t=10, b=20, l=0, r=0))
        st.plotly_chart(fig_kw, width='stretch')

with tab_comments:
    if dfc_filtered.empty:
        st.info("No comments loaded for the current time range/filters.")
    else:
        texts = dfc_filtered['body'].fillna('').tolist()
        kw = top_keywords(texts, top_n=40)
        if WordCloud is not None and len(kw) > 0:
            wc = WordCloud(width=900, height=450, background_color='white').generate_from_frequencies(dict(kw))
            st.image(wc.to_array(), caption="Top comment keywords")
        else:
            st.info("WordCloud not available; showing keyword bar chart instead.")

        if len(kw) > 0:
            kw_df = pd.DataFrame({'keyword': list(kw.keys()), 'count': list(kw.values())})
            fig_kw = px.bar(kw_df, x='count', y='keyword', orientation='h', labels={'count': 'Frequency', 'keyword': ''})
            fig_kw.update_layout(height=520, margin=dict(t=10, b=20, l=0, r=0))
            st.plotly_chart(fig_kw, width='stretch')

# Comment analysis
if include_comments:
    st.header("💬 Comment Analysis")
    if dfc_filtered.empty:
        st.info("No comments found for the selected range/filters.")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            c_sent_counts = dfc_filtered['sentiment'].value_counts()
            fig_cpie = go.Figure(data=[go.Pie(
                labels=c_sent_counts.index,
                values=c_sent_counts.values,
                hole=0.4
            )])
            fig_cpie.update_layout(height=320, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_cpie, width='stretch')

        with c2:
            fig_chist = px.histogram(
                dfc_filtered,
                x='compound',
                nbins=30,
                color='sentiment',
                color_discrete_map=colors,
                labels={'compound': 'Comment compound score'}
            )
            fig_chist.update_layout(height=320, margin=dict(t=30, b=40, l=0, r=0))
            st.plotly_chart(fig_chist, width='stretch')

        st.subheader("Most negative comments")
        worst = dfc_filtered.nsmallest(max_top_items, 'compound')
        for _, row in worst.iterrows():
            preview = (row.get('body') or '')[:180].replace('\n', ' ')
            st.markdown(f"- ({row['compound']:.3f}) {preview}…  [link]({row.get('permalink', '')})")

# Top posts
st.header("🔥 Top Posts")

tab1, tab2, tab3 = st.tabs(["Most Positive", "Most Negative", "Most Popular"])

with tab1:
    positive_posts = df_filtered[df_filtered['sentiment'] == 'Positive'].nlargest(max_top_items, 'compound')
    for _, post in positive_posts.iterrows():
        with st.expander(f"⬆️ {post['score']} | {post['title'][:80]}..."):
            st.markdown(f"**Sentiment Score:** {post['compound']:.3f}")
            st.markdown(f"**Author:** u/{post['author']}")
            st.markdown(f"**Posted:** {post['created_utc']}")
            st.markdown(f"**Comments:** {post['num_comments']}")
            if post['text']:
                st.markdown(f"**Text:** {post['text'][:300]}...")
            st.markdown(f"[View on Reddit]({post['permalink']})")

with tab2:
    negative_posts = df_filtered[df_filtered['sentiment'] == 'Negative'].nsmallest(max_top_items, 'compound')
    for _, post in negative_posts.iterrows():
        with st.expander(f"⬆️ {post['score']} | {post['title'][:80]}..."):
            st.markdown(f"**Sentiment Score:** {post['compound']:.3f}")
            st.markdown(f"**Author:** u/{post['author']}")
            st.markdown(f"**Posted:** {post['created_utc']}")
            st.markdown(f"**Comments:** {post['num_comments']}")
            if post['text']:
                st.markdown(f"**Text:** {post['text'][:300]}...")
            st.markdown(f"[View on Reddit]({post['permalink']})")

with tab3:
    popular_posts = df_filtered.nlargest(max_top_items, 'score')
    for _, post in popular_posts.iterrows():
        sentiment_emoji = {'Positive': '😊', 'Negative': '😞', 'Neutral': '😐'}
        with st.expander(f"⬆️ {post['score']} | {sentiment_emoji[post['sentiment']]} | {post['title'][:80]}..."):
            st.markdown(f"**Sentiment:** {post['sentiment']} ({post['compound']:.3f})")
            st.markdown(f"**Author:** u/{post['author']}")
            st.markdown(f"**Posted:** {post['created_utc']}")
            st.markdown(f"**Comments:** {post['num_comments']}")
            if post['text']:
                st.markdown(f"**Text:** {post['text'][:300]}...")
            st.markdown(f"[View on Reddit]({post['permalink']})")

# Footer
st.divider()
cities_str = ', '.join([f"r/{s}" for s in selected_subreddits]) if selected_subreddits else "No cities selected"
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data sources: {cities_str} | Filters applied: {len(df_filtered)}/{len(df)} posts")
