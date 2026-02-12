
import pandas as pd

def detect_failures(df: pd.DataFrame):
    """
    Identifies conversations where the bot likely failed.
    Criteria:
    1. Bot uses "failure" phrases (e.g., "no puedo", "lo siento").
    2. User repeats the same message (sign of frustration).
    3. High proportion of negative sentiment.
    """
    
    # 1. Bot keywords
    failure_keywords = [
        "no puedo", "no tengo información", "no estoy seguro", 
        "te recomiendo comunicarte", "no me es posible", "fuera de mi alcance", 
        "no cuento con", "lo siento, no", "no tengo acceso", 
        "intenta más tarde", "error", "no disponible", "no entiendo"
    ]
    
    # Create a mask for bot messages detecting failure keywords
    # Ensure text is string and handle NaNs
    bot_msgs = df[df['type'] == 'ai'].copy()
    if bot_msgs.empty:
        return pd.DataFrame()
        
    bot_msgs['failure_keyword'] = bot_msgs['text'].astype(str).str.lower().apply(
        lambda x: any(kw in x for kw in failure_keywords)
    )
    
    failed_threads_keywords = bot_msgs[bot_msgs['failure_keyword']]['thread_id'].unique()

    # 2. User repetition (heuristic: same text > 1 time in thread by human)
    human_msgs = df[df['type'] == 'human'].copy()
    if not human_msgs.empty:
        # Group by thread and text, count occurrences
        repetition = human_msgs.groupby(['thread_id', 'text']).size().reset_index(name='count')
        failed_threads_repetition = repetition[repetition['count'] > 1]['thread_id'].unique()
    else:
        failed_threads_repetition = []

    # 3. Accumulated Negative Sentiment (> 50% of messages are negative)
    if 'sentiment' in df.columns:
        sentiment_counts = df.groupby(['thread_id', 'sentiment']).size().unstack(fill_value=0)
        if 'negativo' in sentiment_counts.columns:
            sentiment_counts['total'] = sentiment_counts.sum(axis=1)
            sentiment_counts['neg_ratio'] = sentiment_counts['negativo'] / sentiment_counts['total']
            failed_threads_sentiment = sentiment_counts[sentiment_counts['neg_ratio'] > 0.5].index.tolist()
        else:
            failed_threads_sentiment = []
    else:
        failed_threads_sentiment = []

    # Combine all
    all_failed_threads = list(set(failed_threads_keywords) | set(failed_threads_repetition) | set(failed_threads_sentiment))
    
    if not all_failed_threads:
        return pd.DataFrame()

    # Optimization: Fully Vectorized Approach
    # 1. Filter relevant messages once
    relevant_df = df[df['thread_id'].isin(all_failed_threads)].copy()
    
    # 2. Aggregations per thread
    # Sort by time/index to ensure first/last are correct (assuming index is somewhat chronological or use sort_values)
    # relevant_df = relevant_df.sort_index() 
    
    grouped = relevant_df.groupby('thread_id')
    
    # Intention, Product, and Date (from first message)
    first_vals = grouped[['intencion', 'product_type', 'fecha']].first()
    
    # Message Count
    msg_counts = grouped.size().rename('msg_count')
    
    # Last User Message
    last_user_msgs = relevant_df[relevant_df['type'] == 'human'].groupby('thread_id')['text'].last().rename('last_user_message')
    
    # Sentiment (Approximate mode or just most frequent)
    # A fast way to get mode is `agg(pd.Series.mode)`, but validation is needed. 
    # Let's fallback to 'first' if mode fails or is complex, or use a custom fast aggregator.
    # For speed, let's take the sentiment of the last message or the most frequent if easy.
    # We will use a lambda but care for performance.
    def get_mode(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else "neutral"
        
    # Optimizing sentiment mode:
    # calculating mode on groupby can be slow. 
    # Alternative: Count values, sort, take top.
    # For now, let's try the simple lambda, if it's slow we'll optimize.
    sentiments = grouped['sentiment'].agg(get_mode).rename('sentiment')

    # 3. Construct Result DataFrame
    result = pd.concat([first_vals, msg_counts, last_user_msgs, sentiments], axis=1)
    
    # 4. Add Criteria (Vectorized-ish)
    # We have the sets.
    def get_criteria(tid):
        c = []
        if tid in failed_threads_keywords: c.append("Respuesta de incapacidad del bot")
        if tid in failed_threads_repetition: c.append("Usuario repite pregunta")
        if tid in failed_threads_sentiment: c.append("Sentimiento negativo predominante")
        return ", ".join(c)

    result['criteria'] = result.index.map(get_criteria)
    
    # Reset index to have thread_id as column
    result = result.reset_index()
    
    # Fill NAs
    result['last_user_message'] = result['last_user_message'].fillna("N/A")
    result['sentiment'] = result['sentiment'].fillna("neutral")
    
    return result

# Simple cache system
_failures_cache = None
_last_df_len = 0

def get_failures_cached(df: pd.DataFrame):
    global _failures_cache, _last_df_len
    
    # Simple invalidation strategy: if DF length changes, re-compute
    # In a real app with immutable DB loads, this might be enough.
    if _failures_cache is not None and len(df) == _last_df_len:
        return _failures_cache
        
    print("Computing failures analysis...")
    _failures_cache = detect_failures(df)
    _last_df_len = len(df)
    return _failures_cache
