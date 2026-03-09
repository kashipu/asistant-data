import pandas as pd
from .referrals import detect_referrals

def get_general_summary(df: pd.DataFrame, start_date: str = None, end_date: str = None):
    """
    ULTRA-OPTIMIZED and THREAD-SAFE version of get_general_summary.
    Uses external series for aggregation to avoid modifying the shared singleton 'df'.
    """
    if df.empty:
        return []

    # 0. Date Filtering (Creates a local copy if filters are applied)
    if start_date or end_date:
        if 'fecha' in df.columns:
            mask = pd.Series(True, index=df.index)
            if start_date: mask &= (df['fecha'] >= pd.to_datetime(start_date))
            if end_date: mask &= (df['fecha'] <= pd.to_datetime(end_date))
            df = df[mask].copy()

    if df.empty:
        return []

    # 1. Determine Thread Metadata (Category, Intention, Product)
    has_yaml = 'categoria_yaml' in df.columns and 'macro_yaml' in df.columns
    
    if has_yaml:
        human_msgs = df[(df['type'] == 'human') & (df['categoria_yaml'].notna())]
        if not human_msgs.empty:
            thread_meta = human_msgs.drop_duplicates(subset=['thread_id'])[['thread_id', 'macro_yaml', 'categoria_yaml']].copy()
            thread_meta.rename(columns={'macro_yaml': 'category', 'categoria_yaml': 'intention'}, inplace=True)
            
            prod_col = 'product_yaml' if 'product_yaml' in human_msgs.columns else 'product_type'
            if prod_col in human_msgs.columns:
                prod_meta = human_msgs[human_msgs[prod_col].notna()].drop_duplicates(subset=['thread_id'])[['thread_id', prod_col]]
                thread_meta = thread_meta.merge(prod_meta.rename(columns={prod_col: 'product'}), on='thread_id', how='left')
            else:
                thread_meta['product'] = 'N/A'
        else:
            thread_meta = pd.DataFrame(columns=['thread_id', 'category', 'intention', 'product'])
    else:
        ai_msgs = df[df['type'] == 'ai']
        if not ai_msgs.empty:
            thread_meta = ai_msgs.drop_duplicates(subset=['thread_id'])[['thread_id', 'product_type', 'intencion']].copy()
            thread_meta.rename(columns={'product_type': 'category', 'intencion': 'intention'}, inplace=True)
            thread_meta['product'] = thread_meta['category']
        else:
            thread_meta = pd.DataFrame(columns=['thread_id', 'category', 'intention', 'product'])

    # 2. Extract mappings for vectorized grouping (No side effects on df)
    cat_map = thread_meta.set_index('thread_id')['category'].to_dict()
    int_map = thread_meta.set_index('thread_id')['intention'].to_dict()
    prd_map = thread_meta.set_index('thread_id')['product'].to_dict()

    # Create temporary Series for grouping (Does NOT modify df)
    tmp_cat = df['thread_id'].map(cat_map).fillna('uncategorized').rename('category')
    tmp_int = df['thread_id'].map(int_map).fillna('sin intención clara').rename('intention')
    tmp_prd = df['thread_id'].map(prd_map).fillna('N/A').rename('product')

    # 3. Message Type & Sentiment indicators as local DataFrames
    stats_df = pd.DataFrame(index=df.index)
    stats_df['is_human'] = (df['type'] == 'human').astype(int)
    stats_df['is_ai'] = (df['type'] == 'ai').astype(int)
    stats_df['is_tool'] = (df['type'] == 'tool').astype(int)
    
    if 'sentiment' in df.columns:
        s_lower = df['sentiment'].str.lower()
        stats_df['s_pos'] = s_lower.isin(['positive', 'positivo']).astype(int)
        stats_df['s_neu'] = s_lower.isin(['neutral', 'neutro', 'neutra']).astype(int)
        stats_df['s_neg'] = s_lower.isin(['negative', 'negativo']).astype(int)
    else:
        stats_df['s_pos'] = stats_df['s_neu'] = stats_df['s_neg'] = 0
    
    stats_df['total_interactions'] = 1 # Each row is an interaction

    # 4. Referrals (Thread-level)
    referrals_df = detect_referrals(df)
    ref_threads = set() if referrals_df.empty else set(referrals_df['thread_id'].unique())
    
    thread_level = thread_meta.copy() if not thread_meta.empty else pd.DataFrame(columns=['thread_id', 'category', 'intention', 'product'])
    
    # If some threads are missing in thread_meta (uncategorized), we add them
    all_threads = df['thread_id'].unique()
    missing_threads = set(all_threads) - set(thread_level['thread_id'])
    if missing_threads:
        missing_df = pd.DataFrame({
            'thread_id': list(missing_threads),
            'category': 'uncategorized',
            'intention': 'sin intención clara',
            'product': 'N/A'
        })
        thread_level = pd.concat([thread_level, missing_df], ignore_index=True)

    thread_level['has_ref'] = thread_level['thread_id'].isin(ref_threads).astype(int)

    # 5. AGGREGATE
    # Group message-level stats using the external Series
    msg_summary = stats_df.groupby([tmp_cat, tmp_int, tmp_prd]).agg({
        'is_human': 'sum',
        'is_ai': 'sum',
        'is_tool': 'sum',
        's_pos': 'sum',
        's_neu': 'sum',
        's_neg': 'sum',
        'total_interactions': 'sum'
    })

    # Group thread-level stats
    thread_summary = thread_level.groupby(['category', 'intention', 'product']).agg({
        'thread_id': 'count',
        'has_ref': 'sum'
    }).rename(columns={'thread_id': 'unique_conversations', 'has_ref': 'servilinea_referrals'})

    # JOIN THEM
    final_df = pd.concat([thread_summary, msg_summary], axis=1).fillna(0).reset_index()
    final_df.rename(columns={
        'is_human': 'human_msgs', 'is_ai': 'ai_msgs', 'is_tool': 'tool_msgs',
        's_pos': 'positive', 's_neu': 'neutral', 's_neg': 'negative'
    }, inplace=True)

    # Sort
    final_df.sort_values(['category', 'unique_conversations'], ascending=[True, False], inplace=True)
    
    return final_df.to_dict(orient='records')

