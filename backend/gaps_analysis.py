import pandas as pd
import numpy as np

def analyze_gaps_and_referrals(df: pd.DataFrame):
    """
    Analyzes AI knowledge gaps (fallbacks) and referral channel distribution.
    Includes samples and theme summaries.
    """
    if df.empty:
        return {
            "gaps": [],
            "top_themes": [],
            "referrals": {
                "distribution": [],
                "total": 0
            }
        }

    # 1. AI Knowledge Gaps Detection
    fallbacks = [
        "no tengo información", 
        "no cuento con información", 
        "no puedo ayudarte con eso", 
        "no entiendo", 
        "uhm!",
        "lo siento, no puedo ayudarte",
        "no tengo info"
    ]
    
    ai_msgs = df[df['type'] == 'ai'].copy()
    ai_msgs['is_fallback'] = ai_msgs['text'].str.lower().apply(
        lambda x: any(f in str(x).lower() for f in fallbacks)
    )
    
    gap_msgs = ai_msgs[ai_msgs['is_fallback']].copy()
    
    gaps_list = []
    if not gap_msgs.empty:
        for idx, gap_row in gap_msgs.iterrows():
            thread_id = gap_row['thread_id']
            # Find the most recent human message before this fallback
            preceding = df[
                (df['thread_id'] == thread_id) & 
                (df['type'] == 'human') & 
                (df.index < idx)
            ].tail(1)
            
            if not preceding.empty:
                human_msg = preceding.iloc[0]
                gaps_list.append({
                    "user_request": human_msg['text'],
                    "ai_response": gap_row['text'],
                    "category": human_msg.get('categoria_yaml', 'Desconocido'),
                    "macro": human_msg.get('macro_yaml', 'Desconocido'),
                    "thread_id": str(thread_id),
                    "timestamp": str(gap_row.get('created_at', ''))
                })

    # Group gaps and provide samples
    gaps_df = pd.DataFrame(gaps_list)
    formatted_gaps = []
    top_themes = []

    if not gaps_df.empty:
        # Group by category and user_request
        gp = gaps_df.groupby(['macro', 'category', 'user_request'])
        
        # Aggregation: count occurrences and collect ALL thread_ids
        res = gp.agg({
            'thread_id': lambda x: list(x.unique()),
            'timestamp': 'size' # using size for count
        }).reset_index()
        
        res = res.rename(columns={'timestamp': 'count', 'thread_id': 'thread_ids'})
        res = res.sort_values('count', ascending=False).head(100) # Increased head to show more
        formatted_gaps = res.to_dict('records')

        # Top Themes (Categories with most gaps)
        themes_df = gaps_df.groupby(['macro', 'category']).size().reset_index(name='count')
        themes_df = themes_df.sort_values('count', ascending=False).head(10)
        
        for _, row in themes_df.iterrows():
            # Get 3 representative examples for this theme
            examples = gaps_df[gaps_df['category'] == row['category']].head(3)['user_request'].tolist()
            top_themes.append({
                "macro": row['macro'],
                "category": row['category'],
                "count": int(row['count']),
                "examples": examples
            })

    # 2. Referral Channel Classification
    phone_kws = ["servilínea", "servilinea", "teléfono", "telefono", "llamar"]
    digital_kws = ["banca móvil", "banca movil", "app", "web", "portal", "digital", "internet"]
    physical_kws = ["oficina", "sucursal", "corresponsal", "físico", "fisico", "donde estamos", "ubicación"]

    def classify_channel(text):
        text_l = str(text).lower()
        if any(kw in text_l for kw in phone_kws): return "Telefónico (Servilínea)"
        if any(kw in text_l for kw in digital_kws): return "Digital (App/Web)"
        if any(kw in text_l for kw in physical_kws): return "Físico (Oficinas)"
        return "Otros"

    ai_texts = df[df['type'] == 'ai']['text'].str.lower()
    is_ref = ai_texts.apply(lambda x: any(kw in str(x) for kw in (phone_kws + digital_kws + physical_kws)))
    
    ref_msgs = df[df['type'] == 'ai'][is_ref].copy()
    
    # Base for percentages: Total unique conversations in this period
    total_convs = df['thread_id'].nunique()
    
    referral_stats = []
    total_refs = 0
    if not ref_msgs.empty:
        ref_msgs['channel'] = ref_msgs['text'].apply(classify_channel)
        # We want to count HOW MANY CONVERSATIONS were referred to each channel
        channel_conv_counts = ref_msgs.groupby('channel')['thread_id'].nunique()
        total_refs = int(ref_msgs['thread_id'].nunique())
        
        for name, count in channel_conv_counts.items():
            referral_stats.append({
                "channel": name,
                "count": int(count),
                "percentage": round((count / total_convs * 100), 1) if total_convs > 0 else 0
            })

    return {
        "gaps": formatted_gaps,
        "top_themes": top_themes,
        "referrals": {
            "distribution": referral_stats,
            "total_referrals": total_refs,
            "total_conversations": total_convs
        }
    }
