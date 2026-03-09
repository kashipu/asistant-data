import pandas as pd
from .referrals import detect_referrals

def get_qualitative_insights(df: pd.DataFrame):
    """
    Returns high-level qualitative insights with the nested structure expected by the frontend.
    """
    if df.empty:
        return {
            "conversations": {"total": 0, "with_referral": 0, "referral_pct": 0},
            "messages": {
                "total": 0, "human": 0, "human_pct": 0, "ai": 0, "ai_pct": 0, "tool": 0, "tool_pct": 0,
                "avg_per_conv": 0
            },
            "referrals": {"total": 0, "pct": 0},
            "summary": {
                "sentiment_distribution": {
                    "positive": 0, "positive_pct": 0, "neutral": 0, "neutral_pct": 0, "negative": 0, "negative_pct": 0
                },
                "top_categories": [],
                "top_intentions": [],
                "top_products": []
            },
            "topics": {}
        }

    total_convs = int(df['thread_id'].nunique())
    total_msgs = len(df)
    
    # Message type counts
    types = df['type'].value_counts()
    human_cnt = int(types.get('human', 0))
    ai_cnt = int(types.get('ai', 0))
    tool_cnt = int(types.get('tool', 0))

    # Referrals
    referrals_df = detect_referrals(df)
    referral_convs = int(referrals_df['thread_id'].nunique()) if not referrals_df.empty else 0
    referral_pct = round((referral_convs / total_convs * 100), 1) if total_convs > 0 else 0

    # Sentiments
    stats = {"positive": 0, "neutral": 0, "negative": 0}
    if 'sentiment' in df.columns:
        s_lower = df['sentiment'].str.lower()
        stats["positive"] = int(s_lower.isin(['positive', 'positivo']).sum())
        stats["neutral"] = int(s_lower.isin(['neutral', 'neutro', 'neutra']).sum())
        stats["negative"] = int(s_lower.isin(['negative', 'negativo']).sum())
    
    total_sent = sum(stats.values())

    # Topics (Proxy)
    topics = {}
    if 'macro_yaml' in df.columns:
        top_topics = df[df['type'] == 'human']['macro_yaml'].value_counts(normalize=True).head(3) * 100
        topics = {str(k): round(float(v), 1) for k, v in top_topics.items()}

    # Helper for top lists
    def get_top_list(col):
        if col not in df.columns: return []
        counts = df[df['type'] == 'human'][col].value_counts().head(5)
        return [{"name": str(k), "count": int(v)} for k, v in counts.items()]

    # Build Response
    return {
        "conversations": {
            "total": total_convs,
            "with_referral": referral_convs,
            "referral_pct": referral_pct
        },
        "messages": {
            "total": total_msgs,
            "human": human_cnt,
            "human_pct": round((human_cnt / total_msgs * 100), 1) if total_msgs > 0 else 0,
            "ai": ai_cnt,
            "ai_pct": round((ai_cnt / total_msgs * 100), 1) if total_msgs > 0 else 0,
            "tool": tool_cnt,
            "tool_pct": round((tool_cnt / total_msgs * 100), 1) if total_msgs > 0 else 0,
            "avg_per_conv": round(total_msgs / total_convs, 1) if total_convs > 0 else 0
        },
        "referrals": {
            "total": referral_convs,
            "pct": referral_pct
        },
        "summary": {
            "sentiment_distribution": {
                "positive": stats["positive"],
                "positive_pct": round((stats["positive"] / total_sent * 100), 1) if total_sent > 0 else 0,
                "neutral": stats["neutral"],
                "neutral_pct": round((stats["neutral"] / total_sent * 100), 1) if total_sent > 0 else 0,
                "negative": stats["negative"],
                "negative_pct": round((stats["negative"] / total_sent * 100), 1) if total_sent > 0 else 0
            },
            "top_categories": get_top_list('macro_yaml'),
            "top_intentions": get_top_list('categoria_yaml'),
            "top_products": get_top_list('product_yaml') if 'product_yaml' in df.columns else get_top_list('product_type')
        },
        "topics": topics
    }

def get_category_insights(df: pd.DataFrame, category: str):
    """
    Extremely detailed category deep dive.
    """
    if df.empty: return {}
    
    if 'macro_yaml' in df.columns:
        cat_df = df[(df['macro_yaml'] == category) | (df['categoria_yaml'] == category)].copy()
    else:
        cat_df = df[df['intencion'] == category].copy()
        
    if cat_df.empty: return {"category": category, "msg_count": 0, "thread_count": 0}

    total_msgs = len(cat_df)
    total_convs = int(cat_df['thread_id'].nunique())
    types = cat_df['type'].value_counts()
    human_cnt = int(types.get('human', 0))
    
    ref_df = detect_referrals(cat_df)
    ref_cnt = int(ref_df['thread_id'].nunique()) if not ref_df.empty else 0

    # Frequent messages with representative thread_ids
    def get_freq_msgs(sub_df, limit=5):
        if sub_df.empty: return []
        counts = sub_df['text'].value_counts().head(limit)
        results = []
        for text, count in counts.items():
            # Pick a sample thread_id for this text
            sample_tid = sub_df[sub_df['text'] == text]['thread_id'].iloc[0]
            results.append({"text": str(text), "count": int(count), "thread_id": str(sample_tid)})
        return results

    frequent_messages = get_freq_msgs(cat_df[cat_df['type'] == 'human'])
    frequent_messages_ai = get_freq_msgs(cat_df[cat_df['type'] == 'ai'])

    # Internal Distribution
    subcats = []
    if 'categoria_yaml' in cat_df.columns:
        counts = cat_df[cat_df['type'] == 'human']['categoria_yaml'].value_counts().head(10)
        subcats = [{"name": str(k), "count": int(v)} for k, v in counts.items()]
        
    prods = []
    prod_col = 'product_yaml' if 'product_yaml' in cat_df.columns else 'product_type'
    if prod_col in cat_df.columns:
        counts = cat_df[cat_df['type'] == 'human'][prod_col].value_counts().head(10)
        prods = [{"name": str(k), "count": int(v)} for k, v in counts.items()]

    return {
        "category": category,
        "messages": {
            "total": total_msgs,
            "human": human_cnt,
            "human_pct": round((human_cnt / total_msgs * 100), 1) if total_msgs > 0 else 0
        },
        "referrals": {
            "total": ref_cnt
        },
        "frequent_messages": frequent_messages,
        "frequent_messages_ai": frequent_messages_ai,
        "distribution": {
            "subcategories": subcats,
            "products": prods
        }
    }