def get_uncategorized_threads(df: pd.DataFrame, page: int = 1, limit: int = 20, start_date: str = None, end_date: str = None):
    if df.empty: return {"data": [], "total": 0, "stats": {"servilinea": 0, "empty_msgs": 0}}
    if start_date or end_date:
        if 'fecha' in df.columns:
            mask = pd.Series(True, index=df.index)
            if start_date: mask &= (df['fecha'] >= pd.to_datetime(start_date))
            if end_date: mask &= (df['fecha'] <= pd.to_datetime(end_date))
            df = df[mask].copy()
    if df.empty: return {"data": [], "total": 0, "stats": {"servilinea": 0, "empty_msgs": 0}}

    if 'categoria_yaml' in df.columns:
        valid_mask = (
            ((df['type'] == 'ai') & (df['product_type'].notna()) & (~df['product_type'].isin(['', 'ninguno', 'nan', 'None', 'sin intencion clara']))) |
            ((df['type'] == 'human') & (df['categoria_yaml'].notna()) & (~df['categoria_yaml'].isin(['', 'uncategorized', 'sin intención clara', 'sin intencion clara', 'nan', 'None'])))
        )
    else:
        valid_mask = (df['type'] == 'ai') & (df['product_type'].notna()) & (~df['product_type'].isin(['', 'ninguno', 'nan', 'None', 'sin intencion clara']))
        
    categorized_threads = set(df[valid_mask]['thread_id'].unique())
    uncategorized_ids = list(set(df['thread_id'].unique()) - categorized_threads)
    if not uncategorized_ids: return {"data": [], "total": 0, "stats": {"servilinea": 0, "empty_msgs": 0}}

    uncat_df = df[df['thread_id'].isin(uncategorized_ids)].copy()
    ref_threads = set(detect_referrals(uncat_df)['thread_id'].unique()) if not detect_referrals(uncat_df).empty else set()
    empty_threads = set(uncat_df[uncat_df['text'].str.strip() == '']['thread_id'].unique())

    # Pagination sorting
    date_map = uncat_df.sort_values('rowid').groupby('thread_id')['fecha'].first().to_dict()
    uncategorized_ids.sort(key=lambda x: str(date_map.get(x, '')), reverse=True)
    
    total = len(uncategorized_ids)
    p_ids = uncategorized_ids[(page-1)*limit:page*limit]
    if not p_ids: return {"data": [], "total": total, "stats": {"servilinea": len(ref_threads), "empty_msgs": len(empty_threads)}}

    p_df = uncat_df[uncat_df['thread_id'].isin(p_ids)]
    msg_counts = p_df.groupby('thread_id').size()
    first_texts = p_df[p_df['type'] == 'human'].sort_values('rowid').groupby('thread_id')['text'].first()
    
    results = [{
        "thread_id": tid, "date": str(date_map.get(tid, '')),
        "msg_count": int(msg_counts.get(tid, 0)), "sample_text": str(first_texts.get(tid, '')),
        "is_servilinea": tid in ref_threads, "has_empty_msg": tid in empty_threads
    } for tid in p_ids]
    return {"data": results, "total": total, "stats": {"servilinea": len(ref_threads), "empty_msgs": len(empty_threads)}}

def get_survey_stats(df: pd.DataFrame, start_date: str = None, end_date: str = None):
    if df.empty: return {"stats": {"total": 0, "useful": 0, "not_useful": 0}, "conversations": []}
    if start_date or end_date:
        if 'fecha' in df.columns:
            mask = pd.Series(True, index=df.index); 
            if start_date: mask &= (df['fecha'] >= pd.to_datetime(start_date))
            if end_date: mask &= (df['fecha'] <= pd.to_datetime(end_date))
            df = df[mask].copy()
    if df.empty: return {"stats": {"total": 0, "useful": 0, "not_useful": 0}, "conversations": []}
    
    s_mask = df['text'].str.contains(r'\[survey\]', case=False, na=False)
    s_df = df[s_mask].copy()
    if s_df.empty: return {"stats": {"total": 0, "useful": 0, "not_useful": 0}, "conversations": []}

    t_low = s_df['text'].str.lower()
    is_not = t_low.str.contains("no me fue útil")
    is_use = t_low.str.contains("me fue útil") & ~is_not
    s_df['status'] = 'unknown'
    s_df.loc[is_not, 'status'] = 'not_useful'
    s_df.loc[is_use, 'status'] = 'useful'
    
    return {
        "stats": {"total": len(s_df), "useful": int(is_use.sum()), "not_useful": int(is_not.sum())},
        "conversations": s_df[['thread_id', 'fecha', 'text', 'status']].rename(columns={'text': 'feedback', 'fecha': 'date'}).to_dict(orient='records')
    }
