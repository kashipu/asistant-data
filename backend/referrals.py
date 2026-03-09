import pandas as pd

def detect_referrals(df: pd.DataFrame):
    """
    Identifies conversations where the bot referred the user to Servílinea.
    Vectorized version.
    """
    if df.empty:
        return pd.DataFrame()

    # Keywords and Channels
    referral_map = {
        "serviline": ["servilínea", "servilinea", "línea de atención", "linea de atencion", "llamar al", "marcar al"],
        "digital": ["banca móvil", "banca movil", "banca virtual", "portal", "página web", "app bolívar", "descarga la app"],
        "office": ["oficina", "sucursal", "punto físico"]
    }
    
    # Combined regex for initial filtering
    all_keywords = [kw for channel in referral_map.values() for kw in channel]
    combined_regex = '|'.join(all_keywords)
    
    # 1. Vectorized Filter: AI messages containing any keyword
    ai_mask = (df['type'] == 'ai') & df['text'].str.contains(combined_regex, case=False, na=False, regex=True)
    if not ai_mask.any():
        return pd.DataFrame()
        
    # Get all threads that have at least one referral message
    referral_msgs = df[ai_mask].copy()
    
    # Optimization: If we only need the thread_ids (as used by get_general_summary), 
    # we could stop early, but we'll maintain the full DataFrame return for compatibility.
    
    # To keep the logic for "first referral context", we use drop_duplicates on thread_id
    # after sorting by rowid (if available) to get the first referral per thread.
    if 'rowid' in referral_msgs.columns:
        referral_msgs.sort_values('rowid', inplace=True)
    
    first_referrals = referral_msgs.drop_duplicates(subset=['thread_id'])
    
    # Map channels vectorized
    first_referrals['channel'] = 'other'
    for channel, kws in referral_map.items():
        channel_regex = '|'.join(kws)
        mask = first_referrals['text'].str.contains(channel_regex, case=False, na=False, regex=True)
        first_referrals.loc[mask, 'channel'] = channel

    # Collecting context (last user message) - This is still slightly tricky to vectorize fully
    # while maintaining "previous message" logic, but we can do a better job than a loop over all threads.
    # However, for get_general_summary, we ONLY care about the thread_id set.
    
    # Return minimal DF if the full context is expensive, OR do a vectorized merge.
    # For now, let's just return the thread_ids and basic info from the referral message itself.
    
    meta_df = first_referrals[['thread_id', 'fecha', 'text', 'channel']].rename(columns={
        'text': 'referral_response',
        'fecha': 'fecha'
    })
    
    # Add sentiment and categories if available (using first message of thread as proxy)
    # We can join with the first row of each thread in the main DF
    thread_first_rows = df.drop_duplicates(subset=['thread_id'])
    
    result = meta_df.merge(thread_first_rows[['thread_id', 'categoria_yaml', 'intencion', 'product_type', 'sentiment']], on='thread_id', how='left')
    result.rename(columns={'categoria_yaml': 'intencion_ref', 'intencion': 'intencion_old'}, inplace=True)
    result['intencion'] = result['intencion_ref'].fillna(result['intencion_old']).fillna('N/A')
    
    # Dummy customer_request to avoid expensive context extraction (usually not used in bulk summary)
    result['customer_request'] = "Contexto simplificado"
    result['msg_count'] = 0 # Placeholder
    
    return result

# Simple cache system
_referrals_cache = None
_last_df_len_ref = 0

def get_referrals_cached(df: pd.DataFrame):
    global _referrals_cache, _last_df_len_ref
    if _referrals_cache is not None and len(df) == _last_df_len_ref:
        return _referrals_cache
    _referrals_cache = detect_referrals(df)
    _last_df_len_ref = len(df)
    return _referrals_cache
