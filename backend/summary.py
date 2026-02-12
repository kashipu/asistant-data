import pandas as pd
from .referrals import detect_referrals

def get_general_summary(df: pd.DataFrame, start_date: str = None, end_date: str = None):
    """
    Generates a summary table aggregated by 'Category' AND 'Intention'.
    Columns: Category, Intention, Conversations, Human Msgs, AI Msgs, Tool Msgs, Positive, Neutral, Negative, Servilínea.
    """
    if df.empty:
        return []

    # 0. Date Filtering
    if start_date or end_date:
        if 'fecha' in df.columns:
            # Create a mask
            mask = pd.Series(True, index=df.index)
            if start_date:
                mask &= (df['fecha'] >= start_date)
            if end_date:
                mask &= (df['fecha'] <= end_date)
            df = df[mask].copy()
    
    if df.empty:
        return []

    # 1. Determine Thread Category AND Intention based on AI messages
    ai_msgs = df[df['type'] == 'ai'].copy()
    
    # Helper to clean strings
    def clean_str(s):
        if pd.isna(s): return None
        s = str(s).strip().lower()
        if s in ['', 'ninguno', 'nan', 'none', 'sin intencion clara']: return None
        return s

    if not ai_msgs.empty:
        ai_msgs['product_type'] = ai_msgs['product_type'].apply(clean_str)
        ai_msgs['intencion'] = ai_msgs['intencion'].apply(clean_str)

    # Dictionary to store thread -> (category, intention)
    thread_metadata = {}
    
    # Group by thread to find mode Category and Mode Intention
    if not ai_msgs.empty:
        # We can do this efficiently by grouping
        grouped_ai = ai_msgs.groupby('thread_id')
        
        for tid, group in grouped_ai:
            # Mode Category
            cat_mode = group['product_type'].mode()
            cat = cat_mode.iloc[0] if not cat_mode.empty else 'uncategorized'
            
            # Mode Intention
            int_mode = group['intencion'].mode()
            intent = int_mode.iloc[0] if not int_mode.empty else 'sin intención clara'
            
            thread_metadata[tid] = (cat or 'uncategorized', intent or 'sin intención clara')

    # 2. Vectorized Aggregation
    
    # Create a DataFrame for Thread Metadata
    # Default to uncategorized
    all_thread_ids = df['thread_id'].unique()
    meta_df = pd.DataFrame(index=all_thread_ids, columns=['category', 'intention'])
    meta_df[:] = ('uncategorized', 'sin intención clara')
    
    # Update with found metadata
    if thread_metadata:
        found_meta = pd.DataFrame.from_dict(thread_metadata, orient='index', columns=['category', 'intention'])
        meta_df.update(found_meta)
        
    meta_df.reset_index(inplace=True)
    meta_df.rename(columns={'index': 'thread_id'}, inplace=True)
    
    # Merge metadata back to main DF to aggregate message-level stats
    # We only need specific columns for aggregation
    # Pre-calculate counts/dummies
    
    # 3. Message Type Counts
    # Faster: Group boolean masks
    type_dummies = pd.get_dummies(df['type'])
    # Ensure columns exist
    for col in ['human', 'ai', 'tool']:
        if col not in type_dummies.columns:
            type_dummies[col] = 0
            
    # Join dummies to df (temporarily) or just group them by thread_id
    # We need to group by (Category, Intention) eventually.
    # So let's merge category/intention to df
    
    df_merged = df.merge(meta_df, on='thread_id', how='left')
    
    # Handle NaNs in category/intention (shouldn't happen due to meta_df init, but safety)
    df_merged['category'] = df_merged['category'].fillna('uncategorized')
    df_merged['intention'] = df_merged['intention'].fillna('sin intención clara')
    
    # Group by Category/Intention for Message Counts
    # We map 'type' column to columns: human_msgs, ai_msgs, tool_msgs
    # pivot_table or groupby unstack
    
    group_cols = ['category', 'intention']
    
    # Aggregations
    # 1. Message counts by type
    # We can simple sum the dummies grouped by [category, intention]
    # But checking 'type' column is cleaner.
    
    # Let's bind dummies to df_merged
    df_merged = pd.concat([df_merged, type_dummies[['human', 'ai', 'tool']]], axis=1)
    
    # 2. Sentiments (only human)
    # create dummies for sentiment
    sent_cols = ['positive', 'neutral', 'negative']
    if 'sentiment' in df.columns:
        # Normalize sentiment
        sents = df['sentiment'].str.lower().map({
            'positive': 'positive', 'positivo': 'positive',
            'neutral': 'neutral', 'neutro': 'neutral', 'neutra': 'neutral',
            'negative': 'negative', 'negativo': 'negative'
        })
        sent_dummies = pd.get_dummies(sents)
        # Rename to ensure english keys
        # Ensure all columns exist
        for col in sent_cols:
            if col not in sent_dummies.columns:
                sent_dummies[col] = 0
    else:
        sent_dummies = pd.DataFrame(0, index=df.index, columns=sent_cols)
        
    df_merged = pd.concat([df_merged, sent_dummies[sent_cols]], axis=1)
    
    # 3. Referrals
    # Referrals are per THREAD. We need to sum them per group.
    # Detect referrals returns a DF of messages or threads? 
    # detect_referrals returns messages DF. 
    # Get thread IDs with referrals
    referrals_df = detect_referrals(df)
    ref_threads = set()
    if not referrals_df.empty:
        ref_threads = set(referrals_df['thread_id'].unique())
        
    # Mark threads with referral in meta_df
    meta_df['servilinea_referrals'] = meta_df['thread_id'].apply(lambda x: 1 if x in ref_threads else 0)
    
    # Now aggregate
    
    # A. Message Level Aggregation (Sums)
    msg_stats = df_merged.groupby(group_cols)[['human', 'ai', 'tool', 'positive', 'neutral', 'negative']].sum()
    
    # B. Thread Level Aggregation (Counts and sums of thread-level props)
    # We aggregate meta_df
    thread_stats = meta_df.groupby(group_cols).agg({
        'thread_id': 'count', # Unique conversations
        'servilinea_referrals': 'sum'
    })
    thread_stats.rename(columns={'thread_id': 'unique_conversations'}, inplace=True)
    
    # C. Total Interactions (Total messages)
    total_interactions = df_merged.groupby(group_cols).size().rename('total_interactions')
    
    # Combine all
    summary_df = pd.concat([thread_stats, msg_stats, total_interactions], axis=1).fillna(0)
    
    # Reset index to turn indices into columns
    summary_df.reset_index(inplace=True)
    # Rename columns to match interface if needed (already match: category, intention, unique_conversations...)
    # human -> human_msgs
    summary_df.rename(columns={
        'human': 'human_msgs',
        'ai': 'ai_msgs',
        'tool': 'tool_msgs'
    }, inplace=True)
    
    # Sort
    summary_df.sort_values(['category', 'unique_conversations'], ascending=[True, False], inplace=True)
    
    return summary_df.to_dict(orient='records')

