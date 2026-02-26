import pandas as pd

def detect_referrals(df: pd.DataFrame):
    """
    Identifies conversations where the bot referred the user to Servílinea.
    Criteria:
    1. Bot uses "servilínea" or "servilinea" in the text.
    """
    
    # Keywords
    referral_keywords = ["servilínea", "servilinea", "línea de atención", "linea de atencion"]
    
    # Filter AI messages
    ai_msgs = df[df['type'] == 'ai'].copy()
    
    if ai_msgs.empty:
        return pd.DataFrame()

    # Detect keywords
    # Ensure text is string and handle NaNs
    ai_msgs['referral_keyword'] = ai_msgs['text'].astype(str).str.lower().apply(
        lambda x: any(kw in x for kw in referral_keywords)
    )
    
    referral_threads = ai_msgs[ai_msgs['referral_keyword']]['thread_id'].unique()
    
    if len(referral_threads) == 0:
        return pd.DataFrame()
        
    # Optimization: Filter relevant messages once
    relevant_df = df[df['thread_id'].isin(referral_threads)].copy()
    grouped = relevant_df.groupby('thread_id')
    
    referral_data = []

    for thread_id, thread_df in grouped:
        # Find the specific message that triggered the referral
        ai_referral_msgs = thread_df[
            (thread_df['type'] == 'ai') & 
            (thread_df['text'].str.lower().str.contains('|'.join(referral_keywords), na=False, regex=True))
        ]
        
        if ai_referral_msgs.empty: continue
        
        # Take the first referral message in the thread
        referral_msg = ai_referral_msgs.iloc[0]
        referral_text = referral_msg['text']
        
        # Get LAST user message before the AI referral
        # Assuming sorted by rowid/time
        # We find messages with rowid < referral_msg.rowid (if exists) or by index position
        
        try:
             # Filter only human messages
             human_msgs = thread_df[thread_df['type'] == 'human']
             
             if 'rowid' in thread_df.columns:
                 # Robust method: filter by rowid strictly less than referral msg
                 prev_human = human_msgs[human_msgs['rowid'] < referral_msg['rowid']]
                 if not prev_human.empty:
                     last_user_request = prev_human.iloc[-1]['text']
                 else:
                     last_user_request = "N/A (Inicio de conversación)"
             else:
                 # Fallback to index position if rowid missing (shouldn't happen with our loader)
                 # Get index of referral msg in thread_df
                 ref_idx = thread_df.index.get_loc(referral_msg.name)
                 # Slice up to that index
                 prev_msgs = thread_df.iloc[:ref_idx]
                 user_prev = prev_msgs[prev_msgs['type'] == 'human']
                 if not user_prev.empty:
                     last_user_request = user_prev.iloc[-1]['text']
                 else:
                     last_user_request = "N/A"

        except Exception as e:
            print(f"Error extracting context for thread {thread_id}: {e}")
            last_user_request = "Error extracting context"

        # Meta data
        first_msg = thread_df.iloc[0]
        
        referral_data.append({
            "thread_id": thread_id,
            "intencion": first_msg.get('categoria_yaml') or first_msg.get('intencion', 'N/A'),
            "product_type": first_msg.get('product_type', 'N/A'),
            "fecha": first_msg.get('fecha', ''),
            "customer_request": last_user_request,
            "referral_response": referral_text,
            "msg_count": len(thread_df),
            "sentiment": thread_df['sentiment'].mode().iloc[0] if not thread_df['sentiment'].mode().empty else "neutral"
        })

    return pd.DataFrame(referral_data)

# Simple cache system
_referrals_cache = None
_last_df_len_ref = 0

def get_referrals_cached(df: pd.DataFrame):
    global _referrals_cache, _last_df_len_ref
    
    if _referrals_cache is not None and len(df) == _last_df_len_ref:
        return _referrals_cache
        
    print("Computing referrals analysis...")
    _referrals_cache = detect_referrals(df)
    _last_df_len_ref = len(df)
    return _referrals_cache