def get_uncategorized_threads(df: pd.DataFrame, page: int = 1, limit: int = 20, start_date: str = None, end_date: str = None):
    """
    Returns a dict with paginated threads and stats for uncategorized conversations.
    """
    if df.empty:
        return {"data": [], "total": 0, "stats": {"servilinea": 0, "empty_msgs": 0}}

    # 0. Date Filtering
    if start_date or end_date:
        if 'fecha' in df.columns:
            mask = pd.Series(True, index=df.index)
            if start_date:
                mask &= (df['fecha'] >= start_date)
            if end_date:
                mask &= (df['fecha'] <= end_date)
            df = df[mask].copy()

    if df.empty:
        return {"data": [], "total": 0, "stats": {"servilinea": 0, "empty_msgs": 0}}

    # 1. Identify Uncategorized Threads
    # Threads where NO AI message has a valid product_type
    
    # Valid AI messages
    valid_ai = df[
        (df['type'] == 'ai') & 
        (df['product_type'].notna()) & 
        (~df['product_type'].isin(['', 'ninguno', 'nan', 'None', 'sin intencion clara']))
    ]
    categorized_threads = set(valid_ai['thread_id'].unique())
    all_threads = set(df['thread_id'].unique())
    uncategorized_ids = list(all_threads - categorized_threads)
    
    if not uncategorized_ids:
        return {"data": [], "total": 0, "stats": {"servilinea": 0, "empty_msgs": 0}}

    # Filter DF to only uncategorized threads
    uncat_df = df[df['thread_id'].isin(uncategorized_ids)].copy()

    # 2. Calculate Global Stats for Uncategorized
    
    # Servilínea
    referrals_df = detect_referrals(uncat_df)
    servilinea_thread_ids = set()
    if not referrals_df.empty:
        servilinea_thread_ids = set(referrals_df['thread_id'].unique())
    
    # Empty Messages (Threads that have at least one empty content message)
    # Checking for empty 'text' or just whitespace
    empty_msg_threads = uncat_df[uncat_df['text'].str.strip() == '']['thread_id'].unique()
    empty_msg_thread_ids = set(empty_msg_threads)

    stats = {
        "servilinea": len(servilinea_thread_ids),
        "empty_msgs": len(empty_msg_thread_ids)
    }

    # 3. Pagination
    # Sort IDs by date (most recent first)
    # We need a mapping of thread_id -> date to sort
    thread_dates = pd.Series(dtype='object')
    if 'fecha' in uncat_df.columns:
        thread_dates = uncat_df.sort_values('rowid').groupby('thread_id')['fecha'].first()
    
    # Create valid date mapping, default to empty string if missing
    date_map = thread_dates.to_dict()
    
    # Sort uncategorized_ids based on date descending
    uncategorized_ids.sort(key=lambda x: str(date_map.get(x, '')), reverse=True)
    
    total_items = len(uncategorized_ids)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    paginated_ids = uncategorized_ids[start_idx:end_idx]
    
    if not paginated_ids:
        return {"data": [], "total": total_items, "stats": stats}

    # 4. Build Result Data for Current Page
    page_df = uncat_df[uncat_df['thread_id'].isin(paginated_ids)]
    
    # Msg Counts
    msg_counts = page_df.groupby('thread_id').size()
    
    # First Human Text
    human_df = page_df[page_df['type'] == 'human'].sort_values('rowid')
    first_texts = human_df.groupby('thread_id')['text'].first()
    
    results = []
    for tid in paginated_ids:
        results.append({
            "thread_id": tid,
            "date": str(date_map.get(tid, '')),
            "msg_count": int(msg_counts.get(tid, 0)),
            "sample_text": str(first_texts.get(tid, '')),
            "is_servilinea": tid in servilinea_thread_ids,
            "has_empty_msg": tid in empty_msg_thread_ids
        })
        
    return {
        "data": results,
        "total": total_items,
        "stats": stats
    }

def get_survey_stats(df: pd.DataFrame, start_date: str = None, end_date: str = None):
    """
    Analyzes [survey] messages.
    Returns:
        - stats: { total, useful, not_useful }
        - conversations: list of threads with survey responses
    """
    if df.empty:
        return {"stats": {"total": 0, "useful": 0, "not_useful": 0}, "conversations": []}

    # 0. Date Filtering
    if start_date or end_date:
        if 'fecha' in df.columns:
            mask = pd.Series(True, index=df.index)
            if start_date:
                mask &= (df['fecha'] >= start_date)
            if end_date:
                mask &= (df['fecha'] <= end_date)
            df = df[mask].copy()

    if df.empty:
        return {"stats": {"total": 0, "useful": 0, "not_useful": 0}, "conversations": []}
        
    # Filter messages containing [survey]
    survey_msgs = df[df['text'].str.contains(r'\[survey\]', case=False, na=False)].copy()
    
    useful_count = 0
    not_useful_count = 0
    conversations = []
    
    for _, row in survey_msgs.iterrows():
        text = str(row['text']).lower()
        is_useful = "me fue útil" in text and "no me fue útil" not in text
        is_not_useful = "no me fue útil" in text
        
        status = "unknown"
        if is_useful:
            useful_count += 1
            status = "useful"
        elif is_not_useful:
            not_useful_count += 1
            status = "not_useful"
            
        conversations.append({
            "thread_id": row['thread_id'],
            "date": row.get('fecha', ''),
            "feedback": row['text'],
            "status": status
        })
        
    return {
        "stats": {
            "total": len(survey_msgs),
            "useful": useful_count,
            "not_useful": not_useful_count
        },
        "conversations": conversations
    }
